"""Estimate ground-plane alignment for feedforward point clouds (numpy only)."""

from __future__ import annotations

import math

import numpy as np

from .schema import FeedforwardPrediction

_GROUND_ALIGN_MAX_POINTS = 80_000


def _fit_plane_from_triplet(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray) -> tuple[np.ndarray, float] | None:
    normal = np.cross(p1 - p0, p2 - p0)
    norm = float(np.linalg.norm(normal))
    if norm < 1e-8:
        return None
    normal = normal / norm
    offset = -float(np.dot(normal, p0))
    return normal, offset


def _plane_distances(points: np.ndarray, normal: np.ndarray, offset: float) -> np.ndarray:
    return np.abs(points @ normal + offset)


def _refine_plane(points: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, float]:
    inliers = points[mask]
    centroid = inliers.mean(axis=0)
    centered = inliers - centroid
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    normal = vh[-1]
    norm = float(np.linalg.norm(normal))
    if norm < 1e-8:
        normal = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    else:
        normal = normal / norm
    offset = -float(np.dot(normal, centroid))
    return normal, offset


def _orient_ground_normal(
    normal: np.ndarray,
    *,
    points: np.ndarray | None = None,
    inlier_mask: np.ndarray | None = None,
) -> np.ndarray:
    """Make the plane normal point upward (+Z) with scene content above the ground."""
    normal = np.asarray(normal, dtype=np.float64)
    norm = float(np.linalg.norm(normal))
    if norm < 1e-8:
        return np.array([0.0, 0.0, 1.0], dtype=np.float64)
    normal = normal / norm

    candidates = (normal, -normal)
    if points is not None and inlier_mask is not None and np.any(inlier_mask):
        inliers = points[inlier_mask]
        outliers = points[~inlier_mask]
        plane_point = inliers.mean(axis=0)
        best = normal if normal[2] >= 0.0 else -normal
        best_score = float("-inf")
        for candidate in candidates:
            if candidate[2] <= 0.0:
                continue
            if outliers.shape[0] == 0:
                score = candidate[2]
            else:
                signed = (outliers - plane_point) @ candidate
                score = float(np.mean(signed > 0.0)) + 0.01 * candidate[2]
            if score > best_score:
                best_score = score
                best = candidate
        return best

    if normal[2] < 0.0:
        normal = -normal
    return normal


def _flip_upside_down_rotation(
    rotation_blender: np.ndarray,
    points: np.ndarray,
    inlier_mask: np.ndarray,
) -> np.ndarray:
    """Flip 180° about X when the ground plane sits above the scene bulk."""
    aligned = (rotation_blender @ points.T).T
    ground_z = float(np.median(aligned[inlier_mask, 2]))
    split_z = float(np.percentile(aligned[:, 2], 40))
    if ground_z > split_z:
        flip = np.diag([1.0, -1.0, -1.0])
        return flip @ rotation_blender
    return rotation_blender


def _rotation_matrix_normal_to_z(normal: np.ndarray) -> np.ndarray:
    """Return 3x3 rotation mapping unit normal onto +Z."""
    normal = normal / max(float(np.linalg.norm(normal)), 1e-8)
    target = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    dot = float(np.clip(np.dot(normal, target), -1.0, 1.0))

    if dot > 1.0 - 1e-8:
        return np.eye(3, dtype=np.float64)
    if dot < -1.0 + 1e-8:
        return np.diag([1.0, -1.0, -1.0])

    axis = np.cross(normal, target)
    axis_norm = float(np.linalg.norm(axis))
    if axis_norm < 1e-8:
        return np.eye(3, dtype=np.float64)
    axis = axis / axis_norm
    angle = math.acos(dot)
    kx, ky, kz = axis
    k = np.array([[0.0, -kz, ky], [kz, 0.0, -kx], [-ky, kx, 0.0]], dtype=np.float64)
    return np.eye(3) + math.sin(angle) * k + (1.0 - math.cos(angle)) * (k @ k)


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


