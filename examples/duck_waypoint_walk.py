"""
Duck Waypoint Walk

Demonstrates the Open Duck robot walking through custom waypoints
in a smooth, curvy path. Shows off the trajectory.create_waypoint_path()
function with the duck's waddle animation.
"""

import sys
import os
import bpy
import argparse
from mathutils import Vector

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from foundation import scene, physics, ground, water, open_duck, objects, materials, lighting, trajectory
from annotation import point_tracking
from utils import viewport


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Duck walking through custom waypoints',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    sim_group = parser.add_argument_group('Simulation Settings')
    sim_group.add_argument('--terrain-size', type=float, default=30.0,
                          help='Size of the ground area')
    sim_group.add_argument('--start-frame', type=int, default=1,
                          help='Animation start frame')
    sim_group.add_argument('--end-frame', type=int, default=400,
                          help='Animation end frame')
    sim_group.add_argument('--walk-speed', type=float, default=0.8,
                          help='Walking speed multiplier')
    
    waypoint_group = parser.add_argument_group('Waypoint Settings')
    waypoint_group.add_argument('--waypoint-pattern', type=str, default='exploration',
                               choices=['exploration', 's_curve', 'figure_eight', 'spiral', 'zigzag'],
                               help='Waypoint pattern to follow')
    waypoint_group.add_argument('--waypoint-scale', type=float, default=8.0,
                               help='Scale of waypoint pattern')
    
    camera_group = parser.add_argument_group('Camera Settings')
    camera_group.add_argument('--camera-radius', type=float, default=25.0,
                             help='Camera distance from center')
    camera_group.add_argument('--camera-height', type=float, default=12.0,
                             help='Camera height')
    camera_group.add_argument('--follow-duck', action='store_true',
                             help='Camera follows the duck')
    
    visual_group = parser.add_argument_group('Visual Settings')
    visual_group.add_argument('--resolution-x', type=int, default=1920,
                             help='Render width')
    visual_group.add_argument('--resolution-y', type=int, default=1080,
                             help='Render height')
    visual_group.add_argument('--water-color', type=float, nargs=3, default=[0.1, 0.3, 0.5],
                             help='Water color RGB')
    visual_group.add_argument('--show-waypoints', action='store_true',
                             help='Show waypoint markers in scene')
    
    tracking_group = parser.add_argument_group('Point Tracking')
    tracking_group.add_argument('--no-point-tracking', action='store_true',
                               help='Disable point tracking visualization')
    tracking_group.add_argument('--points-per-object', type=int, default=20,
                               help='Number of tracked points')
    
    output_group = parser.add_argument_group('Output Settings')
    output_group.add_argument('--output', type=str, default='duck_waypoint_walk.blend',
                             help='Output blend file name')
    
    # Parse args
    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
    else:
        argv = []
    
    return parser.parse_args(argv)


def create_waypoint_pattern(pattern, scale=8.0):
    """
    Create different waypoint patterns.
    
    Args:
        pattern: Pattern name
        scale: Size scaling factor
        
    Returns:
        List of (x, y) waypoints
    """
    if pattern == 'exploration':
        # Exploration pattern - visits different areas
        waypoints = [
            (0, 0),
            (scale, scale * 0.5),
            (scale * 0.5, scale),
            (-scale * 0.3, scale * 0.8),
            (-scale, scale * 0.2),
            (-scale * 0.8, -scale * 0.5),
            (0, -scale),
            (scale * 0.6, -scale * 0.7),
            (scale * 0.8, 0),
        ]
    
    elif pattern == 's_curve':
        # Smooth S-curve
        waypoints = [
            (-scale, -scale),
            (-scale * 0.5, -scale * 0.3),
            (0, 0),
            (scale * 0.5, scale * 0.3),
            (scale, scale),
            (scale * 0.5, scale * 0.7),
            (0, scale * 0.4),
            (-scale * 0.5, 0),
        ]
    
    elif pattern == 'figure_eight':
        # Figure-8 with more control points for smoothness
        waypoints = [
            (0, 0),
            (scale * 0.7, scale * 0.5),
            (scale * 0.9, scale * 0.9),
            (scale * 0.5, scale),
            (0, scale * 0.7),
            (-scale * 0.5, scale),
            (-scale * 0.9, scale * 0.9),
            (-scale * 0.7, scale * 0.5),
            (0, 0),
            (scale * 0.7, -scale * 0.5),
            (scale * 0.9, -scale * 0.9),
            (scale * 0.5, -scale),
            (0, -scale * 0.7),
            (-scale * 0.5, -scale),
            (-scale * 0.9, -scale * 0.9),
            (-scale * 0.7, -scale * 0.5),
        ]
    
    elif pattern == 'spiral':
        # Outward spiral
        import math
        waypoints = []
        num_points = 12
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi * 2  # 2 full rotations
            radius = scale * (0.2 + i / num_points * 0.8)  # Grow from 0.2 to 1.0
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            waypoints.append((x, y))
    
    elif pattern == 'zigzag':
        # Zigzag pattern
        waypoints = [
            (-scale, -scale * 0.8),
            (scale, -scale * 0.5),
            (-scale * 0.8, -scale * 0.2),
            (scale * 0.9, scale * 0.1),
            (-scale, scale * 0.4),
            (scale * 0.8, scale * 0.7),
            (-scale * 0.7, scale),
        ]
    
    return waypoints


