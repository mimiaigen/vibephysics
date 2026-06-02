"""Estimate ground-plane alignment for feedforward point clouds (numpy only)."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from .schema import FeedforwardPrediction

# OpenCV world is Y-down; physical "up" is -Y (ground align rotates into this frame).
_OPENCV_UP = np.array([0.0, -1.0, 0.0], dtype=np.float64)

# Point subsampling for floor fit (single global pool; fraction of all valid points).
_GROUND_ALIGN_SAMPLE_FRAC = 0.20
_GROUND_ALIGN_DEFAULT_MIN_CONFIDENCE = 2.0
_GROUND_ALIGN_PREFILTER_LOW_PERCENTILE = 28.0
_GROUND_ALIGN_PREFILTER_MIN_FRAC = 0.04  # apply low-band prefilter only if enough mass there

# 1D Hough on height along scene_up → horizontal floor slabs.
_FLOOR_HOUGH_BINS = 96
_FLOOR_HOUGH_SMOOTH_BINS = 7
_FLOOR_HOUGH_MIN_PEAK_SEP_FRAC = 0.05
_FLOOR_HOUGH_MIN_PEAK_VOTE_FRAC = 0.012  # loose histogram peak gate (see in-band frac below)
_FLOOR_CLUSTER_HALF_WIDTH_FRAC = 0.03
_FLOOR_MIN_CLUSTER_POINT_FRAC = 0.15  # keep peak only if this fraction of points lie in band

# Fallback low band when Hough finds no qualifying peak.
_FLOOR_BOTTOM_PERCENTILE = 22.0
_FLOOR_BOTTOM_PERCENTILE_WIDE = 35.0

# Plane fit on the chosen low band (bumpy depth — damp tilt, trim outliers above plane).
_FLOOR_TRIM_PASSES = 3
_FLOOR_TRIM_KEEP_PERCENTILE = 88.0
_FLOOR_NORMAL_HORIZ_KEEP = 0.25
# After leveling, translate so the floor band sits above z=0 (Blender Z-up).
_GROUND_Z_CLEARANCE = 0.01
_FLOOR_HEIGHT_PERCENTILE = 8.0


def _heights(points: np.ndarray, up: np.ndarray = _OPENCV_UP) -> np.ndarray:
    return points @ up


def _normalize(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-8 else _OPENCV_UP.copy()


def _c2w_from_extrinsic(w2c: np.ndarray, *, w2c_as_camera_pose: bool) -> np.ndarray:
    w2c4 = np.vstack([np.asarray(w2c, dtype=np.float64), [0.0, 0.0, 0.0, 1.0]])
    return w2c4 if w2c_as_camera_pose else np.linalg.inv(w2c4)


def _first_frame_camera(
    extrinsics: np.ndarray,
    *,
    w2c_as_camera_pose: bool,
) -> tuple[np.ndarray, np.ndarray]:
    """Frame-0 camera position and up (+Y opencv camera -> -R[:,1] in world)."""
    c2w = _c2w_from_extrinsic(extrinsics[0], w2c_as_camera_pose=w2c_as_camera_pose)
    return c2w[:3, 3].copy(), _normalize(-c2w[:3, 1])


def _camera_up_consensus(
    extrinsics: np.ndarray,
    *,
    w2c_as_camera_pose: bool,
) -> tuple[np.ndarray, float]:
    """Median OpenCV camera-up in world space; agreement in [0, 1]."""
    vecs: list[np.ndarray] = []
    for w2c in extrinsics:
        c2w = _c2w_from_extrinsic(w2c, w2c_as_camera_pose=w2c_as_camera_pose)
        vecs.append(_normalize(-c2w[:3, 1]))
    if not vecs:
        return _OPENCV_UP.copy(), 0.0
    ref = vecs[0]
    aligned = [v if float(v @ ref) >= 0.0 else -v for v in vecs]
    stack = np.stack(aligned, axis=0)
    up = _normalize(np.median(stack, axis=0))
    return up, float(np.median(np.abs(stack @ up)))


def _up_from_point_axes(points: np.ndarray) -> np.ndarray:
    """Pick ±X/±Y/±Z with the best near-horizontal low band (engine-agnostic fallback)."""
    best_up = _OPENCV_UP.copy()
    best_score = -1.0
    for axis in range(3):
        for sign in (-1.0, 1.0):
            u = np.zeros(3, dtype=np.float64)
            u[axis] = sign
            heights = _heights(points, u)
            band = points[heights <= float(np.percentile(heights, _FLOOR_BOTTOM_PERCENTILE))]
            if band.shape[0] < 50:
                continue
            normal, _ = _refine_plane(band, np.ones(band.shape[0], dtype=bool))
            normal = _normalize(normal)
            horiz = abs(float(normal @ u))
            if horiz < 0.5:
                continue
            score = float(band.shape[0]) * horiz
            if score > best_score:
                best_score = score
                best_up = u if float(normal @ u) > 0.0 else -u
    return _normalize(best_up)


def _collect_frame0_points(
    predictions: dict | FeedforwardPrediction,
    *,
    max_points: int = 30_000,
) -> np.ndarray | None:
    """Finite world points from frame 0 only (reference view for gravity/up)."""
    if isinstance(predictions, FeedforwardPrediction):
        world_points = predictions.world_points
    else:
        world_points = predictions.get("world_points_from_depth", predictions.get("world_points"))
    if world_points is None or len(world_points) == 0:
        return None

    frame0 = np.asarray(world_points[0], dtype=np.float64).reshape(-1, 3)
    valid = np.isfinite(frame0).all(axis=1)
    pts = frame0[valid]
    if pts.shape[0] < 50:
        return None
    if pts.shape[0] > max_points:
        rng = np.random.default_rng(0)
        idx = rng.choice(pts.shape[0], max_points, replace=False)
        pts = pts[idx]
    return pts


def _scene_bulk_below_camera(
    points: np.ndarray,
    cam_pos: np.ndarray,
    up: np.ndarray,
    *,
    min_below_frac: float = 0.52,
) -> bool:
    """True when most of the scene lies below the camera along ``up``."""
    relative = (points - cam_pos) @ _normalize(up)
    return float(np.mean(relative < 0.0)) >= min_below_frac


def _orient_scene_up_from_first_camera(
    points: np.ndarray,
    up: np.ndarray,
    cam_pos: np.ndarray,
    cam_up: np.ndarray,
) -> np.ndarray:
    """Use frame-0 camera up; flip if the reference view bulk sits above the camera."""
    up = _normalize(cam_up if float(up @ cam_up) >= 0.0 else -up)
    if not _scene_bulk_below_camera(points, cam_pos, up):
        up = -up
    return _normalize(up)


def _estimate_scene_up(
    points: np.ndarray,
    extrinsics: np.ndarray,
    *,
    w2c_as_camera_pose: bool,
    frame0_points: np.ndarray | None = None,
) -> np.ndarray:
    """Gravity-up from frame-0 camera pose and frame-0 scene geometry."""
    cam_pos, first_up = _first_frame_camera(extrinsics, w2c_as_camera_pose=w2c_as_camera_pose)
    orient_pts = frame0_points
    if orient_pts is None or orient_pts.shape[0] < 50:
        orient_pts = points
    up = _orient_scene_up_from_first_camera(orient_pts, first_up, cam_pos, first_up)

    if len(extrinsics) >= 3:
        cam_up, agree = _camera_up_consensus(extrinsics, w2c_as_camera_pose=w2c_as_camera_pose)
        if agree >= 0.6 and float(cam_up @ first_up) >= 0.0:
            up = _orient_scene_up_from_first_camera(orient_pts, cam_up, cam_pos, first_up)
    return up


def _plane_distances(points: np.ndarray, normal: np.ndarray, offset: float) -> np.ndarray:
    return np.abs(points @ normal + offset)


def _refine_plane(
    points: np.ndarray,
    mask: np.ndarray,
    *,
    fallback_up: np.ndarray = _OPENCV_UP,
) -> tuple[np.ndarray, float]:
    inliers = points[mask]
    centroid = inliers.mean(axis=0)
    centered = inliers - centroid
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    normal = vh[-1]
    norm = float(np.linalg.norm(normal))
    if norm < 1e-8:
        normal = fallback_up.copy()
    else:
        normal = normal / norm
    offset = -float(np.dot(normal, centroid))
    return normal, offset


def _orient_ground_normal(
    normal: np.ndarray,
    *,
    points: np.ndarray | None = None,
    inlier_mask: np.ndarray | None = None,
    up: np.ndarray = _OPENCV_UP,
) -> np.ndarray:
    """Orient plane normal to point along physical up (+up direction)."""
    normal = np.asarray(normal, dtype=np.float64)
    norm = float(np.linalg.norm(normal))
    if norm < 1e-8:
        return up.copy()
    normal = normal / norm

    candidates = (normal, -normal)
    if points is not None and inlier_mask is not None and np.any(inlier_mask):
        inliers = points[inlier_mask]
        outliers = points[~inlier_mask]
        plane_point = inliers.mean(axis=0)
        best = normal if float(normal @ up) >= 0.0 else -normal
        best_score = float("-inf")
        for candidate in candidates:
            if float(candidate @ up) <= 0.0:
                continue
            if outliers.shape[0] == 0:
                score = float(candidate @ up)
            else:
                signed = (outliers - plane_point) @ candidate
                score = float(np.mean(signed > 0.0)) + 0.01 * float(candidate @ up)
            if score > best_score:
                best_score = score
                best = candidate
        return best

    if float(normal @ up) < 0.0:
        normal = -normal
    return normal


def _snap_floor_normal(
    normal: np.ndarray,
    *,
    up: np.ndarray = _OPENCV_UP,
    horiz_keep: float = _FLOOR_NORMAL_HORIZ_KEEP,
) -> np.ndarray:
    """Tilt estimate from a bumpy low band — damp tilt perpendicular to up."""
    normal = _orient_ground_normal(normal, up=up)
    along = float(normal @ up) * up
    horiz = normal - along
    if float(np.linalg.norm(along)) < 0.35:
        return up.copy()
    damped = along + horiz_keep * horiz
    return _normalize(damped)


def _rotation_matrix_align_normal(normal: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Return 3x3 rotation mapping unit normal onto target."""
    normal = normal / max(float(np.linalg.norm(normal)), 1e-8)
    target = np.asarray(target, dtype=np.float64)
    target = target / max(float(np.linalg.norm(target)), 1e-8)
    dot = float(np.clip(np.dot(normal, target), -1.0, 1.0))

    if dot > 1.0 - 1e-8:
        return np.eye(3, dtype=np.float64)
    if dot < -1.0 + 1e-8:
        axis = np.cross(normal, target)
        if float(np.linalg.norm(axis)) < 1e-8:
            return np.diag([1.0, -1.0, -1.0])
        return _rotation_matrix_align_normal(-normal, target)

    axis = np.cross(normal, target)
    axis_norm = float(np.linalg.norm(axis))
    if axis_norm < 1e-8:
        return np.eye(3, dtype=np.float64)
    axis = axis / axis_norm
    angle = math.acos(dot)
    kx, ky, kz = axis
    k = np.array([[0.0, -kz, ky], [kz, 0.0, -kx], [-ky, kx, 0.0]], dtype=np.float64)
    return np.eye(3) + math.sin(angle) * k + (1.0 - math.cos(angle)) * (k @ k)


