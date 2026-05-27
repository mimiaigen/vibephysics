"""Post-process saved Blender scenes for clean presentation exports."""

from __future__ import annotations

import argparse
from pathlib import Path

import bpy


TRAJECTORY_NAME_TOKENS = (
    "trajectory",
    "traj",
    "motion_trail",
    "trail",
    "waypoint",
)

TRAJECTORY_EXACT_NAMES = {
    "path",
    "duckpath",
    "waypointpath",
}

TARGET_CROSS_NAME_TOKENS = (
    "camera_target",
    "camera-target",
    "camera target",
    "target_center",
    "target-centre",
    "target_centre",
    "target center",
    "target centre",
    "target_cross",
    "target-cross",
    "target cross",
    "cross_target",
    "cross-target",
    "cross target",
    "round_target",
)


def _normalized_name(obj: bpy.types.Object) -> str:
    return obj.name.lower().replace(".", "_")


def is_trajectory_object(obj: bpy.types.Object) -> bool:
    """Match visible/debug path helpers without removing ordinary scene objects."""
    name = _normalized_name(obj)
    base_name = name.rsplit("_", 1)[0] if name.rsplit("_", 1)[-1].isdigit() else name
    if base_name in TRAJECTORY_EXACT_NAMES:
        return obj.type in {"CURVE", "MESH", "EMPTY"}
    if any(token in name for token in TRAJECTORY_NAME_TOKENS):
        return obj.type in {"CURVE", "MESH", "EMPTY"}
    return False


def is_target_cross_object(obj: bpy.types.Object) -> bool:
    name = _normalized_name(obj)
    if any(token in name for token in TARGET_CROSS_NAME_TOKENS):
        return True
    if obj.type == "EMPTY" and "target" in name:
        return True
    return False


def _unlink_helper_from_scene(obj: bpy.types.Object) -> None:
    """Keep constraint targets valid while removing helper markers from visible collections."""
    obj.hide_viewport = True
    obj.hide_render = True
    try:
        obj.hide_set(True)
    except RuntimeError:
        pass
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)


def remove_objects(*, remove_trajectories: bool = True, remove_target_crosses: bool = True) -> list[str]:
    removed: list[str] = []
    for obj in list(bpy.data.objects):
        if remove_trajectories and is_trajectory_object(obj):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        if remove_target_crosses and is_target_cross_object(obj):
            removed.append(obj.name)
            _unlink_helper_from_scene(obj)
    return removed


def set_black_background() -> None:
    scene = bpy.context.scene
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.0, 0.0, 0.0)
    world.use_nodes = True

    nodes = world.node_tree.nodes
    background = nodes.get("Background")
    if background is None:
        background = nodes.new(type="ShaderNodeBackground")
    background.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    background.inputs["Strength"].default_value = 1.0

    output = nodes.get("World Output")
    if output is None:
        output = nodes.new(type="ShaderNodeOutputWorld")
    links = world.node_tree.links
    surface = output.inputs["Surface"]
    for link in list(surface.links):
        links.remove(link)
    links.new(background.outputs["Background"], surface)

    for scene in bpy.data.scenes:
        scene.world = world
        scene.render.film_transparent = False
        if hasattr(scene, "display") and hasattr(scene.display, "shading"):
            shading = scene.display.shading
            if hasattr(shading, "background_type"):
                shading.background_type = "VIEWPORT"
            if hasattr(shading, "background_color"):
                shading.background_color = (0.0, 0.0, 0.0)


def remove_viewport_grid() -> None:
    overlay_flags = (
        "show_floor",
        "show_axis_x",
        "show_axis_y",
        "show_axis_z",
        "show_grid_floor",
        "show_cursor",
        "show_object_origins",
        "show_relationship_lines",
    )
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type != "VIEW_3D":
                continue
            for space in area.spaces:
                if space.type != "VIEW_3D":
                    continue
                for flag in overlay_flags:
                    if hasattr(space.overlay, flag):
                        setattr(space.overlay, flag, False)
                space.shading.type = "MATERIAL"
                space.shading.background_type = "VIEWPORT"
                space.shading.background_color = (0.0, 0.0, 0.0)
                for flag in ("use_scene_world", "use_scene_world_render"):
                    if hasattr(space.shading, flag):
                        setattr(space.shading, flag, False)


