"""Shared utilities for feedforward reconstruction adapters."""

from __future__ import annotations

import os
import subprocess
import warnings
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

import numpy as np

VoxelKey: TypeAlias = tuple[int, int, int]
RandomPointsLimit: TypeAlias = int | float

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".JPG", ".PNG"}


def parse_random_points_limit(value: object, *, name: str) -> RandomPointsLimit | None:
    """
    Parse subsample limit: ``0``/empty = off; ``int >= 1`` = max count; ``float`` in (0, 1] = ratio.

    YAML ``1`` is one point; YAML ``1.0`` / ``0.5`` are ratios (100% / 50%).
    """
    if value is None or value == "":
        return None
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("", "none", "null"):
            return None
        if "." in text or "e" in text:
            value = float(text)
        else:
            value = int(text)
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a number, not a boolean")
    if isinstance(value, int):
        return None if value <= 0 else value
    num = float(value)
    if num <= 0:
        return None
    if isinstance(value, float) and num <= 1.0:
        return num
    if num > 1.0 and num == int(num):
        return int(num)
    raise ValueError(
        f"{name} must be 0 (off), a float ratio in (0, 1], or an integer count >= 1; got {value!r}"
    )


def random_points_limit_enabled(limit: RandomPointsLimit | None) -> bool:
    return limit is not None


def resolve_random_sample_count(limit: RandomPointsLimit, num_points: int) -> int:
    """How many points to keep after random subsampling (``<= num_points``)."""
    if num_points <= 0:
        return 0
    if isinstance(limit, float):
        if limit >= 1.0:
            return num_points
        keep = max(1, int(round(limit * num_points)))
        return min(keep, num_points)
    return min(int(limit), num_points)

DEFAULT_LINGBOT_MAP_MODEL = "lingbot-map"

LINGBOT_MAP_GIT = "git+https://github.com/robbyant/lingbot-map.git"
VGGT_OMEGA_GIT = "git+https://github.com/facebookresearch/vggt-omega.git"
VGG_TTT_GIT = "git+https://github.com/nv-dvl/vgg-ttt.git"
MAP_ANYTHING_GIT = "git+https://github.com/facebookresearch/map-anything.git"
R3_GIT = "git+https://github.com/KevinXu02/R3.git"
DVLT_GIT = "git+https://github.com/nv-tlabs/dvlt.git"
DEFAULT_VIDEO_FPS = 2.0
VIDEO_EXTRACT_FPS_FILE = ".vibephysics_extract_fps"