def _level_ground_rotation(
    rotation: np.ndarray,
    points: np.ndarray,
    *,
    passes: int = 4,
    height_percentile: float = 20.0,
    tilt_stop_deg: float = 0.05,
    up: np.ndarray = _OPENCV_UP,
) -> np.ndarray:
    """Iteratively fit the lowest points and align their plane normal to up."""
    rot = rotation
    for _ in range(passes):
        aligned = (rot @ points.T).T
        heights = _heights(aligned, up)
        h_cut = float(np.percentile(heights, height_percentile))
        ground = aligned[heights <= h_cut]
        if ground.shape[0] < 50:
            ground = aligned
        if ground.shape[0] < 3:
            break
        normal, _ = _refine_plane(ground, np.ones(ground.shape[0], dtype=bool))
        normal = _orient_ground_normal(normal, up=up)
        tilt_deg = math.degrees(
            math.acos(float(np.clip(abs(float(normal @ up)), 0.0, 1.0)))
        )
        if tilt_deg < tilt_stop_deg:
            break
        rot = _rotation_matrix_align_normal(normal, up) @ rot
    return rot


def _c2w_after_rotation(
    w2c: np.ndarray,
    rotation: np.ndarray,
    *,
    w2c_as_camera_pose: bool,
) -> np.ndarray:
    c2w = _c2w_from_extrinsic(w2c, w2c_as_camera_pose=w2c_as_camera_pose)
    out = np.eye(4, dtype=np.float64)
    rot = np.asarray(rotation, dtype=np.float64)
    out[:3, :3] = rot @ c2w[:3, :3]
    out[:3, 3] = rot @ c2w[:3, 3]
    return out


