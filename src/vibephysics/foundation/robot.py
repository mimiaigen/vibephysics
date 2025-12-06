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
    """
    origin = Vector((xy_point[0], xy_point[1], start_height))
    direction = Vector((0, 0, -1))
    
    # Raycast scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    
    success, location, normal, index, object, matrix = scene.ray_cast(depsgraph, origin, direction)
    
    if success:
        if ground_objects is None or object in ground_objects:
            return location.z
    
    return 0.0 # Default floor


# Trajectory functions moved to foundation/trajectory.py
# Import and use: from foundation import trajectory
# trajectory.evaluate_curve_at_t(), trajectory.create_circular_path(), etc.

def setup_collision_meshes(part_objects, kinematic=True, friction=0.8, restitution=0.1):
    """
    Sets up collision for robot parts/meshes.
    If kinematic=True, they follow animation but collide with other active objects.
    """
    print("  - setting up robot collision physics...")
    count = 0
    for part in part_objects:
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
            print(f"Warning: Could not add rigid body to {part.name}: {e}")
            
    print(f"    Added collision to {count} mesh parts")
    return count

def animate_walking(armature, path_curve, ground_object, 
                   start_frame=1, end_frame=250, speed=1.0,
                   scale_mult=None,
                   hips_height_ratio=0.33, 
                   stride_ratio=1.6,
                   step_height_ratio=0.8,
                   foot_spacing_ratio=0.6,
                   foot_ik_names=('leg_ik.l', 'leg_ik.r')):
    """
    Animates a rigged robot (using IK) walking along a path on uneven ground.
    
    scale_mult: General scaling factor (auto-computed from armature.scale if None)
    ratios: Parameters relative to scale_mult.
    """
    print("  - animating walk cycle...")
    scene = bpy.context.scene
    
    # Auto-compute scale multiplier if not provided
    if scale_mult is None:
        scale_mult = armature.scale[0]
    
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    bones = armature.pose.bones
    
    # Try to set IK mode if controller exists (common in some rigs)
    fk_ik_ctrl = bones.get('fk_ik_controller')
    if fk_ik_ctrl and 'fk_ik' in fk_ik_ctrl:
        fk_ik_ctrl['fk_ik'] = 1.0
        fk_ik_ctrl.keyframe_insert(data_path='["fk_ik"]', frame=start_frame)
    
    foot_ik_l = foot_ik_names[0]
    foot_ik_r = foot_ik_names[1]
    
    # Clear any existing constraints on IK bones
    for b_name in [foot_ik_l, foot_ik_r]:
        if b_name in bones:
            for c in list(bones[b_name].constraints):
                bones[b_name].constraints.remove(c)
    
    # Walking parameters
    hips_height = hips_height_ratio * scale_mult
    stride_length = stride_ratio * scale_mult
    step_height = step_height_ratio * scale_mult
    foot_spacing = foot_spacing_ratio * scale_mult
    
    foot_height_offset = 0.0
    
    # Cycle timing - frames per full step cycle
    frames_per_cycle = int(20 / speed)
    
    # Track foot plant positions
    foot_plants_l = {}
    foot_plants_r = {}
    
    for frame in range(start_frame, end_frame + 1):
        scene.frame_set(frame)
        
        # Calculate path position
        t = (frame - start_frame) / (end_frame - start_frame)
        t = min(t, 0.9999)
        
        path_pos_world, tangent_world = trajectory.evaluate_curve_at_t(path_curve, t)
        
        # Get ground height
        ground_z = raycast_ground(scene, path_pos_world, start_height=20.0, 
                                  ground_objects=[ground_object])
        
        # Place armature on ground
        armature_loc = Vector((path_pos_world.x, path_pos_world.y, ground_z))
        armature.location = armature_loc
        armature.keyframe_insert(data_path="location", frame=frame)
        
        # Rotation
        rot_quat = tangent_world.to_track_quat('-Y', 'Z')
        armature.rotation_euler = rot_quat.to_euler()
        armature.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        # Build transform matrix
        current_matrix = Matrix.LocRotScale(armature_loc, rot_quat, armature.scale)
        arm_mat_inv = current_matrix.inverted()
        
        # Direction vectors
        forward_vec = tangent_world.normalized()
        right_vec = forward_vec.cross(Vector((0, 0, 1))).normalized()
        
        # Calculate cycle phase
        cycle_phase = ((frame - start_frame) % frames_per_cycle) / frames_per_cycle
        current_cycle = (frame - start_frame) // frames_per_cycle
        
        # Root bone bounce
        if 'root' in bones:
            bounce = math.sin(cycle_phase * 4 * math.pi) * 0.008 * (scale_mult / 0.3) # Approximate scaling
            bones['root'].location.z = hips_height + bounce
            bones['root'].keyframe_insert(data_path="location", frame=frame)
        
        def get_foot_position(is_left, phase_offset):
            foot_phase = (cycle_phase + phase_offset) % 1.0
            side_sign = 1 if is_left else -1
            side_offset = right_vec * side_sign * foot_spacing
            
            is_stance = foot_phase < 0.5
            foot_plants = foot_plants_l if is_left else foot_plants_r
            
            if is_stance:
                plant_key = (current_cycle, is_left, 'stance')
                if plant_key not in foot_plants:
                    plant_pos = armature_loc + side_offset + forward_vec * (stride_length * 0.5)
                    plant_z = raycast_ground(scene, plant_pos, start_height=20.0, 
                                            ground_objects=[ground_object])
                    foot_plants[plant_key] = Vector((plant_pos.x, plant_pos.y, plant_z + foot_height_offset))
                return foot_plants[plant_key]
            else:
                swing_progress = (foot_phase - 0.5) / 0.5
                
                prev_plant_key = (current_cycle, is_left, 'stance')
                if prev_plant_key in foot_plants:
                    start_pos = foot_plants[prev_plant_key]
                else:
                    start_pos = armature_loc + side_offset - forward_vec * (stride_length * 0.5)
                    start_z = raycast_ground(scene, start_pos, start_height=20.0, ground_objects=[ground_object])
                    start_pos = Vector((start_pos.x, start_pos.y, start_z + foot_height_offset))
                
                end_pos = armature_loc + side_offset + forward_vec * (stride_length * 0.5)
                end_z = raycast_ground(scene, end_pos, start_height=20.0, ground_objects=[ground_object])
                end_pos = Vector((end_pos.x, end_pos.y, end_z + foot_height_offset))
                
                current_pos = start_pos.lerp(end_pos, swing_progress)
                lift = math.sin(swing_progress * math.pi) * step_height
                current_pos.z = current_pos.z + lift
                
                return current_pos
        
        def update_foot_bone(bone_name, world_pos):
            if bone_name not in bones:
                return
            bone = bones[bone_name]
            local_pos = arm_mat_inv @ world_pos
            bone.location = local_pos
            bone.keyframe_insert(data_path="location", frame=frame)
        
        left_pos = get_foot_position(True, 0.0)
        right_pos = get_foot_position(False, 0.5)
        
        update_foot_bone(foot_ik_l, left_pos)
        update_foot_bone(foot_ik_r, right_pos)
    
    bpy.ops.object.mode_set(mode='OBJECT')

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
            if "Background" in obj.name:
                continue

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
