"""3D change detection via new voxel occupancy vs a reference frame."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .schema import FeedforwardPrediction

CHANGE_BBOX_COLOR = (0.0, 0.85, 1.0, 1.0)

_NEIGHBOR_OFFSETS_26 = tuple(
    (dx, dy, dz)
    for dx in (-1, 0, 1)
    for dy in (-1, 0, 1)
    for dz in (-1, 0, 1)
    if not (dx == dy == dz == 0)
)
_NEIGHBOR_OFFSETS_6 = (
    (1, 0, 0),
    (-1, 0, 0),
    (0, 1, 0),
    (0, -1, 0),
    (0, 0, 1),
    (0, 0, -1),
)


@dataclass
class ChangeBBox:
    frame: int
    changed_voxels: int
    changed_points: int
    change_fraction: float
    min: list[float]
    max: list[float]
    center: list[float]
    size: list[float]
    label: str | None = None
    voxel_centers: list[list[float]] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BboxVisibilitySpan:
    """Progressive Blender visibility: appear at *appear_frame*, hide when superseded."""

    bbox: ChangeBBox
    appear_frame: int
    hide_frame: int | None = None  # recon frame when hidden (replacement NMS); None = stays on


@dataclass
class BboxReferenceContext:
    reference_frame: int
    ref_origin: np.ndarray
    ref_indices: np.ndarray
    ref_set: set[tuple[int, int, int]]
    ref_centroid: np.ndarray | None = None
    ref_bounds_min: np.ndarray | None = None
    ref_bounds_max: np.ndarray | None = None


def _frame_points(
    prediction: FeedforwardPrediction,
    frame_idx: int,
    *,
    min_confidence: float,
) -> np.ndarray:
    points = prediction.world_points[frame_idx].reshape(-1, 3)
    conf = prediction.conf[frame_idx].reshape(-1)
    valid = np.isfinite(points).all(axis=1)
    if min_confidence > 0:
        valid &= conf >= min_confidence
    return points[valid]


def _occupancy_voxel_indices(
    points: np.ndarray,
    origin: np.ndarray,
    voxel_size: float,
    *,
    min_points_per_voxel: int = 1,
) -> np.ndarray:
    """Return voxel indices occupied by at least ``min_points_per_voxel`` points."""
    if len(points) == 0:
        return np.empty((0, 3), dtype=np.int32)

    indices = np.floor((points - origin) / voxel_size).astype(np.int32)
    if min_points_per_voxel <= 1:
        return np.unique(indices, axis=0)

    unique, counts = np.unique(indices, axis=0, return_counts=True)
    return unique[counts >= min_points_per_voxel]


def _classify_voxel_diff(
    ref_indices: np.ndarray,
    frame_indices: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Voxel-by-voxel comparison on a shared grid.

    Returns ``(new, stable, lost)`` where:
    - new: occupied in frame, empty in ref (new geometry)
    - stable: occupied in both (background, ignored)
    - lost: occupied in ref, empty in frame (occlusion, ignored)
    """
    ref_set = _index_set(ref_indices)
    frame_set = _index_set(frame_indices)

    new_rows = [row for row in frame_indices if tuple(row) not in ref_set]
    stable_rows = [row for row in frame_indices if tuple(row) in ref_set]
    lost_rows = [row for row in ref_indices if tuple(row) not in frame_set]

    def _as_array(rows: list) -> np.ndarray:
        if not rows:
            return np.empty((0, 3), dtype=np.int32)
        return np.asarray(rows, dtype=np.int32)

    return _as_array(new_rows), _as_array(stable_rows), _as_array(lost_rows)


def _neighbor_count_26(
    voxel: tuple[int, int, int],
    occupied: set[tuple[int, int, int]],
) -> int:
    x, y, z = voxel
    return sum(
        1
        for dx, dy, dz in _NEIGHBOR_OFFSETS_26
        if (x + dx, y + dy, z + dz) in occupied
    )


def _dilate_index_set(
    index_set: set[tuple[int, int, int]],
    radius: int,
) -> set[tuple[int, int, int]]:
    dilated = set(index_set)
    for _ in range(radius):
        frontier = tuple(dilated)
        for x, y, z in frontier:
            for dx, dy, dz in _NEIGHBOR_OFFSETS_26:
                dilated.add((x + dx, y + dy, z + dz))
    return dilated


def _gap_closed_components(
    new_indices: np.ndarray,
    *,
    gap_close: int,
) -> list[np.ndarray]:
    """Merge new-voxel clusters separated by small reconstruction gaps."""
    if len(new_indices) == 0:
        return []
    if gap_close <= 0:
        return _connected_components(new_indices)

    dilated = _dilate_index_set(_index_set(new_indices), gap_close)
    dilated_components = _connected_components(
        np.asarray(list(dilated), dtype=np.int32),
    )
    merged: list[np.ndarray] = []
    for component in dilated_components:
        component_set = _index_set(component)
        members = [row for row in new_indices if tuple(row) in component_set]
        if members:
            merged.append(np.asarray(members, dtype=np.int32))
    merged.sort(key=len, reverse=True)
    return merged


def _filter_background_shell_voxels(
    new_indices: np.ndarray,
    ref_set: set[tuple[int, int, int]],
    *,
    min_new_neighbors: int = 1,
) -> np.ndarray:
    """
    Drop ref-adjacent new voxels that look like background / map-shift noise.

    Keeps free-space new voxels and ref-adjacent voxels that belong to a new blob
    (e.g. feet on the floor). Isolated one-voxel shells on existing geometry are
    removed at the voxel level before clustering.
    """
    if len(new_indices) == 0:
        return new_indices

    new_set = _index_set(new_indices)
    kept: list[np.ndarray] = []
    for row in new_indices:
        voxel = tuple(row)
        if not _voxel_touches_ref(voxel, ref_set):
            kept.append(row)
            continue
        if _neighbor_count_26(voxel, new_set) >= min_new_neighbors:
            kept.append(row)

    if not kept:
        return np.empty((0, 3), dtype=np.int32)
    return np.stack(kept).astype(np.int32)


def _voxel_centers(indices: np.ndarray, origin: np.ndarray, voxel_size: float) -> np.ndarray:
    if len(indices) == 0:
        return np.empty((0, 3), dtype=np.float64)
    return origin + (indices.astype(np.float64) + 0.5) * voxel_size


def _index_set(indices: np.ndarray) -> set[tuple[int, int, int]]:
    return {tuple(row) for row in indices}


def _connected_components(indices: np.ndarray) -> list[np.ndarray]:
    """26-connected components over integer voxel indices."""
    if len(indices) == 0:
        return []

    remaining = _index_set(indices)
    components: list[np.ndarray] = []

    while remaining:
        start = remaining.pop()
        stack = [start]
        component: list[tuple[int, int, int]] = []
        while stack:
            cur = stack.pop()
            component.append(cur)
            x, y, z = cur
            for dx, dy, dz in _NEIGHBOR_OFFSETS_26:
                neighbor = (x + dx, y + dy, z + dz)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        components.append(np.asarray(component, dtype=np.int32))

    components.sort(key=len, reverse=True)
    return components

def _face_neighbor_count(
    voxel: tuple[int, int, int],
    occupied: set[tuple[int, int, int]],
) -> int:
    x, y, z = voxel
    return sum(
        1
        for dx, dy, dz in _NEIGHBOR_OFFSETS_6
        if (x + dx, y + dy, z + dz) in occupied
    )


def _dense_core_indices(
    indices: np.ndarray,
    *,
    min_neighbors: int,
) -> np.ndarray:
    """Keep voxels with enough face-adjacent neighbors in the same set."""
    if len(indices) == 0 or min_neighbors <= 0:
        return indices

    occupied = _index_set(indices)
    dense_rows = [
        row
        for row in indices
        if _face_neighbor_count(tuple(row), occupied) >= min_neighbors
    ]
    if not dense_rows:
        return np.empty((0, 3), dtype=np.int32)
    return np.asarray(dense_rows, dtype=np.int32)


