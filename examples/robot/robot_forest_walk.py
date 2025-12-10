"""
Duck Forest Walk

Demonstrates the Open Duck robot walking through a dense forest on uneven terrain.
Features:
- Uneven ground (hill-like terrain)
- Dense forest with 100 trees using Blender instancing
- Path-finding that avoids tree collisions
- Trees positioned correctly on uneven ground
- Realistic scaling and random variations
- IK-based walking on uneven terrain
"""

import sys
import os
import bpy
import argparse
import random
import math
from mathutils import Vector

# Setup imports (works with both pip install and local development)
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(_root, 'src'))

from vibephysics.foundation import scene, physics, ground, objects, materials, lighting, trajectory, open_duck, robot
from vibephysics.annotation import AnnotationManager, viewport
from vibephysics.camera import CameraManager
from vibephysics.setup import importer, save_blend


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Duck walking through forest on uneven terrain',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    sim_group = parser.add_argument_group('Simulation Settings')
    sim_group.add_argument('--terrain-size', type=float, default=150.0,
                          help='Size of the ground area (default: 150m for more trees)')
    sim_group.add_argument('--terrain-strength', type=float, default=3.0,
                          help='Height variation of terrain')
    sim_group.add_argument('--start-frame', type=int, default=1,
                          help='Animation start frame')
    sim_group.add_argument('--end-frame', type=int, default=350,
                          help='Animation end frame')
    sim_group.add_argument('--walk-speed', type=float, default=0.6,
                          help='Walking speed multiplier')
    
    forest_group = parser.add_argument_group('Forest Settings')
    forest_group.add_argument('--tree-asset', type=str, 
                             default='./assets/tree_asset_grid.blend',
                             help='Path to tree asset blend file')
    forest_group.add_argument('--num-trees', type=int, default=50,
                             help='Number of trees in forest')
    forest_group.add_argument('--tree-height-min', type=float, default=5.0,
                             help='Minimum tree height in meters (default: 5.0m)')
    forest_group.add_argument('--tree-height-max', type=float, default=8.0,
                             help='Maximum tree height in meters (default: 8.0m)')
    forest_group.add_argument('--min-tree-distance', type=float, default=0.5,
                             help='Minimum distance between trees in meters (default: 0.5m)')
    forest_group.add_argument('--path-width', type=float, default=1.5,
                             help='Width of walking path through forest')
    forest_group.add_argument('--robot-height', type=float, default=0.5,
                             help='Robot height in meters (default: 0.5m)')
    forest_group.add_argument('--tree-collision', action='store_true',
                             help='Enable rigid body collision on trees (slower but allows physics interaction)')
    forest_group.add_argument('--no-physics', action='store_true',
                             help='Disable all physics (fastest playback, pure animation only)')
    
    camera_group = parser.add_argument_group('Camera Settings')
    camera_group.add_argument('--camera-radius', type=float, default=30.0,
                             help='Camera distance from center (for center rig)')
    camera_group.add_argument('--camera-height', type=float, default=15.0,
                             help='Camera height')
    camera_group.add_argument('--active-camera', type=str, default='mounted',
                             choices=['center', 'following', 'mounted'],
                             help='Which camera rig to activate by default')
    camera_group.add_argument('--center-cameras', type=int, default=4,
                             help='Number of center-pointing cameras')
    camera_group.add_argument('--mounted-cameras', type=int, default=4,
                             help='Number of mounted cameras')
    camera_group.add_argument('--mounted-distance', type=float, default=0.15,
                             help='Distance of mounted cameras from robot head')
    camera_group.add_argument('--mounted-mesh', type=str, default='head',
                             help='Name (or partial name) of mesh to mount cameras on')
    camera_group.add_argument('--mounted-rotation', type=float, default=0.0,
                             help='Rotation offset for mounted cameras in degrees')
    
    visual_group = parser.add_argument_group('Visual Settings')
    visual_group.add_argument('--resolution-x', type=int, default=1920,
                             help='Render width')
    visual_group.add_argument('--resolution-y', type=int, default=1080,
                             help='Render height')
    
    annotation_group = parser.add_argument_group('Annotation Settings')
    annotation_group.add_argument('--no-annotations', action='store_true',
                                 help='Disable all annotations')
    annotation_group.add_argument('--no-bbox', action='store_true',
                                 help='Disable bounding box annotations')
    annotation_group.add_argument('--no-trail', action='store_true',
                                 help='Disable motion trail annotations')
    annotation_group.add_argument('--no-point-tracking', action='store_true',
                                 help='Disable point tracking visualization')
    annotation_group.add_argument('--points-per-object', type=int, default=30,
                                 help='Number of tracked points per object')
    annotation_group.add_argument('--trail-step', type=int, default=2,
                                 help='Frame step for motion trail sampling')
    annotation_group.add_argument('--frustum-mode', type=str, default='frustum_only',
                                 choices=['all', 'highlight', 'frustum_only'],
                                 help='Point tracking frustum mode: all (show all), highlight (all visible, in-frustum red), frustum_only (only in-frustum visible)')
    annotation_group.add_argument('--frustum-distance', type=float, default=30.0,
                                 help='Frustum far distance in meters (default: 20m)')
    annotation_group.add_argument('--points-per-tree', type=int, default=100,
                                 help='Number of tracked points per tree (default: 1000)')
    
    output_group = parser.add_argument_group('Output Settings')
    output_group.add_argument('--output', type=str, default='output/duck_forest_walk.blend',
                             help='Output blend file path')
    
    # Support both: python script.py --arg  AND  blender -P script.py -- --arg
    if '--' in sys.argv:
        argv = sys.argv[sys.argv.index('--') + 1:]
    else:
        argv = sys.argv[1:]
    
    return parser.parse_args(argv)


