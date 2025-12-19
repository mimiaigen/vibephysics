"""
Go2 Waypoint Walk

Demonstrates the Unitree Go2 robot dog walking through custom waypoints
in a smooth, curvy path on extreme uneven terrain.

Features:
- Extreme uneven terrain with configurable strength
- Multiple waypoint patterns (exploration, figure_eight, spiral, etc.)
- Multi-camera setup (center pointing, following)
- Dual viewport display (scene view + annotation view)
- Annotation support (bounding boxes, motion trails)

This script is a composition of foundation modules:
- foundation.trajectory: Waypoint patterns and path creation
- foundation.go2: Go2 loading, rigging, and animation
- camera.CameraManager: Multi-camera setup
- annotation.AnnotationManager: Bbox and trail annotations
"""

import sys
import os
import bpy
import argparse

# Setup imports (works with both pip install and local development)
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(_root, 'src'))

from vibephysics.foundation import scene, physics, ground, water, objects, materials, lighting, trajectory, go2
from vibephysics.annotation import AnnotationManager, viewport
from vibephysics.camera import CameraManager
from vibephysics.setup import save_blend


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Go2 robot walking through custom waypoints',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    sim_group = parser.add_argument_group('Simulation Settings')
    sim_group.add_argument('--terrain-size', type=float, default=30.0,
                          help='Size of the ground area')
    sim_group.add_argument('--terrain-strength', type=float, default=1.5,
                          help='Strength of terrain unevenness (higher = more extreme)')
    sim_group.add_argument('--puddle-depth', type=float, default=0.8,
                          help='Depth of water puddles (higher = more water coverage)')
    sim_group.add_argument('--start-frame', type=int, default=1,
                          help='Animation start frame')
    sim_group.add_argument('--end-frame', type=int, default=250,
                          help='Animation end frame')
    sim_group.add_argument('--walk-speed', type=float, default=1.0,
                          help='Walking speed multiplier')
    sim_group.add_argument('--num-spheres', type=int, default=100,
                          help='Number of falling debris spheres')
    
    waypoint_group = parser.add_argument_group('Waypoint Settings')
    waypoint_group.add_argument('--waypoint-pattern', type=str, default='exploration',
                               choices=trajectory.WAYPOINT_PATTERNS,
                               help='Waypoint pattern to follow')
    waypoint_group.add_argument('--waypoint-scale', type=float, default=6.0,
                               help='Scale of waypoint pattern')
    
    camera_group = parser.add_argument_group('Camera Settings')
    camera_group.add_argument('--camera-radius', type=float, default=15.0,
                             help='Camera distance from center (for center rig)')
    camera_group.add_argument('--camera-height', type=float, default=8.0,
                             help='Camera height')
    camera_group.add_argument('--active-camera', type=str, default='mounted',
                             choices=['center', 'following', 'mounted'],
                             help='Which camera rig to activate by default')
    camera_group.add_argument('--center-cameras', type=int, default=4,
                             help='Number of center-pointing cameras')
    camera_group.add_argument('--mounted-cameras', type=int, default=4,
                             help='Number of mounted cameras')
    camera_group.add_argument('--mounted-distance', type=float, default=0.3,
                             help='Distance of mounted cameras from robot')
    camera_group.add_argument('--mounted-mesh', type=str, default='visuals.001',
                             help='Name of mesh to mount cameras on')
    camera_group.add_argument('--mounted-rotation', type=float, default=-90.0,
                             help='Rotation offset for mounted cameras in degrees')
    
    visual_group = parser.add_argument_group('Visual Settings')
    visual_group.add_argument('--resolution-x', type=int, default=1920,
                             help='Render width')
    visual_group.add_argument('--resolution-y', type=int, default=1080,
                             help='Render height')
    visual_group.add_argument('--show-waypoints', action='store_true',
                             help='Show waypoint markers in scene')
    
    # Annotation Settings
    annotation_group = parser.add_argument_group('Annotation Settings')
    annotation_group.add_argument('--no-annotations', action='store_true',
                                 help='Disable all annotations')
    annotation_group.add_argument('--no-bbox', action='store_true',
                                 help='Disable bounding box annotations')
    annotation_group.add_argument('--no-trail', action='store_true',
                                 help='Disable motion trail annotations')
    annotation_group.add_argument('--trail-step', type=int, default=2,
                                 help='Frame step for motion trail sampling')
    
    output_group = parser.add_argument_group('Output Settings')
    output_group.add_argument('--output', type=str, default='output/go2_waypoint_walk.blend',
                             help='Output blend file name')
    
    # Support both: python script.py --arg  AND  blender -P script.py -- --arg
    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
    else:
        argv = sys.argv[1:]
    
    return parser.parse_args(argv)


