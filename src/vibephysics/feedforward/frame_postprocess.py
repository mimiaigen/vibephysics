"""Parallel per-frame 3D NMS (point cloud) and change-bbox detection."""

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from .algo_3d_bbox import (
    BboxReferenceContext,
    ChangeBBox,
    _bbox_uses_point_cloud_pipeline,
    compute_bbox_for_frame,
    compute_masked_occupancy_bbox_for_frame,
    prepare_bbox_reference,
)
from .common import (
    collect_single_frame_point_chunk,
    collect_single_frame_world_points,
    filter_points_3d_nms,
    is_blender_z_up,
    opencv_to_blender_points,
)
from .schema import FeedforwardPrediction

if TYPE_CHECKING:
    from .detection_seg import DetectionSegResult

FrameBboxEntry = list[ChangeBBox] | None


@dataclass
class PerFramePostprocessTimings:
    wall_s: float = 0.0
    nms_cpu_s: float = 0.0
    bbox_cpu_s: float = 0.0
    nms_removed_total: int = 0


@dataclass
class PerFramePostprocessResult:
    bboxes: list[FrameBboxEntry] | None
    point_chunks: list[np.ndarray] = field(default_factory=list)
    color_chunks: list[np.ndarray] = field(default_factory=list)
    conf_chunks: list[np.ndarray] = field(default_factory=list)
    frame_id_chunks: list[np.ndarray] = field(default_factory=list)
    timings: PerFramePostprocessTimings = field(default_factory=PerFramePostprocessTimings)


@dataclass
class _FrameWorkResult:
    frame_idx: int
    bboxes: FrameBboxEntry = None
    points: np.ndarray | None = None
    colors_u8: np.ndarray | None = None
    conf: np.ndarray | None = None
    nms_removed: int = 0
    nms_elapsed_s: float = 0.0
    bbox_elapsed_s: float = 0.0


def _default_max_workers(num_frames: int) -> int:
    cpus = os.cpu_count() or 4
    return max(1, min(int(num_frames), int(cpus)))


def _frame_points_for_bbox(
    prediction: FeedforwardPrediction,
    frame_idx: int,
    *,
    min_confidence: float,
    point_cloud_3d_nms: bool,
    nms_radius: float,
    nms_min_neighbors: int,
    random_points_per_frame: int | None,
) -> np.ndarray | None:
    if _bbox_uses_point_cloud_pipeline(
        point_cloud_3d_nms=point_cloud_3d_nms,
        random_points_per_frame=random_points_per_frame,
    ):
        return collect_single_frame_world_points(
            prediction,
            frame_idx,
            min_confidence=min_confidence,
            point_cloud_3d_nms=point_cloud_3d_nms,
            point_cloud_3d_nms_radius=nms_radius,
            point_cloud_3d_nms_min_neighbors=nms_min_neighbors,
            random_points_per_frame=random_points_per_frame,
            rng_seed=frame_idx,
        )
    from .algo_3d_bbox import _frame_points

    return _frame_points(prediction, frame_idx, min_confidence=min_confidence)


def _apply_optional_nms(
    points: np.ndarray,
    *,
    run_nms: bool,
    nms_radius: float,
    nms_min_neighbors: int,
) -> tuple[np.ndarray, int]:
    if not run_nms or len(points) == 0:
        return points, 0
    keep = filter_points_3d_nms(
        points,
        radius=nms_radius,
        min_neighbors=nms_min_neighbors,
    )
    return points[keep], int((~keep).sum())


def _frame_points_masked_for_bbox(
    prediction: FeedforwardPrediction,
    frame_idx: int,
    *,
    min_confidence: float,
    run_nms: bool,
    nms_radius: float,
    nms_min_neighbors: int,
    random_points_per_frame: int | None,
    detection: DetectionSegResult | None,
    instance: "InstanceMask | None" = None,
) -> np.ndarray | None:
    """Confidence (+ subsample), optional instance mask, then optional NMS."""
    if detection is not None and instance is not None:
        from .detection_seg import collect_masked_frame_points

        pts = collect_masked_frame_points(
            prediction,
            frame_idx,
            detection,
            instance.class_name,
            instance=instance,
            min_confidence=min_confidence,
        )
        if len(pts) == 0:
            return None
    else:
        pts = _frame_points_for_bbox(
            prediction,
            frame_idx,
            min_confidence=min_confidence,
            point_cloud_3d_nms=False,
            nms_radius=nms_radius,
            nms_min_neighbors=nms_min_neighbors,
            random_points_per_frame=random_points_per_frame,
        )
        if pts is None or len(pts) == 0:
            return None
    pts, _ = _apply_optional_nms(
        pts,
        run_nms=run_nms,
        nms_radius=nms_radius,
        nms_min_neighbors=nms_min_neighbors,
    )
    return pts if len(pts) > 0 else None


