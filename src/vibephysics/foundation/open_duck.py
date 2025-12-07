"""
Open Duck Robot Control

Model-specific control for the Open Duck mini robot.
Provides high-level functions with duck-specific proportions, bone names, and behavior.

References: /Users/shamangary/codeDemo/Open_Duck_Blender/open-duck-mini.blend
"""

import os
from tqdm import tqdm
from . import robot
from . import trajectory


# Duck-specific constants
DUCK_BONE_NAMES = {
    'left_foot_ik': 'leg_ik.l',
    'right_foot_ik': 'leg_ik.r',
    'fk_ik_controller': 'fk_ik_controller'
}

# Duck-specific proportions (all relative to scale)
DUCK_PROPORTIONS = {
    'base_height_ratio': 4.5,      # Lift whole robot up to put feet on z=0
    'hips_height_ratio': 0.1,      # Low slung body relative to origin
    'stride_ratio': 1.5,           # Step length (offset from rest position)
    'step_height_ratio': 0.8,      # Step lift height
    'foot_spacing_ratio': 0.2,     # Narrow stance
}

# Default duck transform
DEFAULT_DUCK_TRANSFORM = {
    'location': (0, 0, 0),
    'rotation': (0, 0, 0),
    'scale': 0.3  # Duck is small
}


def load_open_duck(blend_path=None, transform=None):
    """
    Load the Open Duck robot with duck-specific defaults.
    
    Args:
        blend_path: Path to open-duck-mini.blend (uses default if None)
        transform: Optional transform override (uses DEFAULT_DUCK_TRANSFORM if None)
        
    Returns:
        tuple: (armature, robot_parts) from robot.load_rigged_robot
    """
    if blend_path is None:
        # Try common locations
        default_paths = [
            "/Users/shamangary/codeDemo/Open_Duck_Blender/open-duck-mini.blend",
            "../Open_Duck_Blender/open-duck-mini.blend",
            "./open-duck-mini.blend"
        ]
        for path in default_paths:
            if os.path.exists(path):
                blend_path = path
                break
        
        if blend_path is None:
            raise FileNotFoundError("Could not find open-duck-mini.blend. Please specify blend_path.")
    
    if transform is None:
        transform = DEFAULT_DUCK_TRANSFORM.copy()
    
    return robot.load_rigged_robot(blend_path, transform=transform)


def create_duck_walk_path(radius=3.5, scale_y=0.5, z_location=2.0):
    """
    Create a typical duck walking path (oval, slightly elevated).
    
    Args:
        radius: Path radius
        scale_y: Y-axis scale (< 1.0 for oval)
        z_location: Height above ground
        
    Returns:
        Curve object for duck to follow
    """
    return trajectory.create_circular_path(
        radius=radius,
        scale_y=scale_y,
        z_location=z_location,
        name="DuckPath"
    )