def _collect_ground_align_points(predictions: dict | FeedforwardPrediction) -> tuple[np.ndarray, int]:
    """Collect finite world points for RANSAC (subsampled, no color pass)."""
    if isinstance(predictions, FeedforwardPrediction):
        world_points = predictions.world_points
    else:
        world_points = predictions.get("world_points_from_depth", predictions.get("world_points"))

    flat = np.asarray(world_points, dtype=np.float64).reshape(-1, 3)
    valid = np.isfinite(flat).all(axis=1)
    pts = flat[valid]
    total = int(pts.shape[0])
    if total < 3:
        raise ValueError("Not enough finite points for ground alignment.")

    out = np.empty_like(pts)
    out[:, 0] = pts[:, 0]
    out[:, 1] = pts[:, 2]
    out[:, 2] = -pts[:, 1]

    if out.shape[0] > _GROUND_ALIGN_MAX_POINTS:
        rng = np.random.default_rng(0)
        idx = rng.choice(out.shape[0], _GROUND_ALIGN_MAX_POINTS, replace=False)
        out = out[idx]
    return out, total


def _msac_score(distances: np.ndarray, threshold: float) -> float:
    """Truncated quadratic (MSAC) score; smoother than hard inlier counting."""
    ratio = distances / max(threshold, 1e-12)
    return float(np.sum(np.maximum(0.0, 1.0 - ratio * ratio)))