def _tighten_bbox_indices(
    cluster: np.ndarray,
    *,
    dense_min_neighbors: int,
    min_dense_voxels: int,
) -> np.ndarray:
    """
    Shrink a detected blob to its dense interior for a tighter bbox.

    Detection uses the full cluster; only the exported box is tightened.
    """
    if len(cluster) == 0 or dense_min_neighbors <= 0:
        return cluster

    current = cluster
    while len(current) >= min_dense_voxels:
        dense = _dense_core_indices(current, min_neighbors=dense_min_neighbors)
        if len(dense) < min_dense_voxels or len(dense) == len(current):
            break
        current = dense

    if len(current) >= min_dense_voxels:
        return current

    for neighbors in range(dense_min_neighbors - 1, 0, -1):
        dense = _dense_core_indices(cluster, min_neighbors=neighbors)
        if len(dense) >= min_dense_voxels:
            return dense

    return cluster


def _voxel_touches_ref(
    voxel: tuple[int, int, int],
    ref_set: set[tuple[int, int, int]],
) -> bool:
    if voxel in ref_set:
        return True
    x, y, z = voxel
    return any((x + dx, y + dy, z + dz) in ref_set for dx, dy, dz in _NEIGHBOR_OFFSETS_26)


def _cluster_interior_stats(
    indices: np.ndarray,
    ref_set: set[tuple[int, int, int]],
) -> tuple[int, float]:
    if len(indices) == 0:
        return 0, 0.0
    interior = sum(1 for row in indices if not _voxel_touches_ref(tuple(row), ref_set))
    return interior, float(interior / len(indices))


def _ref_adjacent_fraction(
    indices: np.ndarray,
    ref_set: set[tuple[int, int, int]],
) -> float:
    if len(indices) == 0:
        return 0.0
    adjacent = sum(1 for row in indices if _voxel_touches_ref(tuple(row), ref_set))
    return float(adjacent / len(indices))


def _is_shift_shell(
    indices: np.ndarray,
    ref_set: set[tuple[int, int, int]],
) -> bool:
    """Large ref-hugging layer with no free-space core (typical map drift)."""
    if len(indices) == 0:
        return False
    interior_count, _ = _cluster_interior_stats(indices, ref_set)
    if interior_count > 0:
        return False
    return _ref_adjacent_fraction(indices, ref_set) >= 0.92


def _blob_score(
    cluster: np.ndarray,
    ref_set: set[tuple[int, int, int]],
    origin: np.ndarray,
    voxel_size: float,
) -> float:
    interior_count, interior_fraction = _cluster_interior_stats(cluster, ref_set)
    centers = _voxel_centers(cluster, origin, voxel_size)
    _, _, _, size = _axis_aligned_bbox(centers, 0.0)
    bbox_volume = float(np.prod(np.maximum(size, voxel_size)))
    fill_ratio = len(cluster) * (voxel_size**3) / max(bbox_volume, voxel_size**3)
    return len(cluster) * fill_ratio * (1.0 + interior_count) * (0.25 + interior_fraction)


def _constrain_indices_to_bounds(
    indices: np.ndarray,
    origin: np.ndarray,
    voxel_size: float,
    bounds_min: np.ndarray,
    bounds_max: np.ndarray,
    *,
    margin: float,
) -> np.ndarray:
    if len(indices) == 0:
        return indices
    centers = _voxel_centers(indices, origin, voxel_size)
    lo = bounds_min - margin
    hi = bounds_max + margin
    keep = np.all(centers >= lo, axis=1) & np.all(centers <= hi, axis=1)
    return indices[keep]


def _select_blob_bbox_indices(
    new_indices: np.ndarray,
    ref_indices: np.ndarray,
    origin: np.ndarray,
    voxel_size: float,
    *,
    min_cluster_voxels: int,
    min_interior_voxels: int,
    min_interior_fraction: float,
    cluster_gap_close: int,
    near_centroid: np.ndarray | None = None,
) -> tuple[np.ndarray | None, str]:
    """
    Pick the best new blob cluster and return its full voxel extent for bbox.

    Uses gap-closing to reconnect sparse recon, strict interior filtering first,
    then relaxed fallbacks for partial blobs (e.g. person near a wall).
    """
    if len(new_indices) == 0:
        return None, "empty"

    ref_set = _index_set(ref_indices)
    clusters = _gap_closed_components(new_indices, gap_close=cluster_gap_close)

    strict_best: tuple[float, np.ndarray] | None = None
    relaxed_best: tuple[float, np.ndarray] | None = None
    largest_valid: np.ndarray | None = None
    largest_valid_size = 0

    for cluster in clusters:
        if len(cluster) < min_cluster_voxels:
            continue
        if _is_shift_shell(cluster, ref_set):
            continue

        if largest_valid is None or len(cluster) > largest_valid_size:
            largest_valid = cluster
            largest_valid_size = len(cluster)

        interior_count, interior_fraction = _cluster_interior_stats(cluster, ref_set)
        score = _blob_score(cluster, ref_set, origin, voxel_size)
        if near_centroid is not None:
            cluster_center = _voxel_centers(cluster, origin, voxel_size).mean(axis=0)
            dist = float(np.linalg.norm(cluster_center - near_centroid))
            score /= 1.0 + dist / max(voxel_size * 4.0, 0.05)

        if interior_count >= min_interior_voxels and interior_fraction >= min_interior_fraction:
            if strict_best is None or score > strict_best[0]:
                strict_best = (score, cluster)
            continue

        if interior_count >= 1:
            relaxed_score = score * (0.5 + interior_fraction)
            if relaxed_best is None or relaxed_score > relaxed_best[0]:
                relaxed_best = (relaxed_score, cluster)

    if strict_best is not None:
        return strict_best[1], "strict"
    if relaxed_best is not None:
        return relaxed_best[1], "relaxed"
    if largest_valid is not None:
        return largest_valid, "largest"
    return None, "none"


DETECTION_SEG_BBOX_METHOD = "masked_cluster_aabb"
DETECTION_SEG_MIN_BBOX_SIZE_M = 0.12


def _select_largest_cluster_indices(
    frame_indices: np.ndarray,
    *,
    min_cluster_voxels: int,
    cluster_gap_close: int,
) -> tuple[np.ndarray | None, str]:
    if len(frame_indices) == 0:
        return None, "empty"
    clusters = _gap_closed_components(frame_indices, gap_close=cluster_gap_close)
    largest_valid: np.ndarray | None = None
    largest_size = 0
    for cluster in clusters:
        if len(cluster) < min_cluster_voxels:
            continue
        if largest_valid is None or len(cluster) > largest_size:
            largest_valid = cluster
            largest_size = len(cluster)
    if largest_valid is not None:
        return largest_valid, "largest"
    return None, "none"


def compute_masked_occupancy_bbox_for_frame(
    frame_idx: int,
    masked_points: np.ndarray,
    *,
    label: str,
    voxel_size: float = 0.02,
    min_cluster_voxels: int = 8,
    cluster_gap_close: int = 1,
    min_points_per_voxel: int = 1,
    padding: float = 0.01,
    verbose: bool = False,
    mode: str = "occupancy",
) -> ChangeBBox | None:
    """BBox from masked points per frame (largest cluster; no reference-frame diff)."""
    min_points = max(int(min_cluster_voxels) * int(min_points_per_voxel), 4)
    if len(masked_points) < min_points:
        return None

    origin = masked_points.min(axis=0)
    frame_indices = _occupancy_voxel_indices(
        masked_points,
        origin,
        voxel_size,
        min_points_per_voxel=min_points_per_voxel,
    )
    if len(frame_indices) == 0:
        return None

    cluster_indices, pick_mode = _select_largest_cluster_indices(
        frame_indices,
        min_cluster_voxels=min_cluster_voxels,
        cluster_gap_close=cluster_gap_close,
    )
    if cluster_indices is None:
        pick_mode = "points"
        mins, maxs, center, size = _axis_aligned_bbox(masked_points, padding)
        changed_points = len(masked_points)
        changed_voxels = len(frame_indices)
        display_indices = frame_indices
    else:
        bbox_centers = _voxel_centers(cluster_indices, origin, voxel_size)
        mins, maxs, center, size = _axis_aligned_bbox(bbox_centers, padding)
        changed_points = len(cluster_indices)
        changed_voxels = len(frame_indices)
        display_indices = cluster_indices

    voxel_world = _voxel_centers(display_indices, origin, voxel_size)

    if verbose:
        print(
            f"[vibephysics] detection_seg bbox: frame {frame_idx} [{label}] "
            f"{mode} {changed_voxels} voxels, cluster {changed_points} ({pick_mode}) -> "
            f"size=({size[0]:.3f}, {size[1]:.3f}, {size[2]:.3f})",
            flush=True,
        )
    return ChangeBBox(
        frame=frame_idx,
        changed_voxels=int(changed_voxels),
        changed_points=int(changed_points),
        change_fraction=1.0,
        min=mins.astype(float).tolist(),
        max=maxs.astype(float).tolist(),
        center=center.astype(float).tolist(),
        size=size.astype(float).tolist(),
        label=label,
        voxel_centers=voxel_world.astype(float).tolist(),
    )