def repo_root() -> Path:
    """Repository root (directory containing pyproject.toml)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    return Path.cwd()


def feedforward_cache_root() -> Path:
    """Local cache for cloned upstream repos and downloaded checkpoints."""
    override = os.environ.get("VIBEPHYSICS_FEEDFORWARD_CACHE")
    if override:
        return Path(override).expanduser().resolve()
    return repo_root() / ".vibephysics" / "feedforward"


def feedforward_engine_dir(engine: str) -> Path:
    path = feedforward_cache_root() / engine
    path.mkdir(parents=True, exist_ok=True)
    return path


def feedforward_hf_hub_cache() -> Path:
    """Hugging Face Hub snapshot cache shared by feedforward engines."""
    path = feedforward_engine_dir("huggingface") / "hub"
    path.mkdir(parents=True, exist_ok=True)
    return path


def feedforward_torch_hub_cache(engine: str) -> Path:
    """torch.hub checkout cache (e.g. facebookresearch/dinov2) for a feedforward engine."""
    path = feedforward_engine_dir(engine) / "torch_hub"
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_lingbot_map_engine(engine: str) -> bool:
    engine = str(engine)
    return engine == "lingbot_map" or engine == "lingbot" or engine.startswith("lingbot_map")


def is_vggt_omega_engine(engine: str) -> bool:
    engine = str(engine)
    return engine == "vggt_omega" or engine == "vggt" or engine.startswith("vggt_omega")


def is_vgg_ttt_engine(engine: str) -> bool:
    engine = str(engine)
    return engine == "vgg_ttt" or engine == "vggttt" or engine.startswith("vgg_ttt")


def is_map_anything_engine(engine: str) -> bool:
    engine = str(engine)
    return engine == "map_anything" or engine == "mapanything" or engine.startswith("map_anything")


def is_r3_engine(engine: str) -> bool:
    engine = str(engine)
    return engine == "r3" or engine.startswith("r3")


def is_dvlt_engine(engine: str) -> bool:
    engine = str(engine).strip().lower()
    return engine == "dvlt" or engine in ("deja_view", "dejaview", "deja-view")


def discover_images(image_path: Path) -> list[Path]:
    image_path = Path(image_path).absolute()
    if not image_path.exists():
        raise FileNotFoundError(f"Image path does not exist: {image_path}")

    if image_path.is_file():
        if image_path.suffix.lower() not in {e.lower() for e in IMAGE_EXTENSIONS}:
            raise ValueError(f"Unsupported image file: {image_path}")
        return [image_path]

    images = [
        p
        for p in image_path.iterdir()
        if p.is_file() and p.suffix in IMAGE_EXTENSIONS
    ]
    images.sort(key=lambda p: p.name.lower())
    if not images:
        raise ValueError(f"No images found in {image_path}")
    return images


def select_skip_frames(image_paths: list[Path], batch_size: int) -> tuple[list[Path], list[int]]:
    """Evenly subsample frames across the full sequence (legacy name)."""
    return select_frames(image_paths, batch_size, mode="spread")


def select_frames(
    image_paths: list[Path],
    max_frames: int,
    *,
    mode: str = "first",
) -> tuple[list[Path], list[int]]:
    """Select up to ``max_frames`` paths and their source indices."""
    if max_frames <= 0:
        raise ValueError("max_frames must be positive")
    if len(image_paths) <= max_frames:
        return image_paths, list(range(len(image_paths)))

    mode = str(mode).strip().lower()
    if mode == "first":
        indices = list(range(max_frames))
    elif mode == "spread":
        indices = np.linspace(0, len(image_paths) - 1, max_frames, dtype=int)
        indices = sorted(set(indices.tolist()))
    else:
        raise ValueError(f"Unknown max_frames mode '{mode}'. Use 'first' or 'spread'.")

    selected = [image_paths[i] for i in indices]
    return selected, indices


def limit_image_frames(
    image_paths: list[Path],
    max_frames: int | None,
    *,
    mode: str = "first",
    verbose: bool = True,
    engine_label: str = "feedforward",
) -> tuple[list[Path], list[int], int]:
    """
    Apply unified frame limits shared by LingBot-Map and VGGT-Omega.

    Returns (selected_paths, source_indices, total_input_count).
    """
    total = len(image_paths)
    if max_frames is None or total <= max_frames:
        return image_paths, list(range(total)), total

    mode = str(mode).strip().lower()
    selected, indices = select_frames(image_paths, max_frames, mode=mode)
    if verbose:
        mode_label = "first consecutive" if mode == "first" else "evenly spread"
        print(
            f"--- [vibephysics] {engine_label}: using {len(selected)}/{total} "
            f"input frames ({mode_label}) ---",
            flush=True,
        )
    return selected, indices, total


def engine_preview_label(engine: str) -> str:
    """Human-readable engine name for CLI frame-plan previews."""
    engine = str(engine).strip().lower()
    if is_lingbot_map_engine(engine):
        return "LingBot-Map"
    if is_vggt_omega_engine(engine):
        return "VGGT-Omega"
    if is_vgg_ttt_engine(engine):
        return "VGG-TTT"
    if is_r3_engine(engine):
        return "R3"
    if is_map_anything_engine(engine):
        return "Map-Anything"
    if is_dvlt_engine(engine):
        return "DVLT"
    return engine.replace("_", " ").strip() or "feedforward"


def estimate_video_frame_count(video_path: Path, extract_fps: float) -> int | None:
    """Estimate extracted frame count from video duration and target fps."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        duration = float(result.stdout.strip())
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        return None
    return max(int(duration * max(float(extract_fps), 1e-6)), 1)


def estimate_input_frame_count(
    input_path: str | Path,
    *,
    max_frames: int | None = None,
    max_frames_mode: str = "first",
    video_fps: float = DEFAULT_VIDEO_FPS,
) -> tuple[int | None, str]:
    """
    Estimate how many frames will be processed from an image folder, image, or video.

    Returns (frame_count, suffix) where suffix notes max_frames limiting when applicable.
    """
    from .reconstruct import (
        default_video_frames_dir,
        existing_frames_in_dir,
        looks_like_video_path,
    )

    path = Path(input_path)
    num_frames: int | None = None

    if path.is_dir():
        try:
            num_frames = len(discover_images(path))
        except (ValueError, FileNotFoundError):
            pass
    elif path.is_file() and looks_like_video_path(path):
        existing = existing_frames_in_dir(default_video_frames_dir(path))
        if existing:
            num_frames = len(existing)
        else:
            num_frames = estimate_video_frame_count(path, video_fps)
    elif path.is_file():
        num_frames = 1

    suffix = ""
    if num_frames is not None and max_frames is not None and num_frames > max_frames:
        num_frames = max_frames
        if max_frames_mode == "first":
            suffix = " [first consecutive frames]"
        else:
            suffix = " [spread across full input]"
    return num_frames, suffix


