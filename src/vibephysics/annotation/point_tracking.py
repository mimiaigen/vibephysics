"""
Point Tracking Visualization Module

Creates 3D point cloud animation tracking all object meshes 
with evenly sampled surface points, each with unique colors.
"""

import bpy
import math
import random
from mathutils import Vector, Color

from . import base
from . import viewport


def sample_mesh_surface_points(obj, num_points=50, seed=None):
    """
    Evenly sample points on the surface of a mesh object.
    
    Args:
        obj: Blender mesh object to sample from
        num_points: Number of points to sample
        seed: Random seed for reproducibility
        
    Returns:
        List of local-space Vector positions
    """
    if seed is not None:
        random.seed(seed)
    
    # Get evaluated mesh (with modifiers applied)
    depsgraph = base.get_depsgraph()
    if not depsgraph:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        
    obj_eval = obj.evaluated_get(depsgraph)
    mesh = obj_eval.to_mesh()
    
    if not mesh.polygons:
        obj_eval.to_mesh_clear()
        return []
    
    # Calculate face areas for weighted sampling
    face_areas = []
    total_area = 0.0
    
    for poly in mesh.polygons:
        area = poly.area
        face_areas.append(area)
        total_area += area
    
    if total_area == 0:
        obj_eval.to_mesh_clear()
        return []
    
    # Normalize areas to create probability distribution
    face_weights = [a / total_area for a in face_areas]
    
    # Sample points
    points = []
    
    for _ in range(num_points):
        # Weighted random face selection
        r = random.random()
        cumulative = 0.0
        face_idx = 0
        
        for i, weight in enumerate(face_weights):
            cumulative += weight
            if r <= cumulative:
                face_idx = i
                break
        
        poly = mesh.polygons[face_idx]
        
        # Get face vertices
        verts = [mesh.vertices[vi].co.copy() for vi in poly.vertices]
        
        if len(verts) >= 3:
            # Random barycentric coordinates for triangles
            v0, v1, v2 = verts[0], verts[1], verts[2]
            
            # Random point in triangle using barycentric coordinates
            r1, r2 = random.random(), random.random()
            if r1 + r2 > 1:
                r1, r2 = 1 - r1, 1 - r2
            
            point = v0 + r1 * (v1 - v0) + r2 * (v2 - v0)
            points.append(point)
    
    obj_eval.to_mesh_clear()
    return points


def generate_distinct_colors(num_colors, saturation=0.8, value=0.9):
    """
    Generate visually distinct colors using HSV color space.
    
    Args:
        num_colors: Number of colors to generate
        saturation: Color saturation (0-1)
        value: Color brightness (0-1)
        
    Returns:
        List of (R, G, B, A) tuples
    """
    colors = []
    
    for i in range(num_colors):
        # Distribute hues evenly with golden ratio offset for better separation
        hue = (i * 0.618033988749895) % 1.0
        
        # Convert HSV to RGB
        c = Color()
        c.hsv = (hue, saturation, value)
        
        colors.append((c.r, c.g, c.b, 1.0))
    
    return colors


