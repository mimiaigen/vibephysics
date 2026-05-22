"""Shared utilities for feedforward reconstruction adapters."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".JPG", ".PNG"}

DEFAULT_LINGBOT_MAP_MODEL = "lingbot-map"
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


def is_lingbot_map_engine(engine: str) -> bool:
    engine = str(engine)
    return engine == "lingbot_map" or engine == "lingbot" or engine.startswith("lingbot_map")


def is_vggt_omega_engine(engine: str) -> bool:
    engine = str(engine)
    return engine == "vggt_omega" or engine == "vggt" or engine.startswith("vggt_omega")


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
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if len(image_paths) <= batch_size:
        return image_paths, list(range(len(image_paths)))

    indices = np.linspace(0, len(image_paths) - 1, batch_size, dtype=int)
    indices = sorted(set(indices.tolist()))
    selected = [image_paths[i] for i in indices]
    return selected, indices


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
        import torch

        if torch.cuda.is_available():
            free, total = torch.cuda.mem_get_info()
            return total / (1024**3)
    except Exception:
        pass
    return None


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
    min_confidence: float = 0.5,
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

    if is_vggt_omega_engine(engine):
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


def _opencv_to_blender_points(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float64)
    out = np.empty_like(points)
    out[:, 0] = points[:, 0]
    out[:, 1] = points[:, 2]
    out[:, 2] = -points[:, 1]
    return out


def collect_colored_point_cloud(
    predictions,
    min_confidence: float = 0.5,
    *,
    to_blender: bool = True,
    with_frame_ids: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray | None]:
    """Return filtered (N,3) positions, (N,3) uint8 RGB, (N,) conf, optional frame ids."""
    from .schema import FeedforwardPrediction

    if isinstance(predictions, FeedforwardPrediction):
        payload = predictions.to_viz_dict()
    else:
        payload = predictions

    points = payload.get("world_points_from_depth", payload.get("world_points"))
    images = resolve_frame_images(payload)
    conf = payload["conf"]

    point_chunks: list[np.ndarray] = []
    color_chunks: list[np.ndarray] = []
    conf_chunks: list[np.ndarray] = []
    frame_id_chunks: list[np.ndarray] = []

    for frame_idx in range(points.shape[0]):
        frame_points = points[frame_idx].reshape(-1, 3)
        frame_colors = images[frame_idx].reshape(-1, 3)
        frame_conf = conf[frame_idx].reshape(-1)
        valid_mask = np.isfinite(frame_points).all(axis=1)
        if min_confidence > 0:
            valid_mask &= frame_conf >= min_confidence
        if not np.any(valid_mask):
            continue
        pts = frame_points[valid_mask]
        if to_blender:
            pts = _opencv_to_blender_points(pts)
        point_chunks.append(pts.astype(np.float32))
        rgb = np.clip(frame_colors[valid_mask], 0.0, 1.0)
        color_chunks.append((rgb * 255.0).astype(np.uint8))
        conf_chunks.append(frame_conf[valid_mask].astype(np.float32))
        if with_frame_ids:
            frame_id_chunks.append(np.full(int(valid_mask.sum()), frame_idx, dtype=np.int32))

    if not point_chunks:
        raise ValueError("No points passed confidence threshold.")

    frame_ids = np.concatenate(frame_id_chunks, axis=0) if with_frame_ids else None
    return (
        np.concatenate(point_chunks, axis=0),
        np.concatenate(color_chunks, axis=0),
        np.concatenate(conf_chunks, axis=0),
        frame_ids,
    )