def _prepare_bbox_contexts(
    prediction: FeedforwardPrediction,
    *,
    bbox_reference_frame: int,
    min_confidence: float,
    point_cloud_3d_nms: bool,
    nms_radius: float,
    nms_min_neighbors: int,
    random_points_per_frame: int | None,
    bbox_kwargs: dict,
    detection: DetectionSegResult | None,
) -> dict[str, BboxReferenceContext]:
    min_changed = int(bbox_kwargs.get("min_changed_voxels", 12))
    voxel_size = float(bbox_kwargs.get("voxel_size", 0.02))
    min_points_per_voxel = int(bbox_kwargs.get("min_points_per_voxel", 1))

    if detection is not None:
        return {cls: None for cls in detection.classes}

    return {
        "_default": prepare_bbox_reference(
            prediction,
            reference_frame=bbox_reference_frame,
            min_confidence=min_confidence,
            voxel_size=voxel_size,
            min_changed_voxels=min_changed,
            min_points_per_voxel=min_points_per_voxel,
            point_cloud_3d_nms=point_cloud_3d_nms,
            point_cloud_3d_nms_radius=nms_radius,
            point_cloud_3d_nms_min_neighbors=nms_min_neighbors,
            random_points_per_frame=random_points_per_frame,
        )
    }


def _compute_bboxes_for_frame(
    prediction: FeedforwardPrediction,
    frame_idx: int,
    *,
    bbox_contexts: dict[str, BboxReferenceContext],
    min_confidence: float,
    point_cloud_3d_nms: bool,
    nms_radius: float,
    nms_min_neighbors: int,
    random_points_per_frame: int | None,
    bbox_kwargs: dict,
    detection: DetectionSegResult | None,
    frame_points: np.ndarray | None = None,
) -> list[ChangeBBox]:
    if detection is None:
        ctx = bbox_contexts.get("_default")
        if ctx is None or frame_idx == ctx.reference_frame:
            return []
        if frame_points is None:
            frame_points = _frame_points_for_bbox(
                prediction,
                frame_idx,
                min_confidence=min_confidence,
                point_cloud_3d_nms=point_cloud_3d_nms,
                nms_radius=nms_radius,
                nms_min_neighbors=nms_min_neighbors,
                random_points_per_frame=random_points_per_frame,
            )
        if frame_points is None or len(frame_points) == 0:
            return []
        bbox = compute_bbox_for_frame(
            prediction,
            frame_idx,
            ctx,
            min_confidence=min_confidence,
            frame_points=frame_points,
            **bbox_kwargs,
        )
        return [bbox] if bbox is not None else []

    from .detection_seg import instance_bbox_label, iter_frame_instances

    found: list[ChangeBBox] = []
    for inst in iter_frame_instances(detection, frame_idx):
        masked = _frame_points_masked_for_bbox(
            prediction,
            frame_idx,
            min_confidence=min_confidence,
            run_nms=False,
            nms_radius=nms_radius,
            nms_min_neighbors=nms_min_neighbors,
            random_points_per_frame=random_points_per_frame,
            detection=detection,
            instance=inst,
        )
        if masked is None:
            continue
        bbox = compute_masked_occupancy_bbox_for_frame(
            frame_idx,
            masked,
            label=instance_bbox_label(inst.class_name, inst.instance_index),
            voxel_size=float(bbox_kwargs.get("voxel_size", 0.02)),
            min_cluster_voxels=int(bbox_kwargs.get("min_cluster_voxels", 8)),
            cluster_gap_close=int(bbox_kwargs.get("cluster_gap_close", 1)),
            min_points_per_voxel=int(bbox_kwargs.get("min_points_per_voxel", 1)),
            padding=float(bbox_kwargs.get("padding", 0.01)),
            verbose=bool(bbox_kwargs.get("verbose", False)),
            mode="masked_cluster",
        )
        if bbox is not None:
            found.append(bbox)
    return found