def get_tree_bounding_dimensions(tree_obj):
    """
    Get the bounding box dimensions of a tree object in LOCAL space.
    Returns (width, depth, height, local_min_z)
    
    local_min_z is the Z coordinate of the bottom of the mesh relative to the object origin.
    If the origin is at the center of the tree, local_min_z will be negative.
    If the origin is at the bottom, local_min_z will be 0.
    """
    # Get LOCAL bounding box corners (relative to object origin, before any transforms)
    # bound_box gives 8 corners in local space
    bbox_corners = [Vector(corner) for corner in tree_obj.bound_box]
    
    # Calculate dimensions in local space
    min_x = min(c.x for c in bbox_corners)
    max_x = max(c.x for c in bbox_corners)
    min_y = min(c.y for c in bbox_corners)
    max_y = max(c.y for c in bbox_corners)
    min_z = min(c.z for c in bbox_corners)
    max_z = max(c.z for c in bbox_corners)
    
    width = max_x - min_x
    depth = max_y - min_y
    height = max_z - min_z
    
    # local_min_z: the Z of the bottom of the mesh relative to origin (usually negative if origin is at center)
    local_min_z = min_z
    
    return width, depth, height, local_min_z


def get_object_world_min_z(obj):
    """
    Get the actual world-space minimum Z of an object's mesh after all transforms.
    This gives the exact bottom of the tree in world coordinates.
    
    Uses the evaluated object from depsgraph to account for any modifiers.
    """
    # Force update to get accurate bounds
    bpy.context.view_layer.update()
    
    # Get evaluated object (with modifiers applied) for accurate bounds
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    
    # Get world-space bounding box corners from evaluated object
    bbox_corners = [obj_eval.matrix_world @ Vector(corner) for corner in obj_eval.bound_box]
    
    # Return minimum Z (the bottom of the mesh in world space)
    return min(c.z for c in bbox_corners)


def place_tree_on_ground(tree_instance, ground_z, terrain):
    """
    Adjust tree position so its mesh bottom is exactly on the ground.
    Uses raycast to verify and the actual world-space bounding box.
    
    Args:
        tree_instance: The tree object to place
        ground_z: Initial ground Z from raycast at tree center
        terrain: The terrain object (for verification raycast)
    """
    # Force scene update to get accurate bounding box
    bpy.context.view_layer.update()
    
    # Get current world min Z of the tree mesh
    current_min_z = get_object_world_min_z(tree_instance)
    
    # Calculate how much we need to move the tree
    z_adjustment = ground_z - current_min_z
    
    # Adjust the tree's Z position
    tree_instance.location.z += z_adjustment
    
    # Update again to reflect the change
    bpy.context.view_layer.update()


