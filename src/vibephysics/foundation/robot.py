"""
Robot Foundation Module

General-purpose rigged robot/character control.
Not model-specific - works with any rigged armature.

For model-specific control (e.g. Open Duck), see foundation/open_duck.py
For trajectory creation, see foundation/trajectory.py
"""

import bpy
import math
import os
from mathutils import Vector, Matrix, Euler
from . import trajectory

def raycast_ground(scene, xy_point, start_height=10.0, ground_objects=None):
    """
    Find ground height at xy_point.
    Continues raycasting through non-ground objects until it finds the ground.
    """
    origin = Vector((xy_point[0], xy_point[1], start_height))
    direction = Vector((0, 0, -1))
    
    depsgraph = bpy.context.evaluated_depsgraph_get()
    
    # Keep raycasting until we hit the ground or nothing
    max_iterations = 20  # Prevent infinite loop
    current_origin = origin.copy()
    
    for _ in range(max_iterations):
        success, location, normal, index, hit_object, matrix = scene.ray_cast(
            depsgraph, current_origin, direction
        )
    
        if not success:
            # No more hits - return default floor
            return 0.0
        
        # Check if we hit the ground
        if ground_objects is None or hit_object in ground_objects:
            return location.z
    
        # Hit something else (debris, water, etc.) - continue from just below
        current_origin = location + direction * 0.01
    
    return 0.0  # Default floor if we exhaust iterations


# Trajectory functions moved to foundation/trajectory.py
# Import and use: from foundation import trajectory
# trajectory.evaluate_curve_at_t(), trajectory.create_circular_path(), etc.

def setup_collision_meshes(part_objects, kinematic=True, friction=0.8, restitution=0.1):
    """
    Sets up collision for robot parts/meshes.
    If kinematic=True, they follow animation but collide with other active objects.
    
    To avoid Blender dependency cycles, we only add rigid bodies to parts that
    are NOT parented to other mesh parts in the same list. Parts parented to
    armature/bones are fine.
    """
    print("  - Setting up robot collision physics...")
    count = 0
    skipped = 0
    
    # Create a set of mesh part names for quick lookup
    part_names = {p.name for p in part_objects if p and p.type == 'MESH'}
    
    for part in part_objects:
        if not part or part.type != 'MESH':
            continue
        
        # Check if this part is parented to another mesh in our list
        # If so, skip it to avoid dependency cycles
        parent = part.parent
        if parent and parent.type == 'MESH' and parent.name in part_names:
            skipped += 1
            continue
            
        # Add rigid body
        bpy.ops.object.select_all(action='DESELECT')
        part.select_set(True)
        bpy.context.view_layer.objects.active = part
        
        try:
            if not part.rigid_body:
                bpy.ops.rigidbody.object_add(type='ACTIVE')
            
            rb = part.rigid_body
            rb.kinematic = kinematic 
            rb.collision_shape = 'CONVEX_HULL'
            rb.friction = friction
            rb.restitution = restitution
            rb.collision_margin = 0.001
            
            count += 1
        except Exception as e:
            print(f"    Warning: Could not add rigid body to {part.name}: {e}")
            
    if skipped > 0:
        print(f"    Added collision to {count} mesh parts (skipped {skipped} children to avoid cycles)")
    else:
    print(f"    Added collision to {count} mesh parts")
    return count

