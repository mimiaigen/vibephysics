import sys
import os
import bpy
import math
import random
import argparse

# Setup imports (works with both pip install and local development)
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(_root, 'src'))

from vibephysics.foundation import scene, physics, water, ground, objects, materials, lighting
from vibephysics.annotation import point_tracking
from vibephysics.camera import create_center_cameras
from vibephysics.setup import save_blend

def parse_args():
    """Parse command-line arguments for water simulation configuration.
    
    When running with Blender, pass script arguments after '--':
    blender -b -P script.py -- --num-spheres 10 --wave-scale 1.0
    """
    parser = argparse.ArgumentParser(
        description='Generate a Blender water simulation with floating spheres',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Simulation Settings
    sim_group = parser.add_argument_group('Simulation Settings')
    sim_group.add_argument('--num-spheres', type=int, default=25,
                          help='Number of floating spheres with different masses')
    sim_group.add_argument('--collision-spawn', action='store_true',
                          help='Spawn spheres randomly in a circle (collision mode)')
    sim_group.add_argument('--spawn-radius', type=float, default=2.0,
                          help='Radius for random sphere spawning')
    
    # Physics Fields
    physics_group = parser.add_argument_group('Physics Settings')
    physics_group.add_argument('--no-buoyancy', action='store_true',
                              help='Disable buoyancy force field')
    physics_group.add_argument('--no-currents', action='store_true',
                              help='Disable underwater currents')
    physics_group.add_argument('--z-bottom', type=float, default=-5.0,
                              help='Z coordinate of the ocean floor')
    physics_group.add_argument('--z-surface', type=float, default=0.0,
                              help='Z coordinate of the water surface')
    physics_group.add_argument('--buoyancy-strength', type=float, default=10.0,
                              help='Strength of buoyancy force (2.0 = typical, higher = stronger lift)')
    physics_group.add_argument('--current-strength', type=float, default=20.0,
                              help='Strength of underwater currents')
    physics_group.add_argument('--turbulence-scale', type=float, default=1.0,
                              help='Size of turbulence noise pattern (meters)')
    physics_group.add_argument('--ripple-strength', type=float, default=10.0,
                              help='Multiplier for ripple height (1.0 = default)')
    physics_group.add_argument('--wave-scale', type=float, default=0.5,
                              help='Scale of visual ocean waves (1.0 = default)')
    physics_group.add_argument('--fixed-wave-time', type=float, default=None,
                              help='Lock waves to specific time (None = animated)')
    physics_group.add_argument('--show-force-fields', action='store_true',
                              help='Show force field visualizations in viewport')
    
    # Visual Settings
    visual_group = parser.add_argument_group('Visual Settings')
    visual_group.add_argument('--water-color', type=float, nargs=4, 
                             default=[0.0, 0.6, 1.0, 1.0],
                             metavar=('R', 'G', 'B', 'A'),
                             help='Water color as RGBA values (0.0-1.0)')
    visual_group.add_argument('--no-caustics', action='store_true',
                             help='Disable caustics lighting effects')
    visual_group.add_argument('--caustic-strength', type=float, default=8000.0,
                             help='Strength of caustic light patterns')
    visual_group.add_argument('--caustic-scale', type=float, default=15.0,
                             help='Scale of caustic light patterns')
    visual_group.add_argument('--no-volumetric', action='store_true',
                             help='Disable volumetric fog effects')
    visual_group.add_argument('--volumetric-density', type=float, default=0.02,
                             help='Density of underwater fog')
    
    # Animation Settings
    anim_group = parser.add_argument_group('Animation Settings')
    anim_group.add_argument('--start-frame', type=int, default=1,
                           help='First frame of animation')
    anim_group.add_argument('--end-frame', type=int, default=250,
                           help='Last frame of animation')
    
    # Camera Settings
    camera_group = parser.add_argument_group('Camera Settings')
    camera_group.add_argument('--camera-radius', type=float, default=20.0,
                             help='Camera distance from center')
    camera_group.add_argument('--camera-height', type=float, default=2.0,
                             help='Camera height above water surface')
    camera_group.add_argument('--resolution-x', type=int, default=1920,
                             help='Render resolution width')
    camera_group.add_argument('--resolution-y', type=int, default=1080,
                             help='Render resolution height')
    
    # Point Tracking Settings
    tracking_group = parser.add_argument_group('Point Tracking Settings')
    tracking_group.add_argument('--no-point-tracking', action='store_true',
                               help='Disable point cloud tracking visualization')
    tracking_group.add_argument('--points-per-object', type=int, default=30,
                               help='Number of surface sample points per object')
    
    # Output Settings
    output_group = parser.add_argument_group('Output Settings')
    output_group.add_argument('--output', type=str, default='water_simulation.blend',
                             help='Output blend file name')
    
    # Support both: python script.py --arg  AND  blender -P script.py -- --arg
    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
    else:
        argv = sys.argv[1:]
    
    return parser.parse_args(argv)

def run_simulation_setup(args):
    """Run the water simulation setup with the given arguments."""
    print("Initializing Water Simulation...")
    print(f"Configuration: {args.num_spheres} spheres, wave scale {args.wave_scale}")
    
    # 1. Scene initialization
    scene.init_simulation(
        start_frame=args.start_frame,
        end_frame=args.end_frame
    )
    
    # Generate sphere masses (logarithmic scale from 0.001 to 1)
    sphere_masses = [0.001 * (1/0.001) ** (i/(args.num_spheres-1)) for i in range(args.num_spheres)]
    
    if not args.no_buoyancy:
        physics.create_buoyancy_field(
            z_bottom=args.z_bottom,
            z_surface=args.z_surface,
            strength=args.buoyancy_strength,
            spawn_radius=args.spawn_radius,
            hide=not args.show_force_fields
        )
        
    if not args.no_currents:
        # Calculate effective strength based on wave scale
        effective_strength = args.current_strength * args.wave_scale
        physics.create_underwater_currents(
            z_bottom=args.z_bottom,
            z_surface=args.z_surface,
            strength=effective_strength,
            turbulence_scale=args.turbulence_scale,
            spawn_radius=args.spawn_radius,
            hide=not args.show_force_fields
        )
        
    ground.create_seabed(z_bottom=args.z_bottom)
    
    # 2. Visual Environment
    water_visual = water.create_visual_water(
        scale=1.0,
        wave_scale=args.wave_scale,
        time=args.fixed_wave_time,
        start_frame=args.start_frame,
        end_frame=args.end_frame
    )
    materials.create_water_material(water_visual, color=tuple(args.water_color))
    
    # 3. Objects
    spheres = []
    base_z = 5.0
    
    # Define safe distance (diameter + margin)
    min_dist = 1.2  # Radius 0.5 * 2 = 1.0 + margin
    
    if args.collision_spawn:
        # Random overlapping-safe spawning
        positions = objects.generate_scattered_positions(
            num_points=len(sphere_masses),
            spawn_radius=args.spawn_radius,
            min_dist=min_dist,
            z_pos=base_z,
            z_range=5.0  # Allow stacking up to 5 meters high if needed
        )
        
        # If we couldn't fit all, just use what we have or fallback
        # But since we iterate by mass, we should match lengths or handle indices carefully
        for i, mass in enumerate(sphere_masses):
            if i < len(positions):
                pos = positions[i]
                # Pos already includes Z from generator
                
                sphere = objects.create_floating_sphere(i, mass, pos, len(sphere_masses))
                spheres.append(sphere)
    else:
        # Linear layout (grid or line)
        spacing = 1.2
        start_x = -((len(sphere_masses) - 1) * spacing) / 2.0
        
        for i, mass in enumerate(sphere_masses):
            pos = (start_x + i * spacing, 0.0, base_z + i * 0.1)
            sphere = objects.create_floating_sphere(i, mass, pos, len(sphere_masses))
            spheres.append(sphere)
        
    # 4. Interactions
    water.setup_dynamic_paint_interaction(water_visual, spheres, args.ripple_strength)
    
    # 5. Rendering
    lighting.setup_lighting(
        resolution_x=args.resolution_x,
        resolution_y=args.resolution_y,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        enable_caustics=not args.no_caustics,
        enable_volumetric=not args.no_volumetric,
        z_surface=args.z_surface,
        z_bottom=args.z_bottom,
        volumetric_density=args.volumetric_density,
        caustic_scale=args.caustic_scale,
        caustic_strength=args.caustic_strength
    )
    
    # Setup camera (4 cameras around scene center)
    create_center_cameras(
        num_cameras=4,
        radius=args.camera_radius,
        height=args.camera_height
    )
    
    # 6. Point Tracking Visualization
    # Creates dual viewport: Left=scene, Right=point cloud tracking
    if not args.no_point_tracking and spheres:
        point_tracking.setup_point_tracking_visualization(
            tracked_objects=spheres,
            points_per_object=args.points_per_object,
            setup_viewport=not bpy.app.background
    )
    
    print("✅ Simulation Ready!")
    print("   - Physics: Bullet Rigid Body + Force Fields (Buoyancy, Currents)")
    print("   - Visuals: Ocean Modifier + Dynamic Paint (Ripples)")
    if not args.no_point_tracking:
        print(f"   - Point Tracking: {args.points_per_object} points per object")

if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_args()
    
    # Run simulation setup
    run_simulation_setup(args)
    
    # Save to output file
    save_blend(args.output)
