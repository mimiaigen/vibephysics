import sys
import os
import bpy
import math
import argparse

# Add parent directory to path to import foundation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from foundation import physics, water, ground, objects, materials, lighting
from annotation import point_tracking

def parse_args():
    """Parse command-line arguments for water bucket simulation configuration.
    
    When running with Blender, pass script arguments after '--':
    blender -b -P script.py -- --wave-intensity 2.0 --num-floats 20
    """
    parser = argparse.ArgumentParser(
        description='Generate a Blender water bucket simulation with periodic waves',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Simulation Settings
    sim_group = parser.add_argument_group('Simulation Settings')
    sim_group.add_argument('--num-floats', type=int, default=25,
                          help='Number of floating objects in the bucket')
    sim_group.add_argument('--bucket-radius', type=float, default=4.0,
                          help='Radius of the water bucket area')
    
    # Wave Settings
    wave_group = parser.add_argument_group('Wave Settings')
    wave_group.add_argument('--wave-intensity', type=float, default=1.5,
                           help='Intensity of periodic waves (1.0 = moderate)')
    wave_group.add_argument('--wave-period', type=int, default=50,
                           help='Number of frames per wave cycle')
    
    # Physics Settings
    physics_group = parser.add_argument_group('Physics Settings')
    physics_group.add_argument('--no-currents', action='store_true',
                              help='Disable underwater currents')
    physics_group.add_argument('--buoyancy-strength', type=float, default=12.0,
                              help='Strength of buoyancy force')
    physics_group.add_argument('--current-strength', type=float, default=15.0,
                              help='Strength of underwater currents')
    physics_group.add_argument('--z-bottom', type=float, default=-3.0,
                              help='Z coordinate of the bucket floor')
    physics_group.add_argument('--z-surface', type=float, default=0.0,
                              help='Z coordinate of the water surface')
    physics_group.add_argument('--show-force-fields', action='store_true',
                              help='Show force field visualizations in viewport')
    
    # Visual Settings
    visual_group = parser.add_argument_group('Visual Settings')
    visual_group.add_argument('--water-color', type=float, nargs=4, 
                             default=[0.3, 0.7, 1.0, 1.0],
                             metavar=('R', 'G', 'B', 'A'),
                             help='Water color as RGBA values (0.0-1.0)')
    visual_group.add_argument('--no-caustics', action='store_true',
                             help='Disable caustics lighting effects')
    visual_group.add_argument('--caustic-strength', type=float, default=7000.0,
                             help='Strength of caustic light patterns')
    visual_group.add_argument('--ripple-strength', type=float, default=8.0,
                             help='Multiplier for ripple height')
    
    # Animation Settings
    anim_group = parser.add_argument_group('Animation Settings')
    anim_group.add_argument('--start-frame', type=int, default=1,
                           help='First frame of animation')
    anim_group.add_argument('--end-frame', type=int, default=250,
                           help='Last frame of animation')
    
    # Camera Settings
    camera_group = parser.add_argument_group('Camera Settings')
    camera_group.add_argument('--camera-radius', type=float, default=10.0,
                             help='Camera distance from center')
    camera_group.add_argument('--camera-height', type=float, default=10.0,
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
    output_group.add_argument('--output', type=str, default='water_bucket.blend',
                             help='Output blend file name')
    
    # Filter out Blender's arguments - only parse after '--'
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    else:
        argv = []  # No script arguments, use defaults
    
    return parser.parse_args(argv)

def run_simulation_setup(args):
    """Run the water bucket simulation setup with the given arguments."""
    print("Initializing Water Bucket Simulation...")
    print(f"Configuration: {args.num_floats} floats, wave intensity {args.wave_intensity}")
    
    # 0. Clear Handlers (avoid duplicates)
    bpy.app.handlers.frame_change_pre.clear()
    
    # cleanup
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Generate float masses (standardized to match water_float.py)
    # Logarithmic scale from 0.001 to 1.0
    float_masses = [0.001 * (1/0.001) ** (i/(args.num_floats-1)) for i in range(args.num_floats)]
    
    # 1. Physics Environment
    physics.setup_rigid_body_world()
    
    # Create buoyancy field
    physics.create_buoyancy_field(
        z_bottom=args.z_bottom,
        z_surface=args.z_surface,
        strength=args.buoyancy_strength,
        spawn_radius=args.bucket_radius,
        hide=not args.show_force_fields
    )
    
    if not args.no_currents:
        # Stronger currents for water bucket effect
        effective_strength = args.current_strength * args.wave_intensity
        physics.create_underwater_currents(
            z_bottom=args.z_bottom,
            z_surface=args.z_surface,
            strength=effective_strength,
            turbulence_scale=2.0,
            spawn_radius=args.bucket_radius,
            hide=not args.show_force_fields
        )
    
    ground.create_bucket_container(
        z_bottom=args.z_bottom,
        z_surface=args.z_surface,
        radius=args.bucket_radius
    )
    
    # 2. Visual Environment - Water Bucket
    # We force wave_scale to 0.0 for the visual water to keep it flat
    # The ripples come from Dynamic Paint which is added next
    water_visual = water.create_visual_water(
        scale=1.0,
        wave_scale=0.0, # Flat water
        radius=args.bucket_radius,
        time=None, 
        start_frame=args.start_frame,
        end_frame=args.end_frame
    )
    materials.create_water_material(water_visual, color=tuple(args.water_color))
    
    # 3. Objects - Distributed across bucket
    floats = []
    
    # Safe spawning using Poisson-like scattering
    min_dist = 1.1 # Diameter 1.0 + small margin
    
    # We spawn slightly above water
    z_spawn = 3.0
    
    positions = objects.generate_scattered_positions(
        num_points=args.num_floats,
        spawn_radius=args.bucket_radius - 0.6, # Keep away from walls
        min_dist=min_dist,
        z_pos=z_spawn,
        z_range=4.0  # Allow stacking
    )
    
    idx = 0
    for pos in positions:
        if idx >= args.num_floats:
            break
        
        sphere = objects.create_floating_sphere(idx, float_masses[idx], pos, args.num_floats)
        floats.append(sphere)
        idx += 1
    
    # 4. Interactions - Strong ripples for water bucket
    water.setup_dynamic_paint_interaction(
        water_visual, 
        floats, 
        ripple_strength=args.ripple_strength
    )
    
    # 5. Rendering
    lighting.setup_lighting_and_camera(
        camera_radius=args.camera_radius,
        camera_height=args.camera_height,
        resolution_x=args.resolution_x,
        resolution_y=args.resolution_y,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        enable_caustics=not args.no_caustics,
        enable_volumetric=False,  # Keep it simple for bucket
        z_surface=args.z_surface,
        z_bottom=args.z_bottom,
        volumetric_density=0.01,
        caustic_scale=10.0,
        caustic_strength=args.caustic_strength
    )
    
    # 6. Point Tracking Visualization (2nd viewport with colored point cloud)
    if not args.no_point_tracking and floats:
        point_tracking.setup_point_tracking_visualization(
            tracked_objects=floats,
            points_per_object=args.points_per_object,
            setup_viewport=not bpy.app.background
        )
    
    print("✅ Water Bucket Simulation Ready!")
    print("   - Physics: Rigid Body + Enhanced Currents")
    print("   - Visuals: Dynamic Waves + Ripples")
    print(f"   - {args.num_floats} floating objects in {args.bucket_radius*2}m bucket")
    if not args.no_point_tracking:
        print(f"   - Point Tracking: {args.points_per_object} points per object")

if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_args()
    
    # Run simulation setup
    run_simulation_setup(args)
    
    # CRITICAL: Disable disk cache RIGHT BEFORE saving to ensure it persists
    print("Disabling all disk caches before save...")
    if bpy.context.scene.rigidbody_world and bpy.context.scene.rigidbody_world.point_cache:
        bpy.context.scene.rigidbody_world.point_cache.use_disk_cache = False
        print("  - Disabled Rigid Body World cache")
        
    for obj in bpy.data.objects:
        for mod in obj.modifiers:
            if mod.type == 'DYNAMIC_PAINT':
                if mod.canvas_settings:
                    for surface in mod.canvas_settings.canvas_surfaces:
                        if hasattr(surface, "point_cache") and surface.point_cache:
                            surface.point_cache.use_disk_cache = False
                            print(f"  - Disabled cache for {obj.name} - {surface.name}")
    
    # Save to output file
    blend_path = os.path.abspath(args.output)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"✅ Saved to {args.output}")
    
    # Clean up blendcache folder
    import shutil
    cache_name = os.path.splitext(os.path.basename(args.output))[0]
    cache_folder = os.path.abspath(f"blendcache_{cache_name}")
    if os.path.exists(cache_folder):
        shutil.rmtree(cache_folder)
        print(f"🗑️  Removed cache folder: {cache_folder}")
