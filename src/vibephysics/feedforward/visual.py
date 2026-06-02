"""
Blender visualization for feedforward dense reconstructions.

Adapted from https://github.com/xy-gao/DA3-blender (utils.py).
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix

from .common import is_lingbot_map_engine, is_vgg_ttt_engine, is_vggt_omega_engine
from .common import collect_colored_point_cloud, resolve_confidence_threshold
from .config import DEFAULT_POINT_SCALE
from .schema import FeedforwardPrediction, load_prediction

ENGINE_COLLECTION_NAMES = {
    "lingbot_map": "LingBot_Map_Result",
    "vggt_omega": "VGGT_Omega_Result",
    "vgg_ttt": "VGGT_TTT_Result",
    "lingbot": "LingBot_Map_Result",
    "vggt": "VGGT_Omega_Result",
}

# Child collections under each engine result (Outliner eye icon toggles whole layer).
VIZ_COLLECTION_POINT_CLOUD = "PointCloud"
VIZ_COLLECTION_CAMERA_POSES = "CameraPoses"
VIZ_COLLECTION_CAMERA_TRAJECTORY = "CameraTrajectory"
VIZ_COLLECTION_CHANGE_BBOXES = "ChangeBBoxes"
VIZ_COLLECTION_OCCUPANCY_VOXELS = "OccupancyVoxels"

# Fixed viewport gizmo sizes in reconstruction coordinates (not scaled to scene extent).
CAMERA_FRUSTUM_DISPLAY_SIZE = 0.02
CAMERA_FRUSTUM_CLIP_START = 0.0005
CAMERA_FRUSTUM_CLIP_END = 0.04
# Playback / render camera must see the full reconstruction (meters), not the tiny gizmo frustum.
PLAYBACK_CAMERA_CLIP_START = 0.01
PLAYBACK_CAMERA_CLIP_END = 1000.0
CAMERA_TRAJECTORY_RADIUS = 0.0008
DEFAULT_POINT_RADIUS = DEFAULT_POINT_SCALE
ANIMATION_MODES = ("progressive", "discrete")


def _srgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    """Decode display-referred JPEG/sRGB colors for Blender's linear color pipeline."""
    rgb = np.clip(rgb, 0.0, 1.0).astype(np.float32)
    low = rgb <= 0.04045
    linear = np.empty_like(rgb)
    linear[low] = rgb[low] / 12.92
    linear[~low] = ((rgb[~low] + 0.055) / 1.055) ** 2.4
    return linear


class _AnimationTiming:
    """Map reconstruction frames onto a Blender timeline that matches source video duration."""

    def __init__(
        self,
        num_frames: int,
        animation_fps: float,
        video_fps: float,
        *,
        mode: str = "progressive",
    ):
        self.num_frames = max(int(num_frames), 1)
        self.animation_fps = max(float(animation_fps), 1.0)
        self.video_fps = max(float(video_fps), 1e-6)
        self.mode = _normalize_animation_mode(mode)
        self.frames_per_recon = self.animation_fps / self.video_fps
        self.frames_per_slot = max(int(round(self.frames_per_recon)), 1)
        self.timeline_start = 1
        self.preview_frame = 0
        if self.discrete:
            self.timeline_end = (
                self.timeline_start
                if self.num_frames <= 1
                else int(round(self.timeline_start + (self.num_frames - 1) * self.frames_per_recon))
            )
            self.duration_seconds = (
                (self.num_frames - 1) / self.video_fps if self.num_frames > 1 else 0.0
            )
        else:
            self.timeline_end = (
                self.timeline_start
                if self.num_frames <= 1
                else int(round(self.timeline_start + (self.num_frames - 1) * self.frames_per_recon))
            )
            self.duration_seconds = (
                (self.num_frames - 1) / self.video_fps if self.num_frames > 1 else 0.0
            )
        self.build_duration = max(self.timeline_end - self.timeline_start, 1)
        self.recon_time_scale = self.video_fps / self.animation_fps

    @property
    def discrete(self) -> bool:
        return self.mode == "discrete"

    def blender_frame(self, recon_index: int) -> int:
        return self.timeline_start + int(round(recon_index * self.frames_per_recon))

    def slot_end(self, recon_index: int) -> int:
        """Last Blender frame (inclusive) for a discrete recon slot."""
        if recon_index + 1 < self.num_frames:
            return self.blender_frame(recon_index + 1) - 1
        return self.playback_frame_end

    @property
    def playback_frame_end(self) -> int:
        """Scene timeline end; last recon frame/bbox stay visible for a full slot."""
        if self.num_frames <= 1:
            return self.timeline_start
        last_show = self.blender_frame(self.num_frames - 1)
        return int(last_show + self.frames_per_slot - 1)

    def equal_slot_timeline_end(self) -> int:
        """Timeline end for visibility keyframes and scene playback."""
        return self.playback_frame_end


def _normalize_animation_mode(mode: str) -> str:
    normalized = str(mode).strip().lower()
    if normalized not in ANIMATION_MODES:
        raise ValueError(
            f"Unknown animation_mode '{mode}'. Choose one of: {', '.join(ANIMATION_MODES)}"
        )
    return normalized


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


def _ensure_child_collection(
    parent: bpy.types.Collection,
    child_name: str,
) -> bpy.types.Collection:
    """Named subcollection under *parent* (stable across re-import)."""
    for child in parent.children:
        if child.name == child_name:
            return child
    col = bpy.data.collections.new(child_name)
    parent.children.link(col)
    return col


