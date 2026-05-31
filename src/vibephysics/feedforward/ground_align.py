"""Estimate ground-plane alignment for feedforward point clouds (numpy only)."""

from __future__ import annotations

import math

import numpy as np

from .schema import FeedforwardPrediction

_GROUND_ALIGN_MAX_POINTS = 80_000
# OpenCV world is Y-down; physical "up" is -Y (same frame ground align rotates in).
_OPENCV_UP = np.array([0.0, -1.0, 0.0], dtype=np.float64)
# Depth reconstructions are bumpy — Hough clusters along scene_up, fit the bottom floor.
_FLOOR_BOTTOM_PERCENTILE = 22.0
_FLOOR_TRIM_PASSES = 3
_FLOOR_TRIM_KEEP_PERCENTILE = 88.0
_FLOOR_NORMAL_HORIZ_KEEP = 0.25
_FLOOR_HOUGH_BINS = 96
_FLOOR_HOUGH_SMOOTH_BINS = 7
_FLOOR_HOUGH_MIN_PEAK_VOTE_FRAC = 0.012
_FLOOR_HOUGH_MIN_PEAK_SEP_FRAC = 0.05
_FLOOR_CLUSTER_HALF_WIDTH_FRAC = 0.03


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


def _orient_scene_up_from_first_camera(
    points: np.ndarray,
    up: np.ndarray,
    cam_pos: np.ndarray,
    cam_up: np.ndarray,
) -> np.ndarray:
    """Match frame-0 camera up; keep scene bulk below the first camera."""
    up = _normalize(up)
    if float(up @ cam_up) < 0.0:
        up = -up
    relative = (points - cam_pos) @ up
    if float(np.percentile(relative, 40.0)) > 0.0:
        up = -up
    return _normalize(up)


def _estimate_scene_up(
    points: np.ndarray,
    extrinsics: np.ndarray,
    *,
    w2c_as_camera_pose: bool,
) -> np.ndarray:
    """Gravity-up from frame-0 camera (refined by consensus / points when needed)."""
    cam_pos, first_up = _first_frame_camera(extrinsics, w2c_as_camera_pose=w2c_as_camera_pose)
    if len(extrinsics) >= 3:
        cam_up, agree = _camera_up_consensus(extrinsics, w2c_as_camera_pose=w2c_as_camera_pose)
        if agree >= 0.6:
            up = cam_up
        else:
            up = first_up
    else:
        up = first_up
    if float(up @ first_up) < 0.0:
        up = -up
    return _orient_scene_up_from_first_camera(points, up, cam_pos, first_up)


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
    cam_h = float(c2w[:3, 3] @ up)
    aligned = (rot @ points.T).T
    floor_h = float(np.median(_heights(aligned[inlier_mask], up))) if np.any(inlier_mask) else cam_h
    if float(cam_up @ up) < 0.0 or floor_h >= cam_h:
        return flip @ rot
    return rot


_GROUND_ALIGN_MAX_RESIDUAL_TILT_DEG = 15.0
_GROUND_ALIGN_MAX_FLOOR_SLOPE = 0.10
_MIN_TILT_IMPROVEMENT_DEG = 1.0


def _is_acceptable_ground_rotation(rotation: np.ndarray, points: np.ndarray) -> tuple[bool, float, float, float]:
    """Accept when alignment clearly improves tilt (floor need not be geometrically flat)."""
    tilt, slope_x, slope_y = _residual_floor_slopes(rotation, points)
    tilt_before, _, _ = _residual_floor_slopes(np.eye(3), points)
    improved = (tilt_before - tilt) >= _MIN_TILT_IMPROVEMENT_DEG
    ok = (
        improved
        and tilt <= _GROUND_ALIGN_MAX_RESIDUAL_TILT_DEG
        and abs(slope_x) <= _GROUND_ALIGN_MAX_FLOOR_SLOPE
        and abs(slope_y) <= _GROUND_ALIGN_MAX_FLOOR_SLOPE
    )
    return ok, tilt, slope_x, slope_y


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


def _bottom_floor_cluster(
    heights: np.ndarray,
    clusters: list[tuple[float, int]],
    *,
    cam_height: float | None = None,
) -> tuple[float, int]:
    """Pick the ground floor: highest Hough peak still below frame-0 camera height."""
    if not clusters:
        return float(np.percentile(heights, _FLOOR_BOTTOM_PERCENTILE)), 0

    if cam_height is not None:
        below = [(center, votes) for center, votes in clusters if center < cam_height]
        if below:
            return max(below, key=lambda item: item[0])
        return min(clusters, key=lambda item: abs(item[0] - cam_height))

    return min(clusters, key=lambda item: item[0])