def animate_duck_walking(armature, path_curve, ground_object, 
                        start_frame=1, end_frame=250, speed=1.0,
                        override_proportions=None):
    """
    Animate the Open Duck walking along a path with duck-specific waddle.
    
    This is the duck-specific implementation with proper foot rotation and IK control.
    
    Args:
        armature: Duck armature
        path_curve: Path to follow
        ground_object: Ground for raycasting
        start_frame: Animation start frame
        end_frame: Animation end frame
        speed: Movement speed multiplier
        override_proportions: Dict to override DUCK_PROPORTIONS
        
    Returns:
        None (animates armature in place)
    """
    import bpy
    import math
    from mathutils import Vector, Euler
    
    # Use duck proportions, allow overrides
    proportions = DUCK_PROPORTIONS.copy()
    if override_proportions:
        proportions.update(override_proportions)
    
    print("  - Animating duck walk cycle...")
    scene = bpy.context.scene
    
    scale_mult = armature.scale[0]
    base_height_offset = proportions['base_height_ratio'] * scale_mult
    
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    bones = armature.pose.bones
    
    # Set IK mode
    fk_ik_ctrl = bones.get(DUCK_BONE_NAMES['fk_ik_controller'])
    if fk_ik_ctrl and 'fk_ik' in fk_ik_ctrl:
        fk_ik_ctrl['fk_ik'] = 1.0
        fk_ik_ctrl.keyframe_insert(data_path='["fk_ik"]', frame=start_frame)
    
    foot_ik_l = DUCK_BONE_NAMES['left_foot_ik']
    foot_ik_r = DUCK_BONE_NAMES['right_foot_ik']
    
    bone_l = bones.get(foot_ik_l)
    bone_r = bones.get(foot_ik_r)
    
    if not bone_l or not bone_r:
        print(f"ERROR: Duck IK foot bones not found! Looking for {foot_ik_l}, {foot_ik_r}")
        bpy.ops.object.mode_set(mode='OBJECT')
        return
    
    # Duck walking parameters
    step_length = proportions['stride_ratio']
    step_height = proportions['step_height_ratio']
    
    # Cycle timing
    frames_per_cycle = int(20 / speed)
    
    for frame in tqdm(range(start_frame, end_frame + 1), desc="    Animating", unit="frame"):
        scene.frame_set(frame)
        
        # Calculate path position
        t = (frame - start_frame) / (end_frame - start_frame)
        t = min(t, 0.9999)
        
        path_pos_world, tangent_world = trajectory.evaluate_curve_at_t(path_curve, t)
        
        # Look ahead to calculate turn rate
        t_ahead = min(t + 0.02, 0.9999)
        _, tangent_ahead = trajectory.evaluate_curve_at_t(path_curve, t_ahead)
        
        # Calculate turn rate (positive = turning left, negative = turning right)
        cross = tangent_world.cross(tangent_ahead)
        turn_rate = cross.z * 10.0  # Scale for visible effect
        
        # Get ground height
        ground_z = robot.raycast_ground(scene, path_pos_world, start_height=20.0, 
                                       ground_objects=[ground_object])
        
        # Place armature at ground level + height offset
        armature_loc = Vector((path_pos_world.x, path_pos_world.y, ground_z + base_height_offset))
        armature.location = armature_loc
        armature.keyframe_insert(data_path="location", frame=frame)
        
        # Rotation - Duck's forward is -Y, so use '-Y' track axis
        rot_quat = tangent_world.to_track_quat('-Y', 'Z')
        armature.rotation_euler = rot_quat.to_euler()
        armature.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        # Calculate cycle phase
        cycle_phase = ((frame - start_frame) % frames_per_cycle) / frames_per_cycle
        
        # Root bone bounce (duck waddle)
        if 'root' in bones:
            bounce = math.sin(cycle_phase * 4 * math.pi) * 0.1
            bones['root'].location.z = bounce
            bones['root'].keyframe_insert(data_path="location", frame=frame)
        
        # Calculate foot offsets from REST POSITION
        def calc_foot_offset(phase_offset):
            foot_phase = (cycle_phase + phase_offset) % 1.0
            
            if foot_phase < 0.5:
                # Stance phase - foot on ground
                t_stance = foot_phase / 0.5
                forward = step_length * (0.5 - t_stance)
                height = 0.0  # At rest position = on ground
                is_swing = False
            else:
                # Swing phase - foot lifting and moving forward
                t_swing = (foot_phase - 0.5) / 0.5
                forward = step_length * (-0.5 + t_swing)
                height = math.sin(t_swing * math.pi) * step_height
                is_swing = True
            
            return forward, height, is_swing
        
        left_forward, left_height, left_swing = calc_foot_offset(0.0)
        right_forward, right_height, right_swing = calc_foot_offset(0.5)
        
        # Set IK target positions as OFFSETS from rest position
        # X=0 (no side offset), Y=forward offset, Z=height offset
        bone_l.location = Vector((0, left_forward, left_height))
        bone_l.keyframe_insert(data_path="location", frame=frame)
        
        bone_r.location = Vector((0, right_forward, right_height))
        bone_r.keyframe_insert(data_path="location", frame=frame)
        
        # Duck-specific foot rotation: -90 degree base rotation
        base_rot = -math.pi / 2
        foot_rot_angle = turn_rate * 0.1  # Subtle turn anticipation
        
        if left_swing:
            # Swing phase - rotate to anticipate turn
            bone_l.rotation_euler = Euler((0, 0, base_rot + foot_rot_angle), 'XYZ')
        else:
            # Stance phase - keep foot aligned
            bone_l.rotation_euler = Euler((0, 0, base_rot), 'XYZ')
        bone_l.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        if right_swing:
            # Swing phase - rotate to anticipate turn
            bone_r.rotation_euler = Euler((0, 0, base_rot + foot_rot_angle), 'XYZ')
        else:
            # Stance phase - keep foot aligned
            bone_r.rotation_euler = Euler((0, 0, base_rot), 'XYZ')
        bone_r.keyframe_insert(data_path="rotation_euler", frame=frame)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"  - Duck animation complete! {end_frame - start_frame + 1} frames ({start_frame}-{end_frame})")


def setup_duck_collision(robot_parts, kinematic=True):
    """
    Setup collision meshes for the Open Duck with duck-appropriate settings.
    
    Args:
        robot_parts: List of duck mesh objects
        kinematic: Whether to use kinematic rigid bodies (follows animation)
        
    Returns:
        Number of parts with collision added
    """
    # Duck is small and light, use slightly lower friction
    return robot.setup_collision_meshes(
        robot_parts, 
        kinematic=kinematic,
        friction=0.7,  # Slightly less than default
        restitution=0.1
    )


# Example usage/recipe function
def setup_duck_simulation(terrain, terrain_size, start_frame=1, end_frame=250, 
                         duck_blend_path=None, walk_speed=1.0):
    """
    Complete duck walking simulation setup (example recipe).
    
    Args:
        terrain: Ground object for walking
        terrain_size: Size of terrain (for path scaling)
        start_frame: Animation start
        end_frame: Animation end
        duck_blend_path: Optional path to duck blend file
        walk_speed: Walking speed multiplier
        
    Returns:
        dict: {'armature': armature, 'parts': robot_parts, 'path': path}
    """
    # 1. Load duck
    armature, robot_parts = load_open_duck(duck_blend_path)
    
    if not armature:
        raise RuntimeError("Failed to load Open Duck!")
    
    # 2. Create walking path
    path = create_duck_walk_path(
        radius=terrain_size * 0.35,
        scale_y=0.5,
        z_location=2.0
    )
    
    # 3. Animate walking
    animate_duck_walking(
        armature=armature,
        path_curve=path,
        ground_object=terrain,
        start_frame=start_frame,
        end_frame=end_frame,
        speed=walk_speed
    )
    
    # 4. Setup collision
    setup_duck_collision(robot_parts, kinematic=True)
    
    return {
        'armature': armature,
        'parts': robot_parts,
        'path': path
    }