def raycast_ground_height(xy_point, ground_object, start_height=100.0):
    """
    Raycast to find exact ground height at a specific XY position.
    Uses foundation.robot.raycast_ground() for robust ground detection.
    
    NOTE: The terrain has a Displace modifier, so we need to raycast against
    the evaluated mesh (which raycast_ground does automatically via depsgraph).
    """
    # Use the foundation module's robust raycast function
    ground_z = robot.raycast_ground(
        bpy.context.scene,
        xy_point,
        start_height=start_height,
        ground_objects=[ground_object]
    )
    return ground_z


def load_tree_assets(tree_asset_path):
    """
    Load tree assets from blend file and return list of tree objects.
    Also prints dimension info for scale verification.
    """
    print(f"  - Loading tree assets from {tree_asset_path}...")
    
    if not os.path.exists(tree_asset_path):
        print(f"❌ Error: Tree asset file not found: {tree_asset_path}")
        return []
    
    # Import all objects from the blend file
    tree_objects = importer.load_asset(tree_asset_path, collection_name="TreeAssets")
    
    # Filter to only keep mesh objects
    tree_meshes = [obj for obj in tree_objects if obj.type == 'MESH']
    
    # Print dimension info for each tree
    print(f"    Found {len(tree_meshes)} tree mesh objects:")
    tree_heights = []
    for i, tree in enumerate(tree_meshes):
        width, depth, height, local_min_z = get_tree_bounding_dimensions(tree)
        tree_heights.append(height)
        print(f"      [{i}] {tree.name}: H={height:.2f}m, W={width:.2f}m, D={depth:.2f}m, local_min_z={local_min_z:.2f}m")
    
    # Print average height info
    if tree_heights:
        avg_height = sum(tree_heights) / len(tree_heights)
        min_height = min(tree_heights)
        max_height = max(tree_heights)
        
        print(f"    Tree asset heights: min={min_height:.2f}m, max={max_height:.2f}m, avg={avg_height:.2f}m")
        print(f"    💡 Default settings will scale trees to 5-8m tall (use --tree-height-min/max to adjust)")
    
    # Hide the originals (they'll be used as instancing sources)
    for tree in tree_meshes:
        tree.hide_viewport = True
        tree.hide_render = True
    
    return tree_meshes


def create_path_through_forest(terrain_size, path_width, num_waypoints=12):
    """
    Create a winding curvy path through the forest area.
    Returns list of waypoints that define the path corridor.
    Path stays well within terrain bounds.
    """
    # Create a serpentine path that winds through the forest
    waypoints = []
    
    # Use smaller portion of terrain for path (stay well within terrain bounds)
    # terrain spans from -terrain_size/2 to +terrain_size/2
    # path_range should be much smaller to stay inside
    path_range = terrain_size * 0.25  # Use middle 50% of terrain (safe margin)
    
    # Generate waypoints in a winding pattern
    for i in range(num_waypoints):
        t = i / (num_waypoints - 1)
        
        # Create a curvy S-curve path (stays within path_range bounds)
        x = -path_range + (path_range * 2) * t
        y = path_range * math.sin(t * math.pi * 2.5) * 0.5  # Reduced amplitude
        
        waypoints.append((x, y))
    
    return waypoints


def check_tree_collision(tree_pos, tree_radius, path_waypoints, path_width, existing_trees, min_tree_distance):
    """
    Check if a tree position collides with the path or other trees.
    - Path must remain completely clear (strict)
    - Trees must have at least min_tree_distance between them (edge to edge)
    """
    # Check collision with path - THIS IS STRICT (path must be clear)
    for i in range(len(path_waypoints) - 1):
        wp1 = Vector((path_waypoints[i][0], path_waypoints[i][1], 0))
        wp2 = Vector((path_waypoints[i + 1][0], path_waypoints[i + 1][1], 0))
        tree_2d = Vector((tree_pos[0], tree_pos[1], 0))
        
        # Distance from point to line segment
        line_vec = wp2 - wp1
        point_vec = tree_2d - wp1
        
        if line_vec.length > 0:
            t = max(0, min(1, point_vec.dot(line_vec) / line_vec.length_squared))
            closest_point = wp1 + t * line_vec
            dist = (tree_2d - closest_point).length
            
            # Consider both path width and tree radius - keep path clear!
            if dist < (path_width / 2 + tree_radius):
                return True
    
    # Check collision with existing trees - minimum distance between tree edges
    for existing_pos, existing_radius in existing_trees:
        dist = math.sqrt((tree_pos[0] - existing_pos[0])**2 + (tree_pos[1] - existing_pos[1])**2)
        # Distance between tree centers must be >= sum of radii + min_tree_distance
        required_distance = tree_radius + existing_radius + min_tree_distance
        if dist < required_distance:
            return True
    
    return False