def preview_feedforward_input_plan(
    engine: str,
    input_path: str | Path,
    *,
    mode: str | None = None,
    keyframe_interval: int | None = None,
    max_streaming_keyframes: int | None = None,
    vram_gb: float | None = None,
    max_frames: int | None = None,
    max_frames_mode: str = "first",
    video_fps: float = DEFAULT_VIDEO_FPS,
    window_size: int = 64,
    overlap_size: int = 16,
) -> str:
    """CLI preview of input frame count; LingBot-Map also shows streaming/windowed plan."""
    label = engine_preview_label(engine)
    num_frames, suffix = estimate_input_frame_count(
        input_path,
        max_frames=max_frames,
        max_frames_mode=max_frames_mode,
        video_fps=video_fps,
    )
    if num_frames is None:
        return f"{label}: frame count unknown until video frames are extracted"

    if is_lingbot_map_engine(engine):
        from .lingbot_map import format_inference_plan

        return (
            format_inference_plan(
                num_frames,
                mode=mode,
                keyframe_interval=keyframe_interval,
                max_streaming_keyframes=max_streaming_keyframes,
                vram_gb=vram_gb,
                window_size=window_size,
                overlap_size=overlap_size,
            )
            + suffix
        )

    return f"{label}: {num_frames} frames{suffix}"


def to_numpy(x) -> np.ndarray:
    import torch

    if isinstance(x, torch.Tensor):
        return x.detach().cpu().float().numpy()
    return np.array(x)


def unproject_depth_map_to_point_map(
    depth: np.ndarray,
    extrinsics_w2c: np.ndarray,
    intrinsics: np.ndarray,
) -> np.ndarray:
    depth = to_numpy(depth)
    extrinsics_w2c = to_numpy(extrinsics_w2c)
    intrinsics = to_numpy(intrinsics)

    n, h, w = depth.shape
    world_points = np.zeros((n, h, w, 3), dtype=np.float32)
    for i in range(n):
        u, v = np.meshgrid(np.arange(w), np.arange(h))
        pixels = np.stack([u, v, np.ones((h, w))], axis=-1).reshape(-1, 3)
        inv_k = np.linalg.inv(intrinsics[i])
        rays = (inv_k @ pixels.T).T
        depths = depth[i].reshape(-1)
        cam_points = rays * depths[:, np.newaxis]
        cam_points_hom = np.hstack([cam_points, np.ones((len(depths), 1))])
        e = np.vstack([extrinsics_w2c[i], [0, 0, 0, 1]])
        cam_to_world = np.linalg.inv(e)
        world_points_hom = (cam_to_world @ cam_points_hom.T).T
        world_points[i] = (world_points_hom[:, :3] / world_points_hom[:, 3:4]).reshape(h, w, 3)
    return world_points