def _process_one_frame(
    frame_idx: int,
    prediction: FeedforwardPrediction,
    *,
    min_confidence: float,
    run_nms: bool,
    nms_radius: float,
    nms_min_neighbors: int,
    to_blender: bool,
    run_bbox: bool,
    bbox_contexts: dict[str, BboxReferenceContext],
    bbox_kwargs: dict,
    random_points_per_frame: int | None,
    detection: DetectionSegResult | None,
) -> _FrameWorkResult:
    out = _FrameWorkResult(frame_idx=frame_idx)
    if detection is not None:
        need_bbox = run_bbox and bool(bbox_contexts)
    else:
        ref_frame = (
            next(iter(bbox_contexts.values())).reference_frame if bbox_contexts else 0
        )
        need_bbox = run_bbox and bool(bbox_contexts) and frame_idx != ref_frame
    use_point_pipeline = _bbox_uses_point_cloud_pipeline(
        point_cloud_3d_nms=run_nms,
        random_points_per_frame=random_points_per_frame,
    )

    def _store_export_chunk(pts: np.ndarray, rgb: np.ndarray, conf: np.ndarray) -> None:
        if to_blender and not is_blender_z_up(prediction):
            pts = opencv_to_blender_points(pts)
        out.points = pts.astype(np.float32)
        out.colors_u8 = rgb
        out.conf = conf

    if need_bbox and (use_point_pipeline or detection is not None):
        if detection is not None:
            t0 = time.perf_counter()
            out.bboxes = _compute_bboxes_for_frame(
                prediction,
                frame_idx,
                bbox_contexts=bbox_contexts,
                min_confidence=min_confidence,
                point_cloud_3d_nms=run_nms,
                nms_radius=nms_radius,
                nms_min_neighbors=nms_min_neighbors,
                random_points_per_frame=random_points_per_frame,
                bbox_kwargs=bbox_kwargs,
                detection=detection,
            ) or None
            out.bbox_elapsed_s = time.perf_counter() - t0
            if run_nms:
                chunk = collect_single_frame_point_chunk(
                    prediction,
                    frame_idx,
                    min_confidence=min_confidence,
                    point_cloud_3d_nms=True,
                    point_cloud_3d_nms_radius=nms_radius,
                    point_cloud_3d_nms_min_neighbors=nms_min_neighbors,
                    random_points_per_frame=random_points_per_frame,
                    rng_seed=frame_idx,
                )
                if chunk is not None:
                    pts, rgb, conf, removed = chunk
                    out.nms_removed = removed
                    _store_export_chunk(pts, rgb, conf)
            return out

        t0 = time.perf_counter()
        chunk = collect_single_frame_point_chunk(
            prediction,
            frame_idx,
            min_confidence=min_confidence,
            point_cloud_3d_nms=run_nms,
            point_cloud_3d_nms_radius=nms_radius,
            point_cloud_3d_nms_min_neighbors=nms_min_neighbors,
            random_points_per_frame=random_points_per_frame,
            rng_seed=frame_idx,
        )
        out.nms_elapsed_s = time.perf_counter() - t0
        frame_points = None
        if chunk is not None:
            frame_points, rgb, conf, removed = chunk
            out.nms_removed = removed
            if run_nms:
                _store_export_chunk(frame_points, rgb, conf)
        t1 = time.perf_counter()
        out.bboxes = _compute_bboxes_for_frame(
            prediction,
            frame_idx,
            bbox_contexts=bbox_contexts,
            min_confidence=min_confidence,
            point_cloud_3d_nms=run_nms,
            nms_radius=nms_radius,
            nms_min_neighbors=nms_min_neighbors,
            random_points_per_frame=random_points_per_frame,
            bbox_kwargs=bbox_kwargs,
            detection=detection,
            frame_points=frame_points,
        ) or None
        out.bbox_elapsed_s = time.perf_counter() - t1
        return out

    if run_nms:
        t0 = time.perf_counter()
        chunk = collect_single_frame_point_chunk(
            prediction,
            frame_idx,
            min_confidence=min_confidence,
            point_cloud_3d_nms=True,
            point_cloud_3d_nms_radius=nms_radius,
            point_cloud_3d_nms_min_neighbors=nms_min_neighbors,
            random_points_per_frame=random_points_per_frame,
            rng_seed=frame_idx,
        )
        out.nms_elapsed_s = time.perf_counter() - t0
        if chunk is None:
            return out
        pts, rgb, conf, removed = chunk
        out.nms_removed = removed
        _store_export_chunk(pts, rgb, conf)
        return out

    if need_bbox:
        t0 = time.perf_counter()
        boxes = _compute_bboxes_for_frame(
            prediction,
            frame_idx,
            bbox_contexts=bbox_contexts,
            min_confidence=min_confidence,
            point_cloud_3d_nms=run_nms,
            nms_radius=nms_radius,
            nms_min_neighbors=nms_min_neighbors,
            random_points_per_frame=random_points_per_frame,
            bbox_kwargs=bbox_kwargs,
            detection=detection,
        )
        out.bboxes = boxes or None
        out.bbox_elapsed_s = time.perf_counter() - t0

    return out


