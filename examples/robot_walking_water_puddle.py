"""
Robot Walking Water Puddle Simulation

Open Duck robot walking through uneven terrain with water puddles.
Features full annotation support (bounding boxes, motion trails, point tracking).
"""

import sys
import os
import bpy
import math
import argparse
import random
from mathutils import Vector, Matrix, Euler

# Add parent directory to path to import foundation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from foundation import scene, physics, water, ground, objects, materials, lighting, open_duck
from annotation import AnnotationManager, point_tracking, viewport


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
    
    # Annotation Settings
    annotation_group = parser.add_argument_group('Annotation Settings')
    annotation_group.add_argument('--no-annotations', action='store_true',
                                 help='Disable all annotations')
    annotation_group.add_argument('--no-bbox', action='store_true',
                                 help='Disable bounding box annotations')
    annotation_group.add_argument('--no-bbox-robot', action='store_true',
                                 help='Disable bounding boxes on robot parts')
    annotation_group.add_argument('--no-bbox-debris', action='store_true',
                                 help='Disable bounding boxes on debris')
    annotation_group.add_argument('--no-trail', action='store_true',
                                 help='Disable motion trail annotations')
    annotation_group.add_argument('--trail-debris', action='store_true',
                                 help='Add trails to debris objects (disabled by default)')
    annotation_group.add_argument('--no-point-tracking', action='store_true',
                                 help='Disable point cloud tracking visualization')
    annotation_group.add_argument('--points-per-object', type=int, default=50,
                                 help='Number of surface sample points per object')
    annotation_group.add_argument('--trail-step', type=int, default=3,
                                 help='Frame step for motion trail sampling')
    
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
    print("=" * 60)
    print("  Robot Walking Water Puddle Simulation")
    print("=" * 60)
    
    # 1. Universal scene initialization
    scene.init_simulation(
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        physics_config={'substeps': 20, 'solver_iters': 20, 'cache_buffer': 50}
    )
    
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
    
    # 3. Water Surface
    z_water_level = z_ground + 0.1
    water_visual = water.create_flat_surface(
        size=args.terrain_size * 0.9,
        z_level=z_water_level,
        subdivisions=200
    )
    materials.create_water_material(water_visual, color=tuple(args.water_color))
    
    # 3a. Add 25 falling balls
    z_spawn = z_water_level + 3.0
    positions = objects.generate_scattered_positions(
        num_points=25,
        spawn_radius=args.terrain_size / 3.0,
        min_dist=0.8,
        z_pos=z_spawn
    )
    debris_objects = objects.create_falling_spheres(
        positions=positions,
        radius_range=(0.15, 0.3),
        physics={'mass': 0.3, 'friction': 0.7, 'restitution': 0.3},
        num_total=25
    )
    
    # 4. Open Duck Robot (model-specific setup)
    duck_result = open_duck.setup_duck_simulation(
        terrain=terrain,
        terrain_size=args.terrain_size,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        walk_speed=args.walk_speed
    )
    
    armature = duck_result['armature']
    robot_parts = duck_result['parts']
    path = duck_result['path']
    
    # 8. Water Interactions
    water.setup_robot_water_interaction(
        water_visual, 
        robot_parts, 
        debris_objects, 
        ripple_strength=15.0
    )
    
    # 9. Full Annotation Setup using AnnotationManager
    # Uses the new annotate_robot() method for fine-grained control
    
    if not args.no_annotations and (robot_parts or debris_objects):
        print("\n📊 Setting up Annotations...")
        
        mgr = AnnotationManager(collection_name="AnnotationViz")
        
        # Determine what to track based on args
        bbox_robot = not args.no_bbox and not args.no_bbox_robot
        bbox_debris = not args.no_bbox and not args.no_bbox_debris
        trail_center = not args.no_trail
        trail_debris = args.trail_debris  # Disabled by default, enable with --trail-debris
        point_tracking = not args.no_point_tracking
        
        # Use the unified annotate_robot method
        mgr.annotate_robot(
            robot_parts=robot_parts,
            center_object=armature,
            debris_objects=debris_objects,
            bbox_robot=bbox_robot,
            bbox_debris=bbox_debris,
            trail_center=trail_center,
            trail_debris=trail_debris,
            point_tracking=point_tracking,
            start_frame=args.start_frame,
            end_frame=args.end_frame,
            trail_step=args.trail_step,
            points_per_object=args.points_per_object
        )
        
        # Finalize - register handlers and create scripts
        mgr.finalize(setup_viewport=False)
        viewport.create_viewport_restore_script("AnnotationViz")
    
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
    
    # Camera tracks robot
    lighting.setup_camera_tracking(armature)
    
    # Bake physics
    print("\n  - Baking physics...")
    physics.bake_all()

    print("\n" + "=" * 60)
    print("✅ Robot Walking Simulation Complete!")
    print("=" * 60)


if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_args()
    
    # Run simulation setup
    run_simulation_setup(args)
    
    # Save to output file
    blend_path = os.path.abspath(args.output)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"💾 Saved to {args.output}")