def apply_edge_filtering(depth: np.ndarray, conf: np.ndarray) -> None:
    import cv2

    for i in range(len(depth)):
        dm = depth[i].astype(np.float32)
        gx = cv2.Sobel(dm, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(dm, cv2.CV_64F, 0, 1, ksize=3)
        mag = np.sqrt(gx**2 + gy**2)
        mn, mx = np.nanmin(mag), np.nanmax(mag)
        norm = (mag - mn) / (mx - mn) if mx > mn else np.zeros_like(mag)
        conf[i][norm >= (12.0 / 255.0)] = 0.0


def c2w_to_w2c(extrinsic_c2w: np.ndarray) -> np.ndarray:
    extrinsic_c2w = to_numpy(extrinsic_c2w)
    if extrinsic_c2w.ndim == 2:
        e = np.vstack([extrinsic_c2w, [0, 0, 0, 1]])
        return np.linalg.inv(e)[:3, :4]
    out = np.zeros((extrinsic_c2w.shape[0], 3, 4), dtype=np.float32)
    for i in range(extrinsic_c2w.shape[0]):
        e = np.vstack([extrinsic_c2w[i], [0, 0, 0, 1]])
        out[i] = np.linalg.inv(e)[:3, :4]
    return out


def get_vram_gb() -> float | None:
    try:
        info = resolve_torch_device(verbose=False)
        if info.device_type == "cuda" and info.cuda_total_memory_gb is not None:
            return info.cuda_total_memory_gb
    except Exception:
        pass
    return None


@dataclass(frozen=True)
class TorchDeviceInfo:
    device_type: str
    torch_version: str
    torch_cuda_version: str | None
    cuda_available: bool
    cuda_device_name: str | None = None
    cuda_capability: tuple[int, int] | None = None
    cuda_total_memory_gb: float | None = None
    cuda_warning: str | None = None
    nvidia_driver_version: str | None = None
    nvidia_gpu_name: str | None = None
    requested_device: str = "auto"

    @property
    def device(self) -> str:
        return self.device_type


def _nvidia_smi_info() -> tuple[str | None, str | None]:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=driver_version,name",
                "--format=csv,noheader",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except Exception:
        return None, None
    first = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
    if not first:
        return None, None
    parts = [part.strip() for part in first.split(",", 1)]
    if len(parts) == 1:
        return parts[0] or None, None
    return parts[0] or None, parts[1] or None


def resolve_torch_device(*, verbose: bool = True) -> TorchDeviceInfo:
    """
    Resolve the inference device for feedforward engines.

    By default this uses CUDA when PyTorch can initialize it, otherwise CPU.
    Set VIBEPHYSICS_DEVICE=cpu or VIBEPHYSICS_DEVICE=cuda to override.
    """
    import torch

    requested = os.environ.get("VIBEPHYSICS_DEVICE", "auto").strip().lower() or "auto"
    if requested not in {"auto", "cuda", "cpu"}:
        raise ValueError("VIBEPHYSICS_DEVICE must be one of: auto, cuda, cpu")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cuda_available = bool(torch.cuda.is_available())
    cuda_warning = str(caught[-1].message) if caught else None

    driver_version, gpu_name = _nvidia_smi_info()
    cuda_device_name = None
    cuda_capability = None
    cuda_total_memory_gb = None
    if cuda_available:
        cuda_device_name = torch.cuda.get_device_name(0)
        cuda_capability = torch.cuda.get_device_capability(0)
        _, total = torch.cuda.mem_get_info(0)
        cuda_total_memory_gb = total / (1024**3)
        gpu_name = gpu_name or cuda_device_name

    if requested == "cuda" and not cuda_available:
        details = _format_cuda_unavailable_reason(
            torch_cuda_version=torch.version.cuda,
            cuda_warning=cuda_warning,
            nvidia_driver_version=driver_version,
            nvidia_gpu_name=gpu_name,
        )
        raise RuntimeError(f"VIBEPHYSICS_DEVICE=cuda was requested, but CUDA is unavailable. {details}")

    device_type = "cuda" if requested in {"auto", "cuda"} and cuda_available else "cpu"
    info = TorchDeviceInfo(
        device_type=device_type,
        torch_version=torch.__version__,
        torch_cuda_version=torch.version.cuda,
        cuda_available=cuda_available,
        cuda_device_name=cuda_device_name,
        cuda_capability=cuda_capability,
        cuda_total_memory_gb=cuda_total_memory_gb,
        cuda_warning=cuda_warning,
        nvidia_driver_version=driver_version,
        nvidia_gpu_name=gpu_name,
        requested_device=requested,
    )
    if verbose:
        print(format_torch_device_info(info), flush=True)
    return info


def _format_cuda_unavailable_reason(
    *,
    torch_cuda_version: str | None,
    cuda_warning: str | None,
    nvidia_driver_version: str | None,
    nvidia_gpu_name: str | None,
) -> str:
    parts = []
    if nvidia_gpu_name:
        parts.append(f"NVIDIA GPU detected: {nvidia_gpu_name}")
    if nvidia_driver_version:
        parts.append(f"driver={nvidia_driver_version}")
    if torch_cuda_version:
        parts.append(f"torch CUDA build={torch_cuda_version}")
    if cuda_warning:
        parts.append(cuda_warning)
    if not parts:
        parts.append("No CUDA-capable PyTorch device was detected.")
    return " ".join(parts)


def format_torch_device_info(info: TorchDeviceInfo) -> str:
    if info.device_type == "cuda":
        memory = (
            f", {info.cuda_total_memory_gb:.1f} GB VRAM"
            if info.cuda_total_memory_gb is not None
            else ""
        )
        capability = (
            f", capability {info.cuda_capability[0]}.{info.cuda_capability[1]}"
            if info.cuda_capability is not None
            else ""
        )
        return (
            f"--- [vibephysics] Torch device: cuda "
            f"({info.cuda_device_name or info.nvidia_gpu_name or 'GPU'}{memory}{capability}; "
            f"torch {info.torch_version}, CUDA {info.torch_cuda_version or 'n/a'}) ---"
        )

    reason = _format_cuda_unavailable_reason(
        torch_cuda_version=info.torch_cuda_version,
        cuda_warning=info.cuda_warning,
        nvidia_driver_version=info.nvidia_driver_version,
        nvidia_gpu_name=info.nvidia_gpu_name,
    )
    if info.requested_device == "cpu":
        return f"--- [vibephysics] Torch device: cpu (forced by VIBEPHYSICS_DEVICE=cpu) ---"
    if info.nvidia_gpu_name or info.nvidia_driver_version or info.cuda_warning:
        return f"--- [vibephysics] Torch device: cpu; CUDA unavailable. {reason} ---"
    return f"--- [vibephysics] Torch device: cpu (torch {info.torch_version}) ---"


def images_chw_to_hwc(images: np.ndarray) -> np.ndarray:
    """Convert model output images to float32 HWC in [0, 1]."""
    if images.ndim == 4 and images.shape[1] == 3:
        rgb = np.transpose(images, (0, 2, 3, 1))
    else:
        rgb = images
    rgb = rgb.astype(np.float32)
    if rgb.max() > 1.5:
        rgb = rgb / 255.0
    return rgb


def confidence_threshold(conf: np.ndarray, percentile: float) -> float:
    """Absolute confidence cutoff from a percentile of finite values."""
    percentile = max(2.0, float(percentile))
    flat = conf.reshape(-1)
    mask = np.isfinite(flat)
    if not np.any(mask):
        return 0.0
    return float(np.percentile(flat[mask], percentile))


def resolve_confidence_threshold(
    predictions,
    min_confidence: float = 2.0,
    *,
    conf_percentile: float | None = None,
) -> float:
    """Resolve an absolute confidence cutoff for point filtering."""
    from .schema import FeedforwardPrediction

    if isinstance(predictions, FeedforwardPrediction):
        engine = predictions.engine
        metadata = predictions.metadata
        conf = predictions.conf
    else:
        engine = predictions.get("engine", "")
        metadata = predictions.get("metadata", {})
        conf = predictions["conf"]

    if is_vggt_omega_engine(engine) or is_vgg_ttt_engine(engine) or is_dvlt_engine(engine):
        percentile = conf_percentile
        if percentile is None and isinstance(metadata, dict):
            percentile = metadata.get("conf_percentile")
        if percentile is None:
            percentile = 50.0
        return confidence_threshold(conf, percentile)

    return min_confidence


def resolve_frame_images(payload: dict) -> np.ndarray:
    """Return per-frame RGB in HWC [0, 1], matching depth resolution."""
    images = payload.get("images")
    if images is not None:
        return images

    image_paths = payload.get("image_paths") or []
    depth = payload["depth"]
    if not image_paths:
        raise ValueError("No images in prediction and image_paths is empty.")

    from PIL import Image

    n_frames, height, width = depth.shape[0], depth.shape[1], depth.shape[2]
    if len(image_paths) < n_frames:
        raise ValueError(
            f"image_paths has {len(image_paths)} entries but depth has {n_frames} frames."
        )

    frames: list[np.ndarray] = []
    for frame_idx in range(n_frames):
        path = Path(str(image_paths[frame_idx]))
        if not path.is_file():
            raise FileNotFoundError(f"Image not found for frame {frame_idx}: {path}")
        with Image.open(path) as img:
            rgb = img.convert("RGB")
            if rgb.size != (width, height):
                rgb = rgb.resize((width, height), Image.Resampling.BICUBIC)
        frames.append(np.asarray(rgb, dtype=np.float32) / 255.0)
    return np.stack(frames, axis=0)


def persist_preprocessed_frames(output_path: Path, prediction) -> list[str]:
    """
    Save model-preprocessed RGB frames next to predictions.npz.

    NPZ coloring must use the same pixels the engine saw (crop/resize), not raw
    source extractions re-resized later.
    """
    from .schema import FeedforwardPrediction

    if not isinstance(prediction, FeedforwardPrediction):
        raise TypeError("prediction must be a FeedforwardPrediction")

    if prediction.images is None:
        return list(prediction.image_paths)

    from PIL import Image

    frames_dir = Path(output_path) / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    rgb = np.asarray(prediction.images, dtype=np.float32)
    if rgb.ndim != 4 or rgb.shape[-1] != 3:
        raise ValueError(f"Expected prediction.images as NHWC RGB, got shape {rgb.shape}")

    paths: list[str] = []
    for frame_idx in range(rgb.shape[0]):
        out_path = frames_dir / f"frame_{frame_idx + 1:04d}.jpg"
        channel_first = rgb.ndim == 4 and rgb.shape[1] == 3
        frame = rgb[frame_idx]
        if channel_first:
            frame = np.transpose(frame, (1, 2, 0))
        frame_u8 = (np.clip(frame, 0.0, 1.0) * 255.0).astype(np.uint8)
        Image.fromarray(frame_u8).save(out_path, quality=95)
        paths.append(str(out_path.resolve()))

    return paths


WORLD_COORDS_OPENCV = "opencv"
WORLD_COORDS_BLENDER_Z_UP = "blender_z_up"


def opencv_world_to_blender_matrix() -> np.ndarray:
    """OpenCV world (x right, y down, z forward) -> Blender (x, z, -y)."""
    return np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )


def opencv_camera_to_blender_matrix() -> np.ndarray:
    """OpenCV camera (+Y down, +Z forward) -> Blender camera (+Y up, -Z forward)."""
    return np.diag([1.0, -1.0, -1.0, 1.0]).astype(np.float64)


def opencv_to_blender_points(points: np.ndarray) -> np.ndarray:
    """OpenCV (x, y, z) -> Blender Z-up (x, z, -y)."""
    points = np.asarray(points, dtype=np.float64)
    out = np.empty_like(points)
    out[:, 0] = points[:, 0]
    out[:, 1] = points[:, 2]
    out[:, 2] = -points[:, 1]
    return out


def _prediction_metadata(predictions) -> dict:
    from .schema import FeedforwardPrediction

    if isinstance(predictions, FeedforwardPrediction):
        return dict(predictions.metadata)
    meta = predictions.get("metadata") or {}
    if isinstance(meta, np.ndarray) and meta.size:
        meta = meta.flat[0]
    return dict(meta) if isinstance(meta, dict) else {}


def resolve_world_coordinates(predictions) -> str:
    """Return ``opencv`` (legacy) or ``blender_z_up`` (canonical saved layout)."""
    meta = _prediction_metadata(predictions)
    coords = str(meta.get("world_coordinates", WORLD_COORDS_OPENCV)).strip().lower()
    if coords in (WORLD_COORDS_BLENDER_Z_UP, "blender", "z_up", "z-up"):
        return WORLD_COORDS_BLENDER_Z_UP
    return WORLD_COORDS_OPENCV


