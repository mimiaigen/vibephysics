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
    is_r3_engine,
    is_vgg_ttt_engine,
    is_vggt_omega_engine,
    persist_preprocessed_frames,
    resolve_confidence_threshold,
)
from .config import FEEDFORWARD_ENGINES
from .schema import save_compact_prediction, save_prediction, save_reconstruct_config

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
    "vgg_ttt": "pip install vibephysics (deps auto-install on first run)",
    "map_anything": "pip install vibephysics (deps auto-install on first run)",
    "r3": "pip install vibephysics (deps auto-install on first run; CUDA + xformers required)",
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
    point_random_points_per_frame: int | None,
    point_total_random_points: int | None,
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
        point_random_points_per_frame=point_random_points_per_frame,
        point_total_random_points=point_total_random_points,
        global_indices=prediction.metadata.get("selected_indices"),
        animate=animate,
        animation_fps=animation_fps,
        video_fps=video_fps,
    )
    save_blend_file(str(blend_path))

    if verbose:
        print(f"Saved Blender scene to {blend_path}")
    return blend_path


def _export_plotly_html(
    predictions_path: Path,
    output_path: Path,
    save_html: str | Path,
    *,
    video_fps: float | None,
) -> Path:
    from argparse import Namespace

    from .export import export_plotly

    html_path = Path(save_html)
    if not html_path.is_absolute():
        html_path = output_path / html_path
    export_plotly(
        Namespace(
            predictions=predictions_path,
            output=html_path,
            min_confidence=None,
            video_fps=video_fps,
            seed=0,
            sample_rounds=8,
            max_points=None,
            frames_dir=None,
            point_size=1.5,
            opacity=0.85,
            trajectory=True,
        )
    )
    return html_path