def _axis_aligned_bbox(points: np.ndarray, padding: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    mins = points.min(axis=0) - padding
    maxs = points.max(axis=0) + padding
    center = (mins + maxs) * 0.5
    size = maxs - mins
    return mins, maxs, center, size


def _bbox_uses_point_cloud_pipeline(
    *,
    point_cloud_3d_nms: bool,
    random_points_per_frame: int | float | None,
) -> bool:
    """Match export path: confidence filter, optional subsample, optional NMS."""
    from .common import random_points_limit_enabled

    if point_cloud_3d_nms:
        return True
    if random_points_limit_enabled(random_points_per_frame):
        return True
    return False


def prepare_bbox_reference(
    prediction: FeedforwardPrediction,
    *,
    reference_frame: int = 0,
    min_confidence: float = 2.0,
    voxel_size: float = 0.02,
    min_changed_voxels: int = 12,
    min_points_per_voxel: int = 1,
    point_cloud_3d_nms: bool = False,
    point_cloud_3d_nms_radius: float = 0.03,
    point_cloud_3d_nms_min_neighbors: int = 3,
    random_points_per_frame: int | float | None = None,
) -> BboxReferenceContext:
    num_frames = int(prediction.world_points.shape[0])
    if not (0 <= reference_frame < num_frames):
        raise ValueError(f"reference_frame {reference_frame} out of range for {num_frames} frames")

    if _bbox_uses_point_cloud_pipeline(
        point_cloud_3d_nms=point_cloud_3d_nms,
        random_points_per_frame=random_points_per_frame,
    ):
        from .common import collect_single_frame_world_points

        ref_points = collect_single_frame_world_points(
            prediction,
            reference_frame,
            min_confidence=min_confidence,
            point_cloud_3d_nms=point_cloud_3d_nms,
            point_cloud_3d_nms_radius=point_cloud_3d_nms_radius,
            point_cloud_3d_nms_min_neighbors=point_cloud_3d_nms_min_neighbors,
            random_points_per_frame=random_points_per_frame,
            rng_seed=reference_frame,
        )
        if ref_points is None:
            ref_points = np.empty((0, 3), dtype=np.float64)
    else:
        ref_points = _frame_points(prediction, reference_frame, min_confidence=min_confidence)
    return prepare_bbox_reference_from_points(
        ref_points,
        reference_frame=reference_frame,
        voxel_size=voxel_size,
        min_changed_voxels=min_changed_voxels,
        min_points_per_voxel=min_points_per_voxel,
    )


def prepare_bbox_reference_from_points(
    ref_points: np.ndarray,
    *,
    reference_frame: int,
    voxel_size: float = 0.02,
    min_changed_voxels: int = 12,
    min_points_per_voxel: int = 1,
) -> BboxReferenceContext:
    if len(ref_points) == 0:
        ref_origin = np.zeros(3, dtype=np.float64)
        ref_indices = np.empty((0, 3), dtype=np.int32)
    else:
        ref_origin = ref_points.min(axis=0)
        ref_indices = _occupancy_voxel_indices(
            ref_points,
            ref_origin,
            voxel_size,
            min_points_per_voxel=min_points_per_voxel,
        )
    ref_set = _index_set(ref_indices)
    if len(ref_indices) < min_changed_voxels:
        raise ValueError(
            f"Reference frame {reference_frame} has too few voxels "
            f"({len(ref_indices)} < {min_changed_voxels})"
        )
    ref_centroid = ref_points.mean(axis=0) if len(ref_points) else None
    ref_bounds_min = ref_points.min(axis=0) if len(ref_points) else None
    ref_bounds_max = ref_points.max(axis=0) if len(ref_points) else None
    return BboxReferenceContext(
        reference_frame=int(reference_frame),
        ref_origin=ref_origin,
        ref_indices=ref_indices,
        ref_set=ref_set,
        ref_centroid=ref_centroid,
        ref_bounds_min=ref_bounds_min,
        ref_bounds_max=ref_bounds_max,
    )


def compute_bbox_for_frame(
    prediction: FeedforwardPrediction,
    frame_idx: int,
    ctx: BboxReferenceContext,
    *,
    min_confidence: float = 2.0,
    voxel_size: float = 0.02,
    min_changed_voxels: int = 12,
    min_change_fraction: float = 0.03,
    min_cluster_voxels: int = 8,
    cluster_gap_close: int = 1,
    min_points_per_voxel: int = 1,
    shell_min_new_neighbors: int = 1,
    min_interior_voxels: int = 2,
    min_interior_fraction: float = 0.04,
    bbox_dense_min_neighbors: int = 3,
    bbox_min_dense_voxels: int = 4,
    padding: float = 0.01,
    verbose: bool = False,
    frame_points: np.ndarray | None = None,
    label: str | None = None,
    change_fraction_denominator: str = "frame",
) -> ChangeBBox | None:
    if frame_idx == ctx.reference_frame:
        return None

    if frame_points is None:
        frame_points = _frame_points(prediction, frame_idx, min_confidence=min_confidence)
    if len(frame_points) == 0:
        return None

    frame_indices = _occupancy_voxel_indices(
        frame_points,
        ctx.ref_origin,
        voxel_size,
        min_points_per_voxel=min_points_per_voxel,
    )
    if len(frame_indices) == 0:
        return None

    new_indices, stable_indices, lost_indices = _classify_voxel_diff(
        ctx.ref_indices,
        frame_indices,
    )
    new_indices = _filter_background_shell_voxels(
        new_indices,
        ctx.ref_set,
        min_new_neighbors=shell_min_new_neighbors,
    )
    if (
        label
        and ctx.ref_bounds_min is not None
        and ctx.ref_bounds_max is not None
        and len(new_indices) > 0
    ):
        extent = float(np.linalg.norm(ctx.ref_bounds_max - ctx.ref_bounds_min))
        margin = max(0.8, 0.4 * extent)
        new_indices = _constrain_indices_to_bounds(
            new_indices,
            ctx.ref_origin,
            voxel_size,
            ctx.ref_bounds_min,
            ctx.ref_bounds_max,
            margin=margin,
        )
    if change_fraction_denominator == "non_stable":
        denom = int(len(frame_indices) - len(stable_indices))
        change_fraction = float(len(new_indices) / max(denom, 1))
        fraction_note = f"new/non-stable={change_fraction:.1%}"
    else:
        change_fraction = float(len(new_indices) / max(len(frame_indices), 1))
        fraction_note = f"new/frame={change_fraction:.1%}"

    if len(new_indices) < min_changed_voxels or change_fraction < min_change_fraction:
        if verbose:
            reason = (
                f"{len(new_indices)} new voxels (< {min_changed_voxels})"
                if len(new_indices) < min_changed_voxels
                else (
                    f"{fraction_note} (< {min_change_fraction:.1%})"
                )
            )
            tag = "detection_seg bbox" if label else "algo_3d_bbox"
            print(
                f"[vibephysics] {tag}: frame {frame_idx} skipped ({reason}; "
                f"stable={len(stable_indices)}, lost={len(lost_indices)})",
                flush=True,
            )
        return None

    cluster_indices, pick_mode = _select_blob_bbox_indices(
        new_indices,
        ctx.ref_indices,
        ctx.ref_origin,
        voxel_size,
        min_cluster_voxels=min_cluster_voxels,
        min_interior_voxels=min_interior_voxels,
        min_interior_fraction=min_interior_fraction,
        cluster_gap_close=cluster_gap_close,
        near_centroid=ctx.ref_centroid if label else None,
    )
    if cluster_indices is None:
        if verbose:
            print(
                f"[vibephysics] algo_3d_bbox: frame {frame_idx} skipped "
                f"(no blob cluster >= {min_cluster_voxels} voxels among "
                f"{len(new_indices)} new voxels; stable={len(stable_indices)})",
                flush=True,
            )
        return None

    bbox_indices = _tighten_bbox_indices(
        cluster_indices,
        dense_min_neighbors=bbox_dense_min_neighbors,
        min_dense_voxels=bbox_min_dense_voxels,
    )
    bbox_centers = _voxel_centers(bbox_indices, ctx.ref_origin, voxel_size)
    interior_count, interior_fraction = _cluster_interior_stats(bbox_indices, ctx.ref_set)
    mins, maxs, center, size = _axis_aligned_bbox(bbox_centers, padding)
    if verbose:
        label_note = f" [{label}]" if label else ""
        tag = "detection_seg bbox" if label else "algo_3d_bbox"
        print(
            f"[vibephysics] {tag}: frame {frame_idx}{label_note} "
            f"{len(new_indices)} new voxels ({fraction_note}), "
            f"stable={len(stable_indices)}, lost={len(lost_indices)}, "
            f"cluster {len(cluster_indices)} voxels ({pick_mode}), "
            f"tight bbox {len(bbox_indices)} voxels "
            f"({interior_count} interior, {interior_fraction:.0%}) -> "
            f"center=({center[0]:.3f}, {center[1]:.3f}, {center[2]:.3f}) "
            f"size=({size[0]:.3f}, {size[1]:.3f}, {size[2]:.3f})",
            flush=True,
        )
    result = ChangeBBox(
        frame=frame_idx,
        changed_voxels=int(len(new_indices)),
        changed_points=int(len(bbox_indices)),
        change_fraction=change_fraction,
        min=mins.astype(float).tolist(),
        max=maxs.astype(float).tolist(),
        center=center.astype(float).tolist(),
        size=size.astype(float).tolist(),
        label=label,
    )
    if (
        label
        and frame_points is not None
        and len(frame_points) > 0
        and float(np.max(size)) < DETECTION_SEG_MIN_BBOX_SIZE_M
    ):
        fallback = compute_masked_occupancy_bbox_for_frame(
            frame_idx,
            frame_points,
            label=label,
            voxel_size=voxel_size,
            min_cluster_voxels=min_cluster_voxels,
            cluster_gap_close=cluster_gap_close,
            min_points_per_voxel=min_points_per_voxel,
            padding=padding,
            verbose=verbose,
            mode="occupancy_fallback",
        )
        if fallback is not None:
            return fallback
    return result


def compute_algo_3d_bboxes(
    prediction: FeedforwardPrediction,
    *,
    reference_frame: int = 0,
    min_confidence: float = 2.0,
    voxel_size: float = 0.02,
    min_changed_voxels: int = 12,
    min_change_fraction: float = 0.03,
    min_cluster_voxels: int = 8,
    cluster_gap_close: int = 1,
    min_points_per_voxel: int = 1,
    shell_min_new_neighbors: int = 1,
    min_interior_voxels: int = 2,
    min_interior_fraction: float = 0.04,
    bbox_dense_min_neighbors: int = 3,
    bbox_min_dense_voxels: int = 4,
    padding: float = 0.01,
    verbose: bool = True,
    max_workers: int | None = None,
) -> list[ChangeBBox | None]:
    """
    Detect substantial new object blobs via voxel-by-voxel diff vs the reference.

    Runs per-frame bbox on dense confidence-filtered points (no NMS). For NMS +
    bbox on the export point pipeline use ``run_per_frame_postprocess``.
    """
    from .frame_postprocess import run_per_frame_postprocess

    result = run_per_frame_postprocess(
        prediction,
        min_confidence=min_confidence,
        point_cloud_3d_nms=False,
        algo_3d_bbox=True,
        bbox_reference_frame=reference_frame,
        bbox_kwargs={
            "voxel_size": voxel_size,
            "min_changed_voxels": min_changed_voxels,
            "min_change_fraction": min_change_fraction,
            "min_cluster_voxels": min_cluster_voxels,
            "cluster_gap_close": cluster_gap_close,
            "min_points_per_voxel": min_points_per_voxel,
            "shell_min_new_neighbors": shell_min_new_neighbors,
            "min_interior_voxels": min_interior_voxels,
            "min_interior_fraction": min_interior_fraction,
            "bbox_dense_min_neighbors": bbox_dense_min_neighbors,
            "bbox_min_dense_voxels": bbox_min_dense_voxels,
            "padding": padding,
            "verbose": verbose,
        },
        max_workers=max_workers,
    )
    return result.bboxes or []


def _frame_bbox_entry_to_json(entry: list[ChangeBBox] | ChangeBBox | None) -> Any:
    if entry is None:
        return None
    if isinstance(entry, list):
        if not entry:
            return None
        return [bbox.to_dict() for bbox in entry]
    return entry.to_dict()


def parse_frame_bbox_entry(entry: Any) -> list[ChangeBBox] | None:
    """Load one frame slot from ``algo_3d_bbox.json`` (legacy single or list)."""
    if entry is None:
        return None
    if isinstance(entry, list):
        out: list[ChangeBBox] = []
        for item in entry:
            if item is None:
                continue
            if isinstance(item, ChangeBBox):
                out.append(item)
                continue
            row = dict(item)
            if "changed_voxels" not in row and "changed_points" in row:
                row["changed_voxels"] = row["changed_points"]
            if row.get("voxel_centers") is None:
                row["voxel_centers"] = None
            out.append(ChangeBBox(**row))
        return out or None
    row = dict(entry)
    if "changed_voxels" not in row and "changed_points" in row:
        row["changed_voxels"] = row["changed_points"]
    if row.get("voxel_centers") is None:
        row["voxel_centers"] = None
    return [ChangeBBox(**row)]


def save_algo_3d_bboxes(
    path: Path,
    bboxes: list[list[ChangeBBox] | ChangeBBox | None],
    *,
    reference_frame: int,
    voxel_size: float,
    min_changed_voxels: int,
    min_change_fraction: float,
    min_cluster_voxels: int,
    cluster_gap_close: int,
    min_points_per_voxel: int,
    shell_min_new_neighbors: int,
    min_interior_voxels: int,
    min_interior_fraction: float,
    bbox_dense_min_neighbors: int,
    bbox_min_dense_voxels: int,
    padding: float,
    min_visualize_changed_voxels: int,
    detection_seg: dict[str, Any] | None = None,
    method: str = "voxel_diff_blob",
) -> None:
    payload = {
        "reference_frame": reference_frame,
        "method": method,
        "voxel_size": voxel_size,
        "min_changed_voxels": min_changed_voxels,
        "min_visualize_changed_voxels": int(min_visualize_changed_voxels),
        "min_change_fraction": min_change_fraction,
        "min_cluster_voxels": min_cluster_voxels,
        "cluster_gap_close": cluster_gap_close,
        "min_points_per_voxel": min_points_per_voxel,
        "shell_min_new_neighbors": shell_min_new_neighbors,
        "min_interior_voxels": min_interior_voxels,
        "min_interior_fraction": min_interior_fraction,
        "bbox_dense_min_neighbors": bbox_dense_min_neighbors,
        "bbox_min_dense_voxels": bbox_min_dense_voxels,
        "padding": padding,
        "frames": [_frame_bbox_entry_to_json(entry) for entry in bboxes],
    }
    if detection_seg:
        payload["detection_seg"] = detection_seg
    path.write_text(json.dumps(payload, indent=2))


def load_algo_3d_bboxes(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _bbox_base_class(label: str | None) -> str:
    if not label:
        return "change"
    return label.split("#", 1)[0].strip().lower()


# Overlapping COCO labels compete in bbox NMS (not only exact class match).
_NMS_OVERLAPPING_CLASS_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"chair", "couch"}),
)
_NMS_CLASS_GROUP_KEY: dict[frozenset[str], str] = {
    group: "|".join(sorted(group)) for group in _NMS_OVERLAPPING_CLASS_GROUPS
}


