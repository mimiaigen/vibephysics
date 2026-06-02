"""Canonical feedforward reconstruction prediction schema."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


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

    def to_viz_dict(self) -> dict:
        """Convert to dict expected by feedforward.visual import helpers."""
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
    def from_dict(cls, payload: dict) -> FeedforwardPrediction:
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


def save_prediction(path: Path, prediction: FeedforwardPrediction) -> None:
    payload = {
        "depth": prediction.depth,
        "conf": prediction.conf,
        "extrinsic": prediction.extrinsic,
        "intrinsic": prediction.intrinsic,
        "world_points": prediction.world_points,
        "world_points_from_depth": prediction.world_points,
        "image_paths": np.array(prediction.image_paths, dtype=object),
        "engine": prediction.engine,
        "metadata": np.array([prediction.metadata], dtype=object),
    }
    np.savez_compressed(path, **payload)


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
            "compact": True,
            "compact_schema": "colored_points_pose_v1",
            "compact_min_confidence": float(min_confidence),
            "random_points_per_frame": random_points_per_frame,
            "total_random_points": total_random_points,
            "compact_point_count": int(points.shape[0]),
            "color_format": "uint8_rgb",
        }
    )
    payload = {
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
    np.savez_compressed(path, **payload)


def load_prediction(path: Path | str) -> FeedforwardPrediction:
    path = Path(path)
    data = np.load(path, allow_pickle=True)
    payload = {key: data[key] for key in data.files}
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