def create_point_cloud_tracker(tracked_objects, points_per_object=50, point_size=0.03, 
                                collection_name=None):
    """
    Create a point cloud mesh that tracks points on multiple objects.
    
    Args:
        tracked_objects: List of Blender objects to track
        points_per_object: Number of sample points per object
        point_size: Size of each point (icosphere radius)
        collection_name: Name of collection to put point cloud in
        
    Returns:
        The point cloud object and tracking data
    """
    if not tracked_objects:
        print("⚠️ No objects to track for point cloud")
        return None, None
    
    # Ensure collection exists
    collection = base.ensure_collection(collection_name)
    
    # Sample points from each object and store tracking data
    tracking_data = []
    all_points = []
    all_colors = []
    
    total_points = len(tracked_objects) * points_per_object
    colors = generate_distinct_colors(total_points)
    color_idx = 0
    
    for obj_idx, obj in enumerate(tracked_objects):
        # Sample points on object surface
        local_points = sample_mesh_surface_points(obj, points_per_object, seed=obj_idx)
        
        for local_pos in local_points:
            tracking_data.append({
                'object': obj,
                'local_pos': local_pos.copy(),
                'color': colors[color_idx]
            })
            
            # Transform to world space for initial position
            world_pos = obj.matrix_world @ local_pos
            all_points.append(world_pos)
            all_colors.append(colors[color_idx])
            color_idx += 1
    
    if not all_points:
        print("⚠️ No points sampled from objects")
        return None, None
    
    # Create point cloud mesh using small icospheres for each point
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=point_size, location=(0, 0, 0))
    template = bpy.context.active_object
    template_mesh = template.data.copy()
    template_verts = len(template_mesh.vertices)
    bpy.data.objects.remove(template, do_unlink=True)
    
    # Create new mesh for all points
    mesh = bpy.data.meshes.new("PointCloudMesh")
    
    # Build mesh data
    vertices = []
    faces = []
    
    for pt_idx, (world_pos, color) in enumerate(zip(all_points, all_colors)):
        base_vert_idx = len(vertices)
        
        # Add icosphere vertices offset to world position
        for v in template_mesh.vertices:
            new_pos = world_pos + Vector(v.co)
            vertices.append(new_pos)
        
        # Add icosphere faces with offset indices
        for poly in template_mesh.polygons:
            face = tuple(base_vert_idx + vi for vi in poly.vertices)
            faces.append(face)
    
    # Create mesh from vertices and faces
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    
    # Add vertex colors
    if not mesh.vertex_colors:
        mesh.vertex_colors.new(name="PointColors")
    
    color_layer = mesh.vertex_colors["PointColors"]
    
    # Assign colors to each vertex via loop colors
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            vert_idx = mesh.loops[loop_idx].vertex_index
            point_idx = vert_idx // template_verts
            if point_idx < len(all_colors):
                color_layer.data[loop_idx].color = all_colors[point_idx]
    
    # Create object
    point_cloud_obj = bpy.data.objects.new("PointCloudTracker", mesh)
    collection.objects.link(point_cloud_obj)
    
    # Create material with vertex colors using base utility
    mat = base.create_vertex_color_material(
        "PointCloudMaterial",
        color_layer_name="PointColors",
        strength=2.0
    )
    point_cloud_obj.data.materials.append(mat)
    
    # Clean up template mesh
    bpy.data.meshes.remove(template_mesh)
    
    # Store tracking data on the object for frame handler
    point_cloud_obj["tracking_data_count"] = len(tracking_data)
    point_cloud_obj["points_per_sphere"] = template_verts
    point_cloud_obj["point_size"] = point_size
    point_cloud_obj["annotation_type"] = "point_tracking"
    
    # Store object references and local positions as custom properties
    tracking_info = []
    for td in tracking_data:
        tracking_info.append({
            'obj_name': td['object'].name,
            'local_pos': list(td['local_pos']),
        })
    
    # Store as JSON string in custom property
    import json
    point_cloud_obj["tracking_info"] = json.dumps(tracking_info)
    
    print(f"✅ Created point cloud with {len(all_points)} tracked points")
    
    return point_cloud_obj, tracking_data


def update_point_cloud_positions(point_cloud_obj, scene=None):
    """
    Update point cloud positions based on tracked objects' transforms.
    Called on each frame change.
    """
    import json
    
    if not point_cloud_obj or "tracking_info" not in point_cloud_obj:
        return
    
    tracking_info = json.loads(point_cloud_obj["tracking_info"])
    verts_per_point = point_cloud_obj["points_per_sphere"]
    
    mesh = point_cloud_obj.data
    
    # Get evaluated depsgraph for physics
    depsgraph = base.get_depsgraph()
        
    # Update vertex positions
    for pt_idx, info in enumerate(tracking_info):
        obj_name = info['obj_name']
        local_pos = Vector(info['local_pos'])
        
        # Use evaluated object from depsgraph if available (during animation)
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            continue
            
        # Try to get evaluated object for correct physics position
        world_matrix = obj.matrix_world
        
        if depsgraph:
            obj_eval = base.get_evaluated_object(obj, depsgraph)
            world_matrix = obj_eval.matrix_world
        
        # Get world position of the local point
        world_pos = world_matrix @ local_pos
        
        # Update all vertices of this point's icosphere
        base_vert_idx = pt_idx * verts_per_point
        
        # Calculate current centroid
        if base_vert_idx + verts_per_point <= len(mesh.vertices):
            centroid = Vector((0, 0, 0))
            for i in range(verts_per_point):
                centroid += mesh.vertices[base_vert_idx + i].co
            centroid /= verts_per_point
            
            # Move all vertices by the delta
            delta = world_pos - centroid
            for i in range(verts_per_point):
                mesh.vertices[base_vert_idx + i].co += delta
    
    mesh.update()
    
    # Force redraw of all 3D viewports to show the updated mesh
    # Only in UI mode
    if not bpy.app.background:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()