def place_forest_trees(tree_templates, terrain, terrain_size, path_waypoints, path_width, 
                      num_trees, tree_height_min, tree_height_max, min_tree_distance, args):
    """
    Place trees in the forest using Blender instancing.
    Trees are placed ON THE GROUND with heights ranging from tree_height_min to tree_height_max.
    Minimum distance between trees is min_tree_distance.
    Path must remain clear for robot navigation.
    """
    print(f"\n  - Placing {num_trees} trees on ground...")
    print(f"    Tree heights: {tree_height_min}m - {tree_height_max}m")
    print(f"    Min tree distance: {min_tree_distance}m")
    print(f"    Path width (must remain clear): {path_width}m")
    
    tree_instances = []
    existing_trees = []  # List of (position, radius) tuples
    
    # Create a collection for tree instances
    tree_collection = bpy.data.collections.new("ForestTrees")
    bpy.context.scene.collection.children.link(tree_collection)
    
    # Robot dimensions for path clearance
    robot_height = args.robot_height if hasattr(args, 'robot_height') else 0.5
    robot_radius = robot_height * 0.5  # Approximate robot width as half its height
    
    attempts = 0
    max_attempts = num_trees * 150
    
    while len(tree_instances) < num_trees and attempts < max_attempts:
        attempts += 1
        
        # Random position within terrain bounds (stay well inside)
        # terrain spans from -terrain_size/2 to +terrain_size/2
        margin = terrain_size * 0.15  # 15% margin from edge to ensure trees are on ground
        x = random.uniform(-terrain_size/2 + margin, terrain_size/2 - margin)
        y = random.uniform(-terrain_size/2 + margin, terrain_size/2 - margin)
        
        # Random tree template
        tree_template = random.choice(tree_templates)
        
        # Get tree base dimensions (at scale 1.0) in LOCAL space
        width, depth, base_height, local_min_z = get_tree_bounding_dimensions(tree_template)
        
        # Calculate scale to achieve target height (randomly between min and max)
        target_height = random.uniform(tree_height_min, tree_height_max)
        if base_height > 0:
            scale = target_height / base_height
        else:
            scale = 1.0
        
        # Calculate actual tree radius at this scale
        tree_radius = max(width, depth) * scale / 2
        
        # Check collision with path and other trees
        if check_tree_collision((x, y), tree_radius + robot_radius, path_waypoints, 
                               path_width, existing_trees, min_tree_distance):
            continue
        
        # Get EXACT ground height at this position using raycast (uses foundation.robot.raycast_ground)
        ground_z = raycast_ground_height((x, y), terrain, start_height=100.0)
        
        # Create instance using linked duplicate
        bpy.ops.object.select_all(action='DESELECT')
        tree_template.select_set(True)
        bpy.context.view_layer.objects.active = tree_template
        
        # Duplicate as instance
        bpy.ops.object.duplicate_move_linked(
            OBJECT_OT_duplicate={"linked": True, "mode": 'TRANSLATION'}
        )
        
        tree_instance = bpy.context.active_object
        tree_instance.hide_viewport = False
        tree_instance.hide_render = False
        
        # Set position (temporary), rotation, and scale FIRST
        tree_instance.location = (x, y, 0)  # Temporary Z
        tree_instance.rotation_euler = (0, 0, random.uniform(0, 2 * math.pi))
        tree_instance.scale = (scale, scale, scale)
        
        # Update scene to get accurate bounding box
        bpy.context.view_layer.update()
        
        # NOW place tree exactly on ground using actual mesh bounds
        place_tree_on_ground(tree_instance, ground_z, terrain)
        
        # Move to tree collection
        for coll in tree_instance.users_collection:
            coll.objects.unlink(tree_instance)
        tree_collection.objects.link(tree_instance)
        
        # Verify tree is on ground (debug first few trees)
        if len(tree_instances) < 5:
            actual_min_z = get_object_world_min_z(tree_instance)
            diff = abs(actual_min_z - ground_z)
            status = "✓" if diff < 0.1 else "⚠️"
            print(f"    {status} Tree {len(tree_instances)}: pos=({x:.1f},{y:.1f}), ground_z={ground_z:.2f}, mesh_bottom={actual_min_z:.2f}, diff={diff:.3f}m")
        
        # Add to lists
        tree_instances.append(tree_instance)
        existing_trees.append(((x, y), tree_radius))
        
        if len(tree_instances) % 20 == 0:
            print(f"    Placed {len(tree_instances)}/{num_trees} trees...")
    
    print(f"  - Successfully placed {len(tree_instances)} trees in dense forest (attempts: {attempts})")
    print(f"    Trees are densely packed, path remains clear for robot")
    
    # Optionally add rigid body collision to trees (disabled by default for performance)
    no_physics = hasattr(args, 'no_physics') and args.no_physics
    tree_collision = hasattr(args, 'tree_collision') and args.tree_collision
    
    if tree_collision and not no_physics:
        print(f"  - Adding rigid body collision to trees (this may slow down animation)...")
        for tree_instance in tree_instances:
            bpy.ops.object.select_all(action='DESELECT')
            tree_instance.select_set(True)
            bpy.context.view_layer.objects.active = tree_instance
            
            try:
                if not tree_instance.rigid_body:
                    bpy.ops.rigidbody.object_add(type='PASSIVE')
                tree_instance.rigid_body.collision_shape = 'CONVEX_HULL'
                tree_instance.rigid_body.friction = 0.8
            except:
                pass  # Skip if collision setup fails
        print(f"    Added collision to {len(tree_instances)} trees")
    elif no_physics:
        print(f"    All physics disabled (--no-physics)")
    else:
        print(f"    Tree collision disabled (use --tree-collision to enable)")
    
    return tree_instances