def is_blender_z_up(predictions) -> bool:
    return resolve_world_coordinates(predictions) == WORLD_COORDS_BLENDER_Z_UP


def apply_only_start_frame_pose(
    prediction,
    *,
    reference_frame: int = 0,
) -> None:
    """
    Reproject every frame with the reference camera pose.

    Depth and intrinsics stay per frame; all extrinsics become the reference pose.
    """
    from .schema import FeedforwardPrediction

    if not isinstance(prediction, FeedforwardPrediction):
        raise TypeError("apply_only_start_frame_pose expects FeedforwardPrediction")

    num_frames = int(prediction.depth.shape[0])
    if not (0 <= reference_frame < num_frames):
        raise ValueError(
            f"reference_frame {reference_frame} out of range for {num_frames} frames"
        )

    ref_extrinsic = prediction.extrinsic[reference_frame].copy()
    shared_extrinsics = np.repeat(ref_extrinsic[None, ...], num_frames, axis=0)
    prediction.world_points = unproject_depth_map_to_point_map(
        prediction.depth,
        shared_extrinsics,
        prediction.intrinsic,
    )
    prediction.extrinsic = shared_extrinsics.astype(np.float32)
    prediction.metadata = dict(prediction.metadata)
    prediction.metadata["only_start_frame_pose"] = True
    prediction.metadata["only_start_frame_pose_index"] = int(reference_frame)


def convert_prediction_to_blender_zup(prediction) -> bool:
    """
    Convert ``world_points`` and ``extrinsic`` to Blender Z-up in place.

    Call after ground align (still runs in OpenCV). Saved NPZ then matches Blender
    without a second coordinate pass in ``visual.py``.
    """
    from .schema import FeedforwardPrediction

    if not isinstance(prediction, FeedforwardPrediction):
        raise TypeError("convert_prediction_to_blender_zup expects FeedforwardPrediction")
    if is_blender_z_up(prediction):
        return False

    wp = prediction.world_points
    flat = opencv_to_blender_points(wp.reshape(-1, 3))
    prediction.world_points = flat.astype(np.float32).reshape(wp.shape)

    world_b = opencv_world_to_blender_matrix()
    cam_b = opencv_camera_to_blender_matrix()
    w2c_as_camera_pose = bool(prediction.metadata.get("w2c_as_camera_pose"))
    new_ext = np.empty_like(prediction.extrinsic)
    for i, ext in enumerate(prediction.extrinsic):
        ext4 = np.vstack([ext, [0.0, 0.0, 0.0, 1.0]])
        pose = ext4 if w2c_as_camera_pose else np.linalg.inv(ext4)
        matrix_world = world_b @ pose @ cam_b
        new_ext[i] = matrix_world[:3, :4]
    prediction.extrinsic = new_ext.astype(np.float32)

    prediction.metadata = dict(prediction.metadata)
    prediction.metadata["world_coordinates"] = WORLD_COORDS_BLENDER_Z_UP
    prediction.metadata["extrinsic_is_matrix_world"] = True
    return True


