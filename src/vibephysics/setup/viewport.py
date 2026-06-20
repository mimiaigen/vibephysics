"""
Viewport Management Module

Handles dual viewport setup with synchronized views using local view.
Each viewport shows different object sets (e.g., left: scene, right: point cloud).
"""

import bpy
import math
from mathutils import Euler


def find_layer_collection(layer_collection, collection_name):
    """Recursively find a layer collection by name."""
    if layer_collection.name == collection_name:
        return layer_collection
    
    for child in layer_collection.children:
        result = find_layer_collection(child, collection_name)
        if result:
            return result
    
    return None


def get_view3d_areas(screen):
    """Get all VIEW_3D areas from a screen, sorted by x position (left to right)."""
    view3d_areas = [a for a in screen.areas if a.type == 'VIEW_3D']
    return sorted(view3d_areas, key=lambda a: a.x)


def _get_view3d_areas_for_layout(screen, layout="left-right"):
    """Get VIEW_3D areas ordered by compare layout."""
    view3d_areas = [a for a in screen.areas if a.type == 'VIEW_3D']
    if layout == "top-down":
        return sorted(view3d_areas, key=lambda a: a.y, reverse=True)
    return sorted(view3d_areas, key=lambda a: a.x)


def get_space_view3d(area):
    """Get the SpaceView3D from an area."""
    for space in area.spaces:
        if space.type == 'VIEW_3D':
            return space
    return None


def split_viewport_pair(factor=0.5, layout="left-right"):
    """
    Split the current 3D viewport into two viewports.

    layout="left-right" creates side-by-side panes. layout="top-down" creates
    vertically stacked panes and returns them as (top, bottom).
    """
    if layout not in {"left-right", "top-down"}:
        raise ValueError("layout must be 'left-right' or 'top-down'")

    screen = bpy.context.screen
    if not screen:
        return None, None
    
    view3d_areas = _get_view3d_areas_for_layout(screen, layout)
    
    if not view3d_areas:
        return None, None
    
    if len(view3d_areas) >= 2:
        return view3d_areas[0], view3d_areas[-1]
    
    area = view3d_areas[0]
    with bpy.context.temp_override(area=area, region=area.regions[0]):
        try:
            direction = 'VERTICAL' if layout == "left-right" else 'HORIZONTAL'
            bpy.ops.screen.area_split(direction=direction, factor=factor)
        except Exception as e:
            print(f"⚠️ Could not split viewport: {e}")
            return None, None
    
    view3d_areas = _get_view3d_areas_for_layout(screen, layout)
    if len(view3d_areas) < 2:
        return None, None
    
    return view3d_areas[0], view3d_areas[-1]


def split_viewport_horizontal(factor=0.5):
    """
    Split the current 3D viewport horizontally into two side-by-side viewports.
    """
    return split_viewport_pair(factor=factor, layout="left-right")


def configure_viewport_shading(space, shading_type='SOLID', light='FLAT', 
                                color_type='VERTEX', background_color=(0.1, 0.1, 0.12)):
    """Configure viewport shading settings."""
    if not space:
        return
    
    space.shading.type = shading_type
    if shading_type == 'SOLID':
        space.shading.light = light
        space.shading.color_type = color_type
    
    space.shading.background_type = 'VIEWPORT'
    space.shading.background_color = background_color


def configure_viewport_overlays(space, show_floor=True, show_axes=True, 
                                 show_cursor=False, show_extras=False):
    """Configure viewport overlay settings."""
    if not space:
        return
    space.overlay.show_floor = show_floor
    space.overlay.show_axis_x = show_axes
    space.overlay.show_axis_y = show_axes
    space.overlay.show_axis_z = show_axes
    space.overlay.show_cursor = show_cursor
    space.overlay.show_object_origins = False
    space.overlay.show_extras = show_extras
    space.overlay.show_relationship_lines = False