@dataclass
class VizSubcollections:
    """Toggleable layers under the engine result collection."""

    root: bpy.types.Collection
    point_cloud: bpy.types.Collection
    camera_poses: bpy.types.Collection
    camera_trajectory: bpy.types.Collection
    change_bboxes: bpy.types.Collection
    occupancy_voxels: bpy.types.Collection


def _configure_hidden_root_empty(root_obj: bpy.types.Object) -> None:
    """Hide the transform empty; must not have visible children parented to it."""
    root_obj.hide_viewport = True
    root_obj.hide_render = True
    root_obj.hide_select = True
    root_obj.show_name = False
    root_obj.empty_display_size = 0.001


def _export_rotation_matrix(
    rotation_degrees: tuple[float, float, float],
) -> Matrix | None:
    """World-space rotation applied to viz objects (degrees, XYZ)."""
    euler = [math.radians(a) for a in rotation_degrees]
    if all(abs(x) < 1e-12 for x in euler):
        return None
    from mathutils import Euler

    return Euler(euler, "XYZ").to_matrix().to_4x4()


def _rotate_object_world(obj: bpy.types.Object | None, rot_mat: Matrix | None) -> None:
    if obj is not None and rot_mat is not None:
        obj.matrix_world = rot_mat @ obj.matrix_world


def setup_viz_subcollections(
    root: bpy.types.Collection,
) -> VizSubcollections:
    return VizSubcollections(
        root=root,
        point_cloud=_ensure_child_collection(root, VIZ_COLLECTION_POINT_CLOUD),
        camera_poses=_ensure_child_collection(root, VIZ_COLLECTION_CAMERA_POSES),
        camera_trajectory=_ensure_child_collection(
            root, VIZ_COLLECTION_CAMERA_TRAJECTORY
        ),
        change_bboxes=_ensure_child_collection(root, VIZ_COLLECTION_CHANGE_BBOXES),
        occupancy_voxels=_ensure_child_collection(
            root, VIZ_COLLECTION_OCCUPANCY_VOXELS
        ),
    )


def get_or_create_point_material(name: str = "FeedforwardPointMaterial") -> bpy.types.Material:
    if name in bpy.data.materials:
        mat = bpy.data.materials[name]
        if mat.use_nodes and any(node.type == "EMISSION" for node in mat.node_tree.nodes):
            return mat
        bpy.data.materials.remove(mat)

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
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Strength"].default_value = 1.0
    output_node_material = nodes.new("ShaderNodeOutputMaterial")

    links.new(conf_attr_node.outputs["Fac"], map_range.inputs["Value"])
    links.new(map_range.outputs["Result"], color_ramp.inputs["Fac"])
    links.new(attr_node.outputs["Color"], mix_node.inputs["A"])
    links.new(color_ramp.outputs["Color"], mix_node.inputs["B"])
    links.new(mix_node.outputs["Result"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], output_node_material.inputs["Surface"])
    return mat