def _set_group_interface_value(node_group: bpy.types.GeometryNodeTree, name: str, value: float) -> int:
    count = 0
    interface = getattr(node_group, "interface", None)
    items_tree = getattr(interface, "items_tree", []) if interface is not None else []
    for item in items_tree:
        if getattr(item, "item_type", None) != "SOCKET":
            continue
        if getattr(item, "in_out", None) != "INPUT":
            continue
        if item.name.lower().replace(" ", "_") != name:
            continue
        if hasattr(item, "default_value"):
            item.default_value = value
            count += 1
    return count


def _set_modifier_socket_value(modifier: bpy.types.Modifier, name: str, value: float) -> int:
    node_group = getattr(modifier, "node_group", None)
    if node_group is None:
        return 0
    count = 0
    interface = getattr(node_group, "interface", None)
    items_tree = getattr(interface, "items_tree", []) if interface is not None else []
    for item in items_tree:
        if getattr(item, "item_type", None) != "SOCKET":
            continue
        if getattr(item, "in_out", None) != "INPUT":
            continue
        if item.name.lower().replace(" ", "_") != name:
            continue
        identifier = getattr(item, "identifier", None)
        if not identifier:
            continue
        try:
            modifier[identifier] = value
            count += 1
        except Exception:
            pass
    return count


def _set_point_radius_nodes(node_group: bpy.types.GeometryNodeTree, value: float) -> int:
    count = 0
    for node in node_group.nodes:
        if node.bl_idname == "GeometryNodeMeshToPoints" and "Radius" in node.inputs:
            radius_input = node.inputs["Radius"]
            radius_input.default_value = value
            for link in radius_input.links:
                from_node = link.from_node
                if (
                    from_node.bl_idname == "ShaderNodeMath"
                    and getattr(from_node, "operation", None) == "MULTIPLY"
                    and len(from_node.inputs) > 1
                ):
                    # Older files used Scale * 0.01. Make Scale itself the absolute radius.
                    from_node.inputs[1].default_value = 1.0
            count += 1
        elif node.bl_idname == "GeometryNodeMeshIcoSphere" and "Radius" in node.inputs:
            node.inputs["Radius"].default_value = value
            count += 1
    return count


def _looks_like_point_cloud_modifier(obj: bpy.types.Object, node_group: bpy.types.GeometryNodeTree) -> bool:
    name = f"{obj.name} {node_group.name}".lower()
    if "point" in name or "pointcloud" in name:
        return True
    return any(node.bl_idname == "GeometryNodeMeshToPoints" for node in node_group.nodes)


def _mesh_color_attribute_name(obj: bpy.types.Object) -> str | None:
    if obj.type != "MESH" or obj.data is None:
        return None
    attrs = getattr(obj.data, "attributes", {})
    for name in ("point_color", "Color"):
        if name in attrs:
            return name
    color_attrs = getattr(obj.data, "color_attributes", None)
    if color_attrs:
        for name in ("point_color", "Color"):
            if name in color_attrs:
                return name
    return None