def collect_colored_point_cloud(
    predictions,
    min_confidence: float = 2.0,
    *,
    to_blender: bool = True,
    with_frame_ids: bool = False,
    random_points_per_frame: RandomPointsLimit | None = None,
    total_random_points: RandomPointsLimit | None = None,
    point_cloud_3d_nms: bool = False,
    point_cloud_3d_nms_radius: float = 0.03,
    point_cloud_3d_nms_min_neighbors: int = 3,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray | None]:
    """
    Return filtered positions/RGB/conf.

    Filtering order is intentional:
      1. drop points below min_confidence within each frame,
      2. if random_points_per_frame is set, randomly sample within each frame,
      3. optional per-frame 3D density NMS (isolated sparse points),
      4. if total_random_points is set, randomly sample globally.
    """
    from .schema import FeedforwardPrediction

    if isinstance(predictions, FeedforwardPrediction):
        payload = predictions.to_viz_dict()
    else:
        payload = predictions

    if to_blender and is_blender_z_up(predictions):
        to_blender = False

    points = payload.get("world_points_from_depth", payload.get("world_points"))
    images = resolve_frame_images(payload)
    conf = payload["conf"]

    if point_cloud_3d_nms:
        from .frame_postprocess import run_per_frame_postprocess

        post = run_per_frame_postprocess(
            predictions,
            min_confidence=min_confidence,
            point_cloud_3d_nms=True,
            point_cloud_3d_nms_radius=point_cloud_3d_nms_radius,
            point_cloud_3d_nms_min_neighbors=point_cloud_3d_nms_min_neighbors,
            to_blender=to_blender,
            with_frame_ids=with_frame_ids,
            random_points_per_frame=random_points_per_frame,
            algo_3d_bbox=False,
        )
        return finalize_colored_point_cloud(
            post.point_chunks,
            post.color_chunks,
            post.conf_chunks,
            post.frame_id_chunks,
            total_random_points=total_random_points,
        )

    point_chunks: list[np.ndarray] = []
    color_chunks: list[np.ndarray] = []
    conf_chunks: list[np.ndarray] = []
    frame_id_chunks: list[np.ndarray] = []

    for frame_idx in range(points.shape[0]):
        chunk = collect_single_frame_point_chunk(
            predictions,
            frame_idx,
            min_confidence=min_confidence,
            point_cloud_3d_nms=False,
            random_points_per_frame=random_points_per_frame,
            rng_seed=frame_idx,
        )
        if chunk is None:
            continue
        pts, rgb, frame_conf_valid, _ = chunk
        if to_blender:
            pts = opencv_to_blender_points(pts)
        point_chunks.append(pts)
        color_chunks.append(rgb)
        conf_chunks.append(frame_conf_valid)
        if with_frame_ids:
            frame_id_chunks.append(np.full(len(frame_conf_valid), frame_idx, dtype=np.int32))

    return finalize_colored_point_cloud(
        point_chunks,
        color_chunks,
        conf_chunks,
        frame_id_chunks,
        total_random_points=total_random_points,
    )


def collect_single_frame_point_chunk(
    prediction,
    frame_idx: int,
    *,
    min_confidence: float = 2.0,
    point_cloud_3d_nms: bool = False,
    point_cloud_3d_nms_radius: float = 0.03,
    point_cloud_3d_nms_min_neighbors: int = 3,
    random_points_per_frame: RandomPointsLimit | None = None,
    rng_seed: int | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, int] | None:
    """Extract one frame's colored points; returns (pts, rgb_u8, conf, nms_removed)."""
    from .schema import FeedforwardPrediction

    if isinstance(prediction, FeedforwardPrediction):
        payload = prediction.to_viz_dict()
    else:
        payload = prediction

    points = payload.get("world_points_from_depth", payload.get("world_points"))
    images = resolve_frame_images(payload)
    conf = payload["conf"]

    frame_points = points[frame_idx].reshape(-1, 3)
    frame_colors = images[frame_idx].reshape(-1, 3)
    frame_conf = conf[frame_idx].reshape(-1)
    valid_mask = np.isfinite(frame_points).all(axis=1)
    if min_confidence > 0:
        valid_mask &= frame_conf >= min_confidence
    if not np.any(valid_mask):
        return None

    pts = frame_points[valid_mask]
    rgb = np.clip(frame_colors[valid_mask], 0.0, 1.0)
    frame_conf_valid = frame_conf[valid_mask].astype(np.float32)
    nms_removed = 0

    if random_points_per_frame is not None:
        random_frame = resolve_random_sample_count(
            random_points_per_frame, len(frame_conf_valid)
        )
        if random_frame < len(frame_conf_valid):
            seed = frame_idx if rng_seed is None else int(rng_seed)
            rng = np.random.default_rng(seed)
            keep = rng.choice(len(frame_conf_valid), size=random_frame, replace=False)
            pts = pts[keep]
            rgb = rgb[keep]
            frame_conf_valid = frame_conf_valid[keep]

    if point_cloud_3d_nms:
        nms_keep = filter_points_3d_nms(
            pts,
            radius=point_cloud_3d_nms_radius,
            min_neighbors=point_cloud_3d_nms_min_neighbors,
        )
        nms_removed = int((~nms_keep).sum())
        pts = pts[nms_keep]
        rgb = rgb[nms_keep]
        frame_conf_valid = frame_conf_valid[nms_keep]
        if len(pts) == 0:
            return None

    return (
        pts.astype(np.float32),
        (rgb * 255.0).astype(np.uint8),
        frame_conf_valid,
        nms_removed,
    )