def add_point_cloud_geo_nodes(
    obj,
    mat,
    scale: float = DEFAULT_POINT_RADIUS,
    *,
    min_confidence: float = 2.0,
    animate_frames: bool = False,
    recon_time_scale: float = 1.0,
    discrete_frames: bool = False,
    frames_per_slot: int = 1,
    timeline_start: float = 1.0,
    keep_start_frame_point_cloud: bool = False,
    point_display: str = "points",
) -> None:
    native_pointcloud = point_display == "pointcloud"
    use_spheres = point_display == "spheres"
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
    mesh_to_points = None
    if not native_pointcloud:
        mesh_to_points = node_group.nodes.new("GeometryNodeMeshToPoints")
        if hasattr(mesh_to_points, "mode"):
            mesh_to_points.mode = "VERTICES"
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

    if native_pointcloud:
        node_group.links.new(input_node.outputs["Geometry"], delete_geo.inputs["Geometry"])
    else:
        node_group.links.new(input_node.outputs["Geometry"], mesh_to_points.inputs["Mesh"])
        if not use_spheres and "Radius" in mesh_to_points.inputs:
            node_group.links.new(input_node.outputs["Scale"], mesh_to_points.inputs["Radius"])
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
        frame_offset.inputs[1].default_value = float(timeline_start)
        recon_max = node_group.nodes.new("ShaderNodeMath")
        recon_max.operation = "FLOOR"
        recon_index_source = frame_offset.outputs["Value"]
        if discrete_frames:
            frame_offset_min = node_group.nodes.new("ShaderNodeMath")
            frame_offset_min.operation = "MAXIMUM"
            frame_offset_min.inputs[1].default_value = 0.0
            node_group.links.new(frame_offset.outputs["Value"], frame_offset_min.inputs[0])
            recon_index_source = frame_offset_min.outputs["Value"]
            slot_div = node_group.nodes.new("ShaderNodeMath")
            slot_div.operation = "DIVIDE"
            slot_div.inputs[1].default_value = float(max(frames_per_slot, 1))
            node_group.links.new(recon_index_source, slot_div.inputs[0])
            node_group.links.new(slot_div.outputs["Value"], recon_max.inputs[0])
        else:
            recon_scale = node_group.nodes.new("ShaderNodeMath")
            recon_scale.operation = "MULTIPLY"
            recon_scale.inputs[1].default_value = float(recon_time_scale)
            node_group.links.new(frame_offset.outputs["Value"], recon_scale.inputs[0])
            node_group.links.new(recon_scale.outputs["Value"], recon_max.inputs[0])
        frame_compare = node_group.nodes.new("FunctionNodeCompare")
        frame_compare.data_type = "INT"
        frame_compare.operation = "NOT_EQUAL" if discrete_frames else "GREATER_THAN"
        delete_frames = node_group.nodes.new("GeometryNodeDeleteGeometry")
        delete_frames.domain = "POINT"
        node_group.links.new(scene_time.outputs["Frame"], frame_floor.inputs[0])
        node_group.links.new(frame_floor.outputs["Value"], frame_offset.inputs[0])
        node_group.links.new(frame_attr.outputs["Attribute"], frame_compare.inputs["A"])
        node_group.links.new(recon_max.outputs["Value"], frame_compare.inputs["B"])
        if discrete_frames:
            delete_selection = frame_compare.outputs["Result"]
        else:
            in_animation = node_group.nodes.new("FunctionNodeCompare")
            in_animation.data_type = "FLOAT"
            in_animation.operation = "GREATER_EQUAL"
            in_animation.inputs[1].default_value = 1.0
            frame_delete_mask = node_group.nodes.new("FunctionNodeBooleanMath")
            frame_delete_mask.operation = "AND"
            node_group.links.new(scene_time.outputs["Frame"], in_animation.inputs[0])
            node_group.links.new(in_animation.outputs["Result"], frame_delete_mask.inputs[0])
            node_group.links.new(frame_compare.outputs["Result"], frame_delete_mask.inputs[1])
            delete_selection = frame_delete_mask.outputs["Boolean"]
        if keep_start_frame_point_cloud:
            start_frame_cmp = node_group.nodes.new("FunctionNodeCompare")
            start_frame_cmp.data_type = "INT"
            start_frame_cmp.operation = "EQUAL"
            start_frame_cmp.inputs[1].default_value = 0
            not_start_frame = node_group.nodes.new("FunctionNodeBooleanMath")
            not_start_frame.operation = "NOT"
            keep_start_mask = node_group.nodes.new("FunctionNodeBooleanMath")
            keep_start_mask.operation = "AND"
            node_group.links.new(frame_attr.outputs["Attribute"], start_frame_cmp.inputs["A"])
            node_group.links.new(start_frame_cmp.outputs["Result"], not_start_frame.inputs[0])
            node_group.links.new(delete_selection, keep_start_mask.inputs[0])
            node_group.links.new(not_start_frame.outputs["Boolean"], keep_start_mask.inputs[1])
            delete_selection = keep_start_mask.outputs["Boolean"]
        node_group.links.new(last_geo, delete_frames.inputs["Geometry"])
        node_group.links.new(delete_selection, delete_frames.inputs["Selection"])
        last_geo = delete_frames.outputs["Geometry"]

    if use_spheres:
        math_node = node_group.nodes.new("ShaderNodeMath")
        math_node.operation = "MULTIPLY"
        math_node.inputs[1].default_value = 1.0
        instance_on_points = node_group.nodes.new("GeometryNodeInstanceOnPoints")
        ico_sphere = node_group.nodes.new("GeometryNodeMeshIcoSphere")
        ico_sphere.inputs["Subdivisions"].default_value = 1
        realize_instances = node_group.nodes.new("GeometryNodeRealizeInstances")
        node_group.links.new(input_node.outputs["Scale"], math_node.inputs[0])
        node_group.links.new(math_node.outputs["Value"], ico_sphere.inputs["Radius"])
        node_group.links.new(last_geo, instance_on_points.inputs["Points"])
        node_group.links.new(ico_sphere.outputs["Mesh"], instance_on_points.inputs["Instance"])
        node_group.links.new(
            instance_on_points.outputs["Instances"], realize_instances.inputs["Geometry"]
        )
        last_geo = realize_instances.outputs["Geometry"]
    node_group.links.new(last_geo, set_material_node.inputs["Geometry"])
    node_group.links.new(set_material_node.outputs["Geometry"], output_node.inputs["Geometry"])


_POINTCLOUD_SPAWN_NODE_GROUP = "_vibephysics_pointcloud_spawn"


def _get_pointcloud_spawn_node_group() -> bpy.types.NodeTree:
    """Cached Geometry Nodes tree that allocates N points (Blender 5.0+)."""
    ng = bpy.data.node_groups.get(_POINTCLOUD_SPAWN_NODE_GROUP)
    if ng is not None:
        return ng
    ng = bpy.data.node_groups.new(_POINTCLOUD_SPAWN_NODE_GROUP, "GeometryNodeTree")
    ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    count_socket = ng.interface.new_socket(name="Count", in_out="INPUT", socket_type="NodeSocketInt")
    count_socket.default_value = 0
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    input_node = ng.nodes.new("NodeGroupInput")
    output_node = ng.nodes.new("NodeGroupOutput")
    points_node = ng.nodes.new("GeometryNodePoints")
    ng.links.new(input_node.outputs["Count"], points_node.inputs["Count"])
    ng.links.new(points_node.outputs["Points"], output_node.inputs["Geometry"])
    return ng