def _flip_upside_down_rotation(
    rotation: np.ndarray,
    points: np.ndarray,
    inlier_mask: np.ndarray,
    extrinsics: np.ndarray,
    *,
    w2c_as_camera_pose: bool,
    up: np.ndarray = _OPENCV_UP,
) -> np.ndarray:
    """180° flip if frame-0 camera or floor band is inverted after leveling."""
    rot = np.asarray(rotation, dtype=np.float64)
    flip = _rotation_matrix_align_normal(-up, up)
    c2w = _c2w_after_rotation(extrinsics[0], rot, w2c_as_camera_pose=w2c_as_camera_pose)
    cam_up = _normalize(-c2w[:3, 1])
    cam_pos = c2w[:3, 3]
    cam_h = float(cam_pos @ up)
    aligned = (rot @ points.T).T
    floor_h = float(np.median(_heights(aligned[inlier_mask], up))) if np.any(inlier_mask) else cam_h
    rel = (aligned - cam_pos) @ up
    frac_below = float(np.mean(rel < 0.0))
    if float(cam_up @ up) < 0.0 or floor_h >= cam_h or frac_below < 0.45:
        return flip @ rot
    return rot


_GROUND_ALIGN_MAX_RESIDUAL_TILT_DEG = 20.0
_GROUND_ALIGN_MAX_FLOOR_SLOPE = 0.12
_MIN_TILT_IMPROVEMENT_DEG = 0.15
_LEVEL_GROUND_PASSES = 6


def _is_acceptable_ground_rotation(rotation: np.ndarray, points: np.ndarray) -> tuple[bool, float, float, float]:
    """Accept when alignment reduces low-band tilt (bumpy floor; slopes stay loose)."""
    tilt, slope_x, slope_y = _residual_floor_slopes(rotation, points)
    tilt_before, _, _ = _residual_floor_slopes(np.eye(3), points)
    improved = (tilt_before - tilt) >= _MIN_TILT_IMPROVEMENT_DEG
    ok = improved and tilt <= _GROUND_ALIGN_MAX_RESIDUAL_TILT_DEG
    return ok, tilt, slope_x, slope_y


def _record_ground_align_metadata(
    prediction: FeedforwardPrediction,
    *,
    status: str,
    tilt_before: float | None = None,
    tilt_after: float | None = None,
    slope_x: float | None = None,
    slope_y: float | None = None,
    euler_deg: tuple[float, float, float] | None = None,
    floor_clusters: list[tuple[float, int]] | None = None,
) -> None:
    prediction.metadata = dict(prediction.metadata)
    prediction.metadata["ground_align_status"] = status
    if tilt_before is not None:
        prediction.metadata["ground_align_tilt_before_deg"] = float(tilt_before)
    if tilt_after is not None:
        prediction.metadata["ground_align_tilt_after_deg"] = float(tilt_after)
    if slope_x is not None:
        prediction.metadata["ground_align_slope_x"] = float(slope_x)
    if slope_y is not None:
        prediction.metadata["ground_align_slope_y"] = float(slope_y)
    if euler_deg is not None:
        prediction.metadata["ground_align_euler_deg"] = list(euler_deg)
    if floor_clusters is not None:
        _store_floor_cluster_metadata(prediction, floor_clusters)


def _matrix_to_euler_xyz(rotation: np.ndarray) -> tuple[float, float, float]:
    """Convert rotation matrix to XYZ Euler angles in radians."""
    rot = np.asarray(rotation, dtype=np.float64)
    sy = math.sqrt(float(rot[0, 0] * rot[0, 0] + rot[1, 0] * rot[1, 0]))
    if sy >= 1e-8:
        x = math.atan2(float(rot[2, 1]), float(rot[2, 2]))
        y = math.atan2(float(-rot[2, 0]), sy)
        z = math.atan2(float(rot[1, 0]), float(rot[0, 0]))
    else:
        x = math.atan2(float(-rot[1, 2]), float(rot[1, 1]))
        y = math.atan2(float(-rot[2, 0]), sy)
        z = 0.0
    return x, y, z


def _hough_floor_clusters(heights: np.ndarray) -> list[tuple[float, int]]:
    """
    1D Hough voting on height along scene_up — peaks are horizontal floor bands.
    Returns [(center_height, votes), ...] sorted low to high.
    """
    heights = np.asarray(heights, dtype=np.float64)
    if heights.shape[0] < 3:
        return []

    h_min = float(heights.min())
    h_max = float(heights.max())
    span = max(h_max - h_min, 1e-6)
    hist, edges = np.histogram(heights, bins=_FLOOR_HOUGH_BINS)
    acc = hist.astype(np.float64)
    if _FLOOR_HOUGH_SMOOTH_BINS > 1:
        kernel = np.ones(_FLOOR_HOUGH_SMOOTH_BINS, dtype=np.float64)
        kernel /= kernel.sum()
        acc = np.convolve(acc, kernel, mode="same")

    min_votes = max(30, int(heights.shape[0] * _FLOOR_HOUGH_MIN_PEAK_VOTE_FRAC))
    min_sep = max(span * _FLOOR_HOUGH_MIN_PEAK_SEP_FRAC, span / _FLOOR_HOUGH_BINS)

    raw: list[tuple[float, int]] = []
    for i in range(1, len(acc) - 1):
        if acc[i] < min_votes or acc[i] < acc[i - 1] or acc[i] < acc[i + 1]:
            continue
        center = 0.5 * (float(edges[i]) + float(edges[i + 1]))
        raw.append((center, int(round(acc[i]))))

    raw.sort(key=lambda item: item[0])
    merged: list[tuple[float, int]] = []
    for center, votes in raw:
        if merged and (center - merged[-1][0]) < min_sep:
            if votes > merged[-1][1]:
                merged[-1] = (center, votes)
        else:
            merged.append((center, votes))
    return merged


