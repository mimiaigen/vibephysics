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
from vibephysics.camera import CenterPointingCameraRig

def parse_args():
    """Parse command-line arguments for storm simulation configuration.
    
    When running with Blender, pass script arguments after '--':
    blender -b -P script.py -- --storm-intensity 3.0 --num-debris 30
    """
    parser = argparse.ArgumentParser(
        description='Generate a Blender storm simulation with intense waves and debris',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Simulation Settings
    sim_group = parser.add_argument_group('Simulation Settings')
    sim_group.add_argument('--num-debris', type=int, default=25,
                          help='Number of debris objects in the storm')
    sim_group.add_argument('--spawn-radius', type=float, default=5.0,
                          help='Radius for debris spawning area')
    
    # Storm Settings
    storm_group = parser.add_argument_group('Storm Settings')
    storm_group.add_argument('--storm-intensity', type=float, default=3.0,
                           help='Intensity of storm (1.0 = moderate, 3.0 = severe)')
    storm_group.add_argument('--wind-chaos', type=float, default=50.0,
                           help='Strength of chaotic wind forces')
    
    # Physics Settings
    physics_group = parser.add_argument_group('Physics Settings')
    physics_group.add_argument('--buoyancy-strength', type=float, default=20.0,
                              help='Strength of buoyancy force (higher for storm)')
    physics_group.add_argument('--z-bottom', type=float, default=-10.0,
                              help='Z coordinate of the ocean floor')
    physics_group.add_argument('--z-surface', type=float, default=0.0,
                              help='Z coordinate of the water surface')
    physics_group.add_argument('--show-force-fields', action='store_true',
                              help='Show force field visualizations in viewport')
    
    # Visual Settings
    visual_group = parser.add_argument_group('Visual Settings')
    visual_group.add_argument('--water-color', type=float, nargs=4, 
                             default=[0.1, 0.2, 0.4, 1.0],
                             metavar=('R', 'G', 'B', 'A'),
                             help='Dark water color for stormy seas')
    visual_group.add_argument('--no-caustics', action='store_true',
                             help='Disable caustics lighting effects')
    visual_group.add_argument('--caustic-strength', type=float, default=10000.0,
                             help='Strength of caustic light patterns')
    visual_group.add_argument('--no-volumetric', action='store_true',
                             help='Disable volumetric fog effects')
    visual_group.add_argument('--volumetric-density', type=float, default=0.05,
                             help='Dense fog for storm atmosphere')
    
    # Animation Settings
    anim_group = parser.add_argument_group('Animation Settings')
    anim_group.add_argument('--start-frame', type=int, default=1,
                           help='First frame of animation')
    anim_group.add_argument('--end-frame', type=int, default=250,
                           help='Last frame of animation')
    
    # Camera Settings
    camera_group = parser.add_argument_group('Camera Settings')
    camera_group.add_argument('--camera-radius', type=float, default=35.0,
                             help='Camera distance from center')
    camera_group.add_argument('--camera-height', type=float, default=3.0,
                             help='Camera height (low for storm drama)')
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
    output_group.add_argument('--output', type=str, default='storm_simulation.blend',
                             help='Output blend file name')
    
    # Support both: python script.py --arg  AND  blender -P script.py -- --arg
    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
    else:
        argv = sys.argv[1:]
    
    return parser.parse_args(argv)

def run_simulation_setup(args):
    """Run the storm simulation setup with the given arguments."""
    print("Initializing Storm Simulation...")
    print(f"Configuration: {args.num_debris} debris objects, storm intensity {args.storm_intensity}")
    
    # 1. Scene initialization with high physics precision for storm
    scene.init_simulation(
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        physics_config={'substeps': 80, 'solver_iters': 80}
    )
    
    # Generate debris masses (logarithmic scale from 0.001 to 1.0)
    debris_masses = [0.001 * (1/0.001) ** (i/(args.num_debris-1)) for i in range(args.num_debris)]
    
    # Create strong buoyancy field
    physics.create_buoyancy_field(
        z_bottom=args.z_bottom,
        z_surface=args.z_surface,
        strength=args.buoyancy_strength,
        spawn_radius=args.spawn_radius,
        hide=not args.show_force_fields
    )
    
    # Create intense underwater currents
    effective_strength = args.wind_chaos * args.storm_intensity
    physics.create_underwater_currents(
        z_bottom=args.z_bottom,
        z_surface=args.z_surface,
        strength=effective_strength,
        turbulence_scale=0.5,  # Small scale = chaotic
        spawn_radius=args.spawn_radius,
        hide=not args.show_force_fields
    )
    
    ground.create_seabed(z_bottom=args.z_bottom)
    
    # 2. Visual Environment - Stormy Sea
    water_visual = water.create_visual_water(
        scale=1.0,
        wave_scale=args.storm_intensity,  # Large, violent waves
        time=None,  # Animated
        start_frame=args.start_frame,
        end_frame=args.end_frame
    )
    materials.create_water_material(water_visual, color=tuple(args.water_color))
    
    # 3. Objects - Scattered debris at various heights
    debris = []
    
    # Safe spawning
    min_dist = 1.2
    
    # For storm, we want them to drop from various heights, but not overlap in X/Y if possible to avoid initial explosions
    # We'll generate X/Y positions first
    positions = objects.generate_scattered_positions(
        num_points=len(debris_masses),
        spawn_radius=args.spawn_radius,
        min_dist=min_dist,
        z_pos=2.0,
        z_range=8.0 # Use range for storm debris
    )
    
    for i, mass in enumerate(debris_masses):
        if i < len(positions):
            # Use position directly
            pos = positions[i]
            sphere = objects.create_floating_sphere(i, mass, pos, args.num_debris)
            debris.append(sphere)
    
    # 4. Interactions - Very strong ripples for storm
    water.setup_dynamic_paint_interaction(
        water_visual, 
        debris, 
        ripple_strength=15.0  # Intense for storm
    )
    
    # 5. Rendering - Dramatic lighting for storm
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
        caustic_scale=20.0,
        caustic_strength=args.caustic_strength
    )
    
    # Camera setup - 4 cameras pointing at center, default at 270°
    cam_rig = CenterPointingCameraRig(
        num_cameras=4,
        radius=args.camera_radius,
        height=args.camera_height
    )
    cam_rig.create(target_object=water_visual)
    
    # Adjust world background for storm (darker, more ominous)
    world = bpy.context.scene.world
    if world and world.use_nodes:
        # Adjust sky texture for stormy look
        sky = world.node_tree.nodes.get("Sky Texture")
        if sky:
            try:
                # NISHITA sky (Blender 2.9-4.x)
                sky.air_density = 3.0  # Thick atmosphere
                sky.dust_density = 5.0  # Heavy dust/clouds
                sky.sun_elevation = math.radians(15)  # Low sun
            except AttributeError:
                # HOSEK_WILKIE sky (Blender 5.0+)
                sky.turbidity = 10.0  # Higher = hazier/stormier
                sky.sun_direction = (0.0, 0.259, 0.966)  # Low sun (15 degrees)
        # Reduce background strength for darker scene
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs['Strength'].default_value = 0.5
    
    # 6. Point Tracking Visualization
    # Creates dual viewport: Left=scene, Right=point cloud tracking
    if not args.no_point_tracking and debris:
        point_tracking.setup_point_tracking_visualization(
            tracked_objects=debris,
            points_per_object=args.points_per_object,
            setup_viewport=not bpy.app.background
        )
    
    print("✅ Storm Simulation Ready!")
    print("   - Physics: Enhanced Rigid Body + Extreme Forces")
    print("   - Visuals: Violent Waves + Intense Ripples")
    print(f"   - {args.num_debris} debris objects in chaotic storm")
    if not args.no_point_tracking:
        print(f"   - Point Tracking: {args.points_per_object} points per object")

if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_args()
    
    # Run simulation setup
    run_simulation_setup(args)
    
    # Save to output file
    blend_path = os.path.abspath(args.output)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"✅ Saved to {args.output}")
