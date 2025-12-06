"""
Open Duck Robot Control

Model-specific control for the Open Duck mini robot.
Provides high-level functions with duck-specific proportions, bone names, and behavior.

References: /Users/shamangary/codeDemo/Open_Duck_Blender/open-duck-mini.blend
"""

import os
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
    'hips_height_ratio': 0.1,      # Low slung body
    'stride_ratio': 0.5,           # Short waddle steps
    'step_height_ratio': 0.25,     # High step lift (waddle)
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
    # Use duck proportions, allow overrides
    proportions = DUCK_PROPORTIONS.copy()
    if override_proportions:
        proportions.update(override_proportions)
    
    return robot.animate_walking(
        armature=armature,
        path_curve=path_curve,
        ground_object=ground_object,
        start_frame=start_frame,
        end_frame=end_frame,
        speed=speed,
        # Duck-specific parameters
        hips_height_ratio=proportions['hips_height_ratio'],
        stride_ratio=proportions['stride_ratio'],
        step_height_ratio=proportions['step_height_ratio'],
        foot_spacing_ratio=proportions['foot_spacing_ratio'],
        foot_ik_names=(DUCK_BONE_NAMES['left_foot_ik'], DUCK_BONE_NAMES['right_foot_ik'])
    )


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