def _cluster_band_fraction(
    heights: np.ndarray,
    center: float,
    *,
    span: float | None = None,
) -> float:
    """Fraction of all heights that lie in the band around a Hough peak."""
    heights = np.asarray(heights, dtype=np.float64)
    if span is None:
        span = max(float(np.ptp(heights)), 1e-6)
    half_w = max(span * _FLOOR_CLUSTER_HALF_WIDTH_FRAC, span * 0.008)
    return float(np.mean(np.abs(heights - center) <= half_w))


def _filter_floor_clusters_by_point_fraction(
    heights: np.ndarray,
    clusters: list[tuple[float, int]],
    *,
    min_frac: float = _FLOOR_MIN_CLUSTER_POINT_FRAC,
) -> list[tuple[float, int, float]]:
    """Keep height bands with enough global point mass; attach in-band fraction."""
    if not clusters:
        return []
    heights = np.asarray(heights, dtype=np.float64)
    span = max(float(np.ptp(heights)), 1e-6)
    kept: list[tuple[float, int, float]] = []
    for center, votes in clusters:
        frac = _cluster_band_fraction(heights, center, span=span)
        if frac >= min_frac:
            kept.append((center, votes, frac))
    return kept


def _dominant_floor_cluster(
    heights: np.ndarray,
    clusters: list[tuple[float, int, float]],
    *,
    cam_height: float | None = None,
) -> tuple[float, int]:
    """
    Pick the globally dominant floor slab (largest in-band point fraction).

    Among Hough peaks that pass the minimum mass threshold, choose the band
    that contains the most points in the pooled multi-frame sample. When
    ``cam_height`` is set, prefer peaks below the camera if any qualify.
    """
    if not clusters:
        return float(np.percentile(heights, _FLOOR_BOTTOM_PERCENTILE)), 0

    heights = np.asarray(heights, dtype=np.float64)
    span = max(float(np.ptp(heights)), 1e-6)
    cam_margin = 0.02 * span

    pool = clusters
    if cam_height is not None:
        below = [
            item for item in clusters if item[0] < float(cam_height) - cam_margin
        ]
        if below:
            pool = below

    center, votes, _frac = max(pool, key=lambda item: (item[2], item[1]))
    return center, votes


def _ground_align_min_confidence(predictions: dict | FeedforwardPrediction) -> float:
    if isinstance(predictions, FeedforwardPrediction):
        meta = predictions.metadata
    else:
        meta = predictions.get("metadata") or {}
    for key in ("compact_min_confidence", "min_confidence"):
        if key in meta and meta[key] is not None:
            return float(meta[key])
    return _GROUND_ALIGN_DEFAULT_MIN_CONFIDENCE


def _collect_ground_align_points(
    predictions: dict | FeedforwardPrediction,
    *,
    up: np.ndarray = _OPENCV_UP,
    prefilter_floor: bool = True,
) -> tuple[np.ndarray, int]:
    """Pool all frames, subsample once globally, then Hough/fit on that cloud."""
    if isinstance(predictions, FeedforwardPrediction):
        world_points = predictions.world_points
        conf = predictions.conf
    else:
        world_points = predictions.get("world_points_from_depth", predictions.get("world_points"))
        conf = predictions.get("conf")

    wp = np.asarray(world_points, dtype=np.float64)
    if wp.ndim < 3:
        raise ValueError("Not enough finite points for ground alignment.")

    min_conf = _ground_align_min_confidence(predictions)
    cf = np.asarray(conf, dtype=np.float64)
    n_frames = int(wp.shape[0])
    pooled: list[np.ndarray] = []
    total_finite = 0

    for fi in range(n_frames):
        pts = wp[fi].reshape(-1, 3)
        frame_conf = cf[fi].reshape(-1) if cf.size else np.ones(pts.shape[0])
        valid = np.isfinite(pts).all(axis=1)
        if min_conf > 0:
            valid &= frame_conf >= min_conf
        pts = pts[valid]
        total_finite += int(pts.shape[0])
        if pts.shape[0] >= 1:
            pooled.append(pts)

    if not pooled:
        raise ValueError("Not enough finite points for ground alignment.")

    out = np.vstack(pooled)
    n_keep = max(3, int(round(out.shape[0] * _GROUND_ALIGN_SAMPLE_FRAC)))
    if out.shape[0] > n_keep:
        rng = np.random.default_rng(0)
        idx = rng.choice(out.shape[0], n_keep, replace=False)
        out = out[idx]

    if prefilter_floor:
        heights = _heights(out, up)
        h_cut = float(np.percentile(heights, _GROUND_ALIGN_PREFILTER_LOW_PERCENTILE))
        floor_pts = out[heights <= h_cut]
        min_floor = max(3, int(round(out.shape[0] * _GROUND_ALIGN_PREFILTER_MIN_FRAC)))
        if floor_pts.shape[0] >= min_floor:
            out = floor_pts
    return out, total_finite