def create_embedded_tracking_script():
    """
    Create an embedded script that runs when the blend file is opened.
    This ensures the point cloud updates during animation playback.
    """
    script_name = "point_cloud_driver.py"
    if script_name in bpy.data.texts:
        return bpy.data.texts[script_name]
        
    script_text = '''"""
Point Cloud Tracking Driver
This script is automatically generated to animate the point cloud.
It runs on file load to register the frame change handler.
"""
import bpy
import json
from mathutils import Vector

def pointcloud_update_positions(scene):
    """Update point cloud positions using evaluated dependency graph."""
    point_cloud_obj = bpy.data.objects.get("PointCloudTracker")
    if not point_cloud_obj or "tracking_info" not in point_cloud_obj:
        return
    
    # Only update if we can get the depsgraph (prevents crashes in some contexts)
    try:
        depsgraph = bpy.context.evaluated_depsgraph_get()
    except:
        return

    tracking_info = json.loads(point_cloud_obj["tracking_info"])
    verts_per_point = point_cloud_obj["points_per_sphere"]
    mesh = point_cloud_obj.data
    
    # Optimize: Cache object references
    objects_map = {obj.name: obj for obj in scene.objects if obj.name in [t['obj_name'] for t in tracking_info]}
    
    for pt_idx, info in enumerate(tracking_info):
        obj_name = info['obj_name']
        if obj_name not in objects_map:
            continue
            
        obj = objects_map[obj_name]
        
        # Get physics position from evaluated object
        try:
            obj_eval = obj.evaluated_get(depsgraph)
            world_matrix = obj_eval.matrix_world
        except:
            world_matrix = obj.matrix_world
            
        local_pos = Vector(info['local_pos'])
        world_pos = world_matrix @ local_pos
        
        # Update vertices
        base_vert_idx = pt_idx * verts_per_point
        
        # Move whole icosphere
        if base_vert_idx + verts_per_point <= len(mesh.vertices):
            # Calculate current centroid to move relative
            centroid = Vector((0,0,0))
            for i in range(verts_per_point):
                centroid += mesh.vertices[base_vert_idx + i].co
            centroid /= verts_per_point
            
            delta = world_pos - centroid
            
            for i in range(verts_per_point):
                mesh.vertices[base_vert_idx + i].co += delta

    mesh.update()
    
    # Tag redraw
    if not bpy.app.background:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

def pointcloud_frame_handler(scene):
    pointcloud_update_positions(scene)

# Register
def register():
    # Clean old handlers with this specific name
    handlers = bpy.app.handlers.frame_change_post
    for h in list(handlers):
        if hasattr(h, '__name__') and h.__name__ == 'pointcloud_frame_handler':
            handlers.remove(h)
    handlers.append(pointcloud_frame_handler)
    print("✅ Point Cloud Tracking Handler Registered")
    
    # Force initial update for current frame
    pointcloud_update_positions(bpy.context.scene)

# Auto-register on load
register()
'''
    return base.create_embedded_script(script_name, script_text)


def register_frame_handler(point_cloud_obj):
    """
    Register a frame change handler to update point cloud positions.
    """
    # Create the embedded script so it works when file is re-opened
    create_embedded_tracking_script()
    
    # Ensure it's marked as module to run on load
    if "point_cloud_driver.py" in bpy.data.texts:
        bpy.data.texts["point_cloud_driver.py"].use_module = True
    
    def pointcloud_frame_handler(scene):
        # Re-fetch object to ensure it's valid
        if point_cloud_obj and point_cloud_obj.name in bpy.data.objects:
            pc_obj = bpy.data.objects[point_cloud_obj.name]
            update_point_cloud_positions(pc_obj, scene)
    
    base.register_frame_handler(pointcloud_frame_handler, "pointcloud_frame_handler")
    print(f"✅ Registered frame handler for point cloud updates")


def create_point_tracking_camera(point_cloud_obj, distance=40.0, angle=45.0, 
                                  collection_name=None):
    """
    Create a dedicated camera for the point tracking view.
    
    Args:
        point_cloud_obj: The point cloud object to track
        distance: Camera distance from center
        angle: Camera elevation angle in degrees
        collection_name: Collection to put camera in
    """
    collection = base.ensure_collection(collection_name)
    
    # Create camera
    angle_rad = math.radians(angle)
    cam_x = distance * math.cos(angle_rad) * 0.7
    cam_y = -distance * math.cos(angle_rad) * 0.7
    cam_z = distance * math.sin(angle_rad)
    
    bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
    tracking_cam = bpy.context.active_object
    tracking_cam.name = "PointTrackingCamera"
    
    # Move to tracking collection
    for coll in tracking_cam.users_collection:
        coll.objects.unlink(tracking_cam)
    collection.objects.link(tracking_cam)
    
    # Point at origin
    tracking_cam.rotation_euler = (math.radians(90 - angle), 0, math.radians(-45))
    
    # Add track-to constraint
    if point_cloud_obj:
        constraint = tracking_cam.constraints.new(type='TRACK_TO')
        constraint.target = point_cloud_obj
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'
    
    # Camera settings
    tracking_cam.data.type = 'ORTHO'
    tracking_cam.data.ortho_scale = 30.0
    
    print(f"  - Created PointTrackingCamera at {tracking_cam.location}")


