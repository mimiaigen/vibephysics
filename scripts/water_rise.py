import sys
import os
import bpy
import math
import argparse

# Add parent directory to path to import foundation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from foundation import physics, visuals, materials, lighting

def parse_args():
    """Parse command-line arguments for water rise simulation configuration.
    
    When running with Blender, pass script arguments after '--':
    blender -b -P script.py -- --rise-height 10 --rise-duration 200
    """
    parser = argparse.ArgumentParser(
        description='Generate a Blender water rise simulation with calm water',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Simulation Settings
    sim_group = parser.add_argument_group('Simulation Settings')
    sim_group.add_argument('--num-objects', type=int, default=25,
                          help='Number of floating objects')
    sim_group.add_argument('--spawn-radius', type=float, default=3.0,
                          help='Radius for random object spawning')
    
    # Water Rise Settings
    rise_group = parser.add_argument_group('Water Rise Settings')
    rise_group.add_argument('--rise-height', type=float, default=10.0,
                           help='Total height water will rise (from z=0 to this value)')
    rise_group.add_argument('--rise-duration', type=int, default=200,
                           help='Number of frames over which water rises')
    rise_group.add_argument('--calm-wave-scale', type=float, default=0.1,
                           help='Scale of visual ocean waves (lower = calmer)')
    
    # Physics Settings
    physics_group = parser.add_argument_group('Physics Settings')
    physics_group.add_argument('--no-buoyancy', action='store_true',
                              help='Disable buoyancy force field')
    physics_group.add_argument('--buoyancy-strength', type=float, default=15.0,
                              help='Strength of buoyancy force')
    physics_group.add_argument('--z-bottom', type=float, default=-5.0,
                              help='Z coordinate of the ocean floor')
    physics_group.add_argument('--show-force-fields', action='store_true',
                              help='Show force field visualizations in viewport')
    
    # Visual Settings
    visual_group = parser.add_argument_group('Visual Settings')
    visual_group.add_argument('--water-color', type=float, nargs=4, 
                             default=[0.0, 0.5, 0.8, 1.0],
                             metavar=('R', 'G', 'B', 'A'),
                             help='Water color as RGBA values (0.0-1.0)')
    visual_group.add_argument('--no-caustics', action='store_true',
                             help='Disable caustics lighting effects')
    visual_group.add_argument('--caustic-strength', type=float, default=6000.0,
                             help='Strength of caustic light patterns')
    visual_group.add_argument('--no-volumetric', action='store_true',
                             help='Disable volumetric fog effects')
    visual_group.add_argument('--volumetric-density', type=float, default=0.015,
                             help='Density of underwater fog')
    
    # Animation Settings
    anim_group = parser.add_argument_group('Animation Settings')
    anim_group.add_argument('--start-frame', type=int, default=1,
                           help='First frame of animation')
    anim_group.add_argument('--end-frame', type=int, default=250,
                           help='Last frame of animation')
    
    # Camera Settings
    camera_group = parser.add_argument_group('Camera Settings')
    camera_group.add_argument('--camera-radius', type=float, default=25.0,
                             help='Camera distance from center')
    camera_group.add_argument('--camera-height', type=float, default=8.0,
                             help='Camera height above initial water surface')
    camera_group.add_argument('--resolution-x', type=int, default=1920,
                             help='Render resolution width')
    camera_group.add_argument('--resolution-y', type=int, default=1080,
                             help='Render resolution height')
    
    # Output Settings
    output_group = parser.add_argument_group('Output Settings')
    output_group.add_argument('--output', type=str, default='water_rise_simulation.blend',
                             help='Output blend file name')
    
    # Filter out Blender's arguments - only parse after '--'
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    else:
        argv = []  # No script arguments, use defaults
    
    return parser.parse_args(argv)

def create_rising_water_handler(water_obj, start_z, end_z, start_frame, end_frame):
    """
    Create a frame change handler to animate water level rising.
    This uses keyframe animation for smooth water rise.
    """
    # Keyframe the water position at start
    water_obj.location.z = start_z
    water_obj.keyframe_insert(data_path="location", index=2, frame=start_frame)
    
    # Keyframe the water position at end
    water_obj.location.z = end_z
    water_obj.keyframe_insert(data_path="location", index=2, frame=start_frame + end_frame)
    
    # Note: In Blender 5.0+, the animation system changed to a layered system
    # The default interpolation (BEZIER) works fine for smooth water rise
    # fcurves manipulation is not available in the new system
    print(f"  - Water will rise from z={start_z} to z={end_z} over {end_frame} frames")

def run_simulation_setup(args):
    """Run the water rise simulation setup with the given arguments."""
    print("Initializing Water Rise Simulation...")
    print(f"Configuration: Water rising from z=0 to z={args.rise_height} over {args.rise_duration} frames")
    
    # 0. Clear Handlers (avoid duplicates)
    bpy.app.handlers.frame_change_pre.clear()
    
    # cleanup
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Generate object masses (standardized to match water_float.py)
    # Logarithmic scale from 0.001 to 1.0
    object_masses = [0.001 * (1/0.001) ** (i/(args.num_objects-1)) for i in range(args.num_objects)]
    
    # 1. Physics Environment
    physics.setup_rigid_body_world()
    
    # Starting water surface is at z=0
    start_z_surface = 0.0
    end_z_surface = args.rise_height
    
    if not args.no_buoyancy:
        # Create initial buoyancy field at z=0
        physics.create_buoyancy_field(
            z_bottom=args.z_bottom,
            z_surface=start_z_surface,
            strength=args.buoyancy_strength,
            spawn_radius=args.spawn_radius,
            hide=not args.show_force_fields
        )
        
        # We'll need to adjust buoyancy field height as water rises
        # For simplicity, we'll create it with max distance to cover the full rise
        buoyancy_obj = bpy.data.objects.get("BuoyancyField")
        if buoyancy_obj:
            # Update max distance to cover the rise
            buoyancy_obj.field.distance_max = end_z_surface - args.z_bottom
            
            # Animate the buoyancy field location to rise with water
            buoyancy_obj.location.z = args.z_bottom
            buoyancy_obj.keyframe_insert(data_path="location", index=2, frame=args.start_frame)
            buoyancy_obj.location.z = args.z_bottom
            buoyancy_obj.keyframe_insert(data_path="location", index=2, frame=args.start_frame + args.rise_duration)
    
    physics.create_seabed(z_bottom=args.z_bottom)
    
    # 2. Visual Environment - Calm Water
    water_visual = visuals.create_visual_water(
        scale=1.0,
        wave_scale=args.calm_wave_scale,  # Very calm waves
        time=None,  # Animated, but very subtle
        start_frame=args.start_frame,
        end_frame=args.end_frame
    )
    materials.create_water_material(water_visual, color=tuple(args.water_color))
    
    # Animate water rising
    create_rising_water_handler(
        water_visual, 
        start_z_surface, 
        end_z_surface, 
        args.start_frame, 
        args.rise_duration
    )
    
    # 3. Objects - Place on ground initially
    objects = []
    import random
    # random.seed(42) # Moved to internal generator or handling
    
    # Safe spawning on seabed
    min_dist = 1.2
    z_spawn = args.z_bottom + 0.6  # Just above seabed
    
    positions = physics.generate_scattered_positions(
        num_points=len(object_masses),
        spawn_radius=args.spawn_radius,
        min_dist=min_dist,
        z_pos=z_spawn
    )
    
    for i, mass in enumerate(object_masses):
        if i < len(positions):
            pos = positions[i]
            sphere = physics.create_floating_sphere(i, mass, pos, len(object_masses))
            objects.append(sphere)
    
    # 4. Interactions - Less intense ripples for calm water
    visuals.setup_dynamic_paint_interaction(
        water_visual, 
        objects, 
        ripple_strength=0.5  # Reduced for calm water
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
        enable_volumetric=not args.no_volumetric,
        z_surface=end_z_surface,  # Use final water height for lighting
        z_bottom=args.z_bottom,
        volumetric_density=args.volumetric_density,
        caustic_scale=15.0,
        caustic_strength=args.caustic_strength
    )
    
    print("✅ Water Rise Simulation Ready!")
    print("   - Physics: Rigid Body + Buoyancy")
    print("   - Visuals: Calm Ocean + Rising Water Level")
    print(f"   - Water rises from z=0 to z={args.rise_height} over {args.rise_duration} frames")

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