def ransac_dominant_ground_plane(
    points: np.ndarray,
    *,
    distance_threshold: float | None = None,
    min_horizontal: float = 0.7,
    max_iterations: int = 600,
    max_sample_points: int = 40_000,
    min_inliers: int = 500,
    rng: np.random.Generator | None = None,
) -> tuple[np.ndarray, float, np.ndarray] | None:
    """
    Find the largest near-horizontal plane in a point cloud.

    Returns (unit_normal, offset, inlier_mask) where normal·p + offset ≈ 0.
    Hypothesis scoring uses a subsample; refinement runs on the same subsample.
    """
    points = np.asarray(points, dtype=np.float64)
    if points.shape[0] < 3:
        return None

    rng = rng or np.random.default_rng(0)
    n_sample = min(points.shape[0], max_sample_points)
    if points.shape[0] > n_sample:
        sample_idx = rng.choice(points.shape[0], n_sample, replace=False)
        sample = points[sample_idx]
    else:
        sample = points

    if distance_threshold is None:
        extent = np.ptp(sample, axis=0)
        distance_threshold = max(float(np.linalg.norm(extent)) * 0.01, 1e-3)

    min_count = min(min_inliers, max(100, sample.shape[0] // 100))
    min_tri_area = max(distance_threshold * distance_threshold, float(np.ptp(sample, axis=0).max()) * 1e-5)

    best_score = -1.0
    best_mean_z = float("inf")
    best_normal: np.ndarray | None = None
    best_offset = 0.0
    stale_iters = 0

    for _ in range(max_iterations):
        idx = rng.choice(sample.shape[0], 3, replace=False)
        p0, p1, p2 = sample[idx[0]], sample[idx[1]], sample[idx[2]]
        if 0.5 * float(np.linalg.norm(np.cross(p1 - p0, p2 - p0))) < min_tri_area:
            continue

        candidate = _fit_plane_from_triplet(p0, p1, p2)
        if candidate is None:
            continue

        normal, offset = candidate
        if abs(float(normal[2])) < min_horizontal:
            continue

        distances = _plane_distances(sample, normal, offset)
        count = int(np.count_nonzero(distances < distance_threshold))
        if count < min_count:
            continue

        score = _msac_score(distances, distance_threshold)
        mean_z = float(sample[distances < distance_threshold, 2].mean()) if count else float("inf")
        if score > best_score + 1e-6 or (
            abs(score - best_score) <= 1e-6 and mean_z < best_mean_z
        ):
            best_score = score
            best_mean_z = mean_z
            best_normal = normal.copy()
            best_offset = float(offset)
            stale_iters = 0
        else:
            stale_iters += 1
            if stale_iters >= 120:
                break

    if best_normal is None:
        return None

    normal = best_normal
    offset = best_offset
    inliers = _plane_distances(sample, normal, offset) < distance_threshold
    normal, offset = _refine_plane(sample, inliers)

    inliers = _plane_distances(points, normal, offset) < distance_threshold
    normal = _orient_ground_normal(normal, points=points, inlier_mask=inliers)
    inlier_pts = points[inliers]
    offset = -float(np.dot(normal, inlier_pts.mean(axis=0)))
    inliers = _plane_distances(points, normal, offset) < distance_threshold
    for _ in range(2):
        normal, offset = _refine_plane(points, inliers)
        inliers = _plane_distances(points, normal, offset) < distance_threshold
        normal = _orient_ground_normal(normal, points=points, inlier_mask=inliers)
        inlier_pts = points[inliers]
        offset = -float(np.dot(normal, inlier_pts.mean(axis=0)))
        inliers = _plane_distances(points, normal, offset) < distance_threshold

    normal = _orient_ground_normal(normal, points=points, inlier_mask=inliers)
    inlier_pts = points[inliers]
    offset = -float(np.dot(normal, inlier_pts.mean(axis=0)))
    return normal, offset, inliers


def _opencv_world_to_blender_matrix_3x3() -> np.ndarray:
    """Linear part of OpenCV world -> Blender (x, z, -y)."""
    return np.array(
        [[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, -1.0, 0.0]],
        dtype=np.float64,
    )


def _blender_rotation_to_opencv(rotation_blender: np.ndarray) -> np.ndarray:
    """Convert a 3x3 rotation estimated in Blender coords to OpenCV world coords."""
    m = _opencv_world_to_blender_matrix_3x3()
    rot = np.asarray(rotation_blender, dtype=np.float64)
    return m.T @ rot @ m


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


def _estimate_ground_rotation_matrix_opencv(
    predictions: dict | FeedforwardPrediction,
) -> np.ndarray | None:
    """Estimate 3x3 ground-alignment rotation in OpenCV world coordinates."""
    try:
        points, total_finite = _collect_ground_align_points(predictions)
    except ValueError:
        return None

    fit = ransac_dominant_ground_plane(points)
    if fit is None:
        return None

    normal, _offset, inliers = fit
    rotation_blender = _rotation_matrix_normal_to_z(normal)
    rotation_blender = _flip_upside_down_rotation(rotation_blender, points, inliers)
    rotation_opencv = _blender_rotation_to_opencv(rotation_blender)
    inlier_count = int(inliers.sum())
    euler = _matrix_to_euler_xyz(rotation_blender)
    aligned = (rotation_blender @ points[inliers].T).T
    _, _, aligned_vh = np.linalg.svd(aligned - aligned.mean(axis=0), full_matrices=False)
    residual_tilt = math.degrees(math.acos(float(np.clip(abs(aligned_vh[-1][2]), 0.0, 1.0))))
    print(
        f"[vibephysics] Ground align: {inlier_count}/{len(points)} inliers "
        f"({total_finite} finite pts), "
        f"normal=({normal[0]:.3f}, {normal[1]:.3f}, {normal[2]:.3f}), "
        f"euler=({math.degrees(euler[0]):.1f}°, {math.degrees(euler[1]):.1f}°, {math.degrees(euler[2]):.1f}°), "
        f"residual tilt={residual_tilt:.2f}°"
    )
    return rotation_opencv


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


def align_prediction_ground(prediction: FeedforwardPrediction) -> bool:
    """
    Align the dominant ground plane to horizontal in canonical OpenCV world coords.

    Single entry point for all engines. Mutates ``world_points`` and ``extrinsic``
    in place. Returns True when applied.
    """
    if prediction.metadata.get("ground_align_applied"):
        return False

    rotation = _estimate_ground_rotation_matrix_opencv(prediction)
    if rotation is None:
        print("[vibephysics] Ground align skipped: could not estimate a dominant ground plane.")
        return False

    m = _opencv_world_to_blender_matrix_3x3()
    rotation_blender = m @ rotation @ m.T
    euler = _matrix_to_euler_xyz(rotation_blender)
    euler_deg = tuple(math.degrees(a) for a in euler)
    apply_world_rotation_to_prediction(prediction, rotation, euler_deg=euler_deg)
    return True
