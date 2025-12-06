import sys
import os
import bpy
import math
import argparse
import random
from mathutils import Vector, Matrix, Euler

# Add parent directory to path to import foundation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from foundation import physics, water, ground, robot, objects, materials, lighting, point_tracking, viewport

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
    output_group.add_argument('--output', type=str, default='duck_walking.blend',
                             help='Output blend file name')
    
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    else:
        argv = []
    
    return parser.parse_args(argv)

def create_walking_path(scale=10.0):
    """Creates a winding curve path for the robot to follow."""
    bpy.ops.curve.primitive_bezier_circle_add(radius=scale, location=(0, 0, 0))
    path = bpy.context.active_object
    path.name = "WalkPath"
    
    path.scale = (1.0, 0.5, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    
    return path

def load_duck_robot(filepath):
    """Loads the open-duck-mini robot from the blend file."""
    if not os.path.exists(filepath):
        print(f"Error: Duck file not found at {filepath}")
        return None, []

    print(f"  - Loading duck from {filepath}...")
    
    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        data_to.objects = data_from.objects

    armature = None
    robot_parts = []
    
    for obj in data_to.objects:
        if obj:
            if "Background" in obj.name:
                continue

            if obj.name not in bpy.context.scene.objects:
                bpy.context.scene.collection.objects.link(obj)
            
            if obj.type == 'ARMATURE':
                armature = obj
            elif obj.type == 'MESH':
                robot_parts.append(obj)
    
    if armature:
        print(f"    Found armature: {armature.name}")
        armature.location = (0, 0, 0)
        armature.rotation_euler = (0, 0, 0)
        armature.scale = (0.3, 0.3, 0.3) 
    else:
        print("    WARNING: No armature found!")
        
    print(f"    Found {len(robot_parts)} mesh parts.")
        
    return armature, robot_parts

def setup_physics_ground(ground_object):
    """Sets up rigid body physics for the ground."""
    bpy.context.view_layer.objects.active = ground_object
    try:
        bpy.ops.rigidbody.object_add(type='PASSIVE')
        grb = ground_object.rigid_body
        grb.friction = 0.9
        grb.restitution = 0.1
        grb.collision_shape = 'MESH'
        grb.mesh_source = 'FINAL'
    except:
        pass

def setup_robot_ripples(water_obj, robot_parts, debris_objects, ripple_strength=10.0):
    """
    Custom dynamic paint setup for robot parts with larger paint_distance.
    Robot parts are small (0.3 scale) so need bigger detection range.
    """
    print("  - setting up water ripple interactions...")
    
    # 1. Setup Canvas (Water)
    bpy.context.view_layer.objects.active = water_obj
    bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
    canvas_mod = water_obj.modifiers[-1]
    canvas_mod.ui_type = 'CANVAS'
    bpy.ops.dpaint.type_toggle(type='CANVAS')
    bpy.ops.dpaint.output_toggle(output='A')
    
    surface = canvas_mod.canvas_settings.canvas_surfaces[-1]
    
    if surface.point_cache:
        surface.point_cache.use_disk_cache = False
        surface.point_cache.use_library_path = False
    
    surface.surface_type = 'WAVE'
    surface.wave_timescale = 1.0
    surface.wave_speed = 2.0  # Faster waves
    surface.wave_damping = 0.04  # Less damping
    surface.wave_spring = 0.3
    surface.wave_smoothness = 1.0
    surface.use_wave_open_border = True

    # 2. Setup Robot Parts as Brushes (with larger paint_distance)
    for obj in robot_parts:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
        brush_mod = obj.modifiers[-1]
        brush_mod.ui_type = 'BRUSH'
        bpy.ops.dpaint.type_toggle(type='BRUSH')
        
        settings = brush_mod.brush_settings
        settings.paint_source = 'VOLUME_DISTANCE'
        settings.paint_distance = 0.5  # Larger for robot parts
        settings.wave_factor = ripple_strength * 1.5  # Strong ripples from robot
        settings.wave_clamp = 10.0
    
    # 3. Setup Debris as Brushes (normal paint_distance)
    for obj in debris_objects:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_add(type='DYNAMIC_PAINT')
        brush_mod = obj.modifiers[-1]
        brush_mod.ui_type = 'BRUSH'
        bpy.ops.dpaint.type_toggle(type='BRUSH')
        
        settings = brush_mod.brush_settings
        settings.paint_source = 'VOLUME_DISTANCE'
        settings.paint_distance = 0.3
        
        # Use mass for wave factor
        current_mass = 1.0
        if obj.rigid_body:
            current_mass = obj.rigid_body.mass
        settings.wave_factor = min(current_mass * 4.0, 4.0) * ripple_strength
        settings.wave_clamp = 8.0
    
    print(f"    Added {len(robot_parts)} robot brushes, {len(debris_objects)} debris brushes")

def setup_robot_collision(robot_parts, armature):
    """
    Sets up collision for robot parts WITHOUT breaking the rig.
    Meshes stay parented to armature and become kinematic rigid bodies.
    They follow the animation but can collide with ground/objects.
    """
    print("  - setting up robot collision physics...")
    
    count = 0
    for part in robot_parts:
        # Add kinematic rigid body to each mesh part
        bpy.ops.object.select_all(action='DESELECT')
        part.select_set(True)
        bpy.context.view_layer.objects.active = part
        
        try:
            bpy.ops.rigidbody.object_add(type='ACTIVE')
            rb = part.rigid_body
            rb.kinematic = True  # Follows animation, doesn't fall
            rb.collision_shape = 'CONVEX_HULL'
            rb.friction = 0.8
            rb.restitution = 0.1
            rb.collision_margin = 0.001
            count += 1
        except Exception as e:
            print(f"    Warning: Could not add rigid body to {part.name}: {e}")
    
    print(f"    Added collision to {count} mesh parts")

def animate_walking(armature, path_curve, ground_object, 
                    start_frame=1, end_frame=250, speed=1.0):
    """
    Animates the robot walking with realistic leg movement.
    Uses IK foot targets for ground contact.
    """
    scene = bpy.context.scene
    
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    bones = armature.pose.bones
    scale_mult = armature.scale[0]
    
    # CRITICAL: Enable IK mode (the duck rig has FK/IK switch)
    if 'fk_ik_controller' in bones:
        fk_ik_ctrl = bones['fk_ik_controller']
        if 'fk_ik' in fk_ik_ctrl:
            print("    Enabling IK mode...")
            fk_ik_ctrl['fk_ik'] = 1.0
            fk_ik_ctrl.keyframe_insert(data_path='["fk_ik"]', frame=start_frame)
    
    # IK bones for foot placement
    foot_ik_l = 'leg_ik.l'
    foot_ik_r = 'leg_ik.r'
    
    # Clear any existing constraints on IK bones
    for b_name in [foot_ik_l, foot_ik_r]:
        if b_name in bones:
            for c in list(bones[b_name].constraints):
                bones[b_name].constraints.remove(c)
    
    # Walking parameters (scaled for duck at 0.3 scale)
    hips_height = 0.1 * scale_mult
    stride_length = 0.5 * scale_mult  # Larger stride for visible movement
    step_height = 0.25 * scale_mult   # Higher step
    foot_spacing = 0.2 * scale_mult
    
    # Note: With puppet physics, we DON'T want an offset because the spring will hold it
    # but the collision will push it up. However, to avoid constant compression force,
    # target slightly above ground is good.
    foot_height_offset = 0.0 
    
    # Cycle timing - frames per full step cycle
    frames_per_cycle = int(20 / speed)
    
    # Track foot plant positions for each cycle
    # Key: cycle_number, Value: planted world position
    foot_plants_l = {}
    foot_plants_r = {}
    
    total_frames = end_frame - start_frame + 1
    
    for frame in range(start_frame, end_frame + 1):
        scene.frame_set(frame)
        
        # Calculate path position
        t = (frame - start_frame) / (end_frame - start_frame)
        t = min(t, 0.9999)
        
        path_pos_world, tangent_world = robot.evaluate_curve_at_t(path_curve, t)
        
        # Get ground height
        ground_z = robot.raycast_ground(scene, path_pos_world, start_height=20.0, 
                                        ground_objects=[ground_object])
        
        # Place armature on ground
        armature_loc = Vector((path_pos_world.x, path_pos_world.y, ground_z))
        armature.location = armature_loc
        armature.keyframe_insert(data_path="location", frame=frame)
        
        # Rotation
        rot_quat = tangent_world.to_track_quat('-Y', 'Z')
        armature.rotation_euler = rot_quat.to_euler()
        armature.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        # Build transform matrix
        current_matrix = Matrix.LocRotScale(armature_loc, rot_quat, armature.scale)
        arm_mat_inv = current_matrix.inverted()
        
        # Direction vectors
        forward_vec = tangent_world.normalized()
        right_vec = forward_vec.cross(Vector((0, 0, 1))).normalized()
        
        # Calculate cycle phase (0 to 1) - continuous across all frames
        cycle_phase = ((frame - start_frame) % frames_per_cycle) / frames_per_cycle
        
        # Which cycle are we in?
        current_cycle = (frame - start_frame) // frames_per_cycle
        
        # Root bone with walking bounce
        if 'root' in bones:
            # Double frequency bounce (once per step)
            bounce = math.sin(cycle_phase * 4 * math.pi) * 0.008 * scale_mult
            bones['root'].location.z = hips_height + bounce
            bones['root'].keyframe_insert(data_path="location", frame=frame)
        
        def get_foot_position(is_left, phase_offset):
            """Calculate foot position for current frame."""
            # Adjust phase for this foot
            foot_phase = (cycle_phase + phase_offset) % 1.0
            
            side_sign = 1 if is_left else -1
            side_offset = right_vec * side_sign * foot_spacing
            
            # Determine if in stance (0.0-0.5) or swing (0.5-1.0)
            is_stance = foot_phase < 0.5
            
            foot_plants = foot_plants_l if is_left else foot_plants_r
            
            if is_stance:
                # Stance phase - foot stays planted
                stance_progress = foot_phase / 0.5  # 0 to 1 during stance
                
                # Plant foot at start of stance if not already
                plant_key = (current_cycle, is_left, 'stance')
                if plant_key not in foot_plants:
                    # Plant position is slightly ahead of body
                    plant_pos = armature_loc + side_offset + forward_vec * (stride_length * 0.5)
                    plant_z = robot.raycast_ground(scene, plant_pos, start_height=20.0, 
                                                   ground_objects=[ground_object])
                    # Add foot height offset
                    foot_plants[plant_key] = Vector((plant_pos.x, plant_pos.y, plant_z + foot_height_offset))
                
                # Return planted position (foot stays in place)
                return foot_plants[plant_key]
            
            else:
                # Swing phase - foot moves from back to front
                swing_progress = (foot_phase - 0.5) / 0.5  # 0 to 1 during swing
                
                # Start position: where foot was planted last
                prev_plant_key = (current_cycle, is_left, 'stance')
                if prev_plant_key in foot_plants:
                    start_pos = foot_plants[prev_plant_key]
                else:
                    # Fallback: behind the body
                    start_pos = armature_loc + side_offset - forward_vec * (stride_length * 0.5)
                    start_z = robot.raycast_ground(scene, start_pos, start_height=20.0,
                                                   ground_objects=[ground_object])
                    start_pos = Vector((start_pos.x, start_pos.y, start_z + foot_height_offset))
                
                # End position: ahead of body (where foot will plant next)
                end_pos = armature_loc + side_offset + forward_vec * (stride_length * 0.5)
                end_z = robot.raycast_ground(scene, end_pos, start_height=20.0,
                                             ground_objects=[ground_object])
                end_pos = Vector((end_pos.x, end_pos.y, end_z + foot_height_offset))
                
                # Interpolate XY
                current_pos = start_pos.lerp(end_pos, swing_progress)
                
                # Add arc for Z (foot lifts during swing)
                lift = math.sin(swing_progress * math.pi) * step_height
                current_pos.z = current_pos.z + lift
                
                return current_pos
        
        def update_foot_bone(bone_name, world_pos):
            """Update IK bone to target world position."""
            if bone_name not in bones:
                return
            
            bone = bones[bone_name]
            
            # Convert world position to armature space
            local_pos = arm_mat_inv @ world_pos
            
            # Set bone location
            bone.location = local_pos
            bone.keyframe_insert(data_path="location", frame=frame)
        
        # Calculate and set foot positions
        left_pos = get_foot_position(is_left=True, phase_offset=0.0)
        right_pos = get_foot_position(is_left=False, phase_offset=0.5)
        
        update_foot_bone(foot_ik_l, left_pos)
        update_foot_bone(foot_ik_r, right_pos)
    
    bpy.ops.object.mode_set(mode='OBJECT')

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
    
    # 2a. Prepare Ground for Boolean (Duplicate for cutting water)
    bpy.ops.object.select_all(action='DESELECT')
    terrain.select_set(True)
    bpy.context.view_layer.objects.active = terrain
    bpy.ops.object.duplicate()
    ground_cutter = bpy.context.active_object
    ground_cutter.name = "Ground_Cutter"
    
    # Solidify the CUTTER downwards massively
    mod_solid = ground_cutter.modifiers.new(name="SolidifyCutter", type='SOLIDIFY')
    mod_solid.thickness = 10.0 
    mod_solid.offset = -1.0 
    
    # Hide cutter
    ground_cutter.hide_render = True
    ground_cutter.hide_viewport = True
    
    # Visual Ground: Give it a small thickness
    mod_solid_vis = terrain.modifiers.new(name="SolidifyVisual", type='SOLIDIFY')
    mod_solid_vis.thickness = 0.5
    mod_solid_vis.offset = -1.0
    
    materials.create_mud_material(terrain)
    setup_physics_ground(terrain)
    
    # 3. Water Surface - Simple high-res GRID for Dynamic Paint ripples
    z_water_level = z_ground + 0.1  # Slightly above ground base
    
    # Cleanup cutter - not needed
    bpy.data.objects.remove(ground_cutter, do_unlink=True)
    
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
    armature, robot_parts = load_duck_robot(duck_path)
    
    if not armature:
        print("Failed to load Duck! Aborting.")
        return

    # 5. Walk Path
    path = create_walking_path(scale=args.terrain_size * 0.35)
    path.location.z = 2.0 
    
    # 6. Animate Walking (Kinematic Driver)
    print("  - animating walk cycle...")
    animate_walking(
        armature=armature,
        path_curve=path,
        ground_object=terrain,
        start_frame=args.start_frame,
        end_frame=args.end_frame,
        speed=args.walk_speed
    )
    
    # 7. Setup Robot Collision (Meshes stay rigged, but can collide)
    setup_robot_collision(robot_parts, armature)
    
    # 8. Water Interactions - Custom setup for robot with larger paint_distance
    setup_robot_ripples(water_visual, robot_parts, debris_objects, ripple_strength=15.0)
    
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