# Waypoint marker creation moved to foundation/objects.py
# Use: objects.create_waypoint_markers(waypoints, z_height)


def run_simulation_setup(args):
    print("🦆 Duck Waypoint Walk Simulation")
    print(f"   Pattern: {args.waypoint_pattern}")
    print(f"   Frames: {args.start_frame} - {args.end_frame}")
    
    # 1. Universal scene initialization
    scene.init_simulation(
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        physics_config={'substeps': 20, 'solver_iters': 20, 'cache_buffer': 50}
    )
    
    # 2. Terrain (Slightly uneven ground)
    z_ground = -1.0
    terrain = ground.create_uneven_ground(
        z_base=z_ground,
        size=args.terrain_size,
        noise_scale=3.0,
        strength=0.4  # Gentle terrain
    )
    ground.apply_thickness(terrain, thickness=0.5, offset=-1.0)
    materials.create_mud_material(terrain)
    physics.setup_ground_physics(terrain)
    
    # 3. Optional water puddle (shallow)
    z_water_level = z_ground + 0.05
    water_visual = water.create_flat_surface(
        size=args.terrain_size * 0.7,
        z_level=z_water_level,
        subdivisions=150
    )
    materials.create_water_material(water_visual, color=tuple(args.water_color))
    
    # 4. Create waypoint pattern
    waypoints = create_waypoint_pattern(args.waypoint_pattern, args.waypoint_scale)
    
    # Show waypoint markers if requested
    if args.show_waypoints:
        objects.create_waypoint_markers(waypoints, z_height=0.5, size=0.3)
    
    # 5. Create smooth path through waypoints
    print(f"  - creating path through {len(waypoints)} waypoints...")
    path = trajectory.create_waypoint_path(
        waypoints=waypoints,
        closed=True,  # Loop back to start
        z_location=2.0,  # Elevated for path following
        name="DuckWaypointPath"
    )
    
    # 6. Load and setup Open Duck
    print(f"  - loading Open Duck robot...")
    armature, robot_parts = open_duck.load_open_duck(
        transform={'location': (0, 0, 0), 'rotation': (0, 0, 0), 'scale': 0.3}
    )
    
    if not armature:
        print("❌ Failed to load Duck! Aborting.")
        return
    
    # 7. Animate duck walking along waypoint path
    print(f"  - animating duck walking...")
    open_duck.animate_duck_walking(
        armature=armature,
        path_curve=path,
        ground_object=terrain,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        speed=args.walk_speed
    )
    
    # 8. Setup collision
    open_duck.setup_duck_collision(robot_parts, kinematic=True)
    
    # 9. Water ripples from duck
    water.setup_robot_water_interaction(
        water_visual,
        robot_parts,
        [],  # No debris
        ripple_strength=12.0
    )
    
    # 10. Point Tracking Visualization
    # Creates dual viewport: Left=scene, Right=point cloud tracking
    if not args.no_point_tracking and robot_parts:
        point_tracking.setup_point_tracking_visualization(
            tracked_objects=robot_parts,
            points_per_object=max(5, args.points_per_object // len(robot_parts)) if robot_parts else 5,
            setup_viewport=not bpy.app.background
        )
    
    # 11. Lighting and Camera
    lighting.setup_lighting_and_camera(
        camera_radius=args.camera_radius,
        camera_height=args.camera_height,
        resolution_x=args.resolution_x,
        resolution_y=args.resolution_y,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        enable_caustics=True,
        enable_volumetric=False,
        z_surface=z_water_level,
        z_bottom=z_ground - 3.0,
        volumetric_density=0.0,
        caustic_scale=8.0
    )
    
    # Optional: Camera follows duck
    if args.follow_duck:
        lighting.setup_camera_tracking(armature, track_axis='TRACK_NEGATIVE_Z', up_axis='UP_Y')
    
    # 12. Bake physics
    print("  - baking physics...")
    physics.bake_all()
    
    print("✅ Duck Waypoint Walk Complete!")
    print(f"   Waypoint pattern: {args.waypoint_pattern}")
    print(f"   Total waypoints: {len(waypoints)}")
    print(f"   Animation: {args.end_frame} frames")


def main():
    args = parse_args()
    run_simulation_setup(args)
    
    # Save blend file
    if not bpy.app.background:
        output_path = os.path.join(os.getcwd(), args.output)
    else:
        output_path = args.output
    
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"💾 Saved to: {output_path}")


if __name__ == "__main__":
    main()
