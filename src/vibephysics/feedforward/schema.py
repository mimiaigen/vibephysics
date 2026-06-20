"""Canonical feedforward reconstruction prediction schema."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


def is_compact_npz_payload(payload: dict) -> bool:
    """True for sampled colored-point saves (``points`` + ``colors``; may include ``depth``)."""
    return "points" in payload and "colors" in payload


def _storage_float16(arr: np.ndarray) -> np.ndarray:
    return np.asarray(arr, dtype=np.float16)


def _encode_float_storage(payload: dict) -> dict:
    encoded: dict = {}
    for key, value in payload.items():
        if isinstance(value, np.ndarray) and np.issubdtype(value.dtype, np.floating):
            encoded[key] = _storage_float16(value)
        else:
            encoded[key] = value
    return encoded


def _normalize_loaded_payload(payload: dict) -> dict:
    """Promote stored half-precision arrays back to float32 for downstream code."""
    for key, value in payload.items():
        if isinstance(value, np.ndarray) and np.issubdtype(value.dtype, np.floating):
            payload[key] = np.asarray(value, dtype=np.float32)
    return payload


@dataclass
class FeedforwardPrediction:
    depth: np.ndarray
    conf: np.ndarray
    extrinsic: np.ndarray
    intrinsic: np.ndarray
    world_points: np.ndarray
    image_paths: list[str]
    engine: str
    images: np.ndarray | None = None
    metadata: dict = field(default_factory=dict)
    compact_points: np.ndarray | None = None
    compact_colors: np.ndarray | None = None
    compact_frame_ids: np.ndarray | None = None

    def is_compact(self) -> bool:
        return self.compact_points is not None

    def to_viz_dict(self) -> dict:
        """Convert to dict expected by feedforward.visual import helpers."""
        if self.is_compact():
            payload = {
                "depth": self.depth,
                "points": self.compact_points,
                "colors": self.compact_colors,
                "conf": self.conf,
                "extrinsic": self.extrinsic,
                "intrinsic": self.intrinsic,
                "image_paths": self.image_paths,
                "engine": self.engine,
            }
            if self.compact_frame_ids is not None:
                payload["frame_ids"] = self.compact_frame_ids
        else:
            payload = {
                "depth": self.depth,
                "conf": self.conf,
                "extrinsic": self.extrinsic,
                "intrinsic": self.intrinsic,
                "world_points_from_depth": self.world_points,
                "image_paths": self.image_paths,
                "engine": self.engine,
            }
        if self.images is not None:
            payload["images"] = self.images
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload

    @classmethod
    def from_compact_dict(cls, payload: dict) -> FeedforwardPrediction:
        image_paths = payload.get("image_paths", [])
        if isinstance(image_paths, np.ndarray):
            image_paths = image_paths.tolist()
        engine = payload.get("engine", "unknown")
        if isinstance(engine, np.ndarray):
            engine = engine.item() if engine.ndim == 0 else str(engine.flat[0])
        metadata = dict(payload.get("metadata") or {})
        metadata.setdefault("compact", True)
        extrinsic = np.asarray(payload["extrinsic"], dtype=np.float32)
        n_frames = len(extrinsic)
        size = int(metadata.get("image_size") or 518)
        points = np.asarray(payload["points"], dtype=np.float32)
        frame_ids = payload.get("frame_ids")
        if frame_ids is not None:
            frame_ids = np.asarray(frame_ids, dtype=np.int32).reshape(-1)
        depth = payload.get("depth")
        if depth is not None:
            depth = np.asarray(depth, dtype=np.float32)
        else:
            depth = np.zeros((n_frames, size, size, 1), dtype=np.float32)
        return cls(
            depth=depth,
            conf=np.asarray(payload["conf"], dtype=np.float32).reshape(-1),
            extrinsic=extrinsic,
            intrinsic=np.asarray(payload["intrinsic"], dtype=np.float32),
            world_points=points,
            image_paths=list(image_paths),
            engine=str(engine),
            images=payload.get("images"),
            metadata=metadata,
            compact_points=points,
            compact_colors=np.asarray(payload["colors"], dtype=np.uint8),
            compact_frame_ids=frame_ids,
        )

    @classmethod
    def from_dict(cls, payload: dict) -> FeedforwardPrediction:
        if is_compact_npz_payload(payload):
            return cls.from_compact_dict(payload)
        world_points = payload.get("world_points")
        if world_points is None:
            world_points = payload.get("world_points_from_depth")
        image_paths = payload.get("image_paths", [])
        if isinstance(image_paths, np.ndarray):
            image_paths = image_paths.tolist()
        engine = payload.get("engine", "unknown")
        if isinstance(engine, np.ndarray):
            engine = engine.item() if engine.ndim == 0 else str(engine.flat[0])
        images = payload.get("images")
        return cls(
            depth=payload["depth"],
            conf=payload["conf"],
            extrinsic=payload["extrinsic"],
            intrinsic=payload["intrinsic"],
            world_points=world_points,
            image_paths=list(image_paths),
            engine=str(engine),
            images=images,
            metadata=payload.get("metadata", {}),
        )


def _npz_base_path(path: Path) -> Path:
    return path.with_suffix("") if path.suffix == ".npz" else path


def _write_npz_payload(path: Path, payload: dict, *, split_files: bool = False) -> None:
    payload = _encode_float_storage(payload)
    if not split_files:
        np.savez_compressed(path, **payload)
        return
    base = _npz_base_path(path)
    for key, value in payload.items():
        np.savez_compressed(base.parent / f"{base.name}.{key}.npz", **{key: value})


def load_npz_payload(path: Path | str) -> dict:
    """Load a monolithic predictions.npz or split predictions.<key>.npz siblings."""
    path = Path(path)
    if path.is_file():
        with np.load(path, allow_pickle=True) as data:
            return _normalize_loaded_payload({key: data[key] for key in data.files})
    base = _npz_base_path(path)
    parts = sorted(base.parent.glob(f"{base.name}.*.npz"))
    if not parts:
        raise FileNotFoundError(f"No monolithic or split NPZ at {path}")
    prefix = f"{base.name}."
    payload: dict = {}
    for part in parts:
        if not part.stem.startswith(prefix):
            continue
        key = part.stem[len(prefix) :]
        with np.load(part, allow_pickle=True) as data:
            payload[key] = data[key]
    if not payload:
        raise FileNotFoundError(f"No monolithic or split NPZ at {path}")
    return _normalize_loaded_payload(payload)


def save_prediction(
    path: Path,
    prediction: FeedforwardPrediction,
    *,
    split_files: bool = False,
) -> None:
    metadata = dict(prediction.metadata)
    metadata["float_storage"] = "float16"
    if split_files:
        metadata["split_files"] = True
    trajectory = prediction.extrinsic[:, :3, 3].astype(np.float32)
    payload = {
        "depth": prediction.depth,
        "conf": prediction.conf,
        "extrinsic": prediction.extrinsic,
        "intrinsic": prediction.intrinsic,
        "trajectory": trajectory,
        "world_points": prediction.world_points,
        "image_paths": np.array(prediction.image_paths, dtype=object),
        "engine": prediction.engine,
        "metadata": np.array([metadata], dtype=object),
    }
    if not split_files:
        payload["world_points_from_depth"] = prediction.world_points
    _write_npz_payload(path, payload, split_files=split_files)


def save_compact_prediction(
    path: Path,
    prediction: FeedforwardPrediction,
    *,
    min_confidence: float = 2.0,
    random_points_per_frame: int | float | None = None,
    total_random_points: int | float | None = None,
    point_cloud_3d_nms: bool = False,
    point_cloud_3d_nms_radius: float = 0.03,
    point_cloud_3d_nms_min_neighbors: int = 3,
    precomputed_points: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None = None,
    split_files: bool = False,
) -> None:
    """Save filtered colored 3D points plus camera pose/trajectory data."""
    from .common import collect_colored_point_cloud

    if precomputed_points is not None:
        points, colors, conf, frame_ids = precomputed_points
    else:
        points, colors, conf, frame_ids = collect_colored_point_cloud(
            prediction,
            min_confidence=min_confidence,
            to_blender=True,
            with_frame_ids=True,
            random_points_per_frame=random_points_per_frame,
            total_random_points=total_random_points,
            point_cloud_3d_nms=point_cloud_3d_nms,
            point_cloud_3d_nms_radius=point_cloud_3d_nms_radius,
            point_cloud_3d_nms_min_neighbors=point_cloud_3d_nms_min_neighbors,
        )
    trajectory = prediction.extrinsic[:, :3, 3].astype(np.float32)
    metadata = dict(prediction.metadata)
    metadata.update(
        {
            "float_storage": "float16",
            "sample_schema": "colored_points_pose_v1",
            "compact_min_confidence": float(min_confidence),
            "random_points_per_frame": random_points_per_frame,
            "total_random_points": total_random_points,
            "sample_point_count": int(points.shape[0]),
            "color_format": "uint8_rgb",
        }
    )
    if split_files:
        metadata["split_files"] = True
    payload = {
        "depth": prediction.depth,
        "points": points.astype(np.float32),
        "colors": colors.astype(np.uint8),
        "conf": conf.astype(np.float32),
        "frame_ids": frame_ids.astype(np.int32),
        "extrinsic": prediction.extrinsic.astype(np.float32),
        "intrinsic": prediction.intrinsic.astype(np.float32),
        "trajectory": trajectory,
        "image_paths": np.array(prediction.image_paths, dtype=object),
        "engine": prediction.engine,
        "metadata": np.array([metadata], dtype=object),
    }
    _write_npz_payload(path, payload, split_files=split_files)


def load_prediction(path: Path | str) -> FeedforwardPrediction:
    path = Path(path)
    payload = load_npz_payload(path)
    if "metadata" in payload:
        meta = payload["metadata"]
        payload["metadata"] = meta[0] if len(meta) else {}
    prediction = FeedforwardPrediction.from_dict(payload)
    _prefer_preprocessed_frame_paths(prediction, path.parent)
    return prediction


def _prefer_preprocessed_frame_paths(prediction: FeedforwardPrediction, output_dir: Path) -> None:
    """Use saved model-preprocessed frames for coloring when available."""
    frames_dir = output_dir / "frames"
    meta_dir = prediction.metadata.get("preprocessed_frames_dir")
    if meta_dir:
        frames_dir = Path(str(meta_dir))
    if not frames_dir.is_dir():
        return

    frames = sorted(frames_dir.glob("frame_*.jpg"))
    if len(frames) < len(prediction.image_paths):
        return

    prediction.image_paths = [str(frame.resolve()) for frame in frames[: len(prediction.image_paths)]]


def save_reconstruct_config(path: Path, config: dict) -> None:
    path.write_text(json.dumps(config, indent=2))
