"""
Viewport Management Module

Handles dual viewport setup with synchronized views.

Two modes of operation:
1. Simple dual viewport (scene-level): Split viewport with different shading modes
2. Local view dual viewport (annotation): Each viewport shows different object sets

The simple mode is decoupled from annotations and can be used during scene init.
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


def get_space_view3d(area):
    """Get the SpaceView3D from an area."""
    for space in area.spaces:
        if space.type == 'VIEW_3D':
            return space
    return None


def split_viewport_horizontal(factor=0.5):
    """
    Split the current 3D viewport horizontally into two viewports.
    """
    screen = bpy.context.screen
    if not screen:
        return None, None
    
    view3d_areas = get_view3d_areas(screen)
    
    if not view3d_areas:
        return None, None
    
    if len(view3d_areas) >= 2:
        return view3d_areas[0], view3d_areas[-1]
    
    area = view3d_areas[0]
    with bpy.context.temp_override(area=area, region=area.regions[0]):
        try:
            bpy.ops.screen.area_split(direction='VERTICAL', factor=factor)
        except Exception as e:
            print(f"⚠️ Could not split viewport: {e}")
            return None, None
    
    view3d_areas = get_view3d_areas(screen)
    if len(view3d_areas) < 2:
        return None, None
    
    return view3d_areas[0], view3d_areas[-1]


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


def lock_viewport_to_camera(space):
    """Lock a viewport to the scene camera."""
    if space and bpy.context.scene.camera:
        space.region_3d.view_perspective = 'CAMERA'


# =============================================================================
# Simple Dual Viewport (No Local View - Scene Level)
# =============================================================================

def setup_dual_viewport_simple(config=None):
    """
    Setup dual viewport with different shading modes.
    
    This is a simple split that doesn't use local view - both viewports
    show the same scene but with different shading/overlay settings.
    
    Use this for general scene visualization without requiring annotations.
    
    Args:
        config: Optional dict with settings:
            - split_factor: Viewport split ratio (default: 0.5)
            - left_shading: Left viewport shading type ('MATERIAL', 'SOLID', 'RENDERED')
            - right_shading: Right viewport shading type ('MATERIAL', 'SOLID', 'RENDERED')
            - right_color_type: Color type for right viewport if SOLID ('VERTEX', 'MATERIAL', etc.)
            - right_light: Light mode for right SOLID viewport ('FLAT', 'STUDIO', 'MATCAP')
            - sync_views: Whether to sync view rotation between viewports
            - background_color: Background color for right viewport (r, g, b)
    
    Returns:
        dict with 'left_area', 'right_area', 'left_space', 'right_space' keys
        or None if failed
    
    Example:
        # Basic split with default settings
        result = setup_dual_viewport_simple()
        
        # Custom configuration
        result = setup_dual_viewport_simple({
            'left_shading': 'MATERIAL',
            'right_shading': 'SOLID',
            'right_color_type': 'VERTEX',
            'sync_views': True
        })
    """
    if bpy.app.background:
        return None
    
    # Default config
    cfg = {
        'split_factor': 0.5,
        'left_shading': 'MATERIAL',
        'right_shading': 'SOLID',
        'right_color_type': 'VERTEX',
        'right_light': 'FLAT',
        'sync_views': True,
        'background_color': (0.1, 0.1, 0.12)
    }
    if config:
        cfg.update(config)
    
    # Split viewport
    left_area, right_area = split_viewport_horizontal(cfg['split_factor'])
    
    if not left_area or not right_area:
        print("⚠️ Could not split viewport")
        return None
    
    left_space = get_space_view3d(left_area)
    right_space = get_space_view3d(right_area)
    
    # Configure left viewport
    if left_space:
        left_space.shading.type = cfg['left_shading']
    
    # Configure right viewport
    if right_space:
        right_space.shading.type = cfg['right_shading']
        if cfg['right_shading'] == 'SOLID':
            right_space.shading.light = cfg['right_light']
            right_space.shading.color_type = cfg['right_color_type']
        right_space.shading.background_type = 'VIEWPORT'
        right_space.shading.background_color = cfg['background_color']
    
    # Sync views to camera if available
    if bpy.context.scene.camera:
        if left_space:
            lock_viewport_to_camera(left_space)
        if right_space:
            lock_viewport_to_camera(right_space)
    
    # Register view sync handler if requested
    if cfg['sync_views'] and left_space and right_space:
        _register_simple_view_sync(left_space, right_space)
    
    print("✅ Dual viewport setup complete (simple mode)")
    
    return {
        'left_area': left_area,
        'right_area': right_area,
        'left_space': left_space,
        'right_space': right_space
    }


def _register_simple_view_sync(left_space, right_space):
    """Register view sync handler for simple dual viewport."""
    def sync_views(scene):
        if left_space and right_space:
            if left_space.region_3d.view_perspective != 'CAMERA':
                right_space.region_3d.view_rotation = left_space.region_3d.view_rotation.copy()
                right_space.region_3d.view_distance = left_space.region_3d.view_distance
                right_space.region_3d.view_location = left_space.region_3d.view_location.copy()
    
    sync_views.__name__ = "simple_dual_viewport_sync"
    
    # Remove existing handler
    for handler in list(bpy.app.handlers.depsgraph_update_post):
        if hasattr(handler, '__name__') and handler.__name__ == "simple_dual_viewport_sync":
            bpy.app.handlers.depsgraph_update_post.remove(handler)
    
    def sync_views_dg(scene, depsgraph):
        sync_views(scene)
    sync_views_dg.__name__ = "simple_dual_viewport_sync"
    
    bpy.app.handlers.depsgraph_update_post.append(sync_views_dg)


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


def enter_local_view(area, objects):
    """
    Enter local view in a specific viewport area with given objects.
    Handles exiting existing local view first.
    """
    if not area:
        return False
        
    space = get_space_view3d(area)
    if not space:
        return False
        
    # 1. Exit Local View if active
    if space.local_view:
        with bpy.context.temp_override(area=area, region=area.regions[-1], space_data=space):
            bpy.ops.view3d.localview()
    
    if not objects:
        return False
        
    # 2. Select objects
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        if obj and obj.name in bpy.data.objects:
            obj.select_set(True)
    
    # 3. Enter Local View
    with bpy.context.temp_override(area=area, region=area.regions[-1], space_data=space):
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