def fit_floor_plane_low_band(
    points: np.ndarray,
    *,
    up: np.ndarray = _OPENCV_UP,
    cam_height: float | None = None,
) -> tuple[np.ndarray, float, np.ndarray, list[tuple[float, int]]] | None:
    """
    Estimate floor tilt from the globally dominant Hough height cluster.

    Returns (unit_normal, offset, inlier_mask, floor_clusters).
    """
    points = np.asarray(points, dtype=np.float64)
    if points.shape[0] < 3:
        return None

    heights = _heights(points, up)
    scored = _filter_floor_clusters_by_point_fraction(
        heights, _hough_floor_clusters(heights)
    )
    floor_clusters = [(center, votes) for center, votes, _frac in scored]
    floor_h, _ = _dominant_floor_cluster(heights, scored, cam_height=cam_height)
    span = max(float(np.ptp(heights)), 1e-6)
    half_w = max(span * _FLOOR_CLUSTER_HALF_WIDTH_FRAC, span * 0.008)
    band = points[np.abs(heights - floor_h) <= half_w]
    if band.shape[0] < 100:
        band = points[heights <= float(np.percentile(heights, _FLOOR_BOTTOM_PERCENTILE))]
    if band.shape[0] < 100:
        band = points[heights <= float(np.percentile(heights, _FLOOR_BOTTOM_PERCENTILE_WIDE))]

    mask = np.ones(band.shape[0], dtype=bool)
    normal = up.copy()
    for _ in range(_FLOOR_TRIM_PASSES):
        if int(mask.sum()) < 3:
            break
        normal, offset = _refine_plane(band, mask)
        normal = _snap_floor_normal(normal, up=up)
        dist = _plane_distances(band, normal, offset)
        cut = float(np.percentile(dist[mask], _FLOOR_TRIM_KEEP_PERCENTILE))
        mask = dist <= max(cut, 1e-6)

    if int(mask.sum()) < 3:
        return None

    normal = _snap_floor_normal(normal, up=up)
    centroid = band[mask].mean(axis=0)
    offset = -float(np.dot(normal, centroid))
    dist_all = _plane_distances(points, normal, offset)
    inliers = dist_all <= float(np.percentile(dist_all, 45.0))
    normal = _orient_ground_normal(normal, points=points, inlier_mask=inliers, up=up)
    offset = -float(np.dot(normal, points[inliers].mean(axis=0)))
    inliers = _plane_distances(points, normal, offset) <= float(np.percentile(dist_all, 45.0))
    return normal, offset, inliers, floor_clusters


def _floor_height_reference(
    points: np.ndarray,
    up: np.ndarray,
    *,
    inlier_mask: np.ndarray | None = None,
    percentile: float = _FLOOR_HEIGHT_PERCENTILE,
) -> float:
    """Robust floor height along ``up`` after the plane is leveled."""
    heights = _heights(np.asarray(points, dtype=np.float64), up)
    if inlier_mask is not None and np.any(inlier_mask):
        heights = heights[np.asarray(inlier_mask, dtype=bool)]
    elif len(heights) > 0:
        heights = heights[heights <= float(np.percentile(heights, percentile))]
    if len(heights) == 0:
        return float(np.percentile(_heights(np.asarray(points, dtype=np.float64), up), percentile))
    return float(np.median(heights))


def shift_prediction_ground_above_z(
    prediction: FeedforwardPrediction,
    clearance: float = _GROUND_Z_CLEARANCE,
    *,
    inlier_mask: np.ndarray | None = None,
    sample_points: np.ndarray | None = None,
) -> float:
    """
    Translate so the fitted floor sits at ``z = clearance`` (Blender Z-up).

    Call after ``convert_prediction_to_blender_zup``. Returns the Z shift applied (m).
    """
    from .common import is_blender_z_up

    if not is_blender_z_up(prediction):
        return 0.0

    wp = prediction.world_points
    flat = np.asarray(wp, dtype=np.float64).reshape(-1, 3)
    valid = np.isfinite(flat).all(axis=1)
    if not np.any(valid):
        return 0.0

    ref_pts = sample_points if sample_points is not None else flat[valid]
    floor_z = _floor_height_reference(ref_pts, np.array([0.0, 0.0, 1.0]))
    dz = float(clearance) - floor_z
    if abs(dz) < 1e-6:
        return 0.0

    shift = np.array([0.0, 0.0, dz], dtype=np.float64)
    flat = flat.copy()
    flat[valid] += shift
    prediction.world_points = flat.astype(np.float32).reshape(wp.shape)

    w2c_as_camera_pose = bool(prediction.metadata.get("w2c_as_camera_pose"))
    new_ext = np.empty_like(prediction.extrinsic)
    for i, w2c in enumerate(prediction.extrinsic):
        w2c4 = np.vstack([w2c, [0.0, 0.0, 0.0, 1.0]])
        if w2c_as_camera_pose:
            pose = w2c4.copy()
            pose[:3, 3] += shift
            new_ext[i] = pose[:3, :4]
        else:
            c2w = np.linalg.inv(w2c4)
            c2w[:3, 3] += shift
            new_ext[i] = np.linalg.inv(c2w)[:3, :4]
    prediction.extrinsic = new_ext.astype(np.float32)

    prediction.metadata = dict(prediction.metadata)
    prediction.metadata["ground_align_z_shift"] = float(dz)
    return float(dz)


def _apply_world_rotation_opencv(
    prediction: FeedforwardPrediction,
    rotation: np.ndarray,
) -> None:
    """Rotate OpenCV world frame: p' = R @ p; update extrinsics to match."""
    rotation = np.asarray(rotation, dtype=np.float64)
    w2c_as_camera_pose = bool(prediction.metadata.get("w2c_as_camera_pose"))

    wp = prediction.world_points
    flat = wp.reshape(-1, 3)
    prediction.world_points = (rotation @ flat.T).T.astype(np.float32).reshape(wp.shape)

    new_ext = np.empty_like(prediction.extrinsic)
    for i, w2c in enumerate(prediction.extrinsic):
        w2c4 = np.vstack([w2c, [0.0, 0.0, 0.0, 1.0]])
        if w2c_as_camera_pose:
            pose = w2c4.copy()
            pose[:3, :3] = rotation @ pose[:3, :3]
            pose[:3, 3] = rotation @ pose[:3, 3]
            new_ext[i] = pose[:3, :4]
        else:
            c2w = np.linalg.inv(w2c4)
            c2w[:3, :3] = rotation @ c2w[:3, :3]
            c2w[:3, 3] = rotation @ c2w[:3, 3]
            new_ext[i] = np.linalg.inv(c2w)[:3, :4]
    prediction.extrinsic = new_ext.astype(np.float32)


