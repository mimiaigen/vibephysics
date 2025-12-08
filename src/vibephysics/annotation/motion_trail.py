"""
Motion Trail Visualization Module

Creates motion paths (trails) for objects over a frame range.
Useful for visualizing trajectories of objects in simulations.
"""

import bpy
from mathutils import Vector

from . import base
from ..setup.importer import ensure_collection


def create_motion_trail(target_obj, start_frame=None, end_frame=None, step=1, 
                        name_suffix="Trail", color=(0.0, 0.8, 1.0, 1.0),
                        bevel_depth=0.05, bevel_resolution=4,
                        collection_name=None):
    """
    Create a static curve object representing the motion path of the object.
    If frames are not specified, uses scene preview range.
    
    Args:
        target_obj: Object to track
        start_frame: Start frame (optional, defaults to scene start)
        end_frame: End frame (optional, defaults to scene end)
        step: Frame step for sampling
        name_suffix: Suffix for the trail object name
        color: RGBA color tuple for the trail
        bevel_depth: Thickness of the trail curve
        bevel_resolution: Smoothness of the trail curve
        collection_name: Collection to put the annotation in
        
    Returns:
        trail_obj: The created curve object
    """
    if not target_obj:
        return None
        
    scene = bpy.context.scene
    
    if start_frame is None:
        start_frame = scene.frame_start
    if end_frame is None:
        end_frame = scene.frame_end
        
    # Ensure collection exists
    collection = ensure_collection(collection_name or base.DEFAULT_COLLECTION_NAME)
        
    # Create curve data
    curve_name = f"{target_obj.name}_{name_suffix}"
    
    # Remove existing if any
    if curve_name in bpy.data.objects:
        old_obj = bpy.data.objects[curve_name]
        bpy.data.objects.remove(old_obj, do_unlink=True)
        
    curve_data = bpy.data.curves.new(name=f"{curve_name}_Data", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.fill_mode = 'FULL'
    curve_data.bevel_depth = bevel_depth
    curve_data.bevel_resolution = bevel_resolution
    
    # Create spline
    spline = curve_data.splines.new(type='NURBS')
    
    # Remember current frame
    current_frame = scene.frame_current
    
    # Bake positions
    print(f"Baking motion trail for {target_obj.name} ({start_frame}-{end_frame})...")
    
    coords = []
    
    for frame in range(start_frame, end_frame + 1, step):
        scene.frame_set(frame)
        
        # Evaluate dependency graph for physics/constraints
        depsgraph = base.get_depsgraph()
        if depsgraph:
            try:
                obj_eval = base.get_evaluated_object(target_obj, depsgraph)
                pos = obj_eval.matrix_world.translation.copy()
            except:
                pos = target_obj.matrix_world.translation.copy()
        else:
            pos = target_obj.matrix_world.translation.copy()
            
        coords.append(pos)
        
    # Restore frame
    scene.frame_set(current_frame)
    
    if len(coords) < 2:
        print("Not enough points for trail.")
        return None
    
    # Set spline points
    spline.points.add(len(coords) - 1)
    
    for i, coord in enumerate(coords):
        # NURBS points are (x, y, z, w)
        spline.points[i].co = (coord.x, coord.y, coord.z, 1.0)
        
    spline.use_endpoint_u = True
    
    # Create object
    trail_obj = bpy.data.objects.new(curve_name, curve_data)
    collection.objects.link(trail_obj)
    
    # Store target reference for debugging/identification
    trail_obj["target_object"] = target_obj.name
    trail_obj["annotation_type"] = "motion_trail"
    
    # Material using base utility
    mat_name = f"{target_obj.name}_TrailMat"
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = base.create_emission_material(
            mat_name,
            color=color,
            strength=2.0
        )
        
    trail_obj.data.materials.append(mat)
    
    print(f"✅ Motion trail created with {len(coords)} points")
    
    return trail_obj


def create_motion_trails(objects, start_frame=None, end_frame=None, step=1,
                         colors=None, collection_name=None):
    """
    Create motion trails for multiple objects.
    
    Args:
        objects: List of objects to track
        start_frame: Start frame (optional)
        end_frame: End frame (optional)
        step: Frame step for sampling
        colors: List of RGBA colors (or None for auto-generated)
        collection_name: Collection to put the annotations in
        
    Returns:
        List of trail curve objects
    """
    if not objects:
        return []
    
    # Auto-generate distinct colors if not provided
    if colors is None:
        from mathutils import Color
        colors = []
        for i, _ in enumerate(objects):
            c = Color()
            c.hsv = ((i * 0.618033988749895 + 0.5) % 1.0, 0.7, 0.95)
            colors.append((c.r, c.g, c.b, 1.0))
    elif not isinstance(colors, list):
        colors = [colors] * len(objects)
    
    trails = []
    for obj, color in zip(objects, colors):
        trail = create_motion_trail(
            obj,
            start_frame=start_frame,
            end_frame=end_frame,
            step=step,
            color=color,
            collection_name=collection_name
        )
        if trail:
            trails.append(trail)
    
    return trails