def _nms_class_group(label: str | None) -> str:
    """NMS bucket: same as base class unless label is in an overlapping group."""
    base = _bbox_base_class(label)
    for group in _NMS_OVERLAPPING_CLASS_GROUPS:
        if base in group:
            return _NMS_CLASS_GROUP_KEY[group]
    return base


def _bbox_aabb_volume(bbox: ChangeBBox) -> float:
    size = np.asarray(bbox.size, dtype=np.float64)
    return float(np.prod(np.maximum(size, 0.0)))


def _bbox_aabb_intersection_volume(a: ChangeBBox, b: ChangeBBox) -> float:
    a_min = np.asarray(a.min, dtype=np.float64)
    a_max = np.asarray(a.max, dtype=np.float64)
    b_min = np.asarray(b.min, dtype=np.float64)
    b_max = np.asarray(b.max, dtype=np.float64)
    inter_min = np.maximum(a_min, b_min)
    inter_max = np.minimum(a_max, b_max)
    inter_size = np.maximum(inter_max - inter_min, 0.0)
    return float(np.prod(inter_size))


def _bbox_suppression_score(a: ChangeBBox, b: ChangeBBox) -> float:
    """Max of IoU and intersection/min-volume (nested smaller box scores high)."""
    inter_vol = _bbox_aabb_intersection_volume(a, b)
    if inter_vol <= 0.0:
        return 0.0
    vol_a = _bbox_aabb_volume(a)
    vol_b = _bbox_aabb_volume(b)
    union = vol_a + vol_b - inter_vol
    iou = inter_vol / union if union > 0.0 else 0.0
    min_vol = min(vol_a, vol_b)
    overlap_min = inter_vol / min_vol if min_vol > 0.0 else 0.0
    return max(iou, overlap_min)