def _engine_available(engine: str) -> bool:
    if engine == "lingbot_map":
        from .lingbot_map import is_available

        return is_available()
    if engine == "vggt_omega":
        from .vggt_omega import is_available

        return is_available()
    if engine == "vgg_ttt":
        from .vgg_ttt import is_available

        return is_available()
    if engine == "map_anything":
        from .map_anything import is_available

        return is_available()
    if engine == "r3":
        from .r3 import is_available

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
    save_blend: str | Path | None = None,
    save_html: str | Path | None = None,
    save_frames: bool = False,
    min_confidence: float = 2.0,
    filter_edges: bool = True,
    point_scale: float = 0.01,
    point_random_points_per_frame: int | None = 4000,
    point_total_random_points: int | None = 400_000,
    compact: bool = False,
    animate: bool = True,
    animation_fps: int = 24,
    align_ground: bool = True,
    max_frames: int | None = None,
    max_frames_mode: str = "first",
    keyframe_interval: int | None = None,
    lingbot_map_max_streaming_keyframes: int | None = None,
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
    vgg_ttt_model_id: str = "nvidia/vgg-ttt",
    vgg_ttt_preprocess_mode: str = "crop",
    vgg_ttt_image_size: int = 518,
    vgg_ttt_conf_percentile: float = 50.0,
    vgg_ttt_depth_edge_rtol: float = 0.03,
    vgg_ttt_num_ttt_steps: int | None = 1,
    vgg_ttt_memory_efficient_inference: bool = False,
    map_anything_model: str = "vggt",
    map_anything_model_kwargs: dict | None = None,
    map_anything_install_all: bool = False,
    map_anything_resolution: int | None = None,
    map_anything_norm_type: str | None = None,
    map_anything_patch_size: int | None = None,
    map_anything_resize_mode: str = "fixed_mapping",
    map_anything_size: int | tuple[int, int] | None = None,
    r3_checkpoint: str | Path | None = None,
    r3_model: str | None = None,
    r3_config_name: str = "r3-large",
    r3_mode: str | None = "local",
    r3_image_size: int = 504,
    r3_kv_backend: str = "dense",
    r3_rel_pose_method: str = "greedy",
    r3_metric_model_name: str = "depth-anything/DA3METRIC-LARGE",
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
                f"--- [vibephysics] {format_inference_plan(num_frames, mode=lingbot_map_mode, keyframe_interval=keyframe_interval, max_streaming_keyframes=lingbot_map_max_streaming_keyframes, vram_gb=vram_gb, window_size=window_size, overlap_size=overlap_size)} ---"
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
                max_streaming_keyframes=lingbot_map_max_streaming_keyframes,
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
        elif engine == "vgg_ttt":
            from .vgg_ttt import run_vgg_ttt

            prediction = run_vgg_ttt(
                image_path=image_path,
                model_id=vgg_ttt_model_id,
                preprocess_mode=vgg_ttt_preprocess_mode,
                image_size=vgg_ttt_image_size,
                max_frames=max_frames,
                max_frames_mode=max_frames_mode,
                filter_depth_edges=filter_edges,
                depth_edge_rtol=vgg_ttt_depth_edge_rtol,
                conf_percentile=vgg_ttt_conf_percentile,
                num_ttt_steps=vgg_ttt_num_ttt_steps,
                memory_efficient_inference=vgg_ttt_memory_efficient_inference,
                verbose=verbose,
            )
        elif engine == "map_anything":
            from .map_anything import run_map_anything

            prediction = run_map_anything(
                image_path=image_path,
                model_name=map_anything_model,
                model_kwargs=map_anything_model_kwargs,
                install_all_extras=map_anything_install_all,
                resolution=map_anything_resolution,
                norm_type=map_anything_norm_type,
                patch_size=map_anything_patch_size,
                resize_mode=map_anything_resize_mode,
                size=map_anything_size,
                max_frames=max_frames,
                max_frames_mode=max_frames_mode,
                verbose=verbose,
            )
        elif engine == "r3":
            from .r3 import run_r3

            prediction = run_r3(
                image_path=image_path,
                checkpoint=r3_checkpoint,
                model_name=r3_model,
                config_name=r3_config_name,
                mode=r3_mode,
                image_size=r3_image_size,
                kv_backend=r3_kv_backend,
                rel_pose_method=r3_rel_pose_method,
                metric_model_name=r3_metric_model_name,
                max_frames=max_frames,
                max_frames_mode=max_frames_mode,
                verbose=verbose,
            )
        else:
            raise ValueError(f"Unknown engine: {engine}")

    export_min_confidence = min_confidence
    if is_vggt_omega_engine(prediction.engine):
        export_min_confidence = resolve_confidence_threshold(
            prediction,
            min_confidence,
            conf_percentile=vggt_omega_conf_percentile,
        )
    elif is_vgg_ttt_engine(prediction.engine):
        export_min_confidence = resolve_confidence_threshold(
            prediction,
            min_confidence,
            conf_percentile=vgg_ttt_conf_percentile,
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
        save_compact = compact or point_random_points_per_frame is not None or point_total_random_points is not None
        if save_frames:
            prediction.image_paths = persist_preprocessed_frames(output_path, prediction)
            prediction.metadata["preprocessed_frames_dir"] = str((output_path / "frames").resolve())
        else:
            prediction.metadata["preprocessed_frames_dir"] = None
        config = {
            "engine": engine,
            "source_path": str(source_path),
            "image_path": str(image_path),
            "num_frames": num_frames,
            "max_frames": max_frames,
            "max_frames_mode": max_frames_mode,
            "vram_gb": vram_gb,
            "min_confidence": export_min_confidence,
            "conf_percentile": (
                vggt_omega_conf_percentile
                if is_vggt_omega_engine(engine)
                else vgg_ttt_conf_percentile
                if is_vgg_ttt_engine(engine)
                else None
            ),
            "point_scale": point_scale,
            "point_random_points_per_frame": point_random_points_per_frame,
            "point_total_random_points": point_total_random_points,
            "compact": save_compact,
            "save_html": save_html,
            "save_frames": save_frames,
            "filter_edges": filter_edges,
            "mask_sky": mask_sky,
            "video_fps": source_video_fps,
            "video_fps_config": video_fps,
            "animation_fps": animation_fps,
            "align_ground": align_ground,
            "prediction_metadata": prediction.metadata,
        }
        save_reconstruct_config(output_path / "reconstruct_config.json", config)
        if save_compact:
            save_compact_prediction(
                output_path / "predictions.npz",
                prediction,
                min_confidence=export_min_confidence,
                random_points_per_frame=point_random_points_per_frame,
                total_random_points=point_total_random_points,
            )
        else:
            save_prediction(output_path / "predictions.npz", prediction)

    if save_html is not None:
        with profiler.stage("html_export"):
            _export_plotly_html(
                output_path / "predictions.npz",
                output_path,
                save_html,
                video_fps=source_video_fps,
            )

    if save_blend is not None:
        with profiler.stage("blend_export"):
            _export_blend_scene(
                prediction,
                output_path,
                save_blend,
                min_confidence=export_min_confidence,
                point_scale=point_scale,
                point_random_points_per_frame=point_random_points_per_frame,
                point_total_random_points=point_total_random_points,
                animate=animate,
                animation_fps=animation_fps,
                video_fps=source_video_fps,
                verbose=verbose,
            )

    profiler.print_summary(engine=engine, num_frames=num_frames, output_path=output_path)
    return output_path


_PREPROCESS_MODES = {
    "vggt_omega": ("balanced", "max_size"),
    "vgg_ttt": ("crop", "pad"),
    "map_anything": ("fixed_mapping", "longest_side", "square", "fixed_size"),
}


def reconstruct_from_config(
    config_path: str | Path,
    image_path: str | Path | None = None,
    output_path: str | Path | None = None,
    preprocess_mode: str | None = None,
    max_frames: int | None = None,
    max_frames_mode: str | None = None,
    point_scale: float | None = None,
    min_confidence: float | None = None,
    random_points_per_frame: int | None = None,
    total_random_points: int | None = None,
    compact: bool | None = None,
    html: bool | None = None,
    frames: bool | None = None,
    map_anything_model: str | None = None,
    map_anything_install_all: bool = False,
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
    if point_scale is not None:
        output = cfg.setdefault("output", {})
        if not isinstance(output, dict):
            raise ValueError("Config section 'output' must be a mapping")
        output["point_scale"] = float(point_scale)
    if min_confidence is not None:
        output = cfg.setdefault("output", {})
        if not isinstance(output, dict):
            raise ValueError("Config section 'output' must be a mapping")
        output["min_confidence"] = float(min_confidence)
    if random_points_per_frame is not None:
        output = cfg.setdefault("output", {})
        if not isinstance(output, dict):
            raise ValueError("Config section 'output' must be a mapping")
        output["random_points_per_frame"] = int(random_points_per_frame)
    if total_random_points is not None:
        output = cfg.setdefault("output", {})
        if not isinstance(output, dict):
            raise ValueError("Config section 'output' must be a mapping")
        output["total_random_points"] = int(total_random_points)
    if compact is not None:
        output = cfg.setdefault("output", {})
        if not isinstance(output, dict):
            raise ValueError("Config section 'output' must be a mapping")
        output["compact"] = bool(compact)
    if html is not None:
        output = cfg.setdefault("output", {})
        if not isinstance(output, dict):
            raise ValueError("Config section 'output' must be a mapping")
        output["save_html"] = "visual.html" if html else None
    if frames is not None:
        output = cfg.setdefault("output", {})
        if not isinstance(output, dict):
            raise ValueError("Config section 'output' must be a mapping")
        output["save_frames"] = bool(frames)
    if map_anything_model is not None:
        if cfg.get("engine") != "map_anything":
            raise ValueError("--model is only supported when engine is 'map_anything'")
        from .map_anything import _model_defaults, default_model_kwargs

        section = cfg.setdefault("map_anything", {})
        if not isinstance(section, dict):
            raise ValueError("Config section 'map_anything' must be a mapping")
        resolution, norm_type, patch_size = _model_defaults(map_anything_model)
        section["model"] = map_anything_model
        section["model_kwargs"] = default_model_kwargs(map_anything_model)
        section["resolution"] = resolution
        section["norm_type"] = norm_type
        section["patch_size"] = patch_size
    if map_anything_install_all:
        if cfg.get("engine") != "map_anything":
            raise ValueError("--map-anything-install-all is only supported when engine is 'map_anything'")
        section = cfg.setdefault("map_anything", {})
        if not isinstance(section, dict):
            raise ValueError("Config section 'map_anything' must be a mapping")
        section["install_all"] = True
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
        if engine == "map_anything":
            section["resize_mode"] = preprocess_mode
        else:
            section["preprocess_mode"] = preprocess_mode
    params = parse_feedforward_config(cfg, config_path=config_path.resolve())
    return reconstruct(**params)


def main() -> None:
    import argparse

    from .config import DEFAULT_FEEDFORWARD_CONFIG

    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

    parser = argparse.ArgumentParser(description="Run dense feedforward reconstruction.")
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
        "--point_scale",
        "--point-scale",
        type=float,
        default=None,
        help="Override output.point_scale as an absolute point radius in the saved .blend.",
    )
    parser.add_argument(
        "--min_confidence",
        "--min-confidence",
        type=float,
        default=None,
        help="Override output.min_confidence for saved predictions and exports.",
    )
    parser.add_argument(
        "--random_points_per_frame",
        "--random-points-per-frame",
        type=int,
        default=None,
        help="Randomly keep up to N points per frame after confidence filtering.",
    )
    parser.add_argument(
        "--total_random_points",
        "--total-random-points",
        type=int,
        default=None,
        help="Randomly keep up to N total points after per-frame filtering.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Save compact predictions.npz with colored points and camera poses only.",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Save an interactive Plotly HTML point cloud next to predictions.npz.",
    )
    parser.add_argument(
        "--frames",
        action="store_true",
        help="Save model-preprocessed RGB frames next to predictions.npz.",
    )
    parser.add_argument(
        "--mode",
        dest="preprocess_mode",
        default=None,
        help="Preprocess mode override (vggt_omega: balanced|max_size; vgg_ttt: crop|pad; map_anything: fixed_mapping|longest_side|square|fixed_size).",
    )
    parser.add_argument(
        "--model",
        dest="map_anything_model",
        default=None,
        help="Map-Anything model_factory key override (for engine=map_anything).",
    )
    parser.add_argument(
        "--map-anything-install-all",
        "--map_anything_install_all",
        action="store_true",
        help="Install Map-Anything with the upstream [all] extra before running.",
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
            point_scale=args.point_scale,
            min_confidence=args.min_confidence,
            random_points_per_frame=args.random_points_per_frame,
            total_random_points=args.total_random_points,
            compact=args.compact if args.compact else None,
            html=args.html if args.html else None,
            frames=args.frames if args.frames else None,
            map_anything_model=args.map_anything_model,
            map_anything_install_all=args.map_anything_install_all,
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