def run_simulation_setup(args):
    print("=" * 60)
    print("  🐕 Go2 Waypoint Walk Simulation")
    print("=" * 60)
    print(f"   Pattern: {args.waypoint_pattern}")
    print(f"   Frames: {args.start_frame} - {args.end_frame}")
    
    # Get USD path (auto-downloads if needed)
    usd_path = go2.get_go2_usd_path()
    
    # 1. Universal scene initialization
    scene.init_simulation(
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        physics_config={'substeps': 20, 'solver_iters': 20, 'cache_buffer': 0}
    )
    
    # 2. Terrain (Extreme Uneven Ground)
    z_ground = 0.0
    strength = args.terrain_strength
    
    terrain = ground.create_uneven_ground(
        z_base=z_ground,
        size=args.terrain_size,
        noise_scale=3.0,  # More frequent bumps
        strength=strength
    )
    ground.apply_thickness(terrain, thickness=0.5, offset=-1.0)
    materials.create_mud_material(terrain)
    
    # 3. Water Surface (Puddles with Boolean cutting)
    print("  - Creating water puddles...")
    z_water_level = z_ground - (args.puddle_depth * 0.15)  # Adjust for water coverage
    water_size = args.terrain_size * 0.95
    
    # Create cutter and water
    ground_cutter = ground.create_ground_cutter(terrain, thickness=10.0, offset=-1.0)
    water_visual = water.create_puddle_water(
        z_level=z_water_level,
        size=water_size,
        ground_cutter_obj=ground_cutter
    )
    materials.create_water_material(water_visual, color=(0.3, 0.5, 0.6, 0.85))  # Blue-ish water
    
    # 3a. Add falling debris spheres
    z_spawn = z_water_level + 3.0
    positions = objects.generate_scattered_positions(
        num_points=args.num_spheres,
        spawn_radius=args.terrain_size / 3.0,
        min_dist=0.8,
        z_pos=z_spawn
    )
    debris_objects = objects.create_falling_spheres(
        positions=positions,
        radius_range=(0.15, 0.3),
        physics={'mass': 0.3, 'friction': 0.7, 'restitution': 0.3},
        num_total=args.num_spheres
    )
    print(f"  - Created {len(debris_objects)} falling spheres")
    
    # 4. Create waypoint pattern (from foundation.trajectory)
    waypoints = trajectory.create_waypoint_pattern(args.waypoint_pattern, args.waypoint_scale)
    
    print(f"\n  - Creating path through {len(waypoints)} waypoints...")
    path = trajectory.create_waypoint_path(
        waypoints=waypoints,
        closed=True,  # Loop back to start
        z_location=1.0,  # Elevated for path following
        name="Go2WaypointPath"
    )
    
    # 5. Load Go2
    print(f"  - Loading Go2 robot from {usd_path}...")
    base_obj, robot_parts, robot_meshes = go2.load_go2(usd_path)
    
    if not base_obj:
        print("❌ Failed to load Go2! Aborting.")
        return None
    
    # 6. Rig Go2
    armature = go2.rig_go2(base_obj)
    
    # 7. Animate Go2 walking along waypoint path
    print(f"  - Animating Go2 walking...")
    go2.animate_go2_walking(
        armature=armature,
        path_curve=path,
        ground_object=terrain,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        speed=args.walk_speed
    )
    
    # 7a. Setup robot collision (kinematic - animated but can push objects)
    # Use go2's dedicated collision setup that handles USD mesh hierarchy correctly
    go2.setup_go2_collision(robot_meshes, kinematic=True, friction=0.8, restitution=0.1)
    
    # 7b. Water Interactions (dynamic paint ripples)
    all_interactors = debris_objects + robot_meshes
    water.setup_dynamic_paint_interaction(
        water_visual,
        all_interactors,
        ripple_strength=2.0
    )
    print(f"  - Water interaction setup: {len(all_interactors)} objects")
    
    # 8. Annotation Setup using AnnotationManager
    if not args.no_annotations and robot_parts:
        print("\n📊 Setting up Annotations...")
        
        mgr = AnnotationManager(collection_name="AnnotationViz")
        
        bbox_robot = not args.no_bbox
        trail_center = not args.no_trail
        
        # Annotate robot parts
        mgr.annotate_robot(
            robot_parts=robot_parts,
            center_object=armature,
            debris_objects=[],
            bbox_robot=bbox_robot,
            bbox_debris=False,
            trail_center=trail_center,
            trail_debris=False,
            point_tracking=False,
            start_frame=args.start_frame,
            end_frame=args.end_frame,
            trail_step=args.trail_step
        )
        
        # Finalize - setup dual viewport
        mgr.finalize(setup_viewport=True)
        viewport.create_viewport_restore_script("AnnotationViz")
    
    # 9. Lighting
    lighting.setup_lighting(
        resolution_x=args.resolution_x,
        resolution_y=args.resolution_y,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        enable_caustics=False,
        enable_volumetric=False
    )
    
    # 10. Camera Setup - Center, Following, and Mounted cameras
    print("\n📷 Setting up Camera Rigs...")
    
    cam_manager = CameraManager()
    
    # 10a. Center pointing cameras - arranged in a circle, pointing at scene center
    center_rig = cam_manager.add_center_pointing(
        'center', 
        num_cameras=args.center_cameras, 
        radius=args.camera_radius, 
        height=args.camera_height
    )
    center_rig.create(target_location=(0, 0, 0))
    print(f"  - Center rig: {args.center_cameras} cameras at radius={args.camera_radius}, height={args.camera_height}")
    
    # 10b. Following camera - follows robot from above
    follow_rig = cam_manager.add_following(
        'following',
        height=args.camera_height,
        look_angle=60
    )
    follow_rig.create(target=armature)
    print(f"  - Following camera: height={args.camera_height}, look_angle=60°")
    
    # 10c. Mounted cameras - attached to robot body (POV cameras)
    mount_target = None
    search_name = args.mounted_mesh.lower()
    
    # Search all objects for mount target mesh (USD imports may not be in robot_parts list)
    # Exclude BBox annotation meshes and hidden objects
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and not obj.name.startswith('BBox'):
            if not obj.hide_viewport:  # Only visible meshes
                if obj.name.lower() == search_name or search_name in obj.name.lower():
                    mount_target = obj
                    break
    
    # Fallback: search for any "visuals" mesh (excluding BBox and hidden)
    if mount_target is None:
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and 'visuals' in obj.name.lower():
                if not obj.name.startswith('BBox') and not obj.hide_viewport:
                    mount_target = obj
                    print(f"  - Warning: '{args.mounted_mesh}' not found, using '{obj.name}'")
                    break
    
    # Final fallback: use armature as mount target
    if mount_target is None and armature:
        mount_target = armature
        print(f"  - Warning: No mesh found, mounting on armature")
    
    if mount_target:
        # Go2 uses +X as forward direction
        mounted_rig = cam_manager.add_object_mounted(
            'mounted',
            num_cameras=args.mounted_cameras,
            distance=args.mounted_distance,
            height_offset=0.1,
            forward_axis='X',  # Go2 faces +X direction
            rotation_offset=args.mounted_rotation
        )
        mounted_cams = mounted_rig.create(parent_object=mount_target, lens=20)
        
        # Add offset to mounted cameras (similar to robot_forest_walk.py)
        for cam in mounted_cams:
            cam.location.x -= 0.5  # back offset
            cam.location.y -= 0.0  # right offset
            cam.location.z -= 0.0  # down offset
        
        print(f"  - Mounted rig: {args.mounted_cameras} cameras on '{mount_target.name}' (lens=20, offset: back=0.2m, right=0.1m)")
    else:
        print("  - Mounted rig: Skipped (no suitable mesh part found)")
    
    # Activate the requested camera rig
    if args.active_camera == 'center':
        cam_manager.activate_rig('center', camera_index=args.center_cameras - 1)
        print(f"  - Active camera: Center rig")
    elif args.active_camera == 'following':
        cam_manager.activate_rig('following', camera_index=0)
        print(f"  - Active camera: Following camera")
    elif args.active_camera == 'mounted' and mount_target:
        cam_manager.activate_rig('mounted', camera_index=0)
        print(f"  - Active camera: Mounted rig (POV)")
    else:
        # Default fallback
        if mount_target:
            cam_manager.activate_rig('mounted', camera_index=0)
            print(f"  - Active camera: Mounted rig (default)")
        else:
            cam_manager.activate_rig('following', camera_index=0)
            print(f"  - Active camera: Following camera (default)")
    
    # 11. Bake physics
    print("\n  - Baking physics...")
    physics.bake_all()
    
    print("\n" + "=" * 60)
    print("✅ Go2 Waypoint Walk Complete!")
    print("=" * 60)
    print(f"   Waypoint pattern: {args.waypoint_pattern}")
    print(f"   Total waypoints: {len(waypoints)}")
    print(f"   Debris spheres: {len(debris_objects)}")
    print(f"   Animation: {args.end_frame} frames")
    print(f"\n💡 Dual viewport setup: Left=Scene, Right=Annotations")
    
    return armature


def main():
    args = parse_args()
    run_simulation_setup(args)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save blend file
    save_blend(args.output)


if __name__ == "__main__":
    main()