def animate_walking(armature, path_curve, ground_object, 
                   start_frame=1, end_frame=250, speed=1.0,
                   scale_mult=None,
                   base_height_offset=0.0,
                   hips_height_ratio=0.33, 
                   stride_ratio=1.6,
                   step_height_ratio=0.8,
                   foot_spacing_ratio=0.6,
                   foot_ik_names=('leg_ik.l', 'leg_ik.r'),
                   forward_axis='Y',
                   foot_rotation_offset=0.0):
    """
    Generic rigged robot walking animation along a path.
    
    This is a simple reference implementation. For model-specific control
    (like Open Duck), see the model-specific modules (e.g., foundation.open_duck).
    
    Args:
        armature: Robot armature object
        path_curve: Curve path to follow
        ground_object: Ground object for raycasting
        start_frame: Animation start frame
        end_frame: Animation end frame
        speed: Movement speed multiplier
        scale_mult: Scale multiplier (auto-computed if None)
        base_height_offset: Vertical offset for armature origin
        stride_ratio: Step length
        step_height_ratio: Step lift height
        foot_spacing_ratio: Lateral foot spacing (not used in simple version)
        foot_ik_names: Tuple of (left_ik, right_ik) bone names
        forward_axis: Forward direction ('Y', '-Y', 'X', '-X')
        foot_rotation_offset: Additional foot rotation in radians
    """
    print("  - animating generic walk cycle...")
    scene = bpy.context.scene
    
    # Auto-compute scale multiplier if not provided
    if scale_mult is None:
        scale_mult = armature.scale[0]
    
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    bones = armature.pose.bones
    
    # Try to set IK mode if controller exists
    fk_ik_ctrl = bones.get('fk_ik_controller')
    if fk_ik_ctrl and 'fk_ik' in fk_ik_ctrl:
        fk_ik_ctrl['fk_ik'] = 1.0
        fk_ik_ctrl.keyframe_insert(data_path='["fk_ik"]', frame=start_frame)
    
    foot_ik_l = foot_ik_names[0]
    foot_ik_r = foot_ik_names[1]
    
    bone_l = bones.get(foot_ik_l)
    bone_r = bones.get(foot_ik_r)
    
    if not bone_l or not bone_r:
        print(f"ERROR: IK foot bones not found! Looking for {foot_ik_l}, {foot_ik_r}")
        bpy.ops.object.mode_set(mode='OBJECT')
        return
    
    # Walking parameters
    step_length = stride_ratio
    step_height = step_height_ratio
    
    # Cycle timing - frames per full step cycle
    frames_per_cycle = int(20 / speed)
    
    for frame in range(start_frame, end_frame + 1):
        scene.frame_set(frame)
        
        # Calculate path position
        t = (frame - start_frame) / (end_frame - start_frame)
        t = min(t, 0.9999)
        
        path_pos_world, tangent_world = trajectory.evaluate_curve_at_t(path_curve, t)
        
        # Get ground height
        ground_z = raycast_ground(scene, path_pos_world, start_height=20.0, 
                                  ground_objects=[ground_object])
        
        # Place armature at ground level + height offset
        armature_loc = Vector((path_pos_world.x, path_pos_world.y, ground_z + base_height_offset))
        armature.location = armature_loc
        armature.keyframe_insert(data_path="location", frame=frame)
        
        # Rotation - face along path tangent
        rot_quat = tangent_world.to_track_quat(forward_axis, 'Z')
        armature.rotation_euler = rot_quat.to_euler()
        armature.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        # Calculate cycle phase
        cycle_phase = ((frame - start_frame) % frames_per_cycle) / frames_per_cycle
        
        # Root bone bounce
        if 'root' in bones:
            bounce = math.sin(cycle_phase * 4 * math.pi) * 0.1
            bones['root'].location.z = bounce
            bones['root'].keyframe_insert(data_path="location", frame=frame)
        
        # Calculate foot offsets from REST POSITION
        def calc_foot_offset(phase_offset):
            foot_phase = (cycle_phase + phase_offset) % 1.0
            
            if foot_phase < 0.5:
                # Stance phase
                t_stance = foot_phase / 0.5
                forward = step_length * (0.5 - t_stance)
                height = 0.0
            else:
                # Swing phase
                t_swing = (foot_phase - 0.5) / 0.5
                forward = step_length * (-0.5 + t_swing)
                height = math.sin(t_swing * math.pi) * step_height
            
            return forward, height
        
        left_forward, left_height = calc_foot_offset(0.0)
        right_forward, right_height = calc_foot_offset(0.5)
        
        # Set IK target positions
        bone_l.location = Vector((0, left_forward, left_height))
        bone_l.keyframe_insert(data_path="location", frame=frame)
        
        bone_r.location = Vector((0, right_forward, right_height))
        bone_r.keyframe_insert(data_path="location", frame=frame)
        
        # Optional foot rotation
        if foot_rotation_offset != 0.0:
            bone_l.rotation_euler = Euler((0, 0, foot_rotation_offset), 'XYZ')
            bone_l.keyframe_insert(data_path="rotation_euler", frame=frame)
            
            bone_r.rotation_euler = Euler((0, 0, foot_rotation_offset), 'XYZ')
            bone_r.keyframe_insert(data_path="rotation_euler", frame=frame)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"  - Animation complete! Frames {start_frame}-{end_frame}")

def load_rigged_robot(filepath, transform=None):
    """
    Generic loader for a robot from a blend file.
    Expects 1 Armature and associated Meshes.
    
    Args:
        filepath: Path to .blend file
        transform: Optional dict with 'location', 'rotation', 'scale' keys
                  e.g. {'location': (0,0,0), 'rotation': (0,0,0), 'scale': 0.3}
    """
    print(f"  - Loading robot from {os.path.basename(filepath)}...")
    
    if not os.path.exists(filepath):
        print(f"Error: Robot file not found at {filepath}")
        return None, []

    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        data_to.objects = data_from.objects

    armature = None
    robot_parts = []
    
    for obj in data_to.objects:
        if obj:
            # Skip unwanted objects from the blend file
            if "Background" in obj.name:
                continue
            if obj.type in ('CAMERA', 'LIGHT', 'FONT'):
                continue  # Don't import cameras, lights, or text from robot blend file

            if obj.name not in bpy.context.scene.objects:
                bpy.context.scene.collection.objects.link(obj)
            
            if obj.type == 'ARMATURE':
                armature = obj
            elif obj.type == 'MESH':
                robot_parts.append(obj)
    
    # Apply transform if provided
    if armature and transform:
        if 'location' in transform:
            armature.location = transform['location']
        if 'rotation' in transform:
            armature.rotation_euler = transform['rotation']
        if 'scale' in transform:
            scale_val = transform['scale']
            if isinstance(scale_val, (int, float)):
                armature.scale = (scale_val, scale_val, scale_val)
            else:
                armature.scale = scale_val
    
    if armature:
        print(f"    Found armature: {armature.name}, {len(robot_parts)} mesh parts")
    else:
        print("    WARNING: No armature found!")
                
    return armature, robot_parts
