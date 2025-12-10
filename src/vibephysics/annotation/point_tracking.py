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
from ..setup import viewport
from ..setup.importer import ensure_collection


# Hidden position for frustum-culled points (far below scene)
HIDDEN_POSITION = Vector((0, 0, -10000))

# Frustum culling modes
FRUSTUM_MODE_ALL = "all"           # Show all points (no culling)
FRUSTUM_MODE_HIGHLIGHT = "highlight"  # Show all, highlight in-frustum as red
FRUSTUM_MODE_ONLY = "frustum_only"    # Only show points in frustum


def is_point_in_camera_view(point_world, camera, scene, margin=0.0, far_distance=None):
    """
    Check if a world-space point is within the camera's view frustum.
    
    Args:
        point_world: Vector - world space position of the point
        camera: Camera object
        scene: Current scene
        margin: Extends frustum bounds (0.0 = exact frustum, 0.5 = 50% extra)
        far_distance: Maximum distance from camera (None = no limit)
        
    Returns:
        True if point is in camera view frustum
    """
    from bpy_extras.object_utils import world_to_camera_view
    
    # Convert to normalized device coordinates
    # co_ndc.x, co_ndc.y are in [0,1] if in view, co_ndc.z is distance from camera
    co_ndc = world_to_camera_view(scene, camera, point_world)
    
    # Check X/Y bounds (in view)
    in_xy_bounds = (
        -margin < co_ndc.x < (1 + margin) and
        -margin < co_ndc.y < (1 + margin)
    )
    
    # Check depth (in front of camera, within far distance)
    in_depth = co_ndc.z > 0  # In front of camera
    
    if far_distance is not None and in_depth:
        # Calculate actual distance from camera to point
        cam_pos = camera.matrix_world.translation
        distance = (point_world - cam_pos).length
        in_depth = distance <= far_distance
    
    return in_xy_bounds and in_depth


def is_object_in_camera_view(obj, camera, scene, margin=0.0, far_distance=None):
    """
    Check if an object's center is within the camera's view frustum.
    (Wrapper for backward compatibility)
    """
    obj_center = obj.matrix_world.translation
    return is_point_in_camera_view(obj_center, camera, scene, margin, far_distance)