def setup_point_tracking_visualization(tracked_objects, points_per_object=30, 
                                        setup_viewport=True, collection_name=None):
    """
    Main entry point for setting up point tracking visualization.
    
    Args:
        tracked_objects: List of objects to track (e.g., floating spheres)
        points_per_object: Number of surface sample points per object
        setup_viewport: Whether to create a dual viewport setup
        collection_name: Collection to use
        
    Returns:
        point_cloud_obj: The created point cloud object
    """
    print("Setting up Point Tracking Visualization...")
    
    # Filter to only mesh objects
    mesh_objects = [obj for obj in tracked_objects if obj.type == 'MESH']
    
    if not mesh_objects:
        print("⚠️ No mesh objects provided for tracking")
        return None
    
    print(f"  - Tracking {len(mesh_objects)} objects with {points_per_object} points each")
    
    # Create point cloud tracker
    point_cloud_obj, tracking_data = create_point_cloud_tracker(
        mesh_objects, 
        points_per_object=points_per_object,
        point_size=0.05,
        collection_name=collection_name
    )
    
    if not point_cloud_obj:
        return None
    
    # Register frame change handler for animation
    register_frame_handler(point_cloud_obj)
    
    # Get tracking collection objects
    coll_name = collection_name or base.DEFAULT_COLLECTION_NAME
    tracking_collection = bpy.data.collections.get(coll_name)
    tracking_objects = list(tracking_collection.objects) if tracking_collection else []
    
    # Setup dual viewport if requested and running in UI mode
    if setup_viewport and not bpy.app.background:
        viewport.setup_dual_viewport(tracking_objects, coll_name)
        viewport.register_viewport_restore_handler(coll_name)
        viewport.create_viewport_restore_script(coll_name)
    else:
        print("  - Skipping viewport setup (background mode or disabled)")
        if tracking_collection:
            tracking_collection.hide_render = True
            print("  - Point cloud hidden from renders")
        viewport.create_viewport_restore_script(coll_name)
    
    # Add point cloud camera for dedicated view
    create_point_tracking_camera(point_cloud_obj, collection_name=coll_name)
    
    print("✅ Point Tracking Visualization Ready!")
    print(f"   - Total tracked points: {len(tracking_data) if tracking_data else 0}")
    print(f"   - View the '{coll_name}' collection for point cloud")
    print("   - Use 'PointTrackingCamera' for dedicated tracking view")
    
    return point_cloud_obj


def bake_point_cloud_animation(point_cloud_obj, start_frame, end_frame):
    """
    Bake point cloud animation by keyframing vertex positions.
    This is useful for export or when frame handlers won't work.
    
    Note: This creates shape keys for each frame, which can be memory intensive.
    """
    import json
    
    if not point_cloud_obj or "tracking_info" not in point_cloud_obj:
        print("⚠️ Cannot bake: invalid point cloud object")
        return
    
    print(f"Baking point cloud animation from frame {start_frame} to {end_frame}...")
    
    mesh = point_cloud_obj.data
    tracking_info = json.loads(point_cloud_obj["tracking_info"])
    verts_per_point = point_cloud_obj["points_per_sphere"]
    
    # Create basis shape key
    if not mesh.shape_keys:
        point_cloud_obj.shape_key_add(name="Basis")
    
    basis = mesh.shape_keys.key_blocks["Basis"]
    
    for frame in range(start_frame, end_frame + 1):
        bpy.context.scene.frame_set(frame)
        
        # Create shape key for this frame
        sk_name = f"Frame_{frame:04d}"
        sk = point_cloud_obj.shape_key_add(name=sk_name)
        
        # Update positions
        for pt_idx, info in enumerate(tracking_info):
            obj_name = info['obj_name']
            local_pos = Vector(info['local_pos'])
            
            obj = bpy.data.objects.get(obj_name)
            if not obj:
                continue
            
            world_pos = obj.matrix_world @ local_pos
            base_vert_idx = pt_idx * verts_per_point
            
            if base_vert_idx + verts_per_point <= len(mesh.vertices):
                centroid = Vector((0, 0, 0))
                for i in range(verts_per_point):
                    centroid += Vector(basis.data[base_vert_idx + i].co)
                centroid /= verts_per_point
                
                delta = world_pos - centroid
                for i in range(verts_per_point):
                    sk.data[base_vert_idx + i].co = Vector(basis.data[base_vert_idx + i].co) + delta
        
        # Keyframe shape key value
        sk.value = 0.0
        sk.keyframe_insert(data_path="value", frame=frame - 1)
        sk.value = 1.0
        sk.keyframe_insert(data_path="value", frame=frame)
        sk.value = 0.0
        sk.keyframe_insert(data_path="value", frame=frame + 1)
        
        if frame % 25 == 0:
            print(f"  - Baked frame {frame}/{end_frame}")
    
    print(f"✅ Baked {end_frame - start_frame + 1} frames of point cloud animation")