def _spawn_pointcloud_via_geometry_nodes(count: int) -> bpy.types.PointCloud:
    """Allocate points via evaluated geometry nodes (Blender 5.0 Python API)."""
    import uuid

    ng = _get_pointcloud_spawn_node_group()
    tag = uuid.uuid4().hex[:8]
    seed_pc = bpy.data.pointclouds.new(f"_vibephysics_spawn_pc_{tag}")
    obj = bpy.data.objects.new(f"_vibephysics_spawn_obj_{tag}", seed_pc)
    collection = bpy.context.collection
    collection.objects.link(obj)
    try:
        mod = obj.modifiers.new(name="_vibephysics_spawn", type="NODES")
        mod.node_group = ng
        for item in ng.interface.items_tree:
            if item.name == "Count":
                mod[item.identifier] = int(count)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = obj.evaluated_get(depsgraph)
        return evaluated.data.copy()
    finally:
        collection.objects.unlink(obj)
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.pointclouds.remove(seed_pc)


def _try_allocate_pointcloud_inplace(pc: bpy.types.PointCloud, count: int) -> bool:
    """Resize in place when the build exposes resize() or points.add()."""
    n = int(count)
    resize = getattr(pc, "resize", None)
    if callable(resize):
        resize(n)
        return len(pc.points) == n
    points = pc.points
    add = getattr(points, "add", None)
    if callable(add):
        delta = n - len(points)
        if delta > 0:
            add(delta)
        return len(points) == n
    return False


def _prepare_pointcloud_with_count(name: str, count: int) -> bpy.types.PointCloud:
    """Return a PointCloud data-block with exactly *count* points."""
    n = int(count)
    placeholder = bpy.data.pointclouds.new(name)
    if _try_allocate_pointcloud_inplace(placeholder, n):
        return placeholder
    bpy.data.pointclouds.remove(placeholder)
    spawned = _spawn_pointcloud_via_geometry_nodes(n)
    spawned.name = name
    return spawned


def _fill_pointcloud_data(
    pc: bpy.types.PointCloud,
    points: np.ndarray,
    colors: np.ndarray,
    confs: np.ndarray,
    *,
    scale: float,
    frame_ids: np.ndarray | None = None,
) -> None:
    n = int(points.shape[0])
    if len(pc.points) != n:
        raise ValueError(f"PointCloud has {len(pc.points)} points, expected {n}")
    coords = np.asarray(points, dtype=np.float32).reshape(n, 3)
    pc.attributes["position"].data.foreach_set("vector", coords.ravel())

    color_attr = pc.attributes.new(name="point_color", type="FLOAT_COLOR", domain="POINT")
    color_attr.data.foreach_set("color", colors.reshape(n, 4).astype(np.float32).ravel().tolist())

    conf_attr = pc.attributes.new(name="conf", type="FLOAT", domain="POINT")
    conf_attr.data.foreach_set("value", np.asarray(confs, dtype=np.float32).reshape(-1).tolist())

    if frame_ids is not None:
        frame_attr = pc.attributes.new(name="frame_id", type="INT", domain="POINT")
        frame_attr.data.foreach_set("value", np.asarray(frame_ids, dtype=np.int32).reshape(-1).tolist())

    radius_attr = pc.attributes.get("radius")
    if radius_attr is None:
        radius_attr = pc.attributes.new(name="radius", type="FLOAT", domain="POINT")
    radius_attr.data.foreach_set("value", np.full(n, float(scale), dtype=np.float32).tolist())