def _warn_spread_frame_sampling(predictions: dict | FeedforwardPrediction) -> None:
    """Spread subsampling mixes distant poses and often breaks floor-plane RANSAC."""
    if isinstance(predictions, FeedforwardPrediction):
        meta = predictions.metadata
    else:
        meta = predictions.get("metadata") or {}
    if str(meta.get("max_frames_mode", "")).lower() != "spread":
        return
    indices = meta.get("selected_indices")
    if not indices or len(indices) < 2:
        return
    span = int(max(indices) - min(indices))
    if span > len(indices) * 3:
        print(
            "[vibephysics] Ground align warning: max_frames_mode=spread samples distant "
            "poses; floor fit may look tilted in one view. Prefer max_frames_mode: first."
        )


def _residual_floor_slopes(rotation: np.ndarray, points: np.ndarray) -> tuple[float, float, float]:
    """Return (tilt_deg, dz/dx, dz/dy) on Blender Z-up floor band for logging."""
    from .common import opencv_to_blender_points

    aligned_cv = (rotation @ points.T).T
    aligned = opencv_to_blender_points(aligned_cv)
    heights = aligned[:, 2]
    ground = aligned[heights <= float(np.percentile(heights, 20))]
    if ground.shape[0] < 3:
        return 0.0, 0.0, 0.0
    _, _, vh = np.linalg.svd(ground - ground.mean(axis=0), full_matrices=False)
    tilt = math.degrees(math.acos(float(np.clip(abs(vh[-1][2]), 0.0, 1.0))))
    coef, _, _, _ = np.linalg.lstsq(
        np.column_stack([ground[:, 0], ground[:, 1], np.ones(ground.shape[0])]),
        ground[:, 2],
        rcond=None,
    )
    return tilt, float(coef[0]), float(coef[1])


def _fit_ground_with_scene_up(
    predictions: dict | FeedforwardPrediction,
    extrinsics: np.ndarray,
    *,
    w2c_as_camera_pose: bool,
    scene_up: np.ndarray,
    cam_pos: np.ndarray,
) -> tuple[np.ndarray | None, np.ndarray | None, list[tuple[float, int]], np.ndarray]:
    """Fit floor plane for a candidate scene-up; returns rotation, points, clusters, scene_up."""
    cam_height = float(cam_pos @ scene_up)
    try:
        points, _ = _collect_ground_align_points(predictions, up=scene_up)
    except ValueError:
        return None, None, [], scene_up

    fit = fit_floor_plane_low_band(points, up=scene_up, cam_height=cam_height)
    if fit is None:
        return None, points, [], scene_up

    normal, _offset, inliers, floor_clusters = fit
    heights = _heights(points, scene_up)
    span = max(float(np.ptp(heights)), 1e-6)
    scored = [
        (center, votes, _cluster_band_fraction(heights, center, span=span))
        for center, votes in floor_clusters
    ]
    floor_h, _ = _dominant_floor_cluster(heights, scored, cam_height=cam_height)
    floor_below_camera = floor_h < float(cam_height) - 0.005 * span

    rotation = _rotation_matrix_align_normal(normal, _OPENCV_UP)
    rotation = _level_ground_rotation(
        rotation, points, passes=_LEVEL_GROUND_PASSES, up=_OPENCV_UP
    )
    rotation = _flip_upside_down_rotation(
        rotation,
        points,
        inliers,
        extrinsics,
        w2c_as_camera_pose=w2c_as_camera_pose,
        up=_OPENCV_UP,
    )
    rotation = _level_ground_rotation(
        rotation, points, passes=_LEVEL_GROUND_PASSES, up=_OPENCV_UP
    )

    if not floor_below_camera:
        # Handheld / low camera: still level to the lowest band we found.
        lowest_h = float(np.percentile(heights, 8.0))
        if floor_h > lowest_h + 0.08 * span:
            return None, points, floor_clusters, scene_up
    return rotation, points, floor_clusters, scene_up


def _estimate_ground_rotation_matrix_opencv(
    predictions: dict | FeedforwardPrediction,
) -> tuple[np.ndarray | None, np.ndarray | None, list[tuple[float, int]]]:
    """Estimate ground-alignment rotation and the subsampled points used for fitting."""
    _warn_spread_frame_sampling(predictions)
    if isinstance(predictions, FeedforwardPrediction):
        extrinsics = predictions.extrinsic
        w2c_as_camera_pose = bool(predictions.metadata.get("w2c_as_camera_pose"))
    else:
        extrinsics = predictions["extrinsic"]
        meta = predictions.get("metadata") or {}
        w2c_as_camera_pose = bool(meta.get("w2c_as_camera_pose"))

    try:
        probe, total_finite = _collect_ground_align_points(
            predictions, prefilter_floor=False
        )
        frame0_points = _collect_frame0_points(predictions)
        scene_up = _estimate_scene_up(
            probe,
            extrinsics,
            w2c_as_camera_pose=w2c_as_camera_pose,
            frame0_points=frame0_points,
        )
        cam_pos, first_up = _first_frame_camera(
            extrinsics, w2c_as_camera_pose=w2c_as_camera_pose
        )
    except ValueError:
        return None, None, []

    rotation, points, floor_clusters, scene_up_used = _fit_ground_with_scene_up(
        predictions,
        extrinsics,
        w2c_as_camera_pose=w2c_as_camera_pose,
        scene_up=scene_up,
        cam_pos=cam_pos,
    )
    up_flipped = False
    if rotation is None:
        up_flipped = True
        rotation, points, floor_clusters, scene_up_used = _fit_ground_with_scene_up(
            predictions,
            extrinsics,
            w2c_as_camera_pose=w2c_as_camera_pose,
            scene_up=-scene_up,
            cam_pos=cam_pos,
        )

    if rotation is None or points is None:
        return None, None, []

    fit = fit_floor_plane_low_band(
        points,
        up=scene_up_used,
        cam_height=float(cam_pos @ scene_up_used),
    )
    if fit is None:
        return None, None, []
    normal, _offset, inliers, floor_clusters = fit
    inlier_count = int(inliers.sum())
    euler = _matrix_to_euler_xyz(rotation)
    residual_tilt, slope_x, slope_y = _residual_floor_slopes(rotation, points)
    heights_log = _heights(points, scene_up_used)
    scored_log = _filter_floor_clusters_by_point_fraction(
        heights_log, [(c, v) for c, v in floor_clusters]
    )
    dominant_h, _ = _dominant_floor_cluster(
        heights_log,
        scored_log,
        cam_height=float(cam_pos @ scene_up_used),
    )
    floor_info = (
        f"{len(floor_clusters)} Hough floor(s), dominant_h={dominant_h:.3f} (global mass)"
        if floor_clusters
        else "Hough fallback percentile"
    )
    flip_note = ", up flipped from frame-0 check" if up_flipped else ""
    print(
        f"[vibephysics] Ground align: {inlier_count}/{len(points)} inliers "
        f"({total_finite} finite pts), {floor_info}, "
        f"scene_up=({scene_up_used[0]:.3f}, {scene_up_used[1]:.3f}, {scene_up_used[2]:.3f}), "
        f"frame0_up=({first_up[0]:.3f}, {first_up[1]:.3f}, {first_up[2]:.3f}){flip_note}, "
        f"normal=({normal[0]:.3f}, {normal[1]:.3f}, {normal[2]:.3f}), "
        f"euler=({math.degrees(euler[0]):.1f}°, {math.degrees(euler[1]):.1f}°, "
        f"{math.degrees(euler[2]):.1f}°), "
        f"residual tilt={residual_tilt:.2f}° (dz/dx={slope_x:.4f}, dz/dy={slope_y:.4f})"
    )
    return rotation, points, floor_clusters


