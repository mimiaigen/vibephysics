"""2D instance segmentation (RF-DETR) for class masks and masked 3D change bboxes."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from ..common import feedforward_engine_dir, feedforward_hf_hub_cache, resolve_frame_images
from ..schema import FeedforwardPrediction

DEFAULT_DETECTION_SEG_MODEL = "Roboflow/rf-detr-seg-medium"

# COCO 2017 thing names (RF-DETR seg uses standard COCO id2label).
CLASS_ALIASES: dict[str, str] = {
    "human": "person",
    "humans": "person",
    "people": "person",
    "pedestrian": "person",
    "pedestrians": "person",
    "automobile": "car",
    "automobiles": "car",
    "vehicle": "car",
    "vehicles": "car",
}


@dataclass
class DetectionSegConfig:
    enabled: bool = False
    model: str = DEFAULT_DETECTION_SEG_MODEL
    classes: list[str] = field(default_factory=lambda: ["person"])
    class_colors: dict[str, tuple[float, float, float, float]] = field(
        default_factory=dict
    )
    threshold: float = 0.5
    save_masks: bool = True


@dataclass
class InstanceMask:
    """One RF-DETR instance (not merged with other instances of the same class)."""

    class_name: str
    instance_index: int
    mask: np.ndarray
    score: float = 0.0
    segment_id: int = 0


@dataclass
class FrameClassMasks:
    """Per-frame instance masks aligned to reconstruction depth resolution (H, W)."""

    instances: list[InstanceMask] = field(default_factory=list)


def instance_bbox_label(class_name: str, instance_index: int = 0) -> str:
    """Detection instance label (class name only; no #N suffix)."""
    return class_name


def iter_frame_instances(
    detection: DetectionSegResult,
    frame_idx: int,
    *,
    class_name: str | None = None,
) -> list[InstanceMask]:
    if frame_idx < 0 or frame_idx >= len(detection.frame_masks):
        return []
    instances = detection.frame_masks[frame_idx].instances
    if class_name is None:
        return list(instances)
    return [inst for inst in instances if inst.class_name == class_name]


@dataclass
class DetectionSegResult:
    model: str
    classes: list[str]
    threshold: float
    frame_masks: list[FrameClassMasks]
    label_to_id: dict[str, int] = field(default_factory=dict)
    class_colors: dict[str, tuple[float, float, float, float]] = field(
        default_factory=dict
    )


def normalize_class_names(classes: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in classes:
        name = CLASS_ALIASES.get(str(raw).strip().lower(), str(raw).strip().lower())
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(name)
    if not out:
        out.append("person")
    return out


def _configure_hf_cache() -> None:
    hf_home = feedforward_engine_dir("huggingface")
    os.environ.setdefault("HF_HOME", str(hf_home))


def ensure_detection_seg_dependencies(*, verbose: bool = True) -> None:
    from ..deps import ensure_engine_dependencies

    if not ensure_engine_dependencies("detection_seg", verbose=verbose):
        raise RuntimeError(
            "detection_seg dependencies missing (torch, transformers, huggingface_hub). "
            "Install with: pip install transformers huggingface_hub"
        )


def resolve_label_ids(model, class_names: list[str]) -> dict[str, int]:
    id2label = getattr(model.config, "id2label", None) or {}
    name_to_id: dict[str, int] = {}
    for key, label in id2label.items():
        name_to_id[str(label).strip().lower()] = int(key)

    resolved: dict[str, int] = {}
    missing: list[str] = []
    for cls in class_names:
        label_id = name_to_id.get(cls)
        if label_id is None:
            missing.append(cls)
            continue
        resolved[cls] = label_id
    if missing:
        known = ", ".join(sorted(name_to_id.keys())[:20])
        raise ValueError(
            f"Unknown detection_seg class(es): {missing}. "
            f"Model labels include (sample): {known}..."
        )
    return resolved


def _load_model_and_processor(model_id: str, *, verbose: bool):
    import torch
    from transformers import AutoImageProcessor, RfDetrForInstanceSegmentation

    _configure_hf_cache()
    cache_dir = feedforward_engine_dir("detection_seg") / "models"
    cache_dir.mkdir(parents=True, exist_ok=True)
    if verbose:
        print(
            f"--- [vibephysics] Loading detection_seg model: {model_id} "
            f"(cache: {feedforward_hf_hub_cache()}) ---",
            flush=True,
        )
    processor = AutoImageProcessor.from_pretrained(
        model_id,
        cache_dir=str(feedforward_hf_hub_cache()),
    )
    model = RfDetrForInstanceSegmentation.from_pretrained(
        model_id,
        cache_dir=str(feedforward_hf_hub_cache()),
    )
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    model.eval()
    return model, processor, device


def _segment_frame(
    rgb_u8: np.ndarray,
    *,
    model,
    processor,
    device: str,
    label_id_to_class: dict[int, str],
    threshold: float,
    target_size: tuple[int, int],
) -> list[InstanceMask]:
    """Return one mask per detected instance (no OR merge across instances)."""
    import torch
    from PIL import Image

    h, w = target_size
    image = Image.fromarray(rgb_u8)
    inputs = processor(images=image, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)
    processed = processor.post_process_instance_segmentation(
        outputs,
        threshold=float(threshold),
        target_sizes=[(h, w)],
    )
    if not processed:
        return []

    item = processed[0]
    seg_map = np.asarray(item["segmentation"])
    segments = sorted(
        item.get("segments_info", []),
        key=lambda info: float(info.get("score", 0.0)),
        reverse=True,
    )
    per_class_index: dict[str, int] = {}
    instances: list[InstanceMask] = []
    for info in segments:
        label_id = int(info["label_id"])
        class_name = label_id_to_class.get(label_id)
        if class_name is None:
            continue
        inst_id = int(info["id"])
        mask = seg_map == inst_id
        if not mask.any():
            continue
        instance_index = per_class_index.get(class_name, 0)
        per_class_index[class_name] = instance_index + 1
        instances.append(
            InstanceMask(
                class_name=class_name,
                instance_index=instance_index,
                mask=mask.copy(),
                score=float(info.get("score", 0.0)),
                segment_id=inst_id,
            )
        )
    return instances


def run_detection_segmentation(
    prediction: FeedforwardPrediction,
    config: DetectionSegConfig,
    *,
    verbose: bool = True,
) -> DetectionSegResult:
    """Run RF-DETR per frame; one mask per instance (not merged per class)."""
    ensure_detection_seg_dependencies(verbose=verbose)
    class_names = normalize_class_names(config.classes)
    model_id = str(config.model or DEFAULT_DETECTION_SEG_MODEL).strip()
    threshold = float(config.threshold)

    model, processor, device = _load_model_and_processor(model_id, verbose=verbose)
    label_to_id = resolve_label_ids(model, class_names)
    label_id_to_class = {label_id: cls for cls, label_id in label_to_id.items()}

    images = resolve_frame_images(prediction.to_viz_dict())
    num_frames = int(images.shape[0])
    height, width = int(images.shape[1]), int(images.shape[2])

    frame_masks: list[FrameClassMasks] = []
    for frame_idx in range(num_frames):
        rgb_u8 = (np.clip(images[frame_idx], 0.0, 1.0) * 255.0).astype(np.uint8)
        instances = _segment_frame(
            rgb_u8,
            model=model,
            processor=processor,
            device=device,
            label_id_to_class=label_id_to_class,
            threshold=threshold,
            target_size=(height, width),
        )
        frame_masks.append(FrameClassMasks(instances=instances))
        if verbose:
            per_class: dict[str, int] = {cls: 0 for cls in class_names}
            pixels: dict[str, int] = {cls: 0 for cls in class_names}
            for inst in instances:
                per_class[inst.class_name] = per_class.get(inst.class_name, 0) + 1
                pixels[inst.class_name] = pixels.get(inst.class_name, 0) + int(
                    inst.mask.sum()
                )
            print(
                f"[vibephysics] detection_seg: frame {frame_idx} "
                f"instances={per_class} mask_pixels={pixels}",
                flush=True,
            )

    return DetectionSegResult(
        model=model_id,
        classes=class_names,
        threshold=threshold,
        frame_masks=frame_masks,
        label_to_id=label_to_id,
        class_colors=dict(config.class_colors),
    )


def save_detection_masks(output_dir: Path, result: DetectionSegResult) -> Path:
    """Write masks only when a class is detected (non-empty) on that frame."""
    from PIL import Image

    root = Path(output_dir) / "detection_seg"
    mask_dir = root / "masks"
    mask_dir.mkdir(parents=True, exist_ok=True)

    paths: list[dict[str, Any]] = []
    for frame_idx, frame in enumerate(result.frame_masks):
        for inst in frame.instances:
            pixels = int(inst.mask.sum())
            if pixels == 0:
                continue
            out_path = (
                mask_dir
                / f"frame_{frame_idx:04d}_{inst.class_name}_{inst.instance_index:02d}.png"
            )
            Image.fromarray((inst.mask.astype(np.uint8) * 255)).save(out_path)
            paths.append(
                {
                    "frame": frame_idx,
                    "class": inst.class_name,
                    "instance_index": inst.instance_index,
                    "score": inst.score,
                    "path": str(out_path.relative_to(root)),
                    "pixels": pixels,
                }
            )

    manifest = {
        "model": result.model,
        "classes": result.classes,
        "threshold": result.threshold,
        "label_to_id": result.label_to_id,
        "class_colors": {
            cls: list(rgba) for cls, rgba in result.class_colors.items()
        },
        "masks": paths,
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return root


def _extrinsic_4x4(prediction: FeedforwardPrediction, frame_idx: int) -> np.ndarray:
    ext = np.asarray(prediction.extrinsic[frame_idx], dtype=np.float64)
    if ext.shape == (4, 4):
        return ext
    return np.vstack([ext.reshape(3, 4), [0.0, 0.0, 0.0, 1.0]])


def _world_to_opencv_camera(
    points: np.ndarray,
    prediction: FeedforwardPrediction,
    frame_idx: int,
) -> np.ndarray:
    """
    Map world points (same layout as ``prediction.world_points``) to OpenCV camera
    coords (Z forward, Y down) for pinhole projection with ``intrinsic``.
    """
    from ..common import is_blender_z_up

    pts = np.asarray(points, dtype=np.float64)
    hom = np.hstack([pts, np.ones((len(pts), 1))])
    ext4 = _extrinsic_4x4(prediction, frame_idx)

    if is_blender_z_up(prediction) and prediction.metadata.get("extrinsic_is_matrix_world"):
        cam = (np.linalg.inv(ext4) @ hom.T).T[:, :3]
        cam[:, 1] *= -1.0
        cam[:, 2] *= -1.0
        return cam

    w2c_as_camera_pose = bool(prediction.metadata.get("w2c_as_camera_pose"))
    w2c = ext4 if w2c_as_camera_pose else np.linalg.inv(ext4)
    return (w2c @ hom.T).T[:, :3]


def project_world_points_to_mask(
    points: np.ndarray,
    mask: np.ndarray,
    prediction: FeedforwardPrediction,
    frame_idx: int,
) -> np.ndarray:
    """Keep 3D points that project into ``True`` mask pixels (same coords as ``world_points``)."""
    if len(points) == 0:
        return points
    h, w = mask.shape
    k = np.asarray(prediction.intrinsic[frame_idx], dtype=np.float64)
    cam = _world_to_opencv_camera(points, prediction, frame_idx)
    z = cam[:, 2]
    valid = z > 1e-6
    u = k[0, 0] * cam[:, 0] / np.maximum(z, 1e-9) + k[0, 2]
    v = k[1, 1] * cam[:, 1] / np.maximum(z, 1e-9) + k[1, 2]
    ui = np.floor(u + 0.5).astype(np.int32)
    vi = np.floor(v + 0.5).astype(np.int32)
    in_bounds = (
        valid
        & (ui >= 0)
        & (ui < w)
        & (vi >= 0)
        & (vi < h)
    )
    keep = np.zeros(len(points), dtype=bool)
    idx = np.where(in_bounds)[0]
    keep[idx] = mask[vi[idx], ui[idx]]
    return points[keep]


def detection_seg_reference_frame(
    detection: DetectionSegResult,
    class_name: str,
    preferred_frame: int = 0,
    *,
    instance_index: int = 0,
) -> int | None:
    """First frame with a non-empty instance mask (prefers ``preferred_frame``)."""
    num_frames = len(detection.frame_masks)

    def _has_instance(frame_idx: int) -> bool:
        for inst in iter_frame_instances(detection, frame_idx, class_name=class_name):
            if inst.instance_index == instance_index and inst.mask.any():
                return True
        return False

    if 0 <= preferred_frame < num_frames and _has_instance(preferred_frame):
        return preferred_frame
    for frame_idx in range(num_frames):
        if _has_instance(frame_idx):
            return frame_idx
    return None


def _collect_points_under_mask(
    prediction: FeedforwardPrediction,
    frame_idx: int,
    mask: np.ndarray,
    *,
    min_confidence: float = 0.0,
) -> np.ndarray:
    """3D points under one instance mask (same grid as ``world_points``)."""
    if mask is None or not mask.any():
        return np.empty((0, 3), dtype=np.float64)

    wp = np.asarray(prediction.world_points[frame_idx], dtype=np.float64)
    if wp.ndim != 3 or wp.shape[:2] != mask.shape:
        flat = wp.reshape(-1, 3)
        return project_world_points_to_mask(flat, mask, prediction, frame_idx)

    conf = np.asarray(prediction.conf[frame_idx], dtype=np.float64)
    valid = np.isfinite(wp).all(axis=-1) & mask
    if min_confidence > 0:
        valid &= conf >= min_confidence
    return wp[valid]


def collect_masked_frame_points(
    prediction: FeedforwardPrediction,
    frame_idx: int,
    detection: DetectionSegResult,
    class_name: str,
    *,
    instance_index: int | None = None,
    instance: InstanceMask | None = None,
    min_confidence: float = 0.0,
) -> np.ndarray:
    """
    3D points under one instance mask (never merges instances of the same class).

    Pass ``instance`` or ``(class_name, instance_index)``.
    """
    if instance is not None:
        mask = instance.mask
    elif instance_index is not None:
        matches = [
            inst
            for inst in iter_frame_instances(
                detection, frame_idx, class_name=class_name
            )
            if inst.instance_index == instance_index
        ]
        if not matches:
            return np.empty((0, 3), dtype=np.float64)
        mask = matches[0].mask
    else:
        raise ValueError(
            "collect_masked_frame_points requires instance_index or instance= "
            "(class-wide merged masks are not supported)"
        )
    if frame_idx < 0 or frame_idx >= len(detection.frame_masks):
        return np.empty((0, 3), dtype=np.float64)
    return _collect_points_under_mask(
        prediction, frame_idx, mask, min_confidence=min_confidence
    )


def filter_points_by_instance_mask(
    points: np.ndarray,
    prediction: FeedforwardPrediction,
    frame_idx: int,
    instance: InstanceMask,
) -> np.ndarray:
    """Project an arbitrary point list through one instance mask."""
    if not instance.mask.any():
        return np.empty((0, 3), dtype=points.dtype)
    return project_world_points_to_mask(points, instance.mask, prediction, frame_idx)


def filter_points_by_class_mask(
    points: np.ndarray,
    prediction: FeedforwardPrediction,
    frame_idx: int,
    detection: DetectionSegResult,
    class_name: str,
    *,
    instance_index: int = 0,
) -> np.ndarray:
    """Legacy alias: one instance only (default ``instance_index=0``)."""
    matches = iter_frame_instances(detection, frame_idx, class_name=class_name)
    for inst in matches:
        if inst.instance_index == instance_index:
            return filter_points_by_instance_mask(
                points, prediction, frame_idx, inst
            )
    return np.empty((0, 3), dtype=points.dtype)


def detection_seg_config_from_dict(section: dict[str, Any] | None) -> DetectionSegConfig:
    from ..config import parse_detection_seg_classes

    section = section or {}
    classes, class_colors = parse_detection_seg_classes(
        section.get("classes", ["person"])
    )
    return DetectionSegConfig(
        enabled=bool(section.get("enabled", False)),
        model=str(section.get("model", DEFAULT_DETECTION_SEG_MODEL)),
        classes=classes,
        class_colors=class_colors,
        threshold=float(section.get("threshold", 0.5)),
        save_masks=bool(section.get("save_masks", True)),
    )
