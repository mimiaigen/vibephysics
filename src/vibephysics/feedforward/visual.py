"""
Blender visualization for feedforward dense reconstructions.

Adapted from https://github.com/xy-gao/DA3-blender (utils.py).
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix

from .common import is_lingbot_map_engine, is_vggt_omega_engine
from .common import collect_colored_point_cloud, resolve_confidence_threshold
from .schema import FeedforwardPrediction, load_prediction

ENGINE_COLLECTION_NAMES = {
    "lingbot_map": "LingBot_Map_Result",
    "vggt_omega": "VGGT_Omega_Result",
    "lingbot": "LingBot_Map_Result",
    "vggt": "VGGT_Omega_Result",
}


class _AnimationTiming:
    """Map reconstruction frames onto a Blender timeline that matches source video duration."""

    def __init__(self, num_frames: int, animation_fps: float, video_fps: float):
        self.num_frames = max(int(num_frames), 1)
        self.animation_fps = max(float(animation_fps), 1.0)
        self.video_fps = max(float(video_fps), 1e-6)
        self.frames_per_recon = self.animation_fps / self.video_fps
        self.timeline_start = 1
        self.preview_frame = 0
        self.timeline_end = (
            self.timeline_start
            if self.num_frames <= 1
            else int(round(self.timeline_start + (self.num_frames - 1) * self.frames_per_recon))
        )
        self.build_duration = max(self.timeline_end - self.timeline_start, 1)
        self.recon_time_scale = self.video_fps / self.animation_fps
        self.duration_seconds = (self.num_frames - 1) / self.video_fps if self.num_frames > 1 else 0.0

    def blender_frame(self, recon_index: int) -> int:
        return self.timeline_start + int(round(recon_index * self.frames_per_recon))


def _ensure_collection(name: str, parent=None) -> bpy.types.Collection:
    if name in bpy.data.collections:
        col = bpy.data.collections[name]
    else:
        col = bpy.data.collections.new(name)
        if parent is not None:
            parent.children.link(col)
        else:
            bpy.context.scene.collection.children.link(col)
    return col


def get_or_create_point_material(name: str = "FeedforwardPointMaterial") -> bpy.types.Material:
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    attr_node = nodes.new("ShaderNodeAttribute")
    attr_node.attribute_name = "point_color"
    conf_attr_node = nodes.new("ShaderNodeAttribute")
    conf_attr_node.attribute_name = "conf"

    map_range = nodes.new("ShaderNodeMapRange")
    map_range.clamp = True
    map_range.inputs["From Min"].default_value = 0.0
    map_range.inputs["From Max"].default_value = 10.0
    map_range.inputs["To Min"].default_value = 0.0
    map_range.inputs["To Max"].default_value = 1.0

    color_ramp = nodes.new("ShaderNodeValToRGB")
    ramp = color_ramp.color_ramp
    ramp.elements[0].color = (1, 0, 0, 1)
    ramp.elements[1].position = 0.2
    ramp.elements[1].color = (1, 0, 0, 1)
    green_start = ramp.elements.new(0.5)
    green_start.color = (0, 1, 0, 1)
    green_end = ramp.elements.new(0.6)
    green_end.color = (0, 1, 0, 1)
    blue_elem = ramp.elements.new(1.0)
    blue_elem.color = (0, 0, 1, 1)

    mix_node = nodes.new("ShaderNodeMix")
    mix_node.data_type = "RGBA"
    mix_node.inputs["Factor"].default_value = 0.0
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    output_node_material = nodes.new("ShaderNodeOutputMaterial")

    links.new(conf_attr_node.outputs["Fac"], map_range.inputs["Value"])
    links.new(map_range.outputs["Result"], color_ramp.inputs["Fac"])
    links.new(attr_node.outputs["Color"], mix_node.inputs["A"])
    links.new(color_ramp.outputs["Color"], mix_node.inputs["B"])
    links.new(mix_node.outputs["Result"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], output_node_material.inputs["Surface"])
    return mat


def add_point_cloud_geo_nodes(
    obj,
    mat,
    scale: float = 1.0,
    *,
    min_confidence: float = 0.5,
    animate_frames: bool = False,
    recon_time_scale: float = 1.0,
) -> None:
    geo_mod = obj.modifiers.new(name="GeometryNodes", type="NODES")
    node_group = bpy.data.node_groups.new(name=f"FeedforwardPointCloud_{obj.name}", type="GeometryNodeTree")

    node_group.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    node_group.interface.new_socket(name="Threshold", in_out="INPUT", socket_type="NodeSocketFloat")
    node_group.interface.items_tree[-1].default_value = float(min_confidence)
    node_group.interface.new_socket(name="Scale", in_out="INPUT", socket_type="NodeSocketFloat")
    node_group.interface.items_tree[-1].default_value = scale
    node_group.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    geo_mod.node_group = node_group
    try:
        for item in node_group.interface.items_tree:
            if item.name == "Scale":
                geo_mod[item.identifier] = float(scale)
            elif item.name == "Threshold":
                geo_mod[item.identifier] = float(min_confidence)
    except Exception:
        pass

    input_node = node_group.nodes.new("NodeGroupInput")
    output_node = node_group.nodes.new("NodeGroupOutput")
    mesh_to_points = node_group.nodes.new("GeometryNodeMeshToPoints")
    math_node = node_group.nodes.new("ShaderNodeMath")
    math_node.operation = "MULTIPLY"
    math_node.inputs[1].default_value = 0.002
    named_attr = node_group.nodes.new("GeometryNodeInputNamedAttribute")
    named_attr.inputs["Name"].default_value = "conf"
    named_attr.data_type = "FLOAT"
    compare = node_group.nodes.new("FunctionNodeCompare")
    compare.data_type = "FLOAT"
    compare.operation = "LESS_THAN"
    delete_geo = node_group.nodes.new("GeometryNodeDeleteGeometry")
    delete_geo.domain = "POINT"
    set_material_node = node_group.nodes.new("GeometryNodeSetMaterial")
    set_material_node.inputs["Material"].default_value = mat

    node_group.links.new(input_node.outputs["Geometry"], mesh_to_points.inputs["Mesh"])
    node_group.links.new(input_node.outputs["Scale"], math_node.inputs[0])
    node_group.links.new(math_node.outputs["Value"], mesh_to_points.inputs["Radius"])
    node_group.links.new(mesh_to_points.outputs["Points"], delete_geo.inputs["Geometry"])
    node_group.links.new(named_attr.outputs["Attribute"], compare.inputs["A"])
    node_group.links.new(input_node.outputs["Threshold"], compare.inputs["B"])
    node_group.links.new(compare.outputs["Result"], delete_geo.inputs["Selection"])

    last_geo = delete_geo.outputs["Geometry"]
    if animate_frames:
        frame_attr = node_group.nodes.new("GeometryNodeInputNamedAttribute")
        frame_attr.inputs["Name"].default_value = "frame_id"
        frame_attr.data_type = "INT"
        scene_time = node_group.nodes.new("GeometryNodeInputSceneTime")
        frame_floor = node_group.nodes.new("ShaderNodeMath")
        frame_floor.operation = "FLOOR"
        frame_offset = node_group.nodes.new("ShaderNodeMath")
        frame_offset.operation = "SUBTRACT"
        frame_offset.inputs[1].default_value = 1.0
        recon_scale = node_group.nodes.new("ShaderNodeMath")
        recon_scale.operation = "MULTIPLY"
        recon_scale.inputs[1].default_value = float(recon_time_scale)
        recon_max = node_group.nodes.new("ShaderNodeMath")
        recon_max.operation = "FLOOR"
        frame_compare = node_group.nodes.new("FunctionNodeCompare")
        frame_compare.data_type = "INT"
        frame_compare.operation = "GREATER_THAN"
        delete_frames = node_group.nodes.new("GeometryNodeDeleteGeometry")
        delete_frames.domain = "POINT"
        node_group.links.new(scene_time.outputs["Frame"], frame_floor.inputs[0])
        node_group.links.new(frame_floor.outputs["Value"], frame_offset.inputs[0])
        node_group.links.new(frame_offset.outputs["Value"], recon_scale.inputs[0])
        node_group.links.new(recon_scale.outputs["Value"], recon_max.inputs[0])
        node_group.links.new(frame_attr.outputs["Attribute"], frame_compare.inputs["A"])
        node_group.links.new(recon_max.outputs["Value"], frame_compare.inputs["B"])
        in_animation = node_group.nodes.new("FunctionNodeCompare")
        in_animation.data_type = "FLOAT"
        in_animation.operation = "GREATER_EQUAL"
        in_animation.inputs[1].default_value = 1.0
        frame_delete_mask = node_group.nodes.new("FunctionNodeBooleanMath")
        frame_delete_mask.operation = "AND"
        node_group.links.new(scene_time.outputs["Frame"], in_animation.inputs[0])
        node_group.links.new(in_animation.outputs["Result"], frame_delete_mask.inputs[0])
        node_group.links.new(frame_compare.outputs["Result"], frame_delete_mask.inputs[1])
        node_group.links.new(last_geo, delete_frames.inputs["Geometry"])
        node_group.links.new(frame_delete_mask.outputs["Boolean"], delete_frames.inputs["Selection"])
        last_geo = delete_frames.outputs["Geometry"]

    node_group.links.new(last_geo, set_material_node.inputs["Geometry"])
    node_group.links.new(set_material_node.outputs["Geometry"], output_node.inputs["Geometry"])


def create_point_cloud_object(
    name: str,
    points: np.ndarray,
    colors: np.ndarray,
    confs: np.ndarray,
    collection=None,
    scale: float = 1.0,
    min_confidence: float = 0.5,
    frame_ids: np.ndarray | None = None,
    recon_time_scale: float = 1.0,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name=name)
    mesh.from_pydata(points.tolist(), [], [])
    color_attr = mesh.attributes.new(name="point_color", type="FLOAT_COLOR", domain="POINT")
    color_attr.data.foreach_set("color", colors.flatten().tolist())
    conf_attr = mesh.attributes.new(name="conf", type="FLOAT", domain="POINT")
    conf_attr.data.foreach_set("value", confs.tolist())
    if frame_ids is not None:
        frame_attr = mesh.attributes.new(name="frame_id", type="INT", domain="POINT")
        frame_attr.data.foreach_set("value", frame_ids.tolist())

    obj = bpy.data.objects.new(name, mesh)
    if collection is not None:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    mat = get_or_create_point_material(f"FeedforwardPointMaterial_{name}")
    obj.data.materials.append(mat)
    add_point_cloud_geo_nodes(
        obj,
        mat,
        scale=scale,
        min_confidence=min_confidence,
        animate_frames=frame_ids is not None,
        recon_time_scale=recon_time_scale,
    )
    return obj


def _opencv_to_blender_points(points: np.ndarray) -> np.ndarray:
    from .common import opencv_to_blender_points

    return opencv_to_blender_points(points)


def _w2c_to_blender_matrix_world(
    w2c: np.ndarray,
    *,
    w2c_as_camera_pose: bool = False,
    predictions: dict | None = None,
) -> Matrix:
    """Build Blender ``matrix_world`` from stored extrinsic (OpenCV or Z-up NPZ)."""
    from .common import (
        is_blender_z_up,
        opencv_camera_to_blender_matrix,
        opencv_world_to_blender_matrix,
    )

    if predictions is not None and is_blender_z_up(predictions):
        return Matrix(np.vstack([w2c, [0.0, 0.0, 0.0, 1.0]]).tolist())

    w2c4 = np.vstack([w2c, [0.0, 0.0, 0.0, 1.0]])
    pose = w2c4 if w2c_as_camera_pose else np.linalg.inv(w2c4)
    m = opencv_world_to_blender_matrix() @ pose @ opencv_camera_to_blender_matrix()
    return Matrix(m.tolist())


def _camera_center_blender(
    w2c: np.ndarray,
    *,
    w2c_as_camera_pose: bool = False,
    predictions: dict | None = None,
) -> np.ndarray:
    m = _w2c_to_blender_matrix_world(
        w2c,
        w2c_as_camera_pose=w2c_as_camera_pose,
        predictions=predictions,
    )
    return np.array(m.translation, dtype=np.float64)


def _scene_scale_from_extrinsics(
    extrinsics: np.ndarray,
    *,
    w2c_as_camera_pose: bool = False,
    predictions: dict | None = None,
) -> float:
    """Scene extent from camera path in Blender space (matches point cloud coords)."""
    if len(extrinsics) <= 1:
        return 1.0
    centers = np.array(
        [
            _camera_center_blender(
                w2c,
                w2c_as_camera_pose=w2c_as_camera_pose,
                predictions=predictions,
            )
            for w2c in extrinsics
        ],
        dtype=np.float64,
    )
    return float(max(np.linalg.norm(np.ptp(centers, axis=0)), 0.1))


def _scene_scale_from_points(
    world_points: np.ndarray,
    *,
    predictions: dict | None = None,
) -> float:
    """Scene extent from point cloud (official GLB export uses 5th–95th percentile)."""
    from .common import is_blender_z_up

    flat = np.asarray(world_points, dtype=np.float64).reshape(-1, 3)
    valid = np.isfinite(flat).all(axis=1)
    pts = flat[valid]
    if pts.shape[0] < 2:
        return 1.0
    if predictions is None or not is_blender_z_up(predictions):
        pts = _opencv_to_blender_points(pts)
    lo = np.percentile(pts, 5, axis=0)
    hi = np.percentile(pts, 95, axis=0)
    return float(max(np.linalg.norm(hi - lo), 0.1))


def _resolve_scene_scale(
    extrinsics: np.ndarray,
    world_points: np.ndarray | None,
    *,
    w2c_as_camera_pose: bool = False,
    predictions: dict | None = None,
) -> float:
    """Size frustums/trajectory from cameras and points (matches official viser/GLB)."""
    cam_scale = _scene_scale_from_extrinsics(
        extrinsics,
        w2c_as_camera_pose=w2c_as_camera_pose,
        predictions=predictions,
    )
    if world_points is None:
        return cam_scale
    return float(
        max(
            cam_scale,
            _scene_scale_from_points(world_points, predictions=predictions),
        )
    )


def _apply_build_animation(obj: bpy.types.Object, timing: _AnimationTiming) -> None:
    """Reveal curve geometry progressively during playback; full path at preview frame."""
    if timing.num_frames <= 1:
        return
    build = obj.modifiers.new(name="Build", type="BUILD")
    build_path = f'modifiers["{build.name}"]'
    build.frame_start = timing.preview_frame - timing.build_duration
    build.frame_duration = timing.build_duration
    obj.keyframe_insert(data_path=f"{build_path}.frame_start", frame=timing.preview_frame)
    obj.keyframe_insert(data_path=f"{build_path}.frame_duration", frame=timing.preview_frame)
    build.frame_start = timing.timeline_start
    build.frame_duration = timing.build_duration
    obj.keyframe_insert(data_path=f"{build_path}.frame_start", frame=timing.timeline_start)
    obj.keyframe_insert(data_path=f"{build_path}.frame_duration", frame=timing.timeline_start)
    _set_constant_interpolation(obj, f"{build_path}.frame_start")
    _set_constant_interpolation(obj, f"{build_path}.frame_duration")


def _keyframe_camera_visibility(cam_obj: bpy.types.Object, timing: _AnimationTiming, frame_index: int) -> None:
    """Static preview shows all frustums; playback reveals them one by one from frame 1."""
    show_frame = timing.blender_frame(frame_index)

    cam_obj.hide_viewport = False
    cam_obj.keyframe_insert(data_path="hide_viewport", frame=timing.preview_frame)

    cam_obj.hide_viewport = True
    cam_obj.keyframe_insert(data_path="hide_viewport", frame=timing.timeline_start)

    if show_frame > timing.timeline_start:
        cam_obj.hide_viewport = True
        cam_obj.keyframe_insert(data_path="hide_viewport", frame=show_frame - 1)

    cam_obj.hide_viewport = False
    cam_obj.keyframe_insert(data_path="hide_viewport", frame=show_frame)
    _set_constant_interpolation(cam_obj, "hide_viewport")


def _iter_action_fcurves(action):
    fcurves = getattr(action, "fcurves", None)
    if fcurves is not None:
        yield from fcurves
        return
    for layer in getattr(action, "layers", []):
        for strip in getattr(layer, "strips", []):
            for channelbag in getattr(strip, "channelbags", []):
                yield from channelbag.fcurves


def _set_constant_interpolation(obj: bpy.types.Object, data_path: str) -> None:
    if not obj.animation_data or not obj.animation_data.action:
        return
    for fcurve in _iter_action_fcurves(obj.animation_data.action):
        if fcurve.data_path == data_path:
            for kp in fcurve.keyframe_points:
                kp.interpolation = "CONSTANT"


def _set_interpolation_mode(obj: bpy.types.Object, data_path: str, mode: str) -> None:
    if not obj.animation_data or not obj.animation_data.action:
        return
    for fcurve in _iter_action_fcurves(obj.animation_data.action):
        if fcurve.data_path == data_path:
            for kp in fcurve.keyframe_points:
                kp.interpolation = mode


def _set_interpolation_paths(obj: bpy.types.Object, data_paths: list[str], mode: str) -> None:
    for data_path in data_paths:
        _set_interpolation_mode(obj, data_path, mode)


def _aligned_quaternions(camera_objects: list[bpy.types.Object]) -> list:
    """Quaternion sequence with sign flips so each step takes the short rotation arc."""
    from mathutils import Quaternion

    quats: list[Quaternion] = []
    for cam_obj in camera_objects:
        quats.append(cam_obj.matrix_world.to_quaternion().copy())
    for i in range(1, len(quats)):
        if quats[i].dot(quats[i - 1]) < 0.0:
            quats[i] = -quats[i]
    return quats


def _create_playback_camera(
    camera_objects: list[bpy.types.Object],
    collection: bpy.types.Collection | None,
    scene_scale: float,
    timing: _AnimationTiming,
    *,
    smooth: bool = True,
) -> bpy.types.Object | None:
    """Animate a playback camera through reconstruction poses on the timeline."""
    if not camera_objects:
        return None

    ref = camera_objects[0]
    playback_data = ref.data.copy()
    playback_data.name = "PlaybackCamera"
    playback_obj = bpy.data.objects.new("PlaybackCamera", playback_data)
    if collection is not None:
        collection.objects.link(playback_obj)
    else:
        bpy.context.scene.collection.objects.link(playback_obj)

    _apply_scene_scale_camera_display(playback_data, scene_scale)
    playback_obj.rotation_mode = "QUATERNION"
    quats = _aligned_quaternions(camera_objects)
    first_cam = camera_objects[0]
    playback_obj.location = first_cam.matrix_world.translation.copy()
    playback_obj.rotation_quaternion = quats[0]
    playback_obj.keyframe_insert(data_path="location", frame=timing.preview_frame)
    playback_obj.keyframe_insert(data_path="rotation_quaternion", frame=timing.preview_frame)
    for frame_idx, (cam_obj, quat) in enumerate(zip(camera_objects, quats)):
        timeline_frame = timing.blender_frame(frame_idx)
        playback_obj.location = cam_obj.matrix_world.translation.copy()
        playback_obj.rotation_quaternion = quat
        playback_obj.keyframe_insert(data_path="location", frame=timeline_frame)
        playback_obj.keyframe_insert(data_path="rotation_quaternion", frame=timeline_frame)

    interp = "LINEAR" if smooth else "CONSTANT"
    _set_interpolation_paths(playback_obj, ["location", "rotation_quaternion"], interp)
    bpy.context.scene.camera = playback_obj
    return playback_obj


def _configure_scene_timeline(timing: _AnimationTiming) -> None:
    scene = bpy.context.scene
    scene.render.fps = int(round(timing.animation_fps))
    scene.frame_start = timing.preview_frame
    scene.frame_end = timing.timeline_end
    scene.frame_current = timing.preview_frame


def _apply_intrinsics_to_blender_camera(
    cam_data: bpy.types.Camera,
    intrinsic: np.ndarray,
    image_width: int,
    image_height: int,
    scene_scale: float,
) -> None:
    """Map OpenCV intrinsics + image size to Blender camera FOV/frustum."""
    f_x, f_y = float(intrinsic[0, 0]), float(intrinsic[1, 1])
    c_x, c_y = float(intrinsic[0, 2]), float(intrinsic[1, 2])
    sensor_width = 36.0
    cam_data.sensor_fit = "HORIZONTAL"
    cam_data.sensor_width = sensor_width
    cam_data.lens = (f_x / image_width) * sensor_width
    # Match vertical FOV: vfov = 2*atan(H/(2*fy)) with horizontal sensor fit.
    cam_data.sensor_height = sensor_width * (image_height / image_width) * (f_x / f_y)
    cam_data.shift_x = (c_x - image_width / 2.0) / image_width
    cam_data.shift_y = -(c_y - image_height / 2.0) / image_height
    _apply_scene_scale_camera_display(cam_data, scene_scale)


def _apply_scene_scale_camera_display(cam_data: bpy.types.Camera, scene_scale: float) -> None:
    """Size viewport frustums relative to scene extent (matches common feedforward viewers)."""
    frustum_width = scene_scale * 0.05
    frustum_depth = scene_scale * 0.10
    cam_data.display_size = max(frustum_width, 0.01)
    cam_data.clip_start = max(frustum_depth * 0.01, 1e-4)
    cam_data.clip_end = max(frustum_depth, 0.05)
    cam_data.show_limits = True


def create_camera_trajectory(
    predictions: dict,
    collection: bpy.types.Collection | None,
    scene_scale: float,
    radius: float | None = None,
    w2c_as_camera_pose: bool = False,
    animate: bool = False,
    timing: _AnimationTiming | None = None,
) -> bpy.types.Object | None:
    """Polyline through camera centers (default trajectory radius 0.005 * scene_scale)."""
    extrinsics = predictions["extrinsic"]
    if len(extrinsics) < 2:
        return None

    if radius is None:
        radius = max(scene_scale * 0.005, 0.002)

    points = [
        _camera_center_blender(
            w2c,
            w2c_as_camera_pose=w2c_as_camera_pose,
            predictions=predictions,
        )
        for w2c in extrinsics
    ]
    curve_data = bpy.data.curves.new(name="CameraTrajectory", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.fill_mode = "FULL"
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 2

    spline = curve_data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for i, co in enumerate(points):
        spline.points[i].co = (float(co[0]), float(co[1]), float(co[2]), 1.0)

    traj_obj = bpy.data.objects.new("CameraTrajectory", curve_data)
    mat = bpy.data.materials.new(name="CameraTrajectoryMaterial")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (0.2, 0.8, 1.0, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.4
    curve_data.materials.append(mat)

    if collection is not None:
        collection.objects.link(traj_obj)
    else:
        bpy.context.scene.collection.objects.link(traj_obj)
    if animate and timing is not None:
        _apply_build_animation(traj_obj, timing)
    return traj_obj


def import_point_cloud(
    predictions: dict,
    collection=None,
    min_confidence: float = 0.5,
    point_scale: float = 1.0,
    animate: bool = False,
    timing: _AnimationTiming | None = None,
) -> bpy.types.Object | None:
    from .common import collect_colored_point_cloud

    try:
        points_batch, colors_u8, conf_batch, frame_ids = collect_colored_point_cloud(
            predictions,
            min_confidence=min_confidence,
            to_blender=True,
            with_frame_ids=animate,
        )
    except ValueError:
        print("[vibephysics] No points passed confidence threshold.")
        return None

    colors_batch = np.hstack(
        (colors_u8.astype(np.float32) / 255.0, np.ones((len(colors_u8), 1), dtype=np.float32))
    )

    return create_point_cloud_object(
        "Points",
        points_batch,
        colors_batch,
        conf_batch,
        collection=collection,
        scale=point_scale,
        min_confidence=min_confidence,
        frame_ids=frame_ids,
        recon_time_scale=timing.recon_time_scale if timing is not None else 1.0,
    )


def create_cameras(
    predictions: dict,
    collection=None,
    global_indices: list[int] | None = None,
    scene_scale: float | None = None,
    w2c_as_camera_pose: bool = False,
    animate: bool = False,
    timing: _AnimationTiming | None = None,
) -> list[bpy.types.Object]:
    scene = bpy.context.scene
    depth = predictions["depth"]
    image_height, image_width = depth.shape[1], depth.shape[2]
    num_cameras = len(predictions["extrinsic"])
    image_paths = predictions.get("image_paths")

    if scene_scale is None:
        scene_scale = _scene_scale_from_extrinsics(
            predictions["extrinsic"],
            w2c_as_camera_pose=w2c_as_camera_pose,
            predictions=predictions,
        )

    target_collection = collection
    if collection is not None:
        cameras_col = bpy.data.collections.new("Cameras")
        collection.children.link(cameras_col)
        target_collection = cameras_col

    camera_objects: list[bpy.types.Object] = []

    scene.render.resolution_x = image_width
    scene.render.resolution_y = image_height
    scene.render.pixel_aspect_x = 1.0
    scene.render.pixel_aspect_y = 1.0

    for i in range(num_cameras):
        cam_name = (
            os.path.splitext(os.path.basename(image_paths[i]))[0]
            if image_paths and i < len(image_paths)
            else f"Camera_{i}"
        )
        cam_data = bpy.data.cameras.new(name=cam_name)
        _apply_intrinsics_to_blender_camera(
            cam_data,
            predictions["intrinsic"][i],
            image_width,
            image_height,
            scene_scale,
        )

        cam_obj = bpy.data.objects.new(name=cam_name, object_data=cam_data)
        cam_obj.matrix_world = _w2c_to_blender_matrix_world(
            predictions["extrinsic"][i],
            w2c_as_camera_pose=w2c_as_camera_pose,
            predictions=predictions,
        )

        if target_collection is not None:
            target_collection.objects.link(cam_obj)
        else:
            scene.collection.objects.link(cam_obj)
        camera_objects.append(cam_obj)
        if global_indices is not None:
            cam_obj["frame_index"] = global_indices[i]
        if animate and timing is not None:
            _keyframe_camera_visibility(cam_obj, timing, i)

    if camera_objects and not animate:
        scene.camera = camera_objects[0]
    elif animate and timing is not None:
        playback = _create_playback_camera(camera_objects, target_collection, scene_scale, timing)
        if playback is not None:
            camera_objects.append(playback)
    return camera_objects


def _collection_name_for_prediction(predictions: dict | FeedforwardPrediction, collection_name: str | None) -> str:
    if collection_name:
        return collection_name
    engine = (
        predictions.engine
        if isinstance(predictions, FeedforwardPrediction)
        else predictions.get("engine", "feedforward")
    )
    return ENGINE_COLLECTION_NAMES.get(engine, f"{engine.upper()}_Result")


def _resolve_video_fps(
    predictions: dict | FeedforwardPrediction,
    video_fps: float | None,
) -> float:
    if video_fps is not None:
        return float(video_fps)
    metadata = (
        predictions.metadata
        if isinstance(predictions, FeedforwardPrediction)
        else predictions.get("metadata", {})
    )
    if isinstance(metadata, dict) and metadata.get("video_fps") is not None:
        return float(metadata["video_fps"])
    return 2.0


def _resolve_w2c_as_camera_pose(predictions: dict | FeedforwardPrediction) -> bool:
    """Whether stored w2c extrinsics should be used directly as the camera pose."""
    metadata = (
        predictions.metadata
        if isinstance(predictions, FeedforwardPrediction)
        else predictions.get("metadata", {})
    )
    if isinstance(metadata, dict) and "w2c_as_camera_pose" in metadata:
        return bool(metadata["w2c_as_camera_pose"])
    engine = (
        predictions.engine
        if isinstance(predictions, FeedforwardPrediction)
        else predictions.get("engine", "feedforward")
    )
    return is_lingbot_map_engine(engine)


def _iter_view3d_spaces(screen: bpy.types.Screen | None = None) -> list[tuple[bpy.types.Area, bpy.types.SpaceView3D, bpy.types.Region]]:
    viewports: list[tuple[bpy.types.Area, bpy.types.SpaceView3D, bpy.types.Region]] = []
    screens = [screen] if screen is not None else bpy.data.screens
    for scr in screens:
        for area in scr.areas:
            if area.type != "VIEW_3D":
                continue
            space = next((s for s in area.spaces if s.type == "VIEW_3D"), None)
            region = next((r for r in area.regions if r.type == "WINDOW"), None)
            if space is not None and region is not None:
                viewports.append((area, space, region))
    return viewports


def _point_cloud_world_bounds(point_obj: bpy.types.Object):
    from mathutils import Vector

    corners = [point_obj.matrix_world @ Vector(corner) for corner in point_obj.bound_box]
    mins = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    maxs = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    center = (mins + maxs) * 0.5
    radius = max((maxs - mins).length * 0.5, 1e-4)
    return center, radius


def _fit_view3d_to_bounds(
    rv3d: bpy.types.RegionView3D,
    region: bpy.types.Region,
    center,
    radius: float,
    *,
    fill: float,
) -> None:
    rv3d.view_perspective = "PERSP"
    rv3d.view_location = center.copy()
    aspect = region.width / max(region.height, 1)
    half_fov_y = math.radians(25.0)
    dist_v = radius / max(fill * math.tan(half_fov_y), 1e-6)
    dist_h = (radius / max(aspect, 1e-6)) / max(fill * math.tan(half_fov_y), 1e-6)
    rv3d.view_distance = max(dist_v, dist_h)


def _copy_view3d_frame(source: bpy.types.RegionView3D, target: bpy.types.RegionView3D) -> None:
    target.view_perspective = source.view_perspective
    target.view_location = source.view_location.copy()
    target.view_rotation = source.view_rotation.copy()
    target.view_distance = source.view_distance


def _frame_viewports_on_point_cloud(point_obj: bpy.types.Object | None, *, fill: float = 0.9) -> None:
    """Frame saved 3D viewports so the point cloud fills ~fill of the screen."""
    if point_obj is None:
        return

    viewports = _iter_view3d_spaces()
    if not viewports:
        return

    center, radius = _point_cloud_world_bounds(point_obj)
    framed_rv3d: bpy.types.RegionView3D | None = None

    wm = bpy.context.window_manager
    if wm.windows:
        window = wm.windows[0]
        active_viewports = _iter_view3d_spaces(window.screen)
        if not active_viewports:
            active_viewports = viewports
        area, space, region = active_viewports[0]
        bpy.ops.object.select_all(action="DESELECT")
        point_obj.select_set(True)
        bpy.context.view_layer.objects.active = point_obj
        try:
            with bpy.context.temp_override(
                window=window,
                screen=window.screen,
                area=area,
                region=region,
                space_data=space,
            ):
                bpy.ops.view3d.view_selected(use_all_regions=False)
            framed_rv3d = space.region_3d
            if framed_rv3d is not None:
                framed_rv3d.view_distance *= fill
        except Exception:
            framed_rv3d = None

    for area, space, region in viewports:
        rv3d = space.region_3d
        if rv3d is None:
            continue
        if framed_rv3d is not None:
            _copy_view3d_frame(framed_rv3d, rv3d)
        else:
            _fit_view3d_to_bounds(rv3d, region, center, radius, fill=fill)


def _configure_viewports_material_preview() -> None:
    """Persist Material Preview shading in saved .blend files."""
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    space.shading.type = "MATERIAL"
                    space.shading.background_type = "VIEWPORT"


def load_reconstruction(
    predictions: dict | FeedforwardPrediction,
    collection_name: str | None = None,
    min_confidence: float = 0.5,
    point_scale: float = 1.0,
    import_cameras: bool = True,
    import_trajectory: bool = True,
    import_points: bool = True,
    global_indices: list[int] | None = None,
    rotation: tuple[float, float, float] = (0, 0, 0),
    frame_viewports: bool = True,
    animate: bool = True,
    animation_fps: int = 24,
    video_fps: float | None = None,
) -> bpy.types.Object | None:
    if isinstance(predictions, FeedforwardPrediction):
        engine = predictions.engine
        if global_indices is None:
            global_indices = predictions.metadata.get("selected_indices")
    else:
        engine = predictions.get("engine", "feedforward")

    if min_confidence == 0.5 and is_lingbot_map_engine(engine):
        min_confidence = 1.5
    elif is_vggt_omega_engine(engine):
        min_confidence = resolve_confidence_threshold(
            predictions,
            min_confidence,
            conf_percentile=(
                predictions.metadata.get("conf_percentile")
                if isinstance(predictions, FeedforwardPrediction)
                else (predictions.get("metadata") or {}).get("conf_percentile")
            ),
        )

    if isinstance(predictions, FeedforwardPrediction):
        payload = predictions.to_viz_dict()
    else:
        payload = predictions

    w2c_as_camera_pose = _resolve_w2c_as_camera_pose(predictions)
    num_frames = len(payload["extrinsic"])
    timing = None
    if animate and num_frames > 0:
        timing = _AnimationTiming(
            num_frames=num_frames,
            animation_fps=animation_fps,
            video_fps=_resolve_video_fps(predictions, video_fps),
        )
        _configure_scene_timeline(timing)
        print(
            f"[vibephysics] Animation: {timing.duration_seconds:.1f}s "
            f"(frames {timing.preview_frame}=full preview, "
            f"{timing.timeline_start}-{timing.timeline_end} progressive @ "
            f"{int(round(timing.animation_fps))} fps, source {timing.video_fps:g} fps)"
        )

    col_name = _collection_name_for_prediction(predictions, collection_name)
    col = _ensure_collection(col_name)
    root_name = f"{col_name}_Root"
    root_obj = bpy.data.objects.get(root_name)
    if root_obj is None:
        root_obj = bpy.data.objects.new(root_name, None)
        col.objects.link(root_obj)
    elif not root_obj.users_collection:
        col.objects.link(root_obj)
    root_obj.rotation_mode = "XYZ"
    user_euler = [math.radians(a) for a in rotation]
    root_obj.rotation_euler = user_euler

    point_obj = None
    world_points = payload.get("world_points_from_depth", payload.get("world_points"))
    scene_scale = _resolve_scene_scale(
        payload["extrinsic"],
        world_points,
        w2c_as_camera_pose=w2c_as_camera_pose,
        predictions=payload,
    )
    if import_points:
        point_obj = import_point_cloud(
            payload,
            collection=col,
            min_confidence=min_confidence,
            point_scale=point_scale,
            animate=animate,
            timing=timing,
        )
        if point_obj is not None:
            point_obj.parent = root_obj
    if import_cameras:
        for cam_obj in create_cameras(
            payload,
            collection=col,
            global_indices=global_indices,
            scene_scale=scene_scale,
            w2c_as_camera_pose=w2c_as_camera_pose,
            animate=animate,
            timing=timing,
        ):
            cam_obj.parent = root_obj
    if import_trajectory and import_cameras:
        traj = create_camera_trajectory(
            payload,
            collection=col,
            scene_scale=scene_scale,
            w2c_as_camera_pose=w2c_as_camera_pose,
            animate=animate,
            timing=timing,
        )
        if traj is not None:
            traj.parent = root_obj

    _configure_viewports_material_preview()
    if frame_viewports:
        _frame_viewports_on_point_cloud(point_obj, fill=0.9)
    return point_obj


def load_predictions_file(predictions_path: str | Path, **kwargs) -> bpy.types.Object | None:
    prediction = load_prediction(Path(predictions_path))
    return load_reconstruction(prediction, **kwargs)
