"""
Trajectory and Path Generation

General-purpose path/trajectory utilities for any moving object.
Not specific to any particular model or rig.
"""

import bpy
from mathutils import Vector


def evaluate_curve_at_t(curve_obj, t):
    """
    Evaluate position and tangent of a curve at factor t (0-1).
    Returns (position, tangent) vectors in world space.
    
    Args:
        curve_obj: Blender curve object
        t: Parameter value (0-1)
        
    Returns:
        tuple: (position_vector, tangent_vector) in world space
    """
    if not curve_obj.data.splines:
        return Vector((0,0,0)), Vector((0,1,0))
    
    spline = curve_obj.data.splines[0]
    depsgraph = bpy.context.evaluated_depsgraph_get()
    curve_eval = curve_obj.evaluated_get(depsgraph)
    mesh = curve_eval.to_mesh()
    
    if len(mesh.vertices) < 2:
        curve_eval.to_mesh_clear()
        return curve_obj.location, Vector((0,1,0))
        
    total_verts = len(mesh.vertices)
    
    if spline.use_cyclic_u:
        idx_float = t * total_verts
    else:
        idx_float = t * (total_verts - 1)
        
    idx = int(idx_float)
    next_idx = (idx + 1) % total_verts
    fraction = idx_float - idx
    
    v1 = mesh.vertices[idx].co
    v2 = mesh.vertices[next_idx].co
    
    # Interpolate local position
    pos_local = v1.lerp(v2, fraction)
    
    # Calculate tangent (direction to next point)
    tangent_local = (v2 - v1).normalized()
    if tangent_local.length_squared == 0:
        tangent_local = Vector((0,1,0))
        
    # Transform to world
    pos_world = curve_obj.matrix_world @ pos_local
    
    # Transform tangent (rotation only)
    tangent_world = curve_obj.matrix_world.to_3x3() @ tangent_local
    tangent_world.normalize()
    
    curve_eval.to_mesh_clear()
    
    return pos_world, tangent_world


def create_circular_path(radius=10.0, scale_y=0.5, z_location=0.0, name="Path"):
    """
    Creates a circular/oval bezier path for any object to follow.
    
    Args:
        radius: Circle radius
        scale_y: Y-axis scaling (< 1.0 = oval, > 1.0 = stretched)
        z_location: Z-coordinate for path
        name: Object name
        
    Returns:
        Blender curve object
    """
    bpy.ops.curve.primitive_bezier_circle_add(radius=radius, location=(0, 0, z_location))
    path = bpy.context.active_object
    path.name = name
    
    path.scale = (1.0, scale_y, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    
    return path


def create_waypoint_path(waypoints, closed=False, z_location=None, name="WaypointPath"):
    """
    Creates a path through multiple waypoints.
    
    Args:
        waypoints: List of (x, y) or (x, y, z) tuples
        closed: Whether to close the path (cyclic)
        z_location: Default Z if waypoints don't specify (ignored if waypoint has z)
        name: Object name
        
    Returns:
        Blender curve object
    """
    if z_location is None:
        z_location = 0.0
    
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    
    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(len(waypoints) - 1)
    spline.use_cyclic_u = closed
    
    for i, wp in enumerate(waypoints):
        if len(wp) == 2:
            pos = (wp[0], wp[1], z_location)
        else:
            pos = wp
        spline.bezier_points[i].co = pos
        spline.bezier_points[i].handle_left_type = 'AUTO'
        spline.bezier_points[i].handle_right_type = 'AUTO'
    
    curve_obj = bpy.data.objects.new(name, curve_data)
    bpy.context.scene.collection.objects.link(curve_obj)
    
    return curve_obj


# =============================================================================
# Waypoint Pattern Presets
# =============================================================================

# Available pattern names for reference
WAYPOINT_PATTERNS = ['exploration', 's_curve', 'figure_eight', 'spiral', 'zigzag', 'circle', 'rectangle']


def create_waypoint_pattern(pattern, scale=8.0):
    """
    Create predefined waypoint patterns for path following.
    
    Args:
        pattern: Pattern name - one of:
            - 'exploration': Visits different areas randomly
            - 's_curve': Smooth S-curve
            - 'figure_eight': Figure-8 pattern
            - 'spiral': Outward spiral (2 rotations)
            - 'zigzag': Zigzag pattern
            - 'circle': Simple circle
            - 'rectangle': Rectangular path
        scale: Size scaling factor
        
    Returns:
        List of (x, y) waypoints
        
    Example:
        waypoints = trajectory.create_waypoint_pattern('exploration', scale=10.0)
        path = trajectory.create_waypoint_path(waypoints, closed=True)
    """
    import math
    
    if pattern == 'exploration':
        # Exploration pattern - visits different areas
        waypoints = [
            (0, 0),
            (scale, scale * 0.5),
            (scale * 0.5, scale),
            (-scale * 0.3, scale * 0.8),
            (-scale, scale * 0.2),
            (-scale * 0.8, -scale * 0.5),
            (0, -scale),
            (scale * 0.6, -scale * 0.7),
            (scale * 0.8, 0),
        ]
    
    elif pattern == 's_curve':
        # Smooth S-curve
        waypoints = [
            (-scale, -scale),
            (-scale * 0.5, -scale * 0.3),
            (0, 0),
            (scale * 0.5, scale * 0.3),
            (scale, scale),
            (scale * 0.5, scale * 0.7),
            (0, scale * 0.4),
            (-scale * 0.5, 0),
        ]
    
    elif pattern == 'figure_eight':
        # Figure-8 with more control points for smoothness
        waypoints = [
            (0, 0),
            (scale * 0.7, scale * 0.5),
            (scale * 0.9, scale * 0.9),
            (scale * 0.5, scale),
            (0, scale * 0.7),
            (-scale * 0.5, scale),
            (-scale * 0.9, scale * 0.9),
            (-scale * 0.7, scale * 0.5),
            (0, 0),
            (scale * 0.7, -scale * 0.5),
            (scale * 0.9, -scale * 0.9),
            (scale * 0.5, -scale),
            (0, -scale * 0.7),
            (-scale * 0.5, -scale),
            (-scale * 0.9, -scale * 0.9),
            (-scale * 0.7, -scale * 0.5),
        ]
    
    elif pattern == 'spiral':
        # Outward spiral (2 full rotations)
        waypoints = []
        num_points = 12
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi * 2  # 2 full rotations
            radius = scale * (0.2 + i / num_points * 0.8)  # Grow from 0.2 to 1.0
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            waypoints.append((x, y))
    
    elif pattern == 'zigzag':
        # Zigzag pattern
        waypoints = [
            (-scale, -scale * 0.8),
            (scale, -scale * 0.5),
            (-scale * 0.8, -scale * 0.2),
            (scale * 0.9, scale * 0.1),
            (-scale, scale * 0.4),
            (scale * 0.8, scale * 0.7),
            (-scale * 0.7, scale),
        ]
    
    elif pattern == 'circle':
        # Simple circle with 8 points
        waypoints = []
        num_points = 8
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            x = scale * math.cos(angle)
            y = scale * math.sin(angle)
            waypoints.append((x, y))
    
    elif pattern == 'rectangle':
        # Rectangular path
        waypoints = [
            (-scale, -scale * 0.5),
            (scale, -scale * 0.5),
            (scale, scale * 0.5),
            (-scale, scale * 0.5),
        ]
    
    else:
        # Default to exploration if unknown pattern
        print(f"⚠️ Unknown pattern '{pattern}', using 'exploration'")
        return create_waypoint_pattern('exploration', scale)
    
    return waypoints