def _rotate_extrinsic_blender_zup(
    extrinsic: np.ndarray,
    rotation: np.ndarray,
    *,
    w2c_as_camera_pose: bool,
) -> np.ndarray:
    """Apply the same world rotation used for Blender Z-up points to camera matrices."""
    rotation = np.asarray(rotation, dtype=np.float64)
    out = np.empty_like(extrinsic, dtype=np.float32)
    for i, w2c in enumerate(extrinsic):
        w2c4 = np.vstack([w2c, [0.0, 0.0, 0.0, 1.0]])
        if w2c_as_camera_pose:
            pose = w2c4.copy()
            pose[:3, :3] = rotation @ pose[:3, :3]
            pose[:3, 3] = rotation @ pose[:3, 3]
            out[i] = pose[:3, :4]
        else:
            c2w = np.linalg.inv(w2c4)
            c2w[:3, :3] = rotation @ c2w[:3, :3]
            c2w[:3, 3] = rotation @ c2w[:3, 3]
            out[i] = np.linalg.inv(c2w)[:3, :4]
    return out


def align_blender_zup_colored_cloud(
    points: np.ndarray,
    extrinsic: np.ndarray,
    *,
    w2c_as_camera_pose: bool = True,
) -> tuple[np.ndarray, np.ndarray, bool]:
    """
    Level a compact Blender Z-up point cloud using global Hough floor clustering on Z.

    Use when ``predictions.npz`` was saved without ``ground_align_applied``.
    """
    points = np.asarray(points, dtype=np.float64)
    if points.shape[0] < 50 or points.ndim != 2 or points.shape[1] != 3:
        return points.astype(np.float32), np.asarray(extrinsic, dtype=np.float32), False, 0.0

    n_fit = max(3, int(round(points.shape[0] * _GROUND_ALIGN_SAMPLE_FRAC)))
    if points.shape[0] > n_fit:
        rng = np.random.default_rng(0)
        fit_idx = rng.choice(points.shape[0], n_fit, replace=False)
        fit_pts = points[fit_idx]
    else:
        fit_pts = points

    up = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    heights = fit_pts[:, 2]
    cam_height = float(np.percentile(heights, 90))
    if extrinsic is not None and len(extrinsic) > 0:
        w2c = np.asarray(extrinsic[0], dtype=np.float64)
        w2c4 = np.vstack([w2c, [0.0, 0.0, 0.0, 1.0]])
        if w2c_as_camera_pose:
            c2w = w2c4
        else:
            c2w = np.linalg.inv(w2c4)
        cam_height = float(c2w[2, 3])

    scored = _filter_floor_clusters_by_point_fraction(heights, _hough_floor_clusters(heights))
    floor_h, _ = _dominant_floor_cluster(heights, scored, cam_height=cam_height)
    span = max(float(np.ptp(heights)), 1e-6)
    half_w = max(span * _FLOOR_CLUSTER_HALF_WIDTH_FRAC, span * 0.008)
    band = fit_pts[np.abs(heights - floor_h) <= half_w]
    if band.shape[0] < 100:
        band = fit_pts[heights <= float(np.percentile(heights, _FLOOR_BOTTOM_PERCENTILE))]

    normal, _ = _refine_plane(band, np.ones(band.shape[0], dtype=bool))
    normal = _orient_ground_normal(normal, up=up)
    if not np.isfinite(normal).all() or float(np.linalg.norm(normal)) < 1e-8:
        return points.astype(np.float32), np.asarray(extrinsic, dtype=np.float32), False, 0.0
    rotation = _rotation_matrix_align_normal(normal, up)
    rotation = _level_ground_rotation(
        rotation, fit_pts, passes=_LEVEL_GROUND_PASSES, up=up, height_percentile=20.0
    )
    points_out = (rotation @ points.T).T.astype(np.float32)
    ext_out = _rotate_extrinsic_blender_zup(
        extrinsic, rotation, w2c_as_camera_pose=w2c_as_camera_pose
    )
    floor_z = _floor_height_reference(points_out, up)
    dz = float(_GROUND_Z_CLEARANCE) - floor_z
    if abs(dz) >= 1e-6:
        shift = np.array([0.0, 0.0, dz], dtype=np.float64)
        points_out = points_out + shift.astype(np.float32)
        ext_out = _translate_extrinsic_blender_zup(
            ext_out, shift, w2c_as_camera_pose=w2c_as_camera_pose
        )
    z_shift = 0.0
    if abs(dz) >= 1e-6:
        z_shift = float(dz)
    return points_out, ext_out, True, z_shift


