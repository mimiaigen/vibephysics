import sys
import os
import bpy
import math
import argparse
import random
from mathutils import Vector, Matrix, Euler

# Add parent directory to path to import foundation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from foundation import physics, water, ground, robot, objects, materials, lighting
from annotation import point_tracking
from utils import viewport

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate a robot walking in water puddles simulation',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    sim_group = parser.add_argument_group('Simulation Settings')
    sim_group.add_argument('--terrain-size', type=float, default=25.0,
                          help='Size of the ground area')
    sim_group.add_argument('--puddle-depth', type=float, default=0.6,
                          help='Depth of displacement for puddles')
    sim_group.add_argument('--walk-speed', type=float, default=1.0,
                          help='Walking speed of the robot')
    
    visual_group = parser.add_argument_group('Visual Settings')
    visual_group.add_argument('--water-color', type=float, nargs=4, 
                             default=[0.4, 0.5, 0.45, 0.9],
                             metavar=('R', 'G', 'B', 'A'),
                             help='Water color as RGBA values')
    
    anim_group = parser.add_argument_group('Animation Settings')
    anim_group.add_argument('--start-frame', type=int, default=1,
                           help='First frame of animation')
    anim_group.add_argument('--end-frame', type=int, default=350,
                           help='Last frame of animation')
    
    camera_group = parser.add_argument_group('Camera Settings')
    camera_group.add_argument('--camera-radius', type=float, default=18.0,
                             help='Camera distance from center')
    camera_group.add_argument('--camera-height', type=float, default=6.0,
                             help='Camera height')
    camera_group.add_argument('--resolution-x', type=int, default=1920,
                             help='Render resolution width')
    camera_group.add_argument('--resolution-y', type=int, default=1080,
                             help='Render resolution height')
    
    tracking_group = parser.add_argument_group('Point Tracking Settings')
    tracking_group.add_argument('--no-point-tracking', action='store_true',
                               help='Disable point cloud tracking visualization')
    tracking_group.add_argument('--points-per-object', type=int, default=100,
                               help='Number of surface sample points per object')
    
    output_group = parser.add_argument_group('Output Settings')
    output_group.add_argument('--output', type=str, default='robot_walk.blend',
                             help='Output blend file name')
    
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    else:
        argv = []
    
    return parser.parse_args(argv)