def run_per_frame_postprocess(
    prediction: FeedforwardPrediction,
    *,
    min_confidence: float,
    point_cloud_3d_nms: bool = False,
    point_cloud_3d_nms_radius: float = 0.03,
    point_cloud_3d_nms_min_neighbors: int = 3,
    to_blender: bool = True,
    with_frame_ids: bool = False,
    random_points_per_frame: int | None = None,
    algo_3d_bbox: bool = False,
    bbox_reference_frame: int = 0,
    bbox_kwargs: dict | None = None,
    detection_seg: DetectionSegResult | None = None,
    max_workers: int | None = None,
) -> PerFramePostprocessResult:
    """
    Run 3D NMS and/or per-frame bbox work in parallel across frames.

    With ``detection_seg``, bbox fits the largest masked point cluster per frame
    (no reference-frame diff; static objects in the mask are included). Tagged by class.
    """
    num_frames = int(prediction.world_points.shape[0])
    workers = max_workers if max_workers is not None else _default_max_workers(num_frames)
    bbox_kwargs = dict(bbox_kwargs or {})
    bbox_contexts: dict[str, BboxReferenceContext] = {}
    if algo_3d_bbox:
        bbox_contexts = _prepare_bbox_contexts(
            prediction,
            bbox_reference_frame=bbox_reference_frame,
            min_confidence=min_confidence,
            point_cloud_3d_nms=point_cloud_3d_nms,
            nms_radius=point_cloud_3d_nms_radius,
            nms_min_neighbors=point_cloud_3d_nms_min_neighbors,
            random_points_per_frame=random_points_per_frame,
            bbox_kwargs=bbox_kwargs,
            detection=detection_seg,
        )
        if detection_seg is not None and not bbox_contexts:
            print(
                "[vibephysics] detection_seg: no classes configured; skipping algo_3d_bbox",
                flush=True,
            )

    run_bbox_work = algo_3d_bbox and bool(bbox_contexts)

    wall_start = time.perf_counter()
    frame_results: list[_FrameWorkResult | None] = [None] * num_frames

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(
                _process_one_frame,
                frame_idx,
                prediction,
                min_confidence=min_confidence,
                run_nms=point_cloud_3d_nms,
                nms_radius=point_cloud_3d_nms_radius,
                nms_min_neighbors=point_cloud_3d_nms_min_neighbors,
                to_blender=to_blender,
                run_bbox=run_bbox_work,
                bbox_contexts=bbox_contexts,
                bbox_kwargs=bbox_kwargs,
                random_points_per_frame=random_points_per_frame,
                detection=detection_seg,
            )
            for frame_idx in range(num_frames)
        ]
        for fut in as_completed(futures):
            result = fut.result()
            frame_results[result.frame_idx] = result

    timings = PerFramePostprocessTimings(wall_s=time.perf_counter() - wall_start)
    bboxes: list[FrameBboxEntry] | None = [None] * num_frames if algo_3d_bbox else None
    point_chunks: list[np.ndarray] = []
    color_chunks: list[np.ndarray] = []
    conf_chunks: list[np.ndarray] = []
    frame_id_chunks: list[np.ndarray] = []

    for frame_idx, result in enumerate(frame_results):
        if result is None:
            continue
        timings.nms_cpu_s += result.nms_elapsed_s
        timings.bbox_cpu_s += result.bbox_elapsed_s
        timings.nms_removed_total += result.nms_removed
        if algo_3d_bbox and bboxes is not None:
            bboxes[frame_idx] = result.bboxes
        if result.points is not None and len(result.points) > 0:
            point_chunks.append(result.points)
            color_chunks.append(result.colors_u8)
            conf_chunks.append(result.conf)
            if with_frame_ids:
                frame_id_chunks.append(
                    np.full(len(result.points), frame_idx, dtype=np.int32)
                )

    if point_cloud_3d_nms and timings.nms_removed_total > 0:
        print(
            f"[vibephysics] 3D NMS: removed {timings.nms_removed_total:,} isolated points "
            f"(radius={float(point_cloud_3d_nms_radius):g} m, "
            f"min_neighbors={int(point_cloud_3d_nms_min_neighbors)}, "
            f"{workers} frame workers)",
            flush=True,
        )

    return PerFramePostprocessResult(
        bboxes=bboxes,
        point_chunks=point_chunks,
        color_chunks=color_chunks,
        conf_chunks=conf_chunks,
        frame_id_chunks=frame_id_chunks,
        timings=timings,
    )
