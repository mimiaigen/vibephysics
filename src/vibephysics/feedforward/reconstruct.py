"""Unified feedforward reconstruction orchestrator and CLI."""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator

try:
    import torch  # noqa: F401
    import torchvision  # noqa: F401
except ImportError:
    pass

from .common import (
    DEFAULT_LINGBOT_MAP_MODEL,
    DEFAULT_VIDEO_FPS,
    IMAGE_EXTENSIONS,
    VIDEO_EXTRACT_FPS_FILE,
    discover_images,
    get_vram_gb,
    is_lingbot_map_engine,
    is_vggt_omega_engine,
    persist_preprocessed_frames,
    resolve_confidence_threshold,
)
from .config import FEEDFORWARD_ENGINES
from .schema import save_prediction, save_reconstruct_config

VIDEO_EXTENSIONS = {".mov", ".mp4", ".avi", ".mkv", ".webm", ".m4v", ".MOV", ".MP4", ".MKV", ".WEBM", ".M4V"}


def is_video_file(path: Path) -> bool:
    return path.is_file() and path.suffix in VIDEO_EXTENSIONS


def looks_like_video_path(path: Path) -> bool:
    return path.suffix in VIDEO_EXTENSIONS


def write_extract_fps(frames_dir: Path, fps: float) -> None:
    path = Path(frames_dir) / VIDEO_EXTRACT_FPS_FILE
    path.write_text(f"{float(fps):g}\n")


def read_extract_fps(frames_dir: Path) -> float | None:
    path = Path(frames_dir) / VIDEO_EXTRACT_FPS_FILE
    if not path.is_file():
        return None
    try:
        return float(path.read_text().strip())
    except ValueError:
        return None


def resolve_source_video_fps(image_path: Path, config_fps: float | None = None) -> float:
    """FPS used when the source video was sampled into frames (for animation timing)."""
    image_path = Path(image_path).absolute()
    if image_path.is_dir():
        recorded = read_extract_fps(image_path)
        if recorded is not None:
            return recorded
    if config_fps is not None:
        return float(config_fps)
    return DEFAULT_VIDEO_FPS


def default_video_frames_dir(video_path: Path) -> Path:
    video_path = Path(video_path).absolute()
    return video_path.parent / "output" / video_path.stem


def existing_frames_in_dir(frames_dir: Path) -> list[Path] | None:
    """Return sorted image paths when a frame folder already has usable images."""
    frames_dir = Path(frames_dir).absolute()
    if not frames_dir.is_dir():
        return None
    try:
        images = discover_images(frames_dir)
    except (ValueError, FileNotFoundError):
        return None
    return images or None


def _log_reusing_frames(
    frames_dir: Path,
    num_frames: int,
    extract_fps: float,
    verbose: bool,
) -> None:
    if not verbose:
        return
    recorded = read_extract_fps(frames_dir)
    if recorded is not None:
        print(
            f"--- [vibephysics] Using {num_frames} existing frames in {frames_dir} "
            f"(extracted at {recorded:g} fps) ---"
        )
        if abs(recorded - extract_fps) > 1e-6:
            print(
                f"--- [vibephysics] Note: config video.fps={extract_fps:g} ignored; "
                f"animation uses recorded {recorded:g} fps ---"
            )
    else:
        print(
            f"--- [vibephysics] Using {num_frames} existing frames in {frames_dir} "
            f"(no {VIDEO_EXTRACT_FPS_FILE}; set video.fps to match extraction, default {extract_fps:g}) ---"
        )