def run_simulation_setup(args):
    print("Initializing Robot Walking Simulation...")
    
    # Cleanup
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # 1. Physics Environment
    physics.setup_rigid_body_world()
    
    scene = bpy.context.scene
    if scene.rigidbody_world:
        scene.rigidbody_world.substeps_per_frame = 20
        scene.rigidbody_world.solver_iterations = 20
        # IMPORTANT: Extend rigid body cache to match animation length
        scene.rigidbody_world.point_cache.frame_start = args.start_frame
        scene.rigidbody_world.point_cache.frame_end = args.end_frame + 50  # Extra buffer
    
    # 2. Terrain (Uneven Ground)
    z_ground = -1.0
    strength = args.puddle_depth * 2.0
    
    terrain = ground.create_uneven_ground(
        z_base=z_ground,
        size=args.terrain_size,
        noise_scale=2.0, 
        strength=strength
    )
    
    # Visual Ground: Give it a small thickness
    ground.apply_thickness(terrain, thickness=0.5, offset=-1.0)
    
    materials.create_mud_material(terrain)
    physics.setup_ground_physics(terrain)
    
    # 3. Water Surface - Simple high-res GRID for Dynamic Paint ripples
    z_water_level = z_ground + 0.1  # Slightly above ground base
    
    # Create simple water grid (no edge pinning = no edge artifacts)
    water_size = args.terrain_size * 0.9
    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions=200,  # High resolution for ripples
        y_subdivisions=200,
        size=water_size,
        location=(0, 0, z_water_level)
    )
    water_visual = bpy.context.active_object
    water_visual.name = "Water_Visual"
    
    bpy.ops.object.shade_smooth()
    
    materials.create_water_material(water_visual, color=tuple(args.water_color))
    
    # Note: No buoyancy field - balls just fall and create ripples, no floating needed
    
    # 3a. Add 25 falling balls (debris)
    print("  - creating 25 falling balls...")
    debris_objects = []
    z_spawn = z_water_level + 3.0  # Spawn above water
    
    positions = objects.generate_scattered_positions(
        num_points=25,
        spawn_radius=args.terrain_size / 3.0,
        min_dist=0.8,
        z_pos=z_spawn
    )
    
    for i, pos in enumerate(positions):
        # Create small spheres
        bpy.ops.mesh.primitive_uv_sphere_add(radius=random.uniform(0.15, 0.3), location=pos)
        obj = bpy.context.active_object
        obj.name = f"Ball_{i}"
        
        # Random rotation
        obj.rotation_euler = (random.random(), random.random(), random.random())
        
        # Physics - active rigid body that falls
        bpy.ops.rigidbody.object_add(type='ACTIVE')
        obj.rigid_body.mass = 0.3
        obj.rigid_body.friction = 0.7
        obj.rigid_body.restitution = 0.3
        
        # Add colored material
        materials.create_sphere_material(obj, i, 25)
        debris_objects.append(obj)
    
    print(f"    Created {len(debris_objects)} balls")
    
    # 4. Robot
    duck_path = "/Users/shamangary/codeDemo/Open_Duck_Blender/open-duck-mini.blend"
    
    # Use generic loader
    armature, robot_parts = robot.load_rigged_robot(duck_path)
    
    if not armature:
        print("Failed to load Duck! Aborting.")
        return
        
    print(f"    Found armature: {armature.name}")
    print(f"    Found {len(robot_parts)} mesh parts.")

    # Configure Duck specifically
    armature.location = (0, 0, 0)
    armature.rotation_euler = (0, 0, 0)
    armature.scale = (0.3, 0.3, 0.3) 

    # 5. Walk Path
    # 0.35 * scale, flattened slightly
    path = robot.create_circular_path(radius=args.terrain_size * 0.35, scale_y=0.5)
    path.location.z = 2.0 
    
    # 6. Animate Walking (Kinematic Driver)
    print("  - animating walk cycle...")
    
    scale_mult = armature.scale[0]
    
    robot.animate_walking(
        armature=armature,
        path_curve=path,
        ground_object=terrain,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        speed=args.walk_speed,
        scale_mult=scale_mult,
        # Duck proportions
        hips_height_ratio=0.1,    # Low slung
        stride_ratio=0.5,         # Short steps
        step_height_ratio=0.25,   # High steps (waddle)
        foot_spacing_ratio=0.2,   # Narrow stance
        foot_ik_names=('leg_ik.l', 'leg_ik.r')
    )
    
    # 7. Setup Robot Collision (Meshes stay rigged, but can collide)
    print("  - setting up robot collision physics...")
    count = robot.setup_collision_meshes(robot_parts, kinematic=True)
    print(f"    Added collision to {count} mesh parts")
    
    # 8. Water Interactions - Custom setup for robot with larger paint_distance
    print("  - setting up water ripple interactions...")
    
    interaction_config = [
        # Robot: Larger paint distance (0.5), stronger ripples (1.5x)
        {
            'objects': robot_parts,
            'paint_distance': 0.5,
            'wave_factor_scale': 1.5,
            'wave_clamp': 10.0
        },
        # Debris: Normal paint distance (0.3), normal ripples
        {
            'objects': debris_objects,
            'paint_distance': 0.3,
            'wave_factor_scale': 1.0,
            'wave_clamp': 8.0
        }
    ]
    
    water.setup_custom_water_interaction(water_visual, interaction_config)
    
    # 9. Point Tracking (track both robot and debris)
    tracked_objects = robot_parts + debris_objects
    if not args.no_point_tracking and tracked_objects:
        print("  - setting up point tracking...")
        point_tracking.setup_point_tracking_visualization(
            tracked_objects=tracked_objects,
            points_per_object=max(5, args.points_per_object // len(tracked_objects)) if tracked_objects else 10,
            setup_viewport=not bpy.app.background
        )
    
    # 10. Lighting and Camera
    lighting.setup_lighting_and_camera(
        camera_radius=args.camera_radius,
        camera_height=args.camera_height,
        resolution_x=args.resolution_x,
        resolution_y=args.resolution_y,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        enable_caustics=True,
        z_surface=z_water_level,
        z_bottom=z_ground - 5.0,
        enable_volumetric=False,
        volumetric_density=0.0,
        caustic_scale=10.0
    )
    
    cam = bpy.context.scene.camera
    if cam:
        constraint = cam.constraints.new(type='TRACK_TO')
        constraint.target = armature
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'
        
    # Bake rigid body physics (dynamic paint WAVE simulates in real-time)
    print("  - baking physics...")
    bpy.ops.ptcache.bake_all(bake=True)

    print("✅ Duck Walking Simulation Ready!")

if __name__ == "__main__":
    args = parse_args()
    run_simulation_setup(args)
    
    blend_path = os.path.abspath(args.output)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"✅ Saved to {args.output}")