def create_point_cloud_object(
    name: str,
    points: np.ndarray,
    colors: np.ndarray,
    confs: np.ndarray,
    collection=None,
    scale: float = DEFAULT_POINT_RADIUS,
    min_confidence: float = 2.0,
    frame_ids: np.ndarray | None = None,
    recon_time_scale: float = 1.0,
    discrete_frames: bool = False,
    frames_per_slot: int = 1,
    timeline_start: float = 1.0,
    keep_start_frame_point_cloud: bool = False,
    point_display: str = "points",
) -> bpy.types.Object:
    gn_display = point_display
    if point_display == "pointcloud":
        pc = None
        try:
            pc = _prepare_pointcloud_with_count(name, int(points.shape[0]))
            _fill_pointcloud_data(pc, points, colors, confs, scale=scale, frame_ids=frame_ids)
            obj = bpy.data.objects.new(name, pc)
        except (AttributeError, KeyError, RuntimeError, ValueError) as exc:
            if pc is not None:
                bpy.data.pointclouds.remove(pc)
            print(
                "[vibephysics] Native PointCloud setup failed "
                f"({exc}); using mesh points display.",
                flush=True,
            )
            gn_display = "points"
            point_display = "points"

    if point_display != "pointcloud":
        n = int(points.shape[0])
        mesh = bpy.data.meshes.new(name=name)
        mesh.vertices.add(n)
        mesh.vertices.foreach_set("co", np.asarray(points, dtype=np.float32).reshape(n, 3).ravel())
        color_attr = mesh.attributes.new(name="point_color", type="FLOAT_COLOR", domain="POINT")
        color_attr.data.foreach_set("color", colors.flatten().tolist())
        conf_attr = mesh.attributes.new(name="conf", type="FLOAT", domain="POINT")
        conf_attr.data.foreach_set("value", confs.tolist())
        if frame_ids is not None:
            frame_attr = mesh.attributes.new(name="frame_id", type="INT", domain="POINT")
            frame_attr.data.foreach_set("value", frame_ids.tolist())
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
    if collection is not None:
        collection.objects.link(obj)
    else:
        bpy.context.collection.objects.link(obj)

    mat = get_or_create_point_material(f"FeedforwardPointMaterial_{name}")
    if hasattr(obj.data, "materials"):
        obj.data.materials.append(mat)
    add_point_cloud_geo_nodes(
        obj,
        mat,
        scale=scale,
        min_confidence=min_confidence,
        animate_frames=frame_ids is not None,
        recon_time_scale=recon_time_scale,
        discrete_frames=discrete_frames,
        frames_per_slot=frames_per_slot,
        timeline_start=timeline_start,
        keep_start_frame_point_cloud=keep_start_frame_point_cloud,
        point_display=gn_display,
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
    """Keyframe camera frustum visibility for progressive or discrete playback."""
    if timing.discrete:
        _keyframe_camera_visibility_discrete(cam_obj, timing, frame_index)
        return

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


def _keyframe_camera_visibility_discrete(
    cam_obj: bpy.types.Object,
    timing: _AnimationTiming,
    frame_index: int,
) -> None:
    """Show one camera frustum at a time; preview frame shows recon frame 0 only."""
    show_frame = timing.blender_frame(frame_index)
    hide_frame = timing.slot_end(frame_index) + 1

    cam_obj.hide_viewport = frame_index != 0
    cam_obj.keyframe_insert(data_path="hide_viewport", frame=timing.preview_frame)

    cam_obj.hide_viewport = True
    cam_obj.keyframe_insert(data_path="hide_viewport", frame=timing.timeline_start)
    if show_frame > timing.timeline_start:
        cam_obj.hide_viewport = True
        cam_obj.keyframe_insert(data_path="hide_viewport", frame=show_frame - 1)

    cam_obj.hide_viewport = False
    cam_obj.keyframe_insert(data_path="hide_viewport", frame=show_frame)

    if hide_frame <= timing.timeline_end + 1:
        cam_obj.hide_viewport = True
        cam_obj.keyframe_insert(data_path="hide_viewport", frame=hide_frame)

    _set_constant_interpolation(cam_obj, "hide_viewport")


def _keyframe_change_bbox_visibility(
    obj: bpy.types.Object,
    timing: _AnimationTiming,
    frame_index: int,
    *,
    hide_frame_index: int | None = None,
) -> None:
    """
    Progressive: show at *frame_index*; optional *hide_frame_index* when NMS replaces
    the box on a later recon frame. Discrete: one slot only.
    """
    if timing.discrete:
        _keyframe_change_bbox_visibility_discrete(obj, timing, frame_index)
        return

    show_frame = timing.blender_frame(frame_index)

    obj.hide_viewport = False
    obj.keyframe_insert(data_path="hide_viewport", frame=timing.preview_frame)
    obj.hide_render = False
    obj.keyframe_insert(data_path="hide_render", frame=timing.preview_frame)

    obj.hide_viewport = True
    obj.keyframe_insert(data_path="hide_viewport", frame=timing.timeline_start)
    obj.hide_render = True
    obj.keyframe_insert(data_path="hide_render", frame=timing.timeline_start)
    if show_frame > timing.timeline_start:
        obj.hide_viewport = True
        obj.keyframe_insert(data_path="hide_viewport", frame=show_frame - 1)
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_render", frame=show_frame - 1)

    obj.hide_viewport = False
    obj.keyframe_insert(data_path="hide_viewport", frame=show_frame)
    obj.hide_render = False
    obj.keyframe_insert(data_path="hide_render", frame=show_frame)

    if hide_frame_index is not None and int(hide_frame_index) > int(frame_index):
        hide_blender_frame = timing.blender_frame(int(hide_frame_index))
        if hide_blender_frame > show_frame:
            obj.hide_viewport = False
            obj.keyframe_insert(data_path="hide_viewport", frame=hide_blender_frame - 1)
            obj.hide_render = False
            obj.keyframe_insert(data_path="hide_render", frame=hide_blender_frame - 1)
            obj.hide_viewport = True
            obj.keyframe_insert(data_path="hide_viewport", frame=hide_blender_frame)
            obj.hide_render = True
            obj.keyframe_insert(data_path="hide_render", frame=hide_blender_frame)

    _set_constant_interpolation(obj, "hide_viewport")
    _set_constant_interpolation(obj, "hide_render")


def _keyframe_change_bbox_visibility_discrete(
    obj: bpy.types.Object,
    timing: _AnimationTiming,
    frame_index: int,
) -> None:
    """Match camera discrete visibility: frame 0 visible at preview_frame."""
    show_frame = timing.blender_frame(frame_index)
    hide_frame = timing.slot_end(frame_index) + 1

    visible_at_preview = frame_index == 0
    obj.hide_viewport = not visible_at_preview
    obj.keyframe_insert(data_path="hide_viewport", frame=timing.preview_frame)
    obj.hide_render = not visible_at_preview
    obj.keyframe_insert(data_path="hide_render", frame=timing.preview_frame)

    obj.hide_viewport = True
    obj.keyframe_insert(data_path="hide_viewport", frame=timing.timeline_start)
    obj.hide_render = True
    obj.keyframe_insert(data_path="hide_render", frame=timing.timeline_start)
    if show_frame > timing.timeline_start:
        obj.hide_viewport = True
        obj.keyframe_insert(data_path="hide_viewport", frame=show_frame - 1)
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_render", frame=show_frame - 1)

    obj.hide_viewport = False
    obj.keyframe_insert(data_path="hide_viewport", frame=show_frame)
    obj.hide_render = False
    obj.keyframe_insert(data_path="hide_render", frame=show_frame)

    if hide_frame <= timing.timeline_end + 1:
        obj.hide_viewport = True
        obj.keyframe_insert(data_path="hide_viewport", frame=hide_frame)
        obj.hide_render = True
        obj.keyframe_insert(data_path="hide_render", frame=hide_frame)

    _set_constant_interpolation(obj, "hide_viewport")
    _set_constant_interpolation(obj, "hide_render")


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

    _apply_camera_viewport_display(playback_data, playback=True)
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


def _configure_scene_timeline(timing: _AnimationTiming, *, frame_end: int | None = None) -> None:
    scene = bpy.context.scene
    scene.render.fps = int(round(timing.animation_fps))
    scene.frame_start = timing.preview_frame
    scene.frame_end = frame_end if frame_end is not None else timing.timeline_end
    scene.frame_current = timing.preview_frame


def _apply_intrinsics_to_blender_camera(
    cam_data: bpy.types.Camera,
    intrinsic: np.ndarray,
    image_width: int,
    image_height: int,
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
    _apply_camera_viewport_display(cam_data)


def _apply_camera_viewport_display(
    cam_data: bpy.types.Camera,
    *,
    playback: bool = False,
) -> None:
    """Fixed-size frustum gizmo for pose cameras; full-scene clip for PlaybackCamera."""
    if playback:
        cam_data.display_size = 0.1
        cam_data.clip_start = PLAYBACK_CAMERA_CLIP_START
        cam_data.clip_end = PLAYBACK_CAMERA_CLIP_END
        cam_data.show_limits = False
        return
    cam_data.display_size = CAMERA_FRUSTUM_DISPLAY_SIZE
    cam_data.clip_start = CAMERA_FRUSTUM_CLIP_START
    cam_data.clip_end = CAMERA_FRUSTUM_CLIP_END
    cam_data.show_limits = False
    if hasattr(cam_data, "show_sensor"):
        cam_data.show_sensor = False


def create_camera_trajectory(
    predictions: dict,
    collection: bpy.types.Collection | None,
    radius: float | None = None,
    w2c_as_camera_pose: bool = False,
    animate: bool = False,
    timing: _AnimationTiming | None = None,
    world_rotation: Matrix | None = None,
) -> bpy.types.Object | None:
    """Polyline through camera centers."""
    extrinsics = predictions["extrinsic"]
    if len(extrinsics) < 2:
        return None

    if radius is None:
        radius = CAMERA_TRAJECTORY_RADIUS

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
    _rotate_object_world(traj_obj, world_rotation)
    if animate and timing is not None:
        if timing.discrete:
            traj_obj.hide_viewport = True
        else:
            _apply_build_animation(traj_obj, timing)
    return traj_obj


def import_point_cloud(
    predictions: dict,
    collection=None,
    min_confidence: float = 2.0,
    point_scale: float = DEFAULT_POINT_RADIUS,
    random_points_per_frame: int | None = None,
    total_random_points: int | None = None,
    animate: bool = False,
    timing: _AnimationTiming | None = None,
    keep_start_frame_point_cloud: bool = False,
    point_cloud_3d_nms: bool | None = None,
    point_cloud_3d_nms_radius: float | None = None,
    point_cloud_3d_nms_min_neighbors: int | None = None,
    precomputed_points: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray | None] | None = None,
    world_rotation: Matrix | None = None,
    point_display: str | None = None,
) -> bpy.types.Object | None:
    from .common import collect_colored_point_cloud
    from .config import blend_default, normalize_point_display

    if point_display is None:
        point_display = normalize_point_display(blend_default("point_display"))
    if point_cloud_3d_nms is None:
        point_cloud_3d_nms = bool(output_default("point_cloud_3d_nms"))
    if point_cloud_3d_nms_radius is None:
        point_cloud_3d_nms_radius = float(output_default("point_cloud_3d_nms_radius"))
    if point_cloud_3d_nms_min_neighbors is None:
        point_cloud_3d_nms_min_neighbors = int(output_default("point_cloud_3d_nms_min_neighbors"))

    try:
        if precomputed_points is not None:
            points_batch, colors_u8, conf_batch, frame_ids = precomputed_points
        else:
            points_batch, colors_u8, conf_batch, frame_ids = collect_colored_point_cloud(
                predictions,
                min_confidence=min_confidence,
                to_blender=True,
                with_frame_ids=animate,
                random_points_per_frame=random_points_per_frame,
                total_random_points=total_random_points,
                point_cloud_3d_nms=point_cloud_3d_nms,
                point_cloud_3d_nms_radius=point_cloud_3d_nms_radius,
                point_cloud_3d_nms_min_neighbors=point_cloud_3d_nms_min_neighbors,
            )
    except ValueError:
        print("[vibephysics] No points passed confidence threshold.")
        return None

    colors_srgb = colors_u8.astype(np.float32) / 255.0
    colors_linear = _srgb_to_linear(colors_srgb)
    colors_batch = np.hstack(
        (colors_linear, np.ones((len(colors_linear), 1), dtype=np.float32))
    )

    obj = create_point_cloud_object(
        "Points",
        points_batch,
        colors_batch,
        conf_batch,
        collection=collection,
        scale=point_scale,
        min_confidence=min_confidence,
        frame_ids=frame_ids,
        recon_time_scale=timing.recon_time_scale if timing is not None else 1.0,
        discrete_frames=timing.discrete if timing is not None else False,
        frames_per_slot=timing.frames_per_slot if timing is not None else 1,
        timeline_start=float(timing.timeline_start) if timing is not None else 1.0,
        keep_start_frame_point_cloud=keep_start_frame_point_cloud,
        point_display=point_display,
    )
    _rotate_object_world(obj, world_rotation)
    return obj


def _prediction_render_resolution(predictions: dict) -> tuple[int, int]:
    """Image height/width for camera intrinsics (dense depth or compact metadata)."""
    depth = predictions.get("depth")
    if depth is not None and getattr(depth, "size", 0) and depth.ndim >= 3:
        height, width = int(depth.shape[1]), int(depth.shape[2])
        if height > 1 and width > 1:
            return height, width
    meta = predictions.get("metadata") or {}
    image_size = meta.get("image_size")
    if image_size is not None:
        size = int(image_size)
        return size, size
    image_paths = predictions.get("image_paths") or []
    if image_paths:
        try:
            from PIL import Image

            with Image.open(image_paths[0]) as image:
                width, height = image.size
            return int(height), int(width)
        except OSError:
            pass
    return 518, 518


def create_cameras(
    predictions: dict,
    collection=None,
    global_indices: list[int] | None = None,
    w2c_as_camera_pose: bool = False,
    animate: bool = False,
    timing: _AnimationTiming | None = None,
    world_rotation: Matrix | None = None,
) -> list[bpy.types.Object]:
    scene = bpy.context.scene
    image_height, image_width = _prediction_render_resolution(predictions)
    num_cameras = len(predictions["extrinsic"])
    image_paths = predictions.get("image_paths")

    target_collection = collection

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
        )

        cam_obj = bpy.data.objects.new(name=cam_name, object_data=cam_data)
        cam_obj.matrix_world = _w2c_to_blender_matrix_world(
            predictions["extrinsic"][i],
            w2c_as_camera_pose=w2c_as_camera_pose,
            predictions=predictions,
        )
        _rotate_object_world(cam_obj, world_rotation)

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
        playback = _create_playback_camera(
            camera_objects,
            target_collection,
            timing,
            smooth=not timing.discrete,
        )
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