def _bbox_sort_key(bbox: ChangeBBox) -> tuple[float, int]:
    return (
        _bbox_aabb_volume(bbox),
        int(getattr(bbox, "changed_voxels", bbox.changed_points)),
    )


def _rebuild_bbox_frames(
    bboxes: list[list[ChangeBBox] | ChangeBBox | None],
    kept_ids: set[int],
) -> list[list[ChangeBBox] | ChangeBBox | None]:
    filtered: list[list[ChangeBBox] | ChangeBBox | None] = []
    for entry in bboxes:
        parsed = parse_frame_bbox_entry(entry)
        if not parsed:
            filtered.append(None)
            continue
        kept_boxes = [b for b in parsed if id(b) in kept_ids]
        filtered.append(kept_boxes if kept_boxes else None)
    return filtered


def compute_progressive_bbox_visibility_spans(
    bboxes: list[list[ChangeBBox] | ChangeBBox | None],
    *,
    iou_threshold: float = 0.25,
) -> list[BboxVisibilitySpan]:
    """
    Frame-order class-group NMS with a visibility timeline for Blender.

    Each kept box appears at its recon frame. When a larger overlapping box
    arrives on a later frame, earlier boxes get ``hide_frame`` set to that
    frame. Boxes suppressed on their own frame are omitted.

    Classes in ``_NMS_OVERLAPPING_CLASS_GROUPS`` (e.g. chair + couch) share one
    NMS bucket because their 3D boxes often overlap.
    """
    if iou_threshold <= 0.0:
        return _all_bbox_visibility_spans(bboxes)

    by_frame: dict[int, list[ChangeBBox]] = {}
    for entry in bboxes:
        parsed = parse_frame_bbox_entry(entry)
        if not parsed:
            continue
        for bbox in parsed:
            by_frame.setdefault(int(bbox.frame), []).append(bbox)

    if not by_frame:
        return []
    if sum(len(v) for v in by_frame.values()) <= 1:
        return _all_bbox_visibility_spans(bboxes)

    kept_by_class: dict[str, list[tuple[ChangeBBox, BboxVisibilitySpan]]] = {}
    spans: list[BboxVisibilitySpan] = []

    for frame_idx in sorted(by_frame):
        by_class: dict[str, list[ChangeBBox]] = {}
        for bbox in by_frame[frame_idx]:
            by_class.setdefault(_nms_class_group(bbox.label), []).append(bbox)

        for cls, candidates in by_class.items():
            class_kept = kept_by_class.setdefault(cls, [])
            for candidate in sorted(candidates, key=_bbox_sort_key, reverse=True):
                replace_at: list[int] = []
                suppressed = False
                hide_at = int(candidate.frame)
                for i, (existing, existing_span) in enumerate(class_kept):
                    if (
                        _bbox_suppression_score(candidate, existing)
                        < iou_threshold
                    ):
                        continue
                    if _bbox_sort_key(candidate) <= _bbox_sort_key(existing):
                        suppressed = True
                        break
                    replace_at.append(i)

                if suppressed:
                    continue

                for i in sorted(replace_at, reverse=True):
                    _, replaced_span = class_kept.pop(i)
                    replaced_span.hide_frame = hide_at

                span = BboxVisibilitySpan(
                    bbox=candidate,
                    appear_frame=hide_at,
                    hide_frame=None,
                )
                class_kept.append((candidate, span))
                spans.append(span)

    return spans


def _all_bbox_visibility_spans(
    bboxes: list[list[ChangeBBox] | ChangeBBox | None],
) -> list[BboxVisibilitySpan]:
    spans: list[BboxVisibilitySpan] = []
    for entry in bboxes:
        parsed = parse_frame_bbox_entry(entry)
        if not parsed:
            continue
        for bbox in parsed:
            spans.append(
                BboxVisibilitySpan(
                    bbox=bbox,
                    appear_frame=int(bbox.frame),
                    hide_frame=None,
                )
            )
    return spans


def nms_change_bboxes_intra_frame(
    bboxes: list[list[ChangeBBox] | ChangeBBox | None],
    *,
    iou_threshold: float = 0.25,
) -> tuple[list[list[ChangeBBox] | ChangeBBox | None], int]:
    """
    Greedy 3D NMS within each reconstruction frame and class group.

    When several same-class boxes overlap on one frame (e.g. duplicate oven
    detections), keeps the largest by volume (then changed_voxels).
    """
    if iou_threshold <= 0.0:
        return bboxes, 0

    filtered: list[list[ChangeBBox] | ChangeBBox | None] = []
    removed = 0
    for entry in bboxes:
        parsed = parse_frame_bbox_entry(entry)
        if not parsed:
            filtered.append(entry)
            continue
        by_class: dict[str, list[ChangeBBox]] = {}
        for bbox in parsed:
            by_class.setdefault(_nms_class_group(bbox.label), []).append(bbox)
        kept: list[ChangeBBox] = []
        for candidates in by_class.values():
            class_kept: list[ChangeBBox] = []
            for candidate in sorted(candidates, key=_bbox_sort_key, reverse=True):
                if any(
                    _bbox_suppression_score(candidate, kept_box) >= iou_threshold
                    for kept_box in class_kept
                ):
                    removed += 1
                    continue
                class_kept.append(candidate)
            kept.extend(class_kept)
        filtered.append(kept if kept else None)
    if removed == 0:
        return bboxes, 0
    return filtered, removed


def resolve_progressive_bbox_spans(
    bboxes: list[list[ChangeBBox] | ChangeBBox | None],
    *,
    timing,
    animate: bool,
    progressive_class_nms_iou: float | None,
) -> list[BboxVisibilitySpan]:
    """Spans for Blender import (intra-frame NMS + optional progressive timeline)."""
    if progressive_class_nms_iou is None:
        from .config import algo_3d_bbox_default

        progressive_class_nms_iou = float(
            algo_3d_bbox_default("progressive_class_nms_iou")
        )
    iou = float(progressive_class_nms_iou)
    if iou <= 0.0:
        return _all_bbox_visibility_spans(bboxes)

    bboxes, intra_removed = nms_change_bboxes_intra_frame(
        bboxes, iou_threshold=iou
    )
    if intra_removed > 0:
        print(
            f"[vibephysics] algo_3d_bbox: removed {intra_removed} same-frame "
            f"overlapping box(es) (per-class 3D IoU >= {iou:g})",
            flush=True,
        )

    if timing is None or not animate:
        return _all_bbox_visibility_spans(bboxes)
    if getattr(timing, "discrete", False):
        return _all_bbox_visibility_spans(bboxes)
    return compute_progressive_bbox_visibility_spans(
        bboxes,
        iou_threshold=iou,
    )