def extract_video_frames(
    video_path: Path,
    output_dir: Path | None = None,
    fps: float | None = None,
    quality: int = 2,
    verbose: bool = True,
) -> Path:
    video_path = Path(video_path).absolute()
    if output_dir is None:
        output_dir = default_video_frames_dir(video_path)
    output_dir = Path(output_dir).absolute()

    extract_fps = DEFAULT_VIDEO_FPS if fps is None else float(fps)
    existing_images = existing_frames_in_dir(output_dir)
    if existing_images is not None:
        _log_reusing_frames(output_dir, len(existing_images), extract_fps, verbose)
        return output_dir

    if not video_path.is_file():
        raise FileNotFoundError(f"Video file does not exist: {video_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    output_pattern = output_dir / "frame_%04d.jpg"
    vf_parts = [f"fps={extract_fps}"]
    cmd = ["ffmpeg", "-i", str(video_path), "-q:v", str(quality)]
    if vf_parts:
        cmd.extend(["-vf", ",".join(vf_parts)])
    cmd.extend([str(output_pattern), "-y"])

    if verbose:
        print(f"--- [vibephysics] Extracting frames from {video_path.name} at {extract_fps:g} fps ---")
        print(f"Running: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True, capture_output=not verbose)
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg not found. Install ffmpeg to use video input.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ffmpeg failed to extract frames from {video_path}") from exc

    extracted = sorted(output_dir.glob("frame_*.jpg"))
    if not extracted:
        raise RuntimeError(f"No frames extracted from {video_path}")
    write_extract_fps(output_dir, extract_fps)
    if verbose:
        print(f"--- [vibephysics] Extracted {len(extracted)} frames to {output_dir} ---")
    return output_dir


def resolve_input(
    input_path: str | Path,
    video_fps: float | None = None,
    video_quality: int = 2,
    frames_dir: Path | None = None,
    verbose: bool = True,
) -> Path:
    """Resolve feedforward input to an image folder or single image path."""
    input_path = Path(input_path).absolute()

    if input_path.is_dir():
        return input_path

    if input_path.is_file() and input_path.suffix.lower() in {ext.lower() for ext in IMAGE_EXTENSIONS}:
        return input_path

    if looks_like_video_path(input_path):
        target_dir = Path(frames_dir).absolute() if frames_dir else default_video_frames_dir(input_path)
        extract_fps = DEFAULT_VIDEO_FPS if video_fps is None else float(video_fps)
        existing_images = existing_frames_in_dir(target_dir)
        if existing_images is not None:
            _log_reusing_frames(target_dir, len(existing_images), extract_fps, verbose)
            return target_dir
        if not input_path.is_file():
            raise FileNotFoundError(f"Video file does not exist: {input_path}")
        return extract_video_frames(
            input_path,
            output_dir=target_dir,
            fps=video_fps,
            quality=video_quality,
            verbose=verbose,
        )

    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    raise ValueError(
        f"Unsupported input: {input_path}. "
        "Provide a video (.mov, .mp4, ...), an image folder, or a single image file."
    )


def prepare_output_directory(
    image_path: Path,
    output_path: Path | None = None,
    engine: str = "lingbot_map",
    verbose: bool = True,
) -> Path:
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = image_path.parent / "feedforward_output" / f"{engine}_{timestamp}"

    output_path = Path(output_path).absolute()
    if verbose:
        print(f"--- [vibephysics] Preparing {engine} reconstruction in: {output_path} ---")

    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def _process_rss_bytes() -> int:
    if sys.platform == "linux":
        page_size = os.sysconf("SC_PAGE_SIZE")
        with open("/proc/self/statm") as handle:
            return int(handle.read().split()[1]) * page_size

    if sys.platform == "darwin":
        proc_pidtaskinfo = 4
        libproc = ctypes.CDLL("/usr/lib/libproc.dylib")

        class ProcTaskInfo(ctypes.Structure):
            _fields_ = [
                ("pfi_virtual_size", ctypes.c_uint64),
                ("pfi_resident_size", ctypes.c_uint64),
                ("pfi_total_user", ctypes.c_uint64),
                ("pfi_total_system", ctypes.c_uint64),
                ("pfi_threads_user", ctypes.c_uint64),
                ("pfi_threads_system", ctypes.c_uint64),
                ("pfi_policy", ctypes.c_int32),
                ("pfi_faults", ctypes.c_int32),
                ("pfi_pageins", ctypes.c_int32),
                ("pfi_cow_faults", ctypes.c_int32),
                ("pfi_messages_sent", ctypes.c_int32),
                ("pfi_messages_received", ctypes.c_int32),
                ("pfi_syscalls_mach", ctypes.c_int32),
                ("pfi_syscalls_unix", ctypes.c_int32),
                ("pfi_csw", ctypes.c_int32),
                ("pfi_threadnum", ctypes.c_int32),
                ("pfi_numrunning", ctypes.c_int32),
                ("pfi_priority", ctypes.c_int32),
            ]

        info = ProcTaskInfo()
        ret = libproc.proc_pidinfo(
            os.getpid(),
            proc_pidtaskinfo,
            0,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if ret == ctypes.sizeof(info):
            return int(info.pfi_resident_size)

    raise OSError(f"Process RSS is unavailable on platform: {sys.platform}")


def _format_bytes(num_bytes: int | None) -> str:
    if num_bytes is None:
        return "—"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.0f} KB"
    if num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"
    return f"{num_bytes / (1024 * 1024 * 1024):.2f} GB"


def _format_seconds(seconds: float) -> str:
    if seconds < 1.0:
        return f"{seconds * 1000:.0f} ms"
    if seconds < 60.0:
        return f"{seconds:.1f} s"
    minutes, remainder = divmod(seconds, 60.0)
    if minutes < 60.0:
        return f"{minutes:.0f}m {remainder:.1f}s"
    hours, minutes = divmod(minutes, 60.0)
    return f"{hours:.0f}h {minutes:.0f}m"


class _MemorySampler:
    def __init__(self, interval_s: float = 0.1) -> None:
        self._interval_s = interval_s
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.peak_rss_bytes = 0

    def start(self) -> None:
        try:
            self.peak_rss_bytes = _process_rss_bytes()
        except OSError:
            self.peak_rss_bytes = 0
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="vibephysics-rss-sampler", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.wait(self._interval_s):
            try:
                rss = _process_rss_bytes()
            except OSError:
                continue
            if rss > self.peak_rss_bytes:
                self.peak_rss_bytes = rss

    def stop(self) -> int | None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        try:
            rss = _process_rss_bytes()
            if rss > self.peak_rss_bytes:
                self.peak_rss_bytes = rss
        except OSError:
            pass
        return self.peak_rss_bytes or None


def reset_cuda_peak_memory() -> None:
    try:
        import torch
    except ImportError:
        return
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()


def cuda_peak_memory_bytes() -> int | None:
    try:
        import torch
    except ImportError:
        return None
    if torch.cuda.is_available():
        return int(torch.cuda.max_memory_allocated())
    return None


@dataclass
class StageRecord:
    name: str
    elapsed_s: float
    peak_rss_bytes: int | None = None
    peak_vram_bytes: int | None = None


@dataclass
class RunProfiler:
    enabled: bool = True
    stages: list[StageRecord] = field(default_factory=list)
    _total_sampler: _MemorySampler | None = field(default=None, repr=False)
    _total_started_at: float | None = field(default=None, repr=False)

    def start(self) -> None:
        if not self.enabled:
            return
        self._total_started_at = time.perf_counter()
        self._total_sampler = _MemorySampler()
        self._total_sampler.start()

    @contextmanager
    def stage(self, name: str, *, track_cuda_peak: bool = False) -> Iterator[None]:
        if not self.enabled:
            yield
            return

        if track_cuda_peak:
            reset_cuda_peak_memory()

        sampler = _MemorySampler()
        sampler.start()
        started_at = time.perf_counter()
        try:
            yield
        finally:
            elapsed_s = time.perf_counter() - started_at
            peak_vram = cuda_peak_memory_bytes() if track_cuda_peak else None
            self.stages.append(
                StageRecord(
                    name=name,
                    elapsed_s=elapsed_s,
                    peak_rss_bytes=sampler.stop(),
                    peak_vram_bytes=peak_vram,
                )
            )

    def print_summary(
        self,
        *,
        engine: str,
        num_frames: int,
        output_path: Path,
    ) -> None:
        if not self.enabled or not self.stages:
            return

        total_elapsed = sum(stage.elapsed_s for stage in self.stages)
        if self._total_started_at is not None:
            total_elapsed = time.perf_counter() - self._total_started_at

        run_peak_rss = max((stage.peak_rss_bytes or 0) for stage in self.stages) or None
        if self._total_sampler is not None:
            run_peak_rss = self._total_sampler.stop()
            run_peak_rss = max(run_peak_rss or 0, *(stage.peak_rss_bytes or 0 for stage in self.stages)) or None

        run_peak_vram = max((stage.peak_vram_bytes or 0) for stage in self.stages) or None
        show_vram = run_peak_vram is not None and run_peak_vram > 0

        stage_width = max(len(stage.name) for stage in self.stages)
        time_width = max(len(_format_seconds(stage.elapsed_s)) for stage in self.stages)
        rss_width = max(len(_format_bytes(stage.peak_rss_bytes)) for stage in self.stages)
        if show_vram:
            vram_width = max(len(_format_bytes(stage.peak_vram_bytes)) for stage in self.stages)

        print("\n--- [vibephysics] Run summary ---")
        print(f"Engine:  {engine}")
        print(f"Frames:  {num_frames}")
        print(f"Output:  {output_path}")
        print()
        if show_vram:
            header = (
                f"{'Stage':<{stage_width}}  "
                f"{'Wall time':>{time_width}}  "
                f"{'Stage peak RSS':>{rss_width}}  "
                f"{'Stage peak VRAM':>{vram_width}}"
            )
        else:
            header = (
                f"{'Stage':<{stage_width}}  "
                f"{'Wall time':>{time_width}}  "
                f"{'Stage peak RSS':>{rss_width}}"
            )
        print(header)
        print("-" * len(header))
        for stage in self.stages:
            if show_vram:
                print(
                    f"{stage.name:<{stage_width}}  "
                    f"{_format_seconds(stage.elapsed_s):>{time_width}}  "
                    f"{_format_bytes(stage.peak_rss_bytes):>{rss_width}}  "
                    f"{_format_bytes(stage.peak_vram_bytes):>{vram_width}}"
                )
            else:
                print(
                    f"{stage.name:<{stage_width}}  "
                    f"{_format_seconds(stage.elapsed_s):>{time_width}}  "
                    f"{_format_bytes(stage.peak_rss_bytes):>{rss_width}}"
                )

        print()
        print(f"Total wall time: {_format_seconds(total_elapsed)}")
        print(f"Run peak RSS (this process): {_format_bytes(run_peak_rss)}")
        if show_vram:
            print(f"Run peak VRAM (CUDA, inference): {_format_bytes(run_peak_vram)}")
        print("Peak memory is the high-water mark for this Python process — not summed across stages.")
        print()


_INSTALL_HINTS = {
    "lingbot_map": "pip install vibephysics (deps auto-install on first run)",
    "vggt_omega": "pip install vibephysics (deps auto-install on first run; HF access required)",
}


def _require_bpy() -> None:
    try:
        import bpy  # noqa: F401
    except ImportError as exc:
        py = f"{sys.version_info.major}.{sys.version_info.minor}"
        raise RuntimeError(
            f"bpy is required for .blend export (current Python {py}). "
            "PyPI bpy 5.0 requires Python 3.11 (not 3.12+). "
            "Use a 3.11 env and: pip install vibephysics bpy"
        ) from exc


def _export_blend_scene(
    prediction,
    output_path: Path,
    save_blend: str | Path,
    *,
    min_confidence: float,
    point_scale: float,
    animate: bool,
    animation_fps: int,
    video_fps: float | None,
    verbose: bool,
) -> Path:
    _require_bpy()
    import bpy
    from vibephysics.setup.exporter import save_blend as save_blend_file

    from .visual import load_reconstruction

    blend_path = Path(save_blend)
    if not blend_path.is_absolute():
        blend_path = output_path / blend_path

    bpy.ops.wm.read_factory_settings(use_empty=True)
    load_reconstruction(
        prediction,
        min_confidence=min_confidence,
        point_scale=point_scale,
        global_indices=prediction.metadata.get("selected_indices"),
        animate=animate,
        animation_fps=animation_fps,
        video_fps=video_fps,
    )
    save_blend_file(str(blend_path))

    if verbose:
        print(f"Saved Blender scene to {blend_path}")
    return blend_path


def _engine_available(engine: str) -> bool:
    if engine == "lingbot_map":
        from .lingbot_map import is_available

        return is_available()
    if engine == "vggt_omega":
        from .vggt_omega import is_available

        return is_available()
    return False


def _ensure_engine(engine: str, vggt_omega_checkpoint: str | Path | None) -> None:
    if engine not in FEEDFORWARD_ENGINES:
        raise ValueError(f"Unknown engine '{engine}'. Choose one of: {', '.join(FEEDFORWARD_ENGINES)}")

    if not _engine_available(engine):
        raise RuntimeError(
            f"Engine '{engine}' is not available. Install with: {_INSTALL_HINTS[engine]}"
        )


def reconstruct(
    image_path: str | Path,
    output_path: str | Path | None = None,
    engine: str = "lingbot_map",
    save_blend: str | Path | None = "scene.blend",
    min_confidence: float = 0.5,
    filter_edges: bool = True,
    point_scale: float = 1.0,
    animate: bool = True,
    animation_fps: int = 24,
    align_ground: bool = True,
    max_frames: int | None = None,
    max_frames_mode: str = "first",
    keyframe_interval: int | None = None,
    lingbot_map_mode: str | None = None,
    window_size: int = 64,
    overlap_size: int = 16,
    overlap_keyframes: int | None = None,
    mask_sky: bool = False,
    use_sdpa: bool = False,
    lingbot_map_model: str = DEFAULT_LINGBOT_MAP_MODEL,
    lingbot_map_checkpoint: str | Path | None = None,
    lingbot_map_image_size: int = 518,
    vggt_omega_checkpoint: str | Path | None = None,
    vggt_omega_checkpoint_name: str = "vggt-omega-1b-512",
    vggt_omega_resolution: int = 512,
    vggt_omega_preprocess_mode: str = "balanced",
    vggt_omega_enable_alignment: bool = False,
    vggt_omega_conf_percentile: float = 50.0,
    vggt_omega_depth_edge_rtol: float = 0.03,
    video_fps: float | None = None,
    video_quality: int = 2,
    verbose: bool = True,
) -> Path:
    profiler = RunProfiler(enabled=verbose)
    profiler.start()

    source_path = Path(image_path).absolute()
    with profiler.stage("prepare_input"):
        image_path = resolve_input(
            source_path,
            video_fps=video_fps,
            video_quality=video_quality,
            verbose=verbose,
        )
        all_images = discover_images(image_path)
        num_frames = len(all_images)
        source_video_fps = resolve_source_video_fps(image_path, video_fps)

    vram_gb = get_vram_gb()
    _ensure_engine(engine, vggt_omega_checkpoint)

    if verbose:
        print(f"--- [vibephysics] Engine: {engine} ({num_frames} frames) ---")
        if engine == "lingbot_map":
            from .lingbot_map import format_inference_plan

            print(
                f"--- [vibephysics] {format_inference_plan(num_frames, mode=lingbot_map_mode, keyframe_interval=keyframe_interval, window_size=window_size, overlap_size=overlap_size)} ---"
            )

    with profiler.stage("inference", track_cuda_peak=True):
        if engine == "lingbot_map":
            from .lingbot_map import run_lingbot_map

            prediction = run_lingbot_map(
                image_path=image_path,
                model_path=Path(lingbot_map_checkpoint) if lingbot_map_checkpoint else None,
                model_name=lingbot_map_model,
                mode=lingbot_map_mode,
                keyframe_interval=keyframe_interval,
                window_size=window_size,
                overlap_size=overlap_size,
                overlap_keyframes=overlap_keyframes,
                use_sdpa=use_sdpa,
                image_size=lingbot_map_image_size,
                max_frames=max_frames,
                max_frames_mode=max_frames_mode,
                verbose=verbose,
            )
        elif engine == "vggt_omega":
            from .vggt_omega import run_vggt_omega

            prediction = run_vggt_omega(
                image_path=image_path,
                checkpoint=vggt_omega_checkpoint,
                checkpoint_name=vggt_omega_checkpoint_name,
                image_resolution=vggt_omega_resolution,
                preprocess_mode=vggt_omega_preprocess_mode,
                enable_alignment=vggt_omega_enable_alignment,
                max_frames=max_frames,
                max_frames_mode=max_frames_mode,
                filter_depth_edges=filter_edges,
                depth_edge_rtol=vggt_omega_depth_edge_rtol,
                conf_percentile=vggt_omega_conf_percentile,
                verbose=verbose,
            )
        else:
            raise ValueError(f"Unknown engine: {engine}")

    export_min_confidence = min_confidence
    if export_min_confidence == 0.5 and is_lingbot_map_engine(prediction.engine):
        export_min_confidence = 1.5
    elif is_vggt_omega_engine(prediction.engine):
        export_min_confidence = resolve_confidence_threshold(
            prediction,
            min_confidence,
            conf_percentile=vggt_omega_conf_percentile,
        )

    if align_ground:
        from .ground_align import align_prediction_ground

        with profiler.stage("ground_align"):
            align_prediction_ground(prediction)

    from .common import convert_prediction_to_blender_zup

    with profiler.stage("save_artifacts"):
        convert_prediction_to_blender_zup(prediction)
        prediction.metadata = dict(prediction.metadata)
        prediction.metadata["video_fps"] = source_video_fps

        output_path = prepare_output_directory(image_path, output_path, engine=engine, verbose=verbose)
        prediction.metadata["source_image_paths"] = list(prediction.image_paths)
        prediction.image_paths = persist_preprocessed_frames(output_path, prediction)
        prediction.metadata["preprocessed_frames_dir"] = str((output_path / "frames").resolve())
        config = {
            "engine": engine,
            "source_path": str(source_path),
            "image_path": str(image_path),
            "num_frames": num_frames,
            "max_frames": max_frames,
            "max_frames_mode": max_frames_mode,
            "vram_gb": vram_gb,
            "min_confidence": export_min_confidence,
            "conf_percentile": vggt_omega_conf_percentile if is_vggt_omega_engine(engine) else None,
            "point_scale": point_scale,
            "filter_edges": filter_edges,
            "mask_sky": mask_sky,
            "video_fps": source_video_fps,
            "video_fps_config": video_fps,
            "animation_fps": animation_fps,
            "align_ground": align_ground,
            "prediction_metadata": prediction.metadata,
        }
        save_reconstruct_config(output_path / "reconstruct_config.json", config)
        save_prediction(output_path / "predictions.npz", prediction)

    if save_blend is not None:
        with profiler.stage("blend_export"):
            _export_blend_scene(
                prediction,
                output_path,
                save_blend,
                min_confidence=export_min_confidence,
                point_scale=point_scale,
                animate=animate,
                animation_fps=animation_fps,
                video_fps=source_video_fps,
                verbose=verbose,
            )

    profiler.print_summary(engine=engine, num_frames=num_frames, output_path=output_path)
    return output_path


_PREPROCESS_MODES = {
    "vggt_omega": ("balanced", "max_size"),
}


def reconstruct_from_config(
    config_path: str | Path,
    image_path: str | Path | None = None,
    output_path: str | Path | None = None,
    preprocess_mode: str | None = None,
    max_frames: int | None = None,
    max_frames_mode: str | None = None,
) -> Path:
    from .config import apply_overrides, apply_video_frame_overrides, load_yaml_config, parse_feedforward_config

    config_path = Path(config_path)
    cfg = apply_overrides(
        load_yaml_config(config_path),
        {"image_path": image_path, "output_path": output_path},
    )
    cfg = apply_video_frame_overrides(
        cfg,
        max_frames=max_frames,
        max_frames_mode=max_frames_mode,
    )
    if preprocess_mode is not None:
        engine = cfg.get("engine")
        if engine not in _PREPROCESS_MODES:
            raise ValueError(f"--mode is not supported for engine '{engine}'")
        allowed = _PREPROCESS_MODES[engine]
        if preprocess_mode not in allowed:
            raise ValueError(
                f"Invalid --mode '{preprocess_mode}' for {engine}. Choose one of: {', '.join(allowed)}"
            )
        section = cfg.setdefault(engine, {})
        if not isinstance(section, dict):
            raise ValueError(f"Config section '{engine}' must be a mapping")
        section["preprocess_mode"] = preprocess_mode
    params = parse_feedforward_config(cfg, config_path=config_path.resolve())
    return reconstruct(**params)


def main() -> None:
    import argparse

    from .config import DEFAULT_FEEDFORWARD_CONFIG

    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

    parser = argparse.ArgumentParser(description="Run dense feedforward reconstruction (LingBot-Map or VGGT-Omega).")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_FEEDFORWARD_CONFIG,
        help=f"YAML config file (default: {DEFAULT_FEEDFORWARD_CONFIG.name})",
    )
    parser.add_argument(
        "--image_path",
        "--input",
        default=None,
        dest="image_path",
        help="Override config image_path (video, image folder, or single image).",
    )
    parser.add_argument("--output_path", default=None, help="Override config output_path.")
    parser.add_argument(
        "--max_frames",
        type=int,
        default=None,
        metavar="N",
        help="Use at most N frames from the input. Overrides config.",
    )
    parser.add_argument(
        "--max_frames_mode",
        choices=("spread", "first"),
        default=None,
        help="How to pick N frames: first=first N consecutive (default), "
        "spread=evenly across full input.",
    )
    parser.add_argument(
        "--mode",
        dest="preprocess_mode",
        default=None,
        help="Preprocess mode override (vggt_omega: balanced|max_size).",
    )
    args = parser.parse_args()

    try:
        reconstruct_from_config(
            args.config,
            args.image_path,
            args.output_path,
            preprocess_mode=args.preprocess_mode,
            max_frames=args.max_frames,
            max_frames_mode=args.max_frames_mode,
        )
        sys.exit(0)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"[ERROR] Reconstruction failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