def _collect_ground_align_points(
    predictions: dict | FeedforwardPrediction,
    *,
    up: np.ndarray = _OPENCV_UP,
    prefilter_floor: bool = True,
) -> tuple[np.ndarray, int]:
    """Collect finite world points for floor tilt estimation (subsampled)."""
    if isinstance(predictions, FeedforwardPrediction):
        world_points = predictions.world_points
    else:
        world_points = predictions.get("world_points_from_depth", predictions.get("world_points"))

    flat = np.asarray(world_points, dtype=np.float64).reshape(-1, 3)
    valid = np.isfinite(flat).all(axis=1)
    out = flat[valid]
    total = int(out.shape[0])
    if total < 3:
        raise ValueError("Not enough finite points for ground alignment.")

    if out.shape[0] > _GROUND_ALIGN_MAX_POINTS:
        rng = np.random.default_rng(0)
        idx = rng.choice(out.shape[0], _GROUND_ALIGN_MAX_POINTS, replace=False)
        out = out[idx]

    if prefilter_floor:
        heights = _heights(out, up)
        h_cut = float(np.percentile(heights, 30))
        floor_pts = out[heights <= h_cut]
        if floor_pts.shape[0] >= 3000:
            out = floor_pts
    return out, total


def fit_floor_plane_low_band(
    points: np.ndarray,
    *,
    up: np.ndarray = _OPENCV_UP,
    cam_height: float | None = None,
) -> tuple[np.ndarray, float, np.ndarray, list[tuple[float, int]]] | None:
    """
    Estimate floor tilt from the bottom Hough floor cluster (multi-floor safe).

    Returns (unit_normal, offset, inlier_mask, floor_clusters).
    """
    points = np.asarray(points, dtype=np.float64)
    if points.shape[0] < 3:
        return None

    heights = _heights(points, up)
    clusters = _hough_floor_clusters(heights)
    bottom_h, _ = _bottom_floor_cluster(heights, clusters, cam_height=cam_height)
    span = max(float(np.ptp(heights)), 1e-6)
    half_w = max(span * _FLOOR_CLUSTER_HALF_WIDTH_FRAC, span * 0.008)
    band = points[np.abs(heights - bottom_h) <= half_w]
    if band.shape[0] < 100:
        band = points[heights <= float(np.percentile(heights, _FLOOR_BOTTOM_PERCENTILE))]
    if band.shape[0] < 100:
        band = points[heights <= float(np.percentile(heights, 35.0))]

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
    return normal, offset, inliers, clusters


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
        scene_up = _estimate_scene_up(
            probe, extrinsics, w2c_as_camera_pose=w2c_as_camera_pose
        )
        cam_pos, first_up = _first_frame_camera(
            extrinsics, w2c_as_camera_pose=w2c_as_camera_pose
        )
        cam_height = float(cam_pos @ scene_up)
        points, _ = _collect_ground_align_points(predictions, up=scene_up)
    except ValueError:
        return None, None, []

    fit = fit_floor_plane_low_band(points, up=scene_up, cam_height=cam_height)
    if fit is None:
        return None, None, []

    normal, _offset, inliers, floor_clusters = fit
    rotation = _rotation_matrix_align_normal(normal, _OPENCV_UP)
    rotation = _level_ground_rotation(rotation, points, up=_OPENCV_UP)
    rotation = _flip_upside_down_rotation(
        rotation,
        points,
        inliers,
        extrinsics,
        w2c_as_camera_pose=w2c_as_camera_pose,
        up=_OPENCV_UP,
    )
    rotation = _level_ground_rotation(rotation, points, up=_OPENCV_UP)

    inlier_count = int(inliers.sum())
    euler = _matrix_to_euler_xyz(rotation)
    residual_tilt, slope_x, slope_y = _residual_floor_slopes(rotation, points)
    floor_info = (
        f"{len(floor_clusters)} Hough floor(s), bottom_h={floor_clusters[0][0]:.3f}"
        if floor_clusters
        else "Hough fallback percentile"
    )
    print(
        f"[vibephysics] Ground align: {inlier_count}/{len(points)} inliers "
        f"({total_finite} finite pts), {floor_info}, "
        f"scene_up=({scene_up[0]:.3f}, {scene_up[1]:.3f}, {scene_up[2]:.3f}), "
        f"frame0_up=({first_up[0]:.3f}, {first_up[1]:.3f}, {first_up[2]:.3f}), "
        f"normal=({normal[0]:.3f}, {normal[1]:.3f}, {normal[2]:.3f}), "
        f"euler=({math.degrees(euler[0]):.1f}°, {math.degrees(euler[1]):.1f}°, "
        f"{math.degrees(euler[2]):.1f}°), "
        f"residual tilt={residual_tilt:.2f}° (dz/dx={slope_x:.4f}, dz/dy={slope_y:.4f})"
    )
    return rotation, points, floor_clusters


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
        print("[vibephysics] Ground align skipped: could not estimate floor tilt from low points.")
        return False

    ok, tilt, slope_x, slope_y = _is_acceptable_ground_rotation(rotation, align_points)
    if not ok:
        euler = _matrix_to_euler_xyz(rotation)
        print(
            "[vibephysics] Ground align rejected: floor still tilted after fit "
            f"(residual={tilt:.2f}°, dz/dx={slope_x:.4f}, dz/dy={slope_y:.4f}; "
            f"euler=({math.degrees(euler[0]):.1f}°, {math.degrees(euler[1]):.1f}°, "
            f"{math.degrees(euler[2]):.1f}°)) — no clear improvement from low-band fit."
        )
        return False

    euler_deg = tuple(math.degrees(a) for a in _matrix_to_euler_xyz(rotation))
    apply_world_rotation_to_prediction(prediction, rotation, euler_deg=euler_deg)
    _store_floor_cluster_metadata(prediction, floor_clusters)
    return True
