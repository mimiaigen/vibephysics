import sys
import os
import bpy
import math
import argparse
import random

# Add parent directory to path to import foundation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from foundation import physics, water, ground, objects, materials, lighting
from annotation import point_tracking

def parse_args():
    """Parse command-line arguments for water puddles simulation."""
    parser = argparse.ArgumentParser(
        description='Generate a Blender simulation with shallow water puddles on uneven ground',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Simulation Settings
    sim_group = parser.add_argument_group('Simulation Settings')
    sim_group.add_argument('--num-debris', type=int, default=30,
                          help='Number of small debris objects')
    sim_group.add_argument('--terrain-size', type=float, default=20.0,
                          help='Size of the ground area')
    sim_group.add_argument('--puddle-depth', type=float, default=0.5,
                          help='Depth of displacement for puddles')
    
    # Physics Settings
    physics_group = parser.add_argument_group('Physics Settings')
    physics_group.add_argument('--buoyancy-strength', type=float, default=15.0,
                              help='Strength of buoyancy force')
    physics_group.add_argument('--z-ground', type=float, default=-1.0,
                              help='Base Z coordinate of the ground')
    physics_group.add_argument('--z-water', type=float, default=-0.8,
                              help='Z coordinate of the water surface')
    
    # Visual Settings
    visual_group = parser.add_argument_group('Visual Settings')
    visual_group.add_argument('--water-color', type=float, nargs=4, 
                             default=[0.4, 0.5, 0.4, 0.9], # Murky water
                             metavar=('R', 'G', 'B', 'A'),
                             help='Water color as RGBA values')
    
    # Animation Settings
    anim_group = parser.add_argument_group('Animation Settings')
    anim_group.add_argument('--start-frame', type=int, default=1,
                           help='First frame of animation')
    anim_group.add_argument('--end-frame', type=int, default=250,
                           help='Last frame of animation')
    
    # Camera Settings
    camera_group = parser.add_argument_group('Camera Settings')
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
    output_group.add_argument('--output', type=str, default='water_puddles.blend',
                             help='Output blend file name')
    
    # Filter out Blender's arguments
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    else:
        argv = []
    
    return parser.parse_args(argv)

def run_simulation_setup(args):
    print("Initializing Water Puddles Simulation...")
    
    # Cleanup
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # 1. Physics Environment
    physics.setup_rigid_body_world()
    
    # Create Buoyancy Field (Global, but only effective below water level)
    # Objects on high ground won't be affected because they are physically supported by the mesh
    physics.create_buoyancy_field(
        z_bottom=args.z_ground - 5.0, # Deep enough
        z_surface=args.z_water, # We'll update this dynamically or just use the arg if we trust it
        strength=args.buoyancy_strength,
        spawn_radius=args.terrain_size,
        hide=True
    )
    
    # 2. Terrain (Uneven Ground)
    # Increase strength to create deeper puddles
    strength = args.puddle_depth * 2.0
    
    terrain = ground.create_uneven_ground(
        z_base=args.z_ground,
        size=args.terrain_size,
        noise_scale=2.0, 
        strength=strength
    )
    # 2a. Prepare Ground for Boolean (Solidify for cutting)
    ground_cutter = ground.create_ground_cutter(terrain, thickness=10.0, offset=-1.0)
    
    # Visual Ground: Give it a small thickness
    ground.apply_thickness(terrain, thickness=0.5, offset=-1.0)
    
    materials.create_mud_material(terrain)
    
    # 3. Water Surface (Static Puddles)
    # We manually create a high-res plane with Noise Displacement to act as "Water"
    
    # Calculate water level relative to ground variation
    z_water_level = args.z_ground - (strength * 0.15)
    
    # Make water plane slightly smaller than terrain
    water_size = args.terrain_size * 0.95 
    
    water_visual = water.create_puddle_water(
        z_level=z_water_level, 
        size=water_size, 
        ground_cutter_obj=ground_cutter
    )
    
    # Cleanup Cutter
    bpy.data.objects.remove(ground_cutter, do_unlink=True)
    
    materials.create_water_material(water_visual, color=tuple(args.water_color))
    
    # 4. Scatter Debris (Small objects)
    debris_objects = []
    
    # Spawn them in the air so they fall
    z_spawn = z_water_level + 2.0
    
    positions = objects.generate_scattered_positions(
        num_points=args.num_debris,
        spawn_radius=args.terrain_size / 2.5,
        min_dist=0.8,
        z_pos=z_spawn
    )
    
    for i, pos in enumerate(positions):
        # Small randomized objects
        bpy.ops.mesh.primitive_cube_add(size=random.uniform(0.2, 0.4), location=pos)
        obj = bpy.context.active_object
        obj.name = f"Debris_{i}"
        
        # Random rotation
        obj.rotation_euler = (random.random(), random.random(), random.random())
        
        # Physics
        bpy.ops.rigidbody.object_add(type='ACTIVE')
        obj.rigid_body.mass = 0.2 # Light
        obj.rigid_body.friction = 0.7
        
        # Add material
        materials.create_sphere_material(obj, i, args.num_debris) # Reuse simple colored material
        debris_objects.append(obj)

    # 5. Interactions
    water.setup_dynamic_paint_interaction(
        water_visual, 
        debris_objects, 
        ripple_strength=2.0
    )
    
    # 6. Lighting
    lighting.setup_lighting_and_camera(
        camera_radius=args.terrain_size * 0.8,
        camera_height=8.0,
        resolution_x=args.resolution_x,
        resolution_y=args.resolution_y,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        enable_caustics=True,
        enable_volumetric=False,
        z_surface=z_water_level,
        z_bottom=args.z_ground,
        volumetric_density=0.0,
        caustic_scale=10.0
    )
    
    # 7. Point Tracking Visualization (2nd viewport with colored point cloud)
    if not args.no_point_tracking and debris_objects:
        point_tracking.setup_point_tracking_visualization(
            tracked_objects=debris_objects,
            points_per_object=args.points_per_object,
            setup_viewport=not bpy.app.background
    )
    
    print("✅ Water Puddles Simulation Ready!")
    if not args.no_point_tracking:
        print(f"   - Point Tracking: {args.points_per_object} points per object")

if __name__ == "__main__":
    try:
        args = parse_args()
        run_simulation_setup(args)
        
        # Disable cache and save
        if bpy.context.scene.rigidbody_world and bpy.context.scene.rigidbody_world.point_cache:
            bpy.context.scene.rigidbody_world.point_cache.use_disk_cache = False
            
        blend_path = os.path.abspath(args.output)
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)
        print(f"✅ Saved to {args.output}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