def _translate_extrinsic_blender_zup(
    extrinsic: np.ndarray,
    translation: np.ndarray,
    *,
    w2c_as_camera_pose: bool,
) -> np.ndarray:
    translation = np.asarray(translation, dtype=np.float64).reshape(3)
    out = np.asarray(extrinsic, dtype=np.float32).copy()
    for i, w2c in enumerate(out):
        w2c4 = np.vstack([w2c, [0.0, 0.0, 0.0, 1.0]])
        if w2c_as_camera_pose:
            pose = w2c4.copy()
            pose[:3, 3] += translation
            out[i] = pose[:3, :4].astype(np.float32)
        else:
            c2w = np.linalg.inv(w2c4)
            c2w[:3, 3] += translation
            out[i] = np.linalg.inv(c2w)[:3, :4].astype(np.float32)
    return out


def realign_compact_predictions_file(path: Path | str) -> bool:
    """Re-level a saved compact ``predictions.npz`` in place (Blender Z-up)."""
    path = Path(path)
    data = dict(np.load(path, allow_pickle=True))
    if "points" not in data:
        print(f"[vibephysics] {path}: not a compact predictions.npz (no points array)")
        return False
    meta = data["metadata"][0] if "metadata" in data and len(data["metadata"]) else {}
    if isinstance(meta, dict) and meta.get("ground_align_applied"):
        print(f"[vibephysics] {path}: ground_align_applied already set")
        return False
    w2c_pose = bool(meta.get("w2c_as_camera_pose", True))
    points_out, ext_out, ok, z_shift = align_blender_zup_colored_cloud(
        data["points"],
        data["extrinsic"],
        w2c_as_camera_pose=w2c_pose,
    )
    if not ok:
        print(f"[vibephysics] {path}: compact realign failed")
        return False
    data["points"] = points_out
    data["extrinsic"] = ext_out
    if "trajectory" in data:
        data["trajectory"] = ext_out[:, :3, 3].astype(np.float32)
    meta = dict(meta)
    meta["ground_align_applied"] = True
    meta["ground_align_status"] = "applied_compact_realign"
    if abs(z_shift) >= 1e-6:
        meta["ground_align_z_shift"] = float(z_shift)
    data["metadata"] = np.array([meta], dtype=object)
    np.savez_compressed(path, **data)
    print(f"[vibephysics] Re-leveled compact predictions: {path}")
    return True


def apply_world_rotation_to_prediction(
    prediction: FeedforwardPrediction,
    rotation: np.ndarray,
    *,
    euler_deg: tuple[float, float, float] | None = None,
) -> None:
    """Apply a world-frame rotation to canonical prediction arrays in place."""
    _apply_world_rotation_opencv(prediction, rotation)
    prediction.metadata = dict(prediction.metadata)
    prediction.metadata["ground_align_applied"] = True
    if euler_deg is not None:
        prediction.metadata["ground_align_euler_deg"] = list(euler_deg)


def _store_floor_cluster_metadata(
    prediction: FeedforwardPrediction,
    clusters: list[tuple[float, int]],
) -> None:
    prediction.metadata["ground_align_floor_count"] = len(clusters)
    if clusters:
        prediction.metadata["ground_align_floor_heights"] = [float(h) for h, _ in clusters]


def align_prediction_ground(prediction: FeedforwardPrediction) -> bool:
    """
    Level mean floor tilt to horizontal in canonical OpenCV world coords (bumpy depth OK).

    Single entry point for all engines. Mutates ``world_points`` and ``extrinsic``
    in place. Returns True when applied.
    """
    if prediction.metadata.get("ground_align_applied"):
        return False

    rotation, align_points, floor_clusters = _estimate_ground_rotation_matrix_opencv(prediction)
    if rotation is None or align_points is None:
        _record_ground_align_metadata(prediction, status="skipped_no_fit")
        print("[vibephysics] Ground align skipped: could not estimate floor tilt from low points.")
        return False

    tilt_before, _, _ = _residual_floor_slopes(np.eye(3), align_points)
    ok, tilt, slope_x, slope_y = _is_acceptable_ground_rotation(rotation, align_points)
    if not ok:
        euler = _matrix_to_euler_xyz(rotation)
        _record_ground_align_metadata(
            prediction,
            status="rejected",
            tilt_before=tilt_before,
            tilt_after=tilt,
            slope_x=slope_x,
            slope_y=slope_y,
            floor_clusters=floor_clusters,
        )
        print(
            "[vibephysics] Ground align rejected: floor still tilted after fit "
            f"(before={tilt_before:.2f}° after={tilt:.2f}°, dz/dx={slope_x:.4f}, dz/dy={slope_y:.4f}; "
            f"euler=({math.degrees(euler[0]):.1f}°, {math.degrees(euler[1]):.1f}°, "
            f"{math.degrees(euler[2]):.1f}°)) — need ≥ {_MIN_TILT_IMPROVEMENT_DEG:g}° improvement."
        )
        return False

    euler_deg = tuple(math.degrees(a) for a in _matrix_to_euler_xyz(rotation))
    apply_world_rotation_to_prediction(prediction, rotation, euler_deg=euler_deg)
    _record_ground_align_metadata(
        prediction,
        status="applied",
        tilt_before=tilt_before,
        tilt_after=tilt,
        slope_x=slope_x,
        slope_y=slope_y,
        euler_deg=euler_deg,
        floor_clusters=floor_clusters,
    )
    print(
        f"[vibephysics] Ground align applied: tilt {tilt_before:.2f}° → {tilt:.2f}° "
        f"(dz/dx={slope_x:.4f}, dz/dy={slope_y:.4f})",
        flush=True,
    )
    return True


def finalize_ground_align_z_shift(prediction: FeedforwardPrediction) -> float:
    """
    After Blender Z-up conversion, raise the leveled floor to ``z > 0``.

    Call when ``ground_align_applied`` is set. Returns the Z shift (m), or 0.
    """
    if not prediction.metadata.get("ground_align_applied"):
        return 0.0
    dz = shift_prediction_ground_above_z(prediction)
    if abs(dz) >= 1e-6:
        print(
            f"[vibephysics] Ground align: shifted floor to z={_GROUND_Z_CLEARANCE:g} m "
            f"(Δz={dz:.3f} m)",
            flush=True,
        )
    return dz