def _configure_scene_display_for_source_colors() -> None:
    """Match source JPEG colors instead of Filmic/AgX highlight wash."""
    scene = bpy.context.scene
    view = scene.view_settings
    view.view_transform = "Standard"
    view.exposure = 0.0
    view.gamma = 1.0
    if hasattr(view, "look"):
        view.look = "None"


def _configure_viewport_overlays(space: bpy.types.SpaceView3D) -> None:
    """Hide constraint/camera helper lines that clutter reconstruction playback."""
    overlay = space.overlay
    if hasattr(overlay, "show_relationship_lines"):
        overlay.show_relationship_lines = False
    if hasattr(overlay, "show_camera_passepartout"):
        overlay.show_camera_passepartout = False


def _configure_viewports_material_preview() -> None:
    """Persist Material Preview shading in saved .blend files."""
    _configure_scene_display_for_source_colors()
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    space.shading.type = "MATERIAL"
                    space.shading.background_type = "VIEWPORT"
                    space.shading.use_scene_world = False
                    if hasattr(space.shading, "use_scene_lights"):
                        space.shading.use_scene_lights = False
                    if hasattr(space.shading, "use_scene_lights_render"):
                        space.shading.use_scene_lights_render = False
                    _configure_viewport_overlays(space)


def load_reconstruction(
    predictions: dict | FeedforwardPrediction,
    collection_name: str | None = None,
    min_confidence: float = 2.0,
    point_scale: float = DEFAULT_POINT_RADIUS,
    random_points_per_frame: int | float | None = None,
    total_random_points: int | float | None = None,
    import_cameras: bool = True,
    import_trajectory: bool = True,
    import_points: bool = True,
    global_indices: list[int] | None = None,
    rotation: tuple[float, float, float] = (0, 0, 0),
    frame_viewports: bool = True,
    animate: bool = True,
    animation_fps: int = 24,
    animation_mode: str = "progressive",
    video_fps: float | None = None,
    algo_3d_bboxes: list | None = None,
    algo_3d_bbox_min_visualize_changed_voxels: int | None = None,
    algo_3d_bbox_class_colors: dict[str, tuple[float, float, float, float]] | None = None,
    keep_start_frame_point_cloud: bool = False,
    point_cloud_3d_nms: bool | None = None,
    point_cloud_3d_nms_radius: float | None = None,
    point_cloud_3d_nms_min_neighbors: int | None = None,
    precomputed_points: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray | None] | None = None,
    point_display: str | None = None,
) -> bpy.types.Object | None:
    if isinstance(predictions, FeedforwardPrediction):
        engine = predictions.engine
        if global_indices is None:
            global_indices = predictions.metadata.get("selected_indices")
    else:
        engine = predictions.get("engine", "feedforward")

    if is_vggt_omega_engine(engine):
        min_confidence = resolve_confidence_threshold(
            predictions,
            min_confidence,
            conf_percentile=(
                predictions.metadata.get("conf_percentile")
                if isinstance(predictions, FeedforwardPrediction)
                else (predictions.get("metadata") or {}).get("conf_percentile")
            ),
        )
    elif is_vgg_ttt_engine(engine):
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
            mode=animation_mode,
        )
        scene_end = (
            timing.playback_frame_end
            if timing.discrete or algo_3d_bboxes
            else timing.timeline_end
        )
        _configure_scene_timeline(timing, frame_end=scene_end)
        if timing.discrete:
            preview_note = (
                f"frame {timing.preview_frame}=recon frame 0 only, "
                f"{timing.timeline_start}-{timing.playback_frame_end} discrete "
                f"({timing.frames_per_slot} blender frames / recon frame)"
            )
        else:
            preview_note = (
                f"frames {timing.preview_frame}=full preview, "
                f"{timing.timeline_start}-{timing.timeline_end} progressive"
            )
        print(
            f"[vibephysics] Animation: {timing.duration_seconds:.1f}s "
            f"({preview_note} @ {int(round(timing.animation_fps))} fps, "
            f"source {timing.video_fps:g} fps)"
        )
        if keep_start_frame_point_cloud:
            print("[vibephysics] Point cloud: keeping reconstruction frame 0 visible during playback")

    col_name = _collection_name_for_prediction(predictions, collection_name)
    col = _ensure_collection(col_name)
    viz_cols = setup_viz_subcollections(col)
    root_name = f"{col_name}_Root"
    root_obj = bpy.data.objects.get(root_name)
    if root_obj is None:
        root_obj = bpy.data.objects.new(root_name, None)
        col.objects.link(root_obj)
    elif not root_obj.users_collection:
        col.objects.link(root_obj)
    root_obj.rotation_mode = "XYZ"
    world_rotation = _export_rotation_matrix(rotation)
    _configure_hidden_root_empty(root_obj)

    point_obj = None
    camera_objects: list[bpy.types.Object] = []
    traj = None
    if import_points:
        point_obj = import_point_cloud(
            payload,
            collection=viz_cols.point_cloud,
            min_confidence=min_confidence,
            point_scale=point_scale,
            random_points_per_frame=random_points_per_frame,
            total_random_points=total_random_points,
            animate=animate,
            timing=timing,
            keep_start_frame_point_cloud=keep_start_frame_point_cloud,
            point_cloud_3d_nms=point_cloud_3d_nms,
            point_cloud_3d_nms_radius=point_cloud_3d_nms_radius,
            point_cloud_3d_nms_min_neighbors=point_cloud_3d_nms_min_neighbors,
            precomputed_points=precomputed_points,
            world_rotation=world_rotation,
            point_display=point_display,
        )
    if import_cameras:
        camera_objects = create_cameras(
            payload,
            collection=viz_cols.camera_poses,
            global_indices=global_indices,
            w2c_as_camera_pose=w2c_as_camera_pose,
            animate=animate,
            timing=timing,
            world_rotation=world_rotation,
        )
    if import_trajectory and import_cameras:
        traj = create_camera_trajectory(
            payload,
            collection=viz_cols.camera_trajectory,
            w2c_as_camera_pose=w2c_as_camera_pose,
            animate=animate,
            timing=timing,
            world_rotation=world_rotation,
        )

    if algo_3d_bboxes:
        from .algo_3d_bbox import (
            import_change_bboxes_to_blender,
            import_detection_occupancy_voxels_to_blender,
        )
        from .config import (
            DEFAULT_FEEDFORWARD_CONFIG,
            algo_3d_bbox_default,
            load_yaml_config,
            parse_detection_seg_classes,
        )

        min_bbox_voxels = (
            int(algo_3d_bbox_min_visualize_changed_voxels)
            if algo_3d_bbox_min_visualize_changed_voxels is not None
            else int(algo_3d_bbox_default("min_visualize_changed_voxels"))
        )
        bbox_class_colors = algo_3d_bbox_class_colors
        if not bbox_class_colors:
            section = load_yaml_config(DEFAULT_FEEDFORWARD_CONFIG).get(
                "detection_seg", {}
            )
            _, bbox_class_colors = parse_detection_seg_classes(
                section.get("classes", ["person"])
            )
        viz_mode = str(algo_3d_bbox_default("visualization")).strip().lower()
        nms_iou = float(algo_3d_bbox_default("progressive_class_nms_iou"))
        bbox_frames = (
            algo_3d_bboxes.get("frames", algo_3d_bboxes)
            if isinstance(algo_3d_bboxes, dict) and "frames" in algo_3d_bboxes
            else algo_3d_bboxes
        )
        blend_kwargs = dict(
            timing=timing,
            animate=animate and timing is not None,
            min_visualize_changed_voxels=min_bbox_voxels,
            class_colors=bbox_class_colors,
            progressive_class_nms_iou=nms_iou,
        )
        if viz_mode in ("voxels", "both"):
            voxel_size = float(algo_3d_bbox_default("voxel_size"))
            if isinstance(algo_3d_bboxes, dict) and "voxel_size" in algo_3d_bboxes:
                voxel_size = float(algo_3d_bboxes["voxel_size"])
            vox_objs = import_detection_occupancy_voxels_to_blender(
                bbox_frames,
                viz_cols.occupancy_voxels,
                voxel_size=voxel_size,
                voxel_alpha=float(algo_3d_bbox_default("voxel_alpha")),
                world_rotation=world_rotation,
                **blend_kwargs,
            )
        if viz_mode in ("bbox", "both"):
            import_change_bboxes_to_blender(
                bbox_frames,
                viz_cols.change_bboxes,
                world_rotation=world_rotation,
                **blend_kwargs,
            )

    _configure_viewports_material_preview()
    if frame_viewports:
        _frame_viewports_on_point_cloud(point_obj, fill=0.9)

    return point_obj


def load_predictions_file(predictions_path: str | Path, **kwargs) -> bpy.types.Object | None:
    prediction = load_prediction(Path(predictions_path))
    return load_reconstruction(prediction, **kwargs)