def nms_change_bboxes_progressive(
    bboxes: list[list[ChangeBBox] | ChangeBBox | None],
    *,
    iou_threshold: float = 0.25,
) -> tuple[list[list[ChangeBBox] | ChangeBBox | None], int]:
    """
    Drop boxes that never appear on the progressive timeline (JSON / static export).

    For Blender progressive playback, use ``compute_progressive_bbox_visibility_spans``
    so earlier boxes stay visible until a later frame replaces them.
    """
    spans = compute_progressive_bbox_visibility_spans(
        bboxes, iou_threshold=iou_threshold
    )
    if not spans:
        return bboxes, 0
    kept_ids = {id(span.bbox) for span in spans}
    total_before = sum(
        len(parsed)
        for entry in bboxes
        if (parsed := parse_frame_bbox_entry(entry))
    )
    removed = total_before - len(kept_ids)
    if removed == 0:
        return bboxes, 0
    return _rebuild_bbox_frames(bboxes, kept_ids), removed


def nms_change_bboxes_per_class(
    bboxes: list[list[ChangeBBox] | ChangeBBox | None],
    *,
    iou_threshold: float = 0.25,
) -> tuple[list[list[ChangeBBox] | ChangeBBox | None], int]:
    """Global greedy NMS per class (all frames at once)."""
    if iou_threshold <= 0.0:
        return bboxes, 0

    all_boxes: list[ChangeBBox] = []
    for entry in bboxes:
        parsed = parse_frame_bbox_entry(entry)
        if parsed:
            all_boxes.extend(parsed)
    if len(all_boxes) <= 1:
        return bboxes, 0

    by_class: dict[str, list[ChangeBBox]] = {}
    for bbox in all_boxes:
        by_class.setdefault(_nms_class_group(bbox.label), []).append(bbox)

    kept_ids: set[int] = set()
    removed = 0
    for boxes in by_class.values():
        class_kept: list[ChangeBBox] = []
        for candidate in sorted(boxes, key=_bbox_sort_key, reverse=True):
            if any(
                _bbox_suppression_score(candidate, kept_box) >= iou_threshold
                for kept_box in class_kept
            ):
                removed += 1
                continue
            class_kept.append(candidate)
            kept_ids.add(id(candidate))

    if removed == 0:
        return bboxes, 0
    return _rebuild_bbox_frames(bboxes, kept_ids), removed


_CUBE_EDGES = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 0),
    (4, 5),
    (5, 6),
    (6, 7),
    (7, 4),
    (0, 4),
    (1, 5),
    (2, 6),
    (3, 7),
)


def _cube_corners(center: np.ndarray, size: np.ndarray) -> list[tuple[float, float, float]]:
    half = np.maximum(size, 1e-4) * 0.5
    cx, cy, cz = center
    hx, hy, hz = half
    return [
        (cx - hx, cy - hy, cz - hz),
        (cx + hx, cy - hy, cz - hz),
        (cx + hx, cy + hy, cz - hz),
        (cx - hx, cy + hy, cz - hz),
        (cx - hx, cy - hy, cz + hz),
        (cx + hx, cy - hy, cz + hz),
        (cx + hx, cy + hy, cz + hz),
        (cx - hx, cy + hy, cz + hz),
    ]


_CUBE_FACES = (
    (0, 1, 2, 3),
    (4, 7, 6, 5),
    (0, 4, 5, 1),
    (1, 5, 6, 2),
    (2, 6, 7, 3),
    (0, 3, 7, 4),
)


def class_colors_from_detection_meta(
    detection_seg: dict[str, Any] | None,
) -> dict[str, tuple[float, float, float, float]]:
    from .config import _parse_rgba, parse_detection_seg_classes

    if not detection_seg:
        return {}
    classes = detection_seg.get("classes") or []
    _, colors_from_yaml = parse_detection_seg_classes(classes)
    raw = detection_seg.get("class_colors")
    if isinstance(raw, dict) and raw:
        colors = dict(colors_from_yaml)
        for key, value in raw.items():
            colors[str(key)] = _parse_rgba(value)
        return colors
    return colors_from_yaml


def _normalize_bbox_rgba(
    color: tuple[float, float, float, float] | list[float],
) -> tuple[float, float, float, float]:
    from .config import _parse_rgba

    return _parse_rgba(list(color))


def display_bbox_label(label: str | None) -> str:
    """Class name for Blender text (no instance #1/#2 suffix)."""
    if not label:
        return ""
    return label.strip().split("#", 1)[0].strip()


def _bbox_color_for_label(
    label: str | None,
    class_colors: dict[str, tuple[float, float, float, float]] | None,
) -> tuple[float, float, float, float]:
    if label and class_colors:
        key = display_bbox_label(label).lower()
        lowered = {str(k).strip().lower(): v for k, v in class_colors.items()}
        if key in lowered:
            return lowered[key]
    return CHANGE_BBOX_COLOR


def _get_bbox_material(
    cache: dict[tuple[float, float, float, float], Any],
    color: tuple[float, float, float, float],
    *,
    suffix: str = "",
) -> Any:
    """Reuse emission materials per RGBA (viewport + render use the same tint)."""
    rgba = _normalize_bbox_rgba(color)
    cached = cache.get(rgba)
    if cached is not None:
        return cached

    from vibephysics.annotation.base import create_emission_material

    name = (
        f"ChangeBBoxMat_{int(rgba[0]*255):02x}{int(rgba[1]*255):02x}"
        f"{int(rgba[2]*255):02x}{suffix}"
    )
    mat = create_emission_material(name, rgba, strength=4.0)
    mat.diffuse_color = rgba
    mat.blend_method = "BLEND"
    mat.use_backface_culling = False
    if hasattr(mat, "shadow_method"):
        mat.shadow_method = "NONE"
    cache[rgba] = mat
    return mat