def configure_viewport_chrome(
    space,
    *,
    show_toolbar: bool = False,
    show_tool_header: bool = False,
    show_ui: bool = False,
) -> None:
    """Hide viewport side panels (toolbar, tool header, N-panel) for a cleaner view."""
    if not space:
        return
    for attr, value in (
        ("show_region_toolbar", show_toolbar),
        ("show_region_tool_header", show_tool_header),
        ("show_region_ui", show_ui),
    ):
        if hasattr(space, attr):
            setattr(space, attr, value)


def lock_viewport_to_camera(space):
    """Lock a viewport to the scene camera."""
    if space and bpy.context.scene.camera:
        space.region_3d.view_perspective = 'CAMERA'


def reset_viewport_single():
    """
    Reset to single viewport by joining areas.
    
    Note: This attempts to join the rightmost VIEW_3D area into the leftmost.
    """
    if bpy.app.background:
        return
    
    screen = bpy.context.screen
    if not screen:
        return
    
    view3d_areas = get_view3d_areas(screen)
    
    if len(view3d_areas) < 2:
        return  # Already single viewport
    
    # Try to join rightmost into leftmost
    left_area = view3d_areas[0]
    right_area = view3d_areas[-1]
    
    try:
        with bpy.context.temp_override(area=left_area, region=left_area.regions[0]):
            # Find the edge between the two areas
            bpy.ops.screen.area_join(cursor=(right_area.x, right_area.y + right_area.height // 2))
        print("✅ Viewport reset to single view")
    except Exception as e:
        print(f"⚠️ Could not reset viewport: {e}")


# =============================================================================
# View Sync Utilities
# =============================================================================

def sync_viewport_views(source_space, target_space):
    """Synchronize view settings from source to target viewport."""
    if not source_space or not target_space:
        return
    target_space.region_3d.view_perspective = source_space.region_3d.view_perspective
    target_space.region_3d.view_rotation = source_space.region_3d.view_rotation.copy()
    target_space.region_3d.view_distance = source_space.region_3d.view_distance
    target_space.region_3d.view_location = source_space.region_3d.view_location.copy()


def _window_region(area):
    return next((region for region in area.regions if region.type == "WINDOW"), None)


def enter_local_view(area, objects):
    """
    Enter local view in a specific viewport area with given objects.
    Handles exiting existing local view first.
    """
    if not area:
        return False
        
    space = get_space_view3d(area)
    region = _window_region(area)
    if not space or not region:
        return False
        
    # 1. Exit Local View if active
    if space.local_view:
        with bpy.context.temp_override(area=area, region=region, space_data=space):
            bpy.ops.view3d.localview()
    
    if not objects:
        return False
        
    # 2. Select objects
    target = _point_cloud_object(objects) or objects[0]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        if obj and obj.name in bpy.data.objects:
            obj.select_set(True)
    if target is not None:
        bpy.context.view_layer.objects.active = target
    
    # 3. Enter Local View
    with bpy.context.temp_override(area=area, region=region, space_data=space):
        bpy.ops.view3d.localview()
        
    return space.local_view is not None


def setup_dual_viewport(point_cloud_objects, collection_name="PointTrackingViz"):
    """
    Setup dual viewports using Dual Local View strategy:
    - Left: Local View (All objects EXCEPT Point Cloud)
    - Right: Local View (ONLY Point Cloud)
    """
    main_area, tracking_area = split_viewport_horizontal(0.5)
    
    if not main_area or not tracking_area:
        return None, None
    
    main_space = get_space_view3d(main_area)
    tracking_space = get_space_view3d(tracking_area)
    
    # === Identify Objects ===
    all_objects = set(bpy.context.scene.objects)
    pc_objects = set(point_cloud_objects)
    scene_objects = list(all_objects - pc_objects)
    tracking_objects = list(pc_objects)
    
    # === Setup LEFT Viewport (Scene Only) ===
    configure_viewport_shading(main_space, shading_type='MATERIAL')
    if scene_objects:
        enter_local_view(main_area, scene_objects)
    
    # === Setup RIGHT Viewport (Point Cloud Only) ===
    configure_viewport_shading(
        tracking_space, 
        shading_type='SOLID', 
        light='FLAT',
        color_type='VERTEX',
        background_color=(0.1, 0.1, 0.12)
    )
    configure_viewport_overlays(tracking_space, show_floor=True, show_axes=True)
    
    if tracking_objects:
        enter_local_view(tracking_area, tracking_objects)
        
        # Frame view on point cloud
        with bpy.context.temp_override(area=tracking_area, region=tracking_area.regions[-1], space_data=tracking_space):
             bpy.ops.view3d.view_all()
    
    # === Sync views ===
    if bpy.context.scene.camera:
        lock_viewport_to_camera(main_space)
        lock_viewport_to_camera(tracking_space)
    else:
        sync_viewport_views(main_space, tracking_space)
    
    register_view_sync_handler(main_area, tracking_area)
    
    print("✅ Dual viewport setup complete (Dual Local View)")
    return main_area, tracking_area


def _objects_in_collection(collection_name: str) -> list[bpy.types.Object]:
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        return []
    return list(collection.all_objects)


def _point_cloud_object(objects: list[bpy.types.Object]) -> bpy.types.Object | None:
    for obj in objects:
        if obj.type == "MESH" and obj.name.startswith("Points"):
            return obj
    for obj in objects:
        if obj.type == "MESH":
            return obj
    return None


def _frame_viewport_area(area, objects: list[bpy.types.Object], *, fill: float = 0.9) -> None:
    space = get_space_view3d(area)
    if not space or not objects:
        return

    region = next((r for r in area.regions if r.type == "WINDOW"), None)
    if region is None:
        return

    target = _point_cloud_object(objects) or objects[0]
    window = bpy.context.window_manager.windows[0] if bpy.context.window_manager.windows else None
    if window is None:
        return

    bpy.ops.object.select_all(action="DESELECT")
    target.select_set(True)
    bpy.context.view_layer.objects.active = target

    try:
        with bpy.context.temp_override(
            window=window,
            screen=window.screen,
            area=area,
            region=region,
            space_data=space,
        ):
            bpy.ops.view3d.view_selected(use_all_regions=False)
        if space.region_3d is not None:
            space.region_3d.view_distance *= fill
    except Exception as exc:
        print(f"⚠️ Could not frame viewport: {exc}")


def _setup_compare_viewport(area, objects: list[bpy.types.Object], *, fill: float = 0.9) -> bool:
    """Configure one compare pane: material shading, local view, and framing."""
    space = get_space_view3d(area)
    if not space or not objects:
        return False

    configure_viewport_shading(space, shading_type="MATERIAL")
    configure_viewport_overlays(space, show_floor=False, show_axes=False, show_extras=True)
    configure_viewport_chrome(space)

    # Isolate the full reconstruction in local view, but frame on the point cloud only
    # (same as single-export blends — not the entire camera path).
    if not enter_local_view(area, objects):
        return False

    _frame_viewport_area(area, objects, fill=fill)
    return space.local_view is not None


def split_viewport_triple():
    """Split the current 3D viewport into three side-by-side panes (left, center, right)."""
    screen = bpy.context.screen
    if not screen:
        return None, None, None

    view3d_areas = sorted([a for a in screen.areas if a.type == "VIEW_3D"], key=lambda a: a.x)
    if len(view3d_areas) >= 3:
        return view3d_areas[0], view3d_areas[1], view3d_areas[2]

    if not view3d_areas:
        return None, None, None

    area = view3d_areas[0]
    with bpy.context.temp_override(area=area, region=area.regions[0]):
        try:
            bpy.ops.screen.area_split(direction="VERTICAL", factor=1 / 3)
        except Exception as exc:
            print(f"⚠️ Could not split viewport (first): {exc}")
            return None, None, None

    view3d_areas = sorted([a for a in screen.areas if a.type == "VIEW_3D"], key=lambda a: a.x)
    if len(view3d_areas) < 2:
        return None, None, None

    right_area = view3d_areas[-1]
    with bpy.context.temp_override(area=right_area, region=right_area.regions[0]):
        try:
            bpy.ops.screen.area_split(direction="VERTICAL", factor=0.5)
        except Exception as exc:
            print(f"⚠️ Could not split viewport (second): {exc}")
            return None, None, None

    view3d_areas = sorted([a for a in screen.areas if a.type == "VIEW_3D"], key=lambda a: a.x)
    if len(view3d_areas) < 3:
        return None, None, None
    return view3d_areas[0], view3d_areas[1], view3d_areas[2]


def setup_compare_triple_viewport(
    left_collection: str,
    center_collection: str,
    right_collection: str,
):
    """
    Split the 3D view into three independent viewports with a shared timeline.

    Each pane isolates one reconstruction via Local View and frames independently.
    """
    pane_specs = (
        ("left", left_collection),
        ("center", center_collection),
        ("right", right_collection),
    )
    objects_by_pane = []
    for label, collection_name in pane_specs:
        objects = _objects_in_collection(collection_name)
        if not objects:
            print(f"⚠️ Compare viewport skipped: missing objects for {label}={collection_name}")
            return None, None, None
        objects_by_pane.append(objects)

    left_area, center_area, right_area = split_viewport_triple()
    if not left_area or not center_area or not right_area:
        print("⚠️ Compare viewport skipped: could not split 3D view into three panes")
        return None, None, None

    areas = (left_area, center_area, right_area)
    ok = True
    for area, objects in zip(areas, objects_by_pane):
        ok = _setup_compare_viewport(area, objects) and ok
    if not ok:
        print("⚠️ Compare viewport setup incomplete (local view may be missing)")

    print(
        "✅ Compare viewport ready: "
        f"left={left_collection}, center={center_collection}, right={right_collection} "
        "(layout=triple, shared timeline, independent views)"
    )
    return left_area, center_area, right_area


def setup_compare_dual_viewport(left_collection: str, right_collection: str, *, layout: str = "left-right"):
    """
    Split the 3D view into two independent viewports with a shared timeline.

    Left/right or top/bottom panes each isolate one reconstruction via Local View.
    View orientation is framed independently per side (not camera-synced).
    """
    left_objects = _objects_in_collection(left_collection)
    right_objects = _objects_in_collection(right_collection)
    if not left_objects or not right_objects:
        print("⚠️ Compare viewport skipped: missing collection objects")
        return None, None

    left_area, right_area = split_viewport_pair(0.5, layout=layout)
    if not left_area or not right_area:
        print("⚠️ Compare viewport skipped: could not split 3D view")
        return None, None

    left_ok = _setup_compare_viewport(left_area, left_objects)
    right_ok = _setup_compare_viewport(right_area, right_objects)
    if not left_ok or not right_ok:
        print("⚠️ Compare viewport setup incomplete (local view may be missing)")

    print(
        f"✅ Compare viewport ready: left={left_collection}, right={right_collection} "
        f"(layout={layout}, shared timeline, independent views)"
    )
    return left_area, right_area


def register_view_sync_handler(main_area, tracking_area):
    """Register view sync handler."""
    main_space = get_space_view3d(main_area)
    tracking_space = get_space_view3d(tracking_area)
    
    def sync_views(scene):
        if main_space and tracking_space:
            if main_space.region_3d.view_perspective != 'CAMERA':
                tracking_space.region_3d.view_rotation = main_space.region_3d.view_rotation.copy()
                tracking_space.region_3d.view_distance = main_space.region_3d.view_distance
                tracking_space.region_3d.view_location = main_space.region_3d.view_location.copy()
    
    sync_views.__name__ = "point_tracking_view_sync"
    
    for handler in list(bpy.app.handlers.frame_change_post):
        if hasattr(handler, '__name__') and handler.__name__ == "point_tracking_view_sync":
            bpy.app.handlers.frame_change_post.remove(handler)
    
    bpy.app.handlers.frame_change_post.append(sync_views)
    
    # Add depsgraph handler for scrubbing
    def sync_views_dg(scene, depsgraph):
        sync_views(scene)
    sync_views_dg.__name__ = "point_tracking_view_sync_dg"
    
    for handler in list(bpy.app.handlers.depsgraph_update_post):
        if hasattr(handler, '__name__') and handler.__name__ == "point_tracking_view_sync_dg":
            bpy.app.handlers.depsgraph_update_post.remove(handler)
    
    bpy.app.handlers.depsgraph_update_post.append(sync_views_dg)


def register_viewport_restore_handler(collection_name="PointTrackingViz"):
    """Register handler to restore viewport on load."""
    def restore_viewport_setup(dummy):
        tracking_collection = bpy.data.collections.get(collection_name)
        if not tracking_collection: return
        
        tracking_objects = list(tracking_collection.objects)
        if not tracking_objects: return
        
        print("🔄 Restoring point tracking viewport...")
        setup_dual_viewport(tracking_objects, collection_name)
    
    handler_name = "restore_point_tracking_viewport"
    for handler in list(bpy.app.handlers.load_post):
        if hasattr(handler, '__name__') and handler.__name__ == handler_name:
            bpy.app.handlers.load_post.remove(handler)
            
    restore_viewport_setup.__name__ = handler_name
    bpy.app.handlers.load_post.append(restore_viewport_setup)


def create_viewport_restore_script(collection_name="PointTrackingViz"):
    """Create manual restore script."""
    script_name = "restore_point_tracking_viewport.py"
    if script_name in bpy.data.texts:
        return bpy.data.texts[script_name]
    
    script_text = f'''"""
Restore Point Tracking Dual Viewport (Dual Local View Strategy)
"""
import bpy

def restore_viewports():
    collection_name = "{collection_name}"
    tracking_collection = bpy.data.collections.get(collection_name)
    if not tracking_collection: return
    
    pc_objects = set(tracking_collection.objects)
    all_objects = set(bpy.context.scene.objects)
    scene_objects = list(all_objects - pc_objects)
    tracking_objects = list(pc_objects)
    
    screen = bpy.context.screen
    view3d_areas = sorted([a for a in screen.areas if a.type == 'VIEW_3D'], key=lambda a: a.x)
    
    if len(view3d_areas) < 2:
        area = view3d_areas[0]
        with bpy.context.temp_override(area=area, region=area.regions[0]):
            bpy.ops.screen.area_split(direction='VERTICAL', factor=0.5)
        view3d_areas = sorted([a for a in screen.areas if a.type == 'VIEW_3D'], key=lambda a: a.x)
    
    main_area = view3d_areas[0]
    tracking_area = view3d_areas[-1]
    
    # Setup Left (Scene)
    main_space = main_area.spaces[0]
    main_space.shading.type = 'MATERIAL'
    
    if main_space.local_view:
        with bpy.context.temp_override(area=main_area, region=main_area.regions[-1], space_data=main_space):
            bpy.ops.view3d.localview()
            
    if scene_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in scene_objects: obj.select_set(True)
        with bpy.context.temp_override(area=main_area, region=main_area.regions[-1], space_data=main_space):
            bpy.ops.view3d.localview()
    
    # Setup Right (Tracking)
    tracking_space = tracking_area.spaces[0]
    tracking_space.shading.type = 'SOLID'
    tracking_space.shading.light = 'FLAT'
    tracking_space.shading.color_type = 'VERTEX'
    tracking_space.shading.background_type = 'VIEWPORT'
    tracking_space.shading.background_color = (0.1, 0.1, 0.12)
    
    if tracking_space.local_view:
        with bpy.context.temp_override(area=tracking_area, region=tracking_area.regions[-1], space_data=tracking_space):
            bpy.ops.view3d.localview()
            
    if tracking_objects:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in tracking_objects: obj.select_set(True)
        with bpy.context.temp_override(area=tracking_area, region=tracking_area.regions[-1], space_data=tracking_space):
            bpy.ops.view3d.localview()
            bpy.ops.view3d.view_all()
            
    if bpy.context.scene.camera:
        main_space.region_3d.view_perspective = 'CAMERA'
        tracking_space.region_3d.view_perspective = 'CAMERA'
        
    print("✅ Dual Local View restored!")

if __name__ == "__main__":
    restore_viewports()
'''
    text_block = bpy.data.texts.new(script_name)
    text_block.write(script_text)
    text_block.use_module = True
    return text_block