def run_simulation_setup(args):
    print("=" * 60)
    print("  🦆🌲 Duck Forest Walk Simulation")
    print("=" * 60)
    print(f"   Terrain size: {args.terrain_size}m")
    print(f"   Terrain strength: {args.terrain_strength}m")
    print(f"   Number of trees: {args.num_trees}")
    print(f"   Tree height range: {args.tree_height_min}m - {args.tree_height_max}m")
    print(f"   Min tree distance: {args.min_tree_distance}m")
    print(f"   Robot height: {args.robot_height}m")
    print(f"   Path width: {args.path_width}m")
    print(f"   Frames: {args.start_frame} - {args.end_frame}")
    
    # 1. Universal scene initialization
    scene.init_simulation(
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        physics_config={'substeps': 20, 'solver_iters': 20, 'cache_buffer': 0}
    )
    
    # 2. Create uneven terrain (hill-like)
    print("\n  - Creating uneven terrain...")
    z_ground = 0.0
    
    terrain = ground.create_uneven_ground(
        z_base=z_ground,
        size=args.terrain_size,
        noise_scale=5.0,  # Larger scale for hill-like terrain
        strength=args.terrain_strength
    )
    ground.apply_thickness(terrain, thickness=0.5, offset=-1.0)
    materials.create_mud_material(terrain)
    
    # 3. Load tree assets
    tree_templates = load_tree_assets(args.tree_asset)
    
    if not tree_templates:
        print("❌ Failed to load tree assets! Aborting.")
        return
    
    # 4. Create path through forest (on ground level)
    print("\n  - Creating path through forest (on ground)...")
    path_waypoints = create_path_through_forest(
        args.terrain_size, 
        args.path_width,
        num_waypoints=8
    )
    
    # Create Blender curve path from waypoints - ON GROUND LEVEL
    path = trajectory.create_waypoint_path(
        waypoints=path_waypoints,
        closed=False,
        z_location=0.5,  # Just slightly above ground for path following (will raycast to actual ground)
        name="ForestPath"
    )
    
    # 5. Place forest trees (on ground)
    tree_instances = place_forest_trees(
        tree_templates=tree_templates,
        terrain=terrain,
        terrain_size=args.terrain_size,
        path_waypoints=path_waypoints,
        path_width=args.path_width,
        num_trees=args.num_trees,
        tree_height_min=args.tree_height_min,
        tree_height_max=args.tree_height_max,
        min_tree_distance=args.min_tree_distance,
        args=args
    )
    
    # 6. Load and setup Open Duck (on ground)
    # Calculate scale to achieve target robot height
    # Open Duck at scale 1.0 is approximately 5.0m tall, so scale = target_height / 5.0
    BASE_DUCK_HEIGHT = 5.0  # Duck height at scale 1.0
    robot_scale = args.robot_height / BASE_DUCK_HEIGHT
    
    print(f"\n  - Loading Open Duck robot (target height={args.robot_height}m, scale={robot_scale:.3f})...")
    armature, robot_parts = open_duck.load_open_duck(
        transform={'location': (0, 0, 0), 'rotation': (0, 0, 0), 'scale': robot_scale}
    )
    
    if not armature:
        print("❌ Failed to load Duck! Aborting.")
        return
    
    # Print robot dimensions for scale verification
    if armature:
        robot_bbox = [armature.matrix_world @ Vector(corner) for corner in armature.bound_box]
        actual_robot_height = (max(c.z for c in robot_bbox) - min(c.z for c in robot_bbox))
        robot_width = (max(c.x for c in robot_bbox) - min(c.x for c in robot_bbox))
        print(f"    Robot dimensions: H={actual_robot_height:.2f}m, W={robot_width:.2f}m (target was {args.robot_height}m)")
    
    # 7. Animate duck walking along forest path
    print(f"  - Animating duck walking through forest...")
    open_duck.animate_duck_walking(
        armature=armature,
        path_curve=path,
        ground_object=terrain,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        speed=args.walk_speed
    )
    
    # 8. Setup collision (optional - skip if --no-physics)
    if not args.no_physics:
        open_duck.setup_duck_collision(robot_parts, kinematic=True)
    else:
        print("  - Skipping robot collision (--no-physics enabled)")
    
    # 9. Annotation Setup using AnnotationManager
    # Point tracking on trees only (not robot), 1000 points per tree
    if not args.no_annotations and (robot_parts or tree_instances):
        print("\n📊 Setting up Annotations...")
        
        mgr = AnnotationManager(collection_name="AnnotationViz")
        
        bbox_robot = not args.no_bbox
        trail_center = not args.no_trail
        point_tracking = not args.no_point_tracking
        
        # Annotate robot parts (NO point tracking on robot)
        mgr.annotate_robot(
            robot_parts=robot_parts,
            center_object=armature,
            debris_objects=[],
            bbox_robot=bbox_robot,
            bbox_debris=False,
            trail_center=trail_center,
            trail_debris=False,
            point_tracking=False,  # No point tracking on robot
            start_frame=args.start_frame,
            end_frame=args.end_frame,
            trail_step=args.trail_step,
            points_per_object=args.points_per_object
        )
        
        # Add point tracking for ALL trees with configurable frustum mode
        # NOTE: Frustum wireframe is created AFTER camera setup (see below)
        if point_tracking and tree_instances:
            mode_desc = {
                'all': 'show all points (no culling)',
                'highlight': 'all visible, in-frustum turn red',
                'frustum_only': 'only show points in frustum'
            }
            print(f"  - Adding point tracking for {len(tree_instances)} trees...")
            print(f"    {args.points_per_tree} points per tree ({len(tree_instances) * args.points_per_tree} total)")
            print(f"    Frustum mode: {args.frustum_mode} ({mode_desc.get(args.frustum_mode, '')})")
            mgr.add_point_tracking(
                tree_instances, 
                points_per_object=args.points_per_tree,
                show_frustum=False,  # Frustum created after camera setup
                frustum_distance=args.frustum_distance,
                frustum_mode=args.frustum_mode
            )
        
        mgr.finalize(setup_viewport=False)
        viewport.create_viewport_restore_script("AnnotationViz")
    
    # 10. Lighting
    print("\n  - Setting up lighting...")
    lighting.setup_lighting(
        resolution_x=args.resolution_x,
        resolution_y=args.resolution_y,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        enable_caustics=False,
        enable_volumetric=True,
        volumetric_density=0.01  # Light forest atmosphere
    )
    
    # 11. Camera Setup - All three camera types (same as robot_waypoint_walk.py)
    print("\n📷 Setting up Camera Rigs...")
    
    cam_manager = CameraManager()
    
    # 11a. Center pointing cameras
    center_rig = cam_manager.add_center_pointing(
        'center', 
        num_cameras=args.center_cameras, 
        radius=args.camera_radius, 
        height=args.camera_height
    )
    center_rig.create(target_location=(0, 0, 0))
    print(f"  - Center rig: {args.center_cameras} cameras at radius={args.camera_radius}, height={args.camera_height}")
    
    # 11b. Following camera
    follow_rig = cam_manager.add_following(
        'following',
        height=args.camera_height,
        look_angle=60
    )
    follow_rig.create(target=armature)
    print(f"  - Following camera: height={args.camera_height}, look_angle=60°")
    
    # 11c. Mounted cameras (same logic as robot_waypoint_walk.py)
    mount_target = None
    search_name = args.mounted_mesh.lower()
    
    for part in robot_parts:
        if part and part.type == 'MESH':
            part_base = part.name.lower().split('.')[0]
            if part_base == search_name or part.name.lower() == search_name:
                mount_target = part
                break
    
    if mount_target is None:
        for part in robot_parts:
            if part and part.type == 'MESH':
                if part.name.lower().startswith(search_name):
                    mount_target = part
                    break
    
    if mount_target is None:
        for part in robot_parts:
            if part and part.type == 'MESH':
                mount_target = part
                print(f"  - Warning: '{args.mounted_mesh}' not found, using '{part.name}'")
                break
    
    if mount_target:
        # Open Duck uses -Y as forward direction
        mounted_rig = cam_manager.add_object_mounted(
            'mounted',
            num_cameras=args.mounted_cameras,
            distance=args.mounted_distance,
            height_offset=0.05,  # Small offset for duck's head
            forward_axis='-Y',  # Open Duck faces -Y direction
            rotation_offset=args.mounted_rotation  # User-adjustable rotation
        )
        mounted_cams = mounted_rig.create(parent_object=mount_target, lens=20)  # Focal length 20
        
        # Add offset to mounted cameras
        for cam in mounted_cams:
            cam.location.x -= 0.12  # back offset
            cam.location.y -= 0.1  # right offset
            cam.location.z -= 0.0  # down offset
        
        print(f"  - Mounted rig: {args.mounted_cameras} cameras on '{mount_target.name}' (lens=20, offset: right=0.1m, back=0.12m)")
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
        cam_manager.activate_rig('center', camera_index=args.center_cameras - 1)
        print(f"  - Active camera: Center rig (default)")
    
    # 12. Create frustum wireframe for active camera (AFTER camera setup)
    # Only needed for highlight and frustum_only modes
    # Automatically reads frustum_distance from PointCloudTracker object
    if not args.no_annotations and not args.no_point_tracking and args.frustum_mode != 'all':
        from vibephysics.annotation import point_tracking as pt_module
        print(f"\n  - Creating camera frustum wireframe...")
        pt_module.setup_frustum_visualization(
            camera=bpy.context.scene.camera,
            collection_name="AnnotationViz"
        )
        print(f"    Frustum follows: {bpy.context.scene.camera.name if bpy.context.scene.camera else 'None'}")
    
    # 13. Bake physics (skip if --no-physics)
    if not args.no_physics:
        print("\n  - Baking physics...")
        physics.bake_all()
    else:
        print("\n  - Skipping physics bake (--no-physics enabled)")
    
    print("\n" + "=" * 60)
    print("✅ Duck Forest Walk Complete!")
    print("=" * 60)
    print(f"   Trees placed: {len(tree_instances)}")
    print(f"   Tree height range: {args.tree_height_min}m - {args.tree_height_max}m")
    print(f"   Min tree distance: {args.min_tree_distance}m")
    print(f"   Robot height: {args.robot_height}m")
    print(f"   Path width: {args.path_width}m")
    print(f"   Animation: {args.end_frame} frames")
    print(f"\n💡 All objects are placed ON THE GROUND (trees, robot, trajectory)")


def main():
    args = parse_args()
    run_simulation_setup(args)
    
    # Save blend file
    save_blend(args.output)


if __name__ == "__main__":
    main()