def collect_single_frame_world_points(
    prediction,
    frame_idx: int,
    *,
    min_confidence: float = 2.0,
    point_cloud_3d_nms: bool = False,
    point_cloud_3d_nms_radius: float = 0.03,
    point_cloud_3d_nms_min_neighbors: int = 3,
    random_points_per_frame: RandomPointsLimit | None = None,
    rng_seed: int | None = None,
) -> np.ndarray | None:
    """World-space points after confidence / subsample / optional 3D NMS (for bbox, etc.)."""
    chunk = collect_single_frame_point_chunk(
        prediction,
        frame_idx,
        min_confidence=min_confidence,
        point_cloud_3d_nms=point_cloud_3d_nms,
        point_cloud_3d_nms_radius=point_cloud_3d_nms_radius,
        point_cloud_3d_nms_min_neighbors=point_cloud_3d_nms_min_neighbors,
        random_points_per_frame=random_points_per_frame,
        rng_seed=rng_seed,
    )
    if chunk is None:
        return None
    return chunk[0]


def finalize_colored_point_cloud(
    point_chunks: list[np.ndarray],
    color_chunks: list[np.ndarray],
    conf_chunks: list[np.ndarray],
    frame_id_chunks: list[np.ndarray],
    *,
    total_random_points: int | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray | None]:
    if not point_chunks:
        raise ValueError("No points passed confidence threshold.")

    points_out = np.concatenate(point_chunks, axis=0)
    colors_out = np.concatenate(color_chunks, axis=0)
    conf_out = np.concatenate(conf_chunks, axis=0)
    frame_ids = np.concatenate(frame_id_chunks, axis=0) if frame_id_chunks else None

    if total_random_points is not None:
        total_random = resolve_random_sample_count(total_random_points, len(conf_out))
        if total_random < len(conf_out):
            rng = np.random.default_rng(0)
            idx = rng.choice(len(conf_out), size=total_random, replace=False)
            points_out = points_out[idx]
            colors_out = colors_out[idx]
            conf_out = conf_out[idx]
            if frame_ids is not None:
                frame_ids = frame_ids[idx]

    return points_out, colors_out, conf_out, frame_ids


def _voxel_key(point: np.ndarray, voxel_size: float) -> VoxelKey:
    cell = np.floor(point / voxel_size).astype(np.int64)
    return int(cell[0]), int(cell[1]), int(cell[2])


def _build_voxel_index(points: np.ndarray, voxel_size: float) -> dict[VoxelKey, list[int]]:
    index: dict[VoxelKey, list[int]] = defaultdict(list)
    for i in range(len(points)):
        index[_voxel_key(points[i], voxel_size)].append(i)
    return index


def _filter_points_3d_nms_voxel(
    points: np.ndarray,
    *,
    radius: float,
    min_neighbors: int,
) -> np.ndarray:
    """
    O(n) voxel-grid density filter (scipy fallback).

    With ``voxel_size == radius``, any neighbor within ``radius`` lies in the
    point's cell or one of the 26 adjacent cells; only those candidates need
    distance checks.
    """
    n = len(points)
    min_neighbors = int(min_neighbors)
    if n == 0:
        return np.zeros(0, dtype=bool)

    r2 = float(radius) ** 2
    voxel_size = float(radius)
    cells = np.floor(points / voxel_size).astype(np.int64)
    voxel_index = _build_voxel_index(points, voxel_size)

    keep = np.zeros(n, dtype=bool)
    offsets = (
        (dx, dy, dz)
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        for dz in (-1, 0, 1)
    )
    for i in range(n):
        cx, cy, cz = cells[i]
        count = 0
        pi = points[i]
        for dx, dy, dz in offsets:
            for j in voxel_index.get((int(cx + dx), int(cy + dy), int(cz + dz)), ()):
                if j == i:
                    continue
                delta = pi - points[j]
                if float(delta @ delta) <= r2:
                    count += 1
                    if count >= min_neighbors:
                        keep[i] = True
                        break
            if keep[i]:
                break
    return keep


def filter_points_3d_nms(
    points: np.ndarray,
    *,
    radius: float,
    min_neighbors: int,
) -> np.ndarray:
    """
    Per-frame density filter: keep points with >= ``min_neighbors`` others within ``radius``.

    Removes sparse airborne outliers that lack a local dense neighborhood.
    """
    n = len(points)
    if n == 0 or min_neighbors <= 0:
        return np.ones(n, dtype=bool)

    radius = float(radius)
    if radius <= 0:
        return np.ones(n, dtype=bool)

    min_neighbors = int(min_neighbors)
    if n <= min_neighbors:
        return np.zeros(n, dtype=bool)

    try:
        from scipy.spatial import cKDTree

        tree = cKDTree(points)
        try:
            neighbor_counts = tree.query_ball_point(
                points,
                r=radius,
                return_length=True,
                workers=-1,
            )
        except TypeError:
            neighbor_counts = tree.query_ball_point(
                points,
                r=radius,
                return_length=True,
            )
        neighbor_counts = np.asarray(neighbor_counts, dtype=np.int64).reshape(-1)
        return (neighbor_counts - 1) >= min_neighbors
    except ImportError:
        return _filter_points_3d_nms_voxel(
            points,
            radius=radius,
            min_neighbors=min_neighbors,
        )