def _ensure_material_reads_attribute(mat: bpy.types.Material, attr_name: str) -> bool:
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    output = next((node for node in nodes if node.bl_idname == "ShaderNodeOutputMaterial"), None)
    if output is None:
        output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = next((node for node in nodes if node.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if bsdf is None:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")

    attr = None
    for node in nodes:
        if node.bl_idname == "ShaderNodeAttribute" and getattr(node, "attribute_name", "") == attr_name:
            attr = node
            break
    if attr is None:
        attr = nodes.new("ShaderNodeAttribute")
        attr.attribute_name = attr_name
    if hasattr(attr, "attribute_type"):
        attr.attribute_type = "GEOMETRY"

    base_color = bsdf.inputs.get("Base Color")
    if base_color is None:
        return False
    if not any(link.from_node == attr and link.to_socket == base_color for link in base_color.links):
        for link in list(base_color.links):
            links.remove(link)
        links.new(attr.outputs["Color"], base_color)

    surface = output.inputs.get("Surface")
    if surface is not None and not any(link.from_node == bsdf and link.to_socket == surface for link in surface.links):
        for link in list(surface.links):
            links.remove(link)
        links.new(bsdf.outputs["BSDF"], surface)
    return True


def repair_point_color_materials() -> list[str]:
    repaired: list[str] = []
    for obj in bpy.data.objects:
        attr_name = _mesh_color_attribute_name(obj)
        if attr_name is None:
            continue
        changed = False
        for slot in obj.material_slots:
            mat = slot.material
            if mat is not None and _ensure_material_reads_attribute(mat, attr_name):
                changed = True
        if changed:
            repaired.append(obj.name)
    return repaired


def set_point_scale(point_scale: float) -> list[str]:
    """Set existing VibePhysics point clouds to an absolute radius."""
    point_scale = float(point_scale)
    if point_scale <= 0:
        raise ValueError("--point_scale must be greater than 0")

    changed: list[str] = []
    for obj in bpy.data.objects:
        object_changed = 0
        for modifier in obj.modifiers:
            if modifier.type != "NODES":
                continue
            node_group = getattr(modifier, "node_group", None)
            if node_group is None:
                continue
            if not _looks_like_point_cloud_modifier(obj, node_group):
                continue
            object_changed += _set_group_interface_value(node_group, "scale", point_scale)
            object_changed += _set_modifier_socket_value(modifier, "scale", point_scale)
            object_changed += _set_point_radius_nodes(node_group, point_scale)
        if object_changed:
            changed.append(obj.name)
    return changed


def clean_blend(
    input_path: Path,
    output_path: Path | None = None,
    *,
    remove_trajectories: bool = True,
    remove_target_crosses: bool = True,
    black_background: bool = True,
    hide_grid: bool = True,
    point_scale: float | None = None,
    compress: bool = False,
) -> Path:
    input_path = input_path.expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input .blend does not exist: {input_path}")
    if input_path.suffix.lower() != ".blend":
        raise ValueError(f"Input must be a .blend file: {input_path}")

    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_clean.blend")
    output_path = output_path.expanduser().resolve()
    if output_path.suffix.lower() != ".blend":
        output_path = output_path.with_suffix(".blend")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.open_mainfile(filepath=str(input_path))
    removed = remove_objects(
        remove_trajectories=remove_trajectories,
        remove_target_crosses=remove_target_crosses,
    )
    if black_background:
        set_black_background()
    if hide_grid:
        remove_viewport_grid()
    repaired_colors = repair_point_color_materials()
    resized = set_point_scale(point_scale) if point_scale is not None else []

    bpy.ops.wm.save_as_mainfile(filepath=str(output_path), compress=compress)
    print(f"Saved cleaned blend: {output_path}")
    if removed:
        print("Removed objects:")
        for name in removed:
            print(f"  - {name}")
    else:
        print("Removed objects: none")
    if point_scale is not None:
        print(f"Point radius set to: {float(point_scale):g}")
        if resized:
            print("Resized point objects:")
            for name in resized:
                print(f"  - {name}")
        else:
            print("Resized point objects: none")
    if repaired_colors:
        print("Verified point color materials:")
        for name in repaired_colors:
            print(f"  - {name}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean a .blend for presentation/export.")
    parser.add_argument("--input", "-i", type=Path, required=True, help="Input .blend file.")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output .blend file. Defaults to <input>_clean.blend.",
    )
    parser.add_argument("--keep-traj", action="store_true", help="Do not remove trajectory/path helpers.")
    parser.add_argument(
        "--keep-target-cross",
        action="store_true",
        help="Do not remove target cross helper objects.",
    )
    parser.add_argument("--keep-grid", action="store_true", help="Do not disable viewport grid overlays.")
    parser.add_argument(
        "--keep-background",
        action="store_true",
        help="Do not force the world and viewport background to black.",
    )
    parser.add_argument(
        "--point_scale",
        "--point-scale",
        type=float,
        default=None,
        help="Set existing point clouds to an absolute point radius.",
    )
    parser.add_argument("--compress", action="store_true", help="Compress the saved .blend.")
    args = parser.parse_args()

    clean_blend(
        args.input,
        args.output,
        remove_trajectories=not args.keep_traj,
        remove_target_crosses=not args.keep_target_cross,
        black_background=not args.keep_background,
        hide_grid=not args.keep_grid,
        point_scale=args.point_scale,
        compress=args.compress,
    )


if __name__ == "__main__":
    main()