def _create_bbox_wireframe_object(
    name: str,
    verts: list[tuple[float, float, float]],
    material,
    rgba: tuple[float, float, float, float],
    *,
    wire_radius: float,
) -> "bpy.types.Object":
    """Colored box edges as a curve with fixed bevel (not mesh WIREFRAME scaling with size)."""
    import bpy

    curve = bpy.data.curves.new(name=f"{name}_WireCurve", type="CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = max(float(wire_radius), 1e-4)
    curve.bevel_resolution = 2

    while curve.splines:
        curve.splines.remove(curve.splines[0])

    for i0, i1 in _CUBE_EDGES:
        spline = curve.splines.new(type="POLY")
        if len(spline.points) < 2:
            spline.points.add(2 - len(spline.points))
        p0 = verts[i0]
        p1 = verts[i1]
        spline.points[0].co = (float(p0[0]), float(p0[1]), float(p0[2]), 1.0)
        spline.points[1].co = (float(p1[0]), float(p1[1]), float(p1[2]), 1.0)

    obj = bpy.data.objects.new(name, curve)
    curve.materials.append(material)
    obj.active_material = material
    obj.color = rgba
    obj.show_in_front = True
    if hasattr(obj, "show_wire"):
        obj.show_wire = False
    return obj


def _voxel_cube_corners(
    center: np.ndarray,
    half_size: float,
) -> list[tuple[float, float, float]]:
    cx, cy, cz = center
    h = float(half_size)
    return [
        (cx - h, cy - h, cz - h),
        (cx + h, cy - h, cz - h),
        (cx + h, cy + h, cz - h),
        (cx - h, cy + h, cz - h),
        (cx - h, cy - h, cz + h),
        (cx + h, cy - h, cz + h),
        (cx + h, cy + h, cz + h),
        (cx - h, cy + h, cz + h),
    ]


def _merged_voxel_cubes_mesh(
    centers: np.ndarray,
    half_size: float,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    verts: list[tuple[float, float, float]] = []
    faces: list[tuple[int, ...]] = []
    for center in centers:
        base = len(verts)
        verts.extend(_voxel_cube_corners(np.asarray(center, dtype=np.float64), half_size))
        faces.extend(tuple(v + base for v in face) for face in _CUBE_FACES)
    return verts, faces


def _get_voxel_material(
    cache: dict[tuple[tuple[float, float, float, float], float], Any],
    color: tuple[float, float, float, float],
    *,
    alpha: float,
) -> Any:
    import bpy

    rgba = _normalize_bbox_rgba(color)
    key = (rgba, float(alpha))
    cached = cache.get(key)
    if cached is not None:
        return cached

    name = (
        f"OccupancyVoxelMat_{int(rgba[0]*255):02x}{int(rgba[1]*255):02x}"
        f"{int(rgba[2]*255):02x}_a{int(alpha * 255):02x}"
    )
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (
            float(rgba[0]),
            float(rgba[1]),
            float(rgba[2]),
            1.0,
        )
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = float(alpha)
    mat.diffuse_color = (float(rgba[0]), float(rgba[1]), float(rgba[2]), float(alpha))
    mat.blend_method = "BLEND"
    mat.use_backface_culling = False
    if hasattr(mat, "shadow_method"):
        mat.shadow_method = "NONE"
    cache[key] = mat
    return mat


def _bbox_visualize_threshold(
    bbox: ChangeBBox,
    min_voxels: int,
) -> int:
    threshold = int(min_voxels)
    if bbox.label:
        threshold = min(threshold, 12)
    return threshold


def _attach_bbox_label_text(
    *,
    display_label: str,
    center: np.ndarray,
    size: np.ndarray,
    collection,
    base_name: str,
    recon_frame: int,
    material_cache: dict[tuple[float, float, float, float], Any],
    rgba: tuple[float, float, float, float],
    timing,
    animate: bool,
    hide_frame_index: int | None = None,
) -> "bpy.types.Object | None":
    """Class-name text above the bbox; same visibility keyframes as the box."""
    if not display_label:
        return None
    from .visual import _keyframe_change_bbox_visibility

    label_mat = _get_bbox_material(material_cache, rgba, suffix="_label")
    label_obj = _create_bbox_label_text(
        display_label,
        center,
        size,
        collection,
        base_name=base_name,
        material=label_mat,
        color=rgba,
    )
    label_obj["change_bbox_frame"] = recon_frame
    label_obj["change_bbox_label"] = display_label
    if animate and timing is not None:
        _keyframe_change_bbox_visibility(
            label_obj,
            timing,
            recon_frame,
            hide_frame_index=hide_frame_index,
        )
    else:
        label_obj.hide_viewport = True
        label_obj.hide_render = True
    return label_obj


def _resolve_bbox_label_camera():
    """Scene camera for label billboards (PlaybackCamera when animated)."""
    import bpy

    cam = bpy.context.scene.camera
    if cam is not None:
        return cam
    playback = bpy.data.objects.get("PlaybackCamera")
    if playback is not None and playback.type == "CAMERA":
        return playback
    for obj in bpy.data.objects:
        if obj.type == "CAMERA":
            return obj
    return None


def _add_bbox_label_track_to_camera(text_obj, camera) -> "bpy.types.Object":
    """Billboard pivot tracks camera; text uses local -X scale to fix mirror (not Z-rotate)."""
    import bpy

    pivot = bpy.data.objects.new(f"{text_obj.name}_TrackPivot", None)
    pivot.location = text_obj.location.copy()
    for coll in text_obj.users_collection:
        coll.objects.link(pivot)
    if not pivot.users_collection:
        bpy.context.scene.collection.objects.link(pivot)

    text_obj.parent = pivot
    text_obj.matrix_parent_inverse = pivot.matrix_world.inverted()
    text_obj.location = (0.0, 0.0, 0.0)
    text_obj.rotation_euler = (0.0, 0.0, 0.0)
    # TRACK_TO aims FONT -Z at the camera; glyphs read mirrored without a local X flip.
    # Do not rotate 180° on Z — that spins in the billboard plane and reads upside-down.
    text_obj.scale = (-1.0, 1.0, 1.0)

    track = pivot.constraints.new(type="TRACK_TO")
    track.target = camera
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    track.owner_space = "WORLD"
    track.target_space = "WORLD"
    if hasattr(track, "show_expires"):
        track.show_expires = False
    # Do not hide_viewport on pivot — that hides child label text in the viewport.
    pivot.empty_display_type = "PLAIN_AXES"
    pivot.empty_display_size = 0.001
    pivot.hide_render = True
    return pivot


def _finalize_bbox_label_orientation(
    text_obj,
    *,
    world_rotation=None,
    face_camera: bool = True,
) -> None:
    """Apply export rotation; billboard to camera when enabled."""
    import math

    from .visual import _rotate_object_world

    if face_camera:
        camera = _resolve_bbox_label_camera()
        if camera is not None:
            pivot = _add_bbox_label_track_to_camera(text_obj, camera)
            _rotate_object_world(pivot, world_rotation)
            return
    text_obj.rotation_euler = (math.pi / 2.0, 0.0, 0.0)
    _rotate_object_world(text_obj, world_rotation)


def _create_bbox_label_text(
    display_label: str,
    center: np.ndarray,
    size: np.ndarray,
    collection,
    *,
    base_name: str,
    material,
    color: tuple[float, float, float, float],
) -> "bpy.types.Object":
    """Z-up text just above the bbox top face (no extra box geometry)."""
    import bpy

    center = np.asarray(center, dtype=np.float64)
    size = np.asarray(size, dtype=np.float64)
    text_height = max(float(np.max(size)) * 0.1, 0.035)
    top_z = float(center[2] + size[2] * 0.5)
    gap = max(text_height * 0.15, 0.01)

    curve = bpy.data.curves.new(name=f"{base_name}_LabelCurve", type="FONT")
    curve.body = display_label
    curve.size = text_height
    curve.extrude = 0.0
    curve.offset = 0.0
    curve.bevel_depth = 0.0
    curve.bevel_resolution = 0
    curve.align_x = "CENTER"
    curve.align_y = "BOTTOM"

    text_obj = bpy.data.objects.new(f"{base_name}_Label", curve)
    text_obj.location = (float(center[0]), float(center[1]), top_z + gap)
    collection.objects.link(text_obj)
    text_obj.data.materials.append(material)
    text_obj.active_material = material
    text_obj.color = color
    text_obj.show_in_front = True
    if hasattr(text_obj, "show_wire"):
        text_obj.show_wire = False
    if hasattr(text_obj, "display_type"):
        text_obj.display_type = "SOLID"
    text_obj["change_bbox_label_text"] = display_label
    return text_obj


def import_detection_occupancy_voxels_to_blender(
    bboxes: list[list[ChangeBBox] | ChangeBBox | None],
    collection,
    *,
    labels_collection=None,
    attach_class_labels: bool = True,
    timing=None,
    animate: bool = True,
    min_visualize_changed_voxels: int,
    class_colors: dict[str, tuple[float, float, float, float]] | None = None,
    progressive_class_nms_iou: float | None = None,
    voxel_size: float = 0.02,
    voxel_alpha: float = 0.1,
    world_rotation=None,
    label_face_camera: bool | None = None,
) -> list:
    """Semi-transparent class-colored cubes at masked occupancy voxel centers."""
    import bpy

    from .config import algo_3d_bbox_default
    from .visual import _keyframe_change_bbox_visibility, _rotate_object_world

    if label_face_camera is None:
        label_face_camera = bool(algo_3d_bbox_default("label_face_camera"))
    label_coll = labels_collection if labels_collection is not None else collection

    spans = resolve_progressive_bbox_spans(
        bboxes,
        timing=timing,
        animate=animate,
        progressive_class_nms_iou=progressive_class_nms_iou,
    )
    if progressive_class_nms_iou and timing is not None and not timing.discrete and animate:
        iou = float(progressive_class_nms_iou or 0.0)
        if iou > 0:
            n_hide = sum(1 for s in spans if s.hide_frame is not None)
            if n_hide:
                print(
                    f"[vibephysics] algo_3d_bbox: {n_hide} progressive box/voxel span(s) "
                    f"hide when replaced by a later same-class detection (IoU >= {iou:g})",
                    flush=True,
                )

    min_voxels = int(min_visualize_changed_voxels)
    half_size = max(float(voxel_size) * 0.5 * 0.98, 1e-4)
    alpha = float(np.clip(voxel_alpha, 0.01, 1.0))
    objects: list = []
    skipped_low_change = 0
    skipped_no_voxels = 0
    material_cache: dict[tuple[tuple[float, float, float, float], float], Any] = {}
    instance_idx = 0

    for span in spans:
        bbox = span.bbox
        recon_frame = int(span.appear_frame)
        hide_frame = span.hide_frame
        changed_voxels = int(getattr(bbox, "changed_voxels", bbox.changed_points))
        if changed_voxels < _bbox_visualize_threshold(bbox, min_voxels):
            skipped_low_change += 1
            continue
        centers = bbox.voxel_centers
        if not centers:
            skipped_no_voxels += 1
            continue

        centers_np = np.asarray(centers, dtype=np.float64)
        if centers_np.ndim != 2 or len(centers_np) == 0:
            skipped_no_voxels += 1
            continue

        label_slug = (bbox.label or "change").replace(" ", "_")
        rgba = _bbox_color_for_label(bbox.label, class_colors)
        verts, faces = _merged_voxel_cubes_mesh(centers_np, half_size)
        obj_name = f"OccupancyVoxel_{label_slug}_{recon_frame}_{instance_idx}"
        instance_idx += 1

        mesh = bpy.data.meshes.new(name=f"{obj_name}_Mesh")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        for poly in mesh.polygons:
            poly.use_smooth = False

        obj = bpy.data.objects.new(obj_name, mesh)
        collection.objects.link(obj)
        obj.color = rgba
        obj.show_in_front = True
        obj["change_bbox_frame"] = recon_frame
        obj["change_bbox_label"] = bbox.label or ""
        obj["changed_voxels"] = changed_voxels
        obj["occupancy_voxel_count"] = len(centers_np)
        if hide_frame is not None:
            obj["change_bbox_hide_frame"] = int(hide_frame)

        mat = _get_voxel_material(material_cache, rgba, alpha=alpha)
        mesh.materials.append(mat)
        obj.active_material = mat
        _rotate_object_world(obj, world_rotation)

        if animate and timing is not None:
            _keyframe_change_bbox_visibility(
                obj,
                timing,
                recon_frame,
                hide_frame_index=hide_frame,
            )
        else:
            obj.hide_viewport = True
            obj.hide_render = True

        objects.append(obj)

        if attach_class_labels:
            display_label = display_bbox_label(bbox.label)
            label_obj = _attach_bbox_label_text(
                display_label=display_label,
                center=np.array(bbox.center, dtype=np.float64),
                size=np.array(bbox.size, dtype=np.float64),
                collection=label_coll,
                base_name=obj_name,
                recon_frame=recon_frame,
                material_cache=material_cache,
                rgba=rgba,
                timing=timing,
                animate=animate,
                hide_frame_index=hide_frame,
            )
            if label_obj is not None:
                _finalize_bbox_label_orientation(
                    label_obj,
                    world_rotation=world_rotation,
                    face_camera=label_face_camera,
                )

    if skipped_low_change:
        print(
            f"[vibephysics] algo_3d_bbox: skipped {skipped_low_change} voxel object(s) with "
            f"changed_voxels below threshold (not shown in Blender)",
            flush=True,
        )
    if skipped_no_voxels:
        print(
            f"[vibephysics] algo_3d_bbox: skipped {skipped_no_voxels} detection entry(ies) "
            f"without voxel_centers (re-run reconstruct with detection_seg)",
            flush=True,
        )
    if objects:
        print(
            f"[vibephysics] algo_3d_bbox: showing {len(objects)} occupancy voxel object(s) "
            f"(alpha={alpha:g}, half_size={half_size:g} m)",
            flush=True,
        )
    return objects


def import_change_bboxes_to_blender(
    bboxes: list[list[ChangeBBox] | ChangeBBox | None],
    collection,
    *,
    labels_collection=None,
    timing=None,
    animate: bool = True,
    min_visualize_changed_voxels: int,
    class_colors: dict[str, tuple[float, float, float, float]] | None = None,
    progressive_class_nms_iou: float | None = None,
    world_rotation=None,
    label_face_camera: bool | None = None,
) -> list:
    """Add colored fixed-thickness wireframe boxes for each detection / change region."""
    import bpy

    from .config import algo_3d_bbox_default
    from .visual import _keyframe_change_bbox_visibility, _rotate_object_world

    if label_face_camera is None:
        label_face_camera = bool(algo_3d_bbox_default("label_face_camera"))
    wire_radius = float(algo_3d_bbox_default("bbox_wire_radius"))
    label_coll = labels_collection if labels_collection is not None else collection

    spans = resolve_progressive_bbox_spans(
        bboxes,
        timing=timing,
        animate=animate,
        progressive_class_nms_iou=progressive_class_nms_iou,
    )

    min_voxels = int(min_visualize_changed_voxels)
    objects = []
    label_objects: list = []
    skipped_low_change = 0
    material_cache: dict[tuple[float, float, float, float], Any] = {}
    instance_idx = 0
    for span in spans:
        bbox = span.bbox
        recon_frame = int(span.appear_frame)
        hide_frame = span.hide_frame
        changed_voxels = int(getattr(bbox, "changed_voxels", bbox.changed_points))
        if changed_voxels < _bbox_visualize_threshold(bbox, min_voxels):
            skipped_low_change += 1
            continue

        label_slug = (bbox.label or "change").replace(" ", "_")
        center = np.array(bbox.center, dtype=np.float64)
        size = np.array(bbox.size, dtype=np.float64)
        rgba = _bbox_color_for_label(bbox.label, class_colors)
        verts = _cube_corners(center, size)
        obj_name = f"ChangeBBox_{label_slug}_{recon_frame}_{instance_idx}"
        instance_idx += 1
        mat = _get_bbox_material(material_cache, rgba)
        obj = _create_bbox_wireframe_object(
            obj_name, verts, mat, rgba, wire_radius=wire_radius
        )
        collection.objects.link(obj)
        obj["change_bbox_frame"] = recon_frame
        obj["change_bbox_label"] = bbox.label or ""
        obj["changed_voxels"] = changed_voxels
        obj["change_fraction"] = bbox.change_fraction
        if hide_frame is not None:
            obj["change_bbox_hide_frame"] = int(hide_frame)
        _rotate_object_world(obj, world_rotation)

        if animate and timing is not None:
            _keyframe_change_bbox_visibility(
                obj,
                timing,
                recon_frame,
                hide_frame_index=hide_frame,
            )
        else:
            obj.hide_viewport = True
            obj.hide_render = True

        objects.append(obj)

        display_label = display_bbox_label(bbox.label)
        label_obj = _attach_bbox_label_text(
            display_label=display_label,
            center=center,
            size=size,
            collection=label_coll,
            base_name=obj_name,
            recon_frame=recon_frame,
            material_cache=material_cache,
            rgba=rgba,
            timing=timing,
            animate=animate,
            hide_frame_index=hide_frame,
        )
        if label_obj is not None:
            _finalize_bbox_label_orientation(
                label_obj,
                world_rotation=world_rotation,
                face_camera=label_face_camera,
            )
            label_objects.append(label_obj)

    if skipped_low_change:
        print(
            f"[vibephysics] algo_3d_bbox: skipped {skipped_low_change} box(es) with "
            f"changed_voxels <= {min_voxels} (not shown in Blender)"
        )
    if objects:
        print(
            f"[vibephysics] algo_3d_bbox: showing {len(objects)} box(es) with "
            f"changed_voxels > {min_voxels}"
        )
    if label_objects:
        print(
            f"[vibephysics] algo_3d_bbox: {len(label_objects)} class label(s) in "
            f"'{label_coll.name}'",
            flush=True,
        )

    return objects + label_objects