def create_frustum_wireframe(camera, scene, near=0.5, far=50.0, collection_name=None):
    """
    Create a wireframe mesh representing the camera's view frustum.
    
    Args:
        camera: Camera object
        scene: Current scene
        near: Near clip distance
        far: Far clip distance for visualization
        collection_name: Collection to add frustum to
        
    Returns:
        The frustum wireframe object
    """
    cam_data = camera.data
    
    # Get render aspect ratio
    render_x = scene.render.resolution_x
    render_y = scene.render.resolution_y
    aspect = render_x / render_y
    
    if cam_data.type == 'PERSP':
        # Get the correct FOV based on sensor_fit (matches world_to_camera_view behavior)
        # cam_data.angle is the horizontal or vertical FOV depending on sensor_fit
        sensor_fit = cam_data.sensor_fit
        
        if sensor_fit == 'AUTO':
            # AUTO uses horizontal for landscape, vertical for portrait
            if aspect >= 1.0:
                sensor_fit = 'HORIZONTAL'
            else:
                sensor_fit = 'VERTICAL'
        
        if sensor_fit == 'HORIZONTAL':
            # angle is horizontal FOV
            fov_h = cam_data.angle
            half_width_near = near * math.tan(fov_h / 2)
            half_height_near = half_width_near / aspect
            half_width_far = far * math.tan(fov_h / 2)
            half_height_far = half_width_far / aspect
        else:  # VERTICAL
            # angle is vertical FOV
            fov_v = cam_data.angle
            half_height_near = near * math.tan(fov_v / 2)
            half_width_near = half_height_near * aspect
            half_height_far = far * math.tan(fov_v / 2)
            half_width_far = half_height_far * aspect
    else:
        # Orthographic camera
        half_height_near = half_height_far = cam_data.ortho_scale / 2
        half_width_near = half_width_far = half_height_near * aspect
    
    # Frustum corners in camera local space (camera looks down -Z)
    # Near plane corners
    n_tl = Vector((-half_width_near, half_height_near, -near))
    n_tr = Vector((half_width_near, half_height_near, -near))
    n_bl = Vector((-half_width_near, -half_height_near, -near))
    n_br = Vector((half_width_near, -half_height_near, -near))
    
    # Far plane corners
    f_tl = Vector((-half_width_far, half_height_far, -far))
    f_tr = Vector((half_width_far, half_height_far, -far))
    f_bl = Vector((-half_width_far, -half_height_far, -far))
    f_br = Vector((half_width_far, -half_height_far, -far))
    
    # Create mesh
    vertices = [n_tl, n_tr, n_br, n_bl, f_tl, f_tr, f_br, f_bl]
    
    # Edges: near plane, far plane, connecting edges
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),  # Near plane
        (4, 5), (5, 6), (6, 7), (7, 4),  # Far plane
        (0, 4), (1, 5), (2, 6), (3, 7),  # Connecting edges
    ]
    
    mesh = bpy.data.meshes.new("FrustumWireframe")
    mesh.from_pydata(vertices, edges, [])
    mesh.update()
    
    # Create object
    frustum_obj = bpy.data.objects.new("CameraFrustum", mesh)
    
    # Add to collection
    collection = ensure_collection(collection_name or base.DEFAULT_COLLECTION_NAME)
    collection.objects.link(frustum_obj)
    
    # Create wireframe material (bright cyan)
    mat = bpy.data.materials.new(name="FrustumMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (0.0, 1.0, 1.0, 1.0)  # Cyan
    emission.inputs['Strength'].default_value = 5.0
    output = nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    frustum_obj.data.materials.append(mat)
    
    # Display settings
    frustum_obj.display_type = 'WIRE'
    frustum_obj.show_in_front = True
    
    # Store reference to camera
    frustum_obj["tracked_camera"] = camera.name
    frustum_obj["frustum_far"] = far
    frustum_obj["annotation_type"] = "frustum"
    
    # Parent to nothing (will be updated via handler)
    # Initial transform
    frustum_obj.matrix_world = camera.matrix_world.copy()
    
    print(f"✅ Created frustum wireframe for camera '{camera.name}'")
    
    return frustum_obj


def update_frustum_wireframe(frustum_obj, scene=None):
    """
    Update frustum wireframe to match current ACTIVE camera position/orientation.
    Always follows scene.camera (whichever camera is currently active).
    """
    if not frustum_obj:
        return
    
    if scene is None:
        scene = bpy.context.scene
    
    # Always follow the active scene camera
    camera = scene.camera
    if not camera:
        return
    
    # Update transform to match camera
    frustum_obj.matrix_world = camera.matrix_world.copy()


def setup_frustum_visualization(camera=None, far_distance=None, collection_name=None):
    """
    Setup frustum visualization for a camera.
    
    Args:
        camera: Camera to visualize (defaults to scene camera)
        far_distance: How far to extend the frustum visualization (None = read from PointCloudTracker)
        collection_name: Collection for the frustum
        
    Returns:
        The frustum wireframe object
    """
    scene = bpy.context.scene
    
    if camera is None:
        camera = scene.camera
    
    if not camera:
        print("⚠️ No camera found for frustum visualization")
        return None
    
    # Auto-read far_distance from PointCloudTracker if not provided
    if far_distance is None:
        pc_obj = bpy.data.objects.get("PointCloudTracker")
        if pc_obj:
            far_distance = pc_obj.get("frustum_far_distance", 20.0)
        else:
            far_distance = 20.0
    
    # Create frustum wireframe
    frustum_obj = create_frustum_wireframe(
        camera, scene, 
        near=0.5, 
        far=far_distance,
        collection_name=collection_name
    )
    
    # Register frame handler to update frustum
    def frustum_update_handler(scene):
        if frustum_obj and frustum_obj.name in bpy.data.objects:
            update_frustum_wireframe(bpy.data.objects[frustum_obj.name], scene)
    
    base.register_frame_handler(frustum_update_handler, "frustum_update_handler")
    
    return frustum_obj


def sample_mesh_surface_points(obj, num_points=50, seed=None):
    """
    Evenly sample points on the surface of a mesh object.
    
    Uses proper triangulation for uniform distribution across all polygon types
    (triangles, quads, n-gons). Points are distributed proportionally to 
    triangle areas for true uniform surface sampling.
    
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
    
    # FIXED: Use preserve_all_data_layers=True and depsgraph parameter
    # to ensure we get the complete mesh, not viewport-optimized version
    mesh = obj_eval.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    
    if not mesh or not mesh.polygons:
        if mesh:
            obj_eval.to_mesh_clear()
        return []
    
    # Build list of triangles with their areas
    # For n-gons, use fan triangulation from first vertex
    # This ensures all parts of quads/n-gons are covered uniformly
    triangles = []  # List of (v0, v1, v2, area) tuples
    total_area = 0.0
    
    for poly in mesh.polygons:
        verts = [mesh.vertices[vi].co.copy() for vi in poly.vertices]
        
        if len(verts) < 3:
            continue
        
        # Fan triangulation: split polygon into triangles from first vertex
        # For a quad with vertices [A, B, C, D], this creates triangles:
        #   - (A, B, C)
        #   - (A, C, D)
        # This covers the entire polygon uniformly
        v0 = verts[0]
        for i in range(1, len(verts) - 1):
            v1 = verts[i]
            v2 = verts[i + 1]
            
            # Calculate triangle area using cross product
            edge1 = v1 - v0
            edge2 = v2 - v0
            area = edge1.cross(edge2).length * 0.5
            
            if area > 0:
                triangles.append((v0.copy(), v1.copy(), v2.copy(), area))
                total_area += area
    
    if total_area == 0 or not triangles:
        obj_eval.to_mesh_clear()
        return []
    
    # Build cumulative distribution for weighted sampling
    cumulative_weights = []
    cumulative = 0.0
    for tri in triangles:
        cumulative += tri[3] / total_area
        cumulative_weights.append(cumulative)
    
    # Sample points
    points = []
    
    for _ in range(num_points):
        # Weighted random triangle selection using binary search
        r = random.random()
        
        # Binary search for the triangle
        lo, hi = 0, len(cumulative_weights) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if cumulative_weights[mid] < r:
                lo = mid + 1
            else:
                hi = mid
        tri_idx = lo
        
        v0, v1, v2, _ = triangles[tri_idx]
            
            # Random point in triangle using barycentric coordinates
        # Using sqrt for uniform distribution in triangle
        r1 = random.random()
        r2 = random.random()
        sqrt_r1 = math.sqrt(r1)
        
        # Barycentric coordinates that give uniform distribution
        u = 1 - sqrt_r1
        v = r2 * sqrt_r1
        
        point = u * v0 + v * v1 + (1 - u - v) * v2
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
    collection = ensure_collection(collection_name or base.DEFAULT_COLLECTION_NAME)
    
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


def update_point_cloud_positions(point_cloud_obj, scene=None, frustum_mode=FRUSTUM_MODE_ALL):
    """
    Update point cloud positions based on tracked objects' transforms.
    Called on each frame change.
    
    Args:
        point_cloud_obj: The point cloud tracker object
        scene: Current scene (optional, defaults to context.scene)
        frustum_mode: One of FRUSTUM_MODE_ALL, FRUSTUM_MODE_HIGHLIGHT, FRUSTUM_MODE_ONLY
    """
    import json
    
    if not point_cloud_obj or "tracking_info" not in point_cloud_obj:
        return
    
    if scene is None:
        scene = bpy.context.scene
    
    tracking_info = json.loads(point_cloud_obj["tracking_info"])
    verts_per_point = point_cloud_obj["points_per_sphere"]
    
    mesh = point_cloud_obj.data
    
    # Get evaluated depsgraph for physics
    depsgraph = base.get_depsgraph()
    
    # Get camera for frustum checks (for highlight and frustum_only modes)
    camera = scene.camera if frustum_mode != FRUSTUM_MODE_ALL else None
    
    # Get frustum far distance from stored property or from CameraFrustum object
    far_distance = point_cloud_obj.get("frustum_far_distance", None)
    if far_distance is None:
        frustum_obj = bpy.data.objects.get("CameraFrustum")
        if frustum_obj:
            far_distance = frustum_obj.get("frustum_far", None)
    
    # For highlight mode, we need to update vertex colors
    color_layer = None
    if frustum_mode == FRUSTUM_MODE_HIGHLIGHT and mesh.vertex_colors:
        color_layer = mesh.vertex_colors.get("PointColors")
    
    # Track per-point frustum status for color updates
    point_in_frustum = []
        
    # Update vertex positions (check each POINT individually, not per object)
    for pt_idx, info in enumerate(tracking_info):
        obj_name = info['obj_name']
        local_pos = Vector(info['local_pos'])
        
        # Use evaluated object from depsgraph if available (during animation)
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            point_in_frustum.append(False)
            continue
            
        # Try to get evaluated object for correct physics position
        world_matrix = obj.matrix_world
        
        if depsgraph:
            obj_eval = base.get_evaluated_object(obj, depsgraph)
            world_matrix = obj_eval.matrix_world
        
        # Calculate world position of this point
        world_pos = world_matrix @ local_pos
        
        # Check if THIS POINT is in frustum (not the object center)
        if camera:
            is_in_frustum = is_point_in_camera_view(
                world_pos, camera, scene, 
                margin=0.0,  # No margin - strict frustum bounds
                far_distance=far_distance
            )
        else:
            is_in_frustum = True
        
        point_in_frustum.append(is_in_frustum)
        
        # Determine if point should be visible based on mode
        if frustum_mode == FRUSTUM_MODE_ONLY:
            is_visible = is_in_frustum
        else:
            is_visible = True  # ALL and HIGHLIGHT show all points
        
        # Get final position (or hidden position if not visible)
        if not is_visible:
            world_pos = HIDDEN_POSITION
        
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
        
    # Update colors for highlight mode (optimized batch update)
    if frustum_mode == FRUSTUM_MODE_HIGHLIGHT and color_layer:
        # Use per-point frustum status (already computed above)
        point_colors = []
        for is_in_frustum in point_in_frustum:
            if is_in_frustum:
                point_colors.append((1.0, 0.0, 0.0, 1.0))  # Red - in frustum
            else:
                point_colors.append((0.3, 0.3, 0.3, 1.0))  # Gray - outside frustum
        
        # Single pass through all loops (much faster)
        for loop in mesh.loops:
            point_idx = loop.vertex_index // verts_per_point
            if point_idx < len(point_colors):
                color_layer.data[loop.index].color = point_colors[point_idx]
    
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
Point Cloud Tracking Driver - Supports 3 frustum modes:
  - "all": Show all points (no culling)
  - "highlight": Show all, in-frustum points turn red
  - "frustum_only": Only show points in frustum
"""
import bpy
import json
from mathutils import Vector

HIDDEN_POSITION = Vector((0, 0, -10000))

def is_point_in_frustum(point_world, camera, scene, margin=0.0, far_distance=None):
    from bpy_extras.object_utils import world_to_camera_view
    co_ndc = world_to_camera_view(scene, camera, point_world)
    in_xy = (-margin < co_ndc.x < (1 + margin) and -margin < co_ndc.y < (1 + margin))
    in_depth = co_ndc.z > 0
    if far_distance is not None and in_depth:
        distance = (point_world - camera.matrix_world.translation).length
        in_depth = distance <= far_distance
    return in_xy and in_depth

def update_frustum_wireframe(scene):
    frustum_obj = bpy.data.objects.get("CameraFrustum")
    if frustum_obj and scene.camera:
        frustum_obj.matrix_world = scene.camera.matrix_world.copy()

def pointcloud_update_positions(scene):
    pc = bpy.data.objects.get("PointCloudTracker")
    if not pc or "tracking_info" not in pc:
        return
    try:
        depsgraph = bpy.context.evaluated_depsgraph_get()
    except:
        return

    tracking_info = json.loads(pc["tracking_info"])
    verts_per_point = pc["points_per_sphere"]
    mesh = pc.data
    frustum_mode = pc.get("frustum_mode", "all")
    
    camera = scene.camera if frustum_mode != "all" else None
    far_distance = pc.get("frustum_far_distance", None)
    if far_distance is None:
        frustum_obj = bpy.data.objects.get("CameraFrustum")
        if frustum_obj:
            far_distance = frustum_obj.get("frustum_far", None)
    
    color_layer = mesh.vertex_colors.get("PointColors") if frustum_mode == "highlight" else None
    
    obj_names = set(t['obj_name'] for t in tracking_info)
    objects_map = {o.name: o for o in scene.objects if o.name in obj_names}
    point_frustum = []  # Per-point frustum status
    
    for pt_idx, info in enumerate(tracking_info):
        obj_name = info['obj_name']
        if obj_name not in objects_map:
            point_frustum.append(False)
            continue
        obj = objects_map[obj_name]
        
        try:
            world_matrix = obj.evaluated_get(depsgraph).matrix_world
        except:
            world_matrix = obj.matrix_world
        
        # Calculate world position of THIS POINT
        world_pos = world_matrix @ Vector(info['local_pos'])
        
        # Check if THIS POINT is in frustum (per-point, not per-object)
        if camera:
            in_frustum = is_point_in_frustum(world_pos, camera, scene, 0.0, far_distance)
        else:
            in_frustum = True
        point_frustum.append(in_frustum)
        
        is_visible = in_frustum if frustum_mode == "frustum_only" else True
        if not is_visible:
            world_pos = HIDDEN_POSITION
        
        base_idx = pt_idx * verts_per_point
        
        if base_idx + verts_per_point <= len(mesh.vertices):
            centroid = sum((mesh.vertices[base_idx + i].co for i in range(verts_per_point)), Vector()) / verts_per_point
            delta = world_pos - centroid
            for i in range(verts_per_point):
                mesh.vertices[base_idx + i].co += delta
        
    # Update colors for highlight mode (per-point)
    if frustum_mode == "highlight" and color_layer:
        point_colors = [(1.0, 0.0, 0.0, 1.0) if in_f else (0.3, 0.3, 0.3, 1.0) for in_f in point_frustum]
        for loop in mesh.loops:
            pt_idx = loop.vertex_index // verts_per_point
            if pt_idx < len(point_colors):
                color_layer.data[loop.index].color = point_colors[pt_idx]

    mesh.update()
    if not bpy.app.background:
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                if a.type == 'VIEW_3D':
                    a.tag_redraw()

def pointcloud_frame_handler(scene):
    update_frustum_wireframe(scene)
    pointcloud_update_positions(scene)

def register():
    for h in list(bpy.app.handlers.frame_change_post):
        if hasattr(h, '__name__') and h.__name__ == 'pointcloud_frame_handler':
            bpy.app.handlers.frame_change_post.remove(h)
    bpy.app.handlers.frame_change_post.append(pointcloud_frame_handler)
    pc = bpy.data.objects.get("PointCloudTracker")
    mode = pc.get("frustum_mode", "all") if pc else "all"
    print(f"✅ Point Cloud Handler Registered (mode: {mode})")
    update_frustum_wireframe(bpy.context.scene)
    pointcloud_update_positions(bpy.context.scene)

register()
'''
    return base.create_embedded_script(script_name, script_text)


def register_frame_handler(point_cloud_obj, frustum_mode=FRUSTUM_MODE_ALL):
    """
    Register a frame change handler to update point cloud positions.
    
    Args:
        point_cloud_obj: The point cloud tracker object
        frustum_mode: Frustum culling mode (all, highlight, frustum_only)
    """
    # Store mode on object for embedded script to use
    point_cloud_obj["frustum_mode"] = frustum_mode
    
    # Create the embedded script so it works when file is re-opened
    create_embedded_tracking_script()
    
    # Ensure it's marked as module to run on load
    if "point_cloud_driver.py" in bpy.data.texts:
        bpy.data.texts["point_cloud_driver.py"].use_module = True
    
    def pointcloud_frame_handler(scene):
        # Re-fetch object to ensure it's valid
        if point_cloud_obj and point_cloud_obj.name in bpy.data.objects:
            pc_obj = bpy.data.objects[point_cloud_obj.name]
            mode = pc_obj.get("frustum_mode", FRUSTUM_MODE_ALL)
            update_point_cloud_positions(pc_obj, scene, frustum_mode=mode)
    
    base.register_frame_handler(pointcloud_frame_handler, "pointcloud_frame_handler")
    print(f"✅ Registered frame handler for point cloud updates (mode: {frustum_mode})")


def setup_point_tracking_visualization(tracked_objects, points_per_object=30, 
                                        setup_viewport=True, collection_name=None,
                                        show_frustum=False, frustum_distance=50.0,
                                        frustum_mode=FRUSTUM_MODE_ALL):
    """
    Main entry point for setting up point tracking visualization.
    
    Args:
        tracked_objects: List of objects to track (e.g., floating spheres)
        points_per_object: Number of surface sample points per object
        setup_viewport: Whether to create a dual viewport setup
        collection_name: Collection to use
        show_frustum: Whether to show camera frustum wireframe
        frustum_distance: How far the frustum extends
        frustum_mode: One of:
            - FRUSTUM_MODE_ALL ("all"): Show all points, no culling
            - FRUSTUM_MODE_HIGHLIGHT ("highlight"): Show all, in-frustum points turn red
            - FRUSTUM_MODE_ONLY ("frustum_only"): Only show points in frustum
        
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
    mode_desc = {
        FRUSTUM_MODE_ALL: "all points visible",
        FRUSTUM_MODE_HIGHLIGHT: "all visible, in-frustum highlighted red",
        FRUSTUM_MODE_ONLY: "only in-frustum visible"
    }
    print(f"  - Frustum mode: {frustum_mode} ({mode_desc.get(frustum_mode, '')})")
    
    # Create point cloud tracker
    point_cloud_obj, tracking_data = create_point_cloud_tracker(
        mesh_objects, 
        points_per_object=points_per_object,
        point_size=0.05,
        collection_name=collection_name
    )
    
    if not point_cloud_obj:
        return None
    
    # Store frustum settings on object
    point_cloud_obj["frustum_far_distance"] = frustum_distance
    point_cloud_obj["frustum_mode"] = frustum_mode
    
    # Create frustum visualization if requested (for highlight and frustum_only modes)
    coll_name = collection_name or base.DEFAULT_COLLECTION_NAME
    if show_frustum and frustum_mode != FRUSTUM_MODE_ALL:
        print(f"  - Creating frustum wireframe (distance: {frustum_distance}m)")
        setup_frustum_visualization(
            camera=None,  # Use scene camera
            far_distance=frustum_distance,
            collection_name=coll_name
        )
    
    # Register frame change handler for animation
    register_frame_handler(point_cloud_obj, frustum_mode=frustum_mode)
    
    # Get tracking collection objects
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
    
    print("✅ Point Tracking Visualization Ready!")
    print(f"   - Total tracked points: {len(tracking_data) if tracking_data else 0}")
    print(f"   - Frustum culling: only visible objects show points")
    if show_frustum:
        print(f"   - Frustum wireframe: visible in viewport 2")
    print(f"   - View the '{coll_name}' collection for point cloud")
    
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
