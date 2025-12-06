"""
Robot Foundation Module

Handles creation of rigged robots and procedural walking animation
adapted to uneven terrain.
"""

import bpy
import math
from mathutils import Vector, Matrix

def create_simple_robot(name="Robot", location=(0, 0, 0), scale=1.0):
    """
    Creates a simple boxy robot with an armature and IK setup.
    Returns the robot object (armature) and the mesh object.
    """
    # Create Armature
    bpy.ops.object.armature_add(enter_editmode=True, location=location)
    armature = bpy.context.active_object
    armature.name = name
    armature.scale = (scale, scale, scale)
    
    # Setup Bones
    amt = armature.data
    
    # Remove default bone
    for bone in amt.edit_bones:
        amt.edit_bones.remove(bone)
        
    # Dimensions
    leg_length = 0.8
    torso_height = 1.0
    shoulder_width = 0.6
    hip_width = 0.4
    
    # --- BONE CREATION ---
    
    # Root/Hips
    root = amt.edit_bones.new('Root')
    root.head = (0, 0, leg_length * 2)
    root.tail = (0, 0, leg_length * 2 + torso_height)
    
    # Legs (Thigh -> Shin -> Foot)
    def create_leg(side, x_offset):
        # Thigh
        thigh = amt.edit_bones.new(f'Thigh.{side}')
        thigh.parent = root
        thigh.head = (x_offset, 0, leg_length * 2)
        thigh.tail = (x_offset, 0, leg_length)
        
        # Shin
        shin = amt.edit_bones.new(f'Shin.{side}')
        shin.parent = thigh
        shin.head = thigh.tail
        shin.tail = (x_offset, 0, 0.1)
        
        # Foot
        foot = amt.edit_bones.new(f'Foot.{side}')
        foot.parent = shin
        foot.head = shin.tail
        foot.tail = (x_offset, 0.3, 0.0)
        
        # IK Target (disconnected)
        ik_target = amt.edit_bones.new(f'IK_Foot.{side}')
        ik_target.head = (x_offset, 0, 0)
        ik_target.tail = (x_offset, 0, 0.1)
        ik_target.parent = None # Root-level control
        
        # Pole Target (knee direction)
        pole = amt.edit_bones.new(f'Pole_Knee.{side}')
        pole.head = (x_offset, 1.0, leg_length)
        pole.tail = (x_offset, 1.1, leg_length)
        pole.parent = None
        
        return thigh, shin, foot, ik_target, pole

    thigh_l, shin_l, foot_l, ik_l, pole_l = create_leg('L', hip_width/2)
    thigh_r, shin_r, foot_r, ik_r, pole_r = create_leg('R', -hip_width/2)
    
    # Exit Edit Mode to setup constraints
    bpy.ops.object.mode_set(mode='POSE')
    
    # --- IK CONSTRAINTS ---
    def setup_ik_constraint(side):
        shin_bone = armature.pose.bones[f'Shin.{side}']
        c = shin_bone.constraints.new('IK')
        c.target = armature
        c.subtarget = f'IK_Foot.{side}'
        c.pole_target = armature
        c.subtarget = f'IK_Foot.{side}'
        c.pole_subtarget = f'Pole_Knee.{side}'
        c.pole_angle = math.radians(-90) if side == 'R' else math.radians(-90)
        c.chain_count = 2 # Shin and Thigh only
        
    setup_ik_constraint('L')
    setup_ik_constraint('R')
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # --- MESH GENERATION ---
    # Create a simple boxy mesh matching the armature
    
    # Helper to add cube aligned to bone
    def add_cube_bone(bone_name, size, offset=(0,0,0)):
        bpy.ops.mesh.primitive_cube_add(size=1)
        obj = bpy.context.active_object
        # Size is (x, y, z)
        obj.scale = size
        
        # Parenting
        obj.parent = armature
        obj.parent_type = 'BONE'
        obj.parent_bone = bone_name
        
        # Apply transforms
        # Bone Local Space: Y is along the bone, X/Z are perpendicular
        obj.location = offset
        return obj

    # Create body parts
    # Torso
    # Root bone: Head(0,0,1.6), Tail(0,0,2.6). Length 1.0. Points +Z world?
    # Wait, Root Bone: head=(0,0,1.6), tail=(0,0,2.6).
    # In Edit Mode, Y axis points from Head to Tail.
    # So Root Bone Y is World +Z.
    # We want Torso to be a vertical box.
    # So Scale Y should be height.
    torso = add_cube_bone('Root', (hip_width*1.5, torso_height, 0.4), (0, torso_height/2, 0))
    torso.name = f"{name}_Torso"
    
    # Head
    # Parent to Root.
    # Position: Above torso.
    # In Root Bone space, Top is Y=1.0.
    head = add_cube_bone('Root', (0.4, 0.4, 0.4), (0, torso_height + 0.2, 0))
    head.name = f"{name}_Head"
    
    # Legs
    def add_leg_mesh(side):
        # Thigh Bone: Head(Hips), Tail(Knee). Points DOWN.
        # So Bone Y axis points DOWN.
        # We want mesh along Y.
        # Length 0.8.
        thigh = add_cube_bone(f'Thigh.{side}', (0.15, leg_length, 0.15), (0, leg_length/2, 0))
        thigh.name = f"{name}_Thigh_{side}"
        
        # Shin Bone: Head(Knee), Tail(Ankle). Points DOWN.
        shin = add_cube_bone(f'Shin.{side}', (0.12, leg_length, 0.12), (0, leg_length/2, 0))
        shin.name = f"{name}_Shin_{side}"
        
        # Foot Bone: Ankle to Toe. Points Forward/Down.
        # Length approx 0.3.
        foot = add_cube_bone(f'Foot.{side}', (0.15, 0.3, 0.05), (0, 0.15, 0))
        foot.name = f"{name}_Foot_{side}"
        return [thigh, shin, foot]

    parts_l = add_leg_mesh('L')
    parts_r = add_leg_mesh('R')
    
    # Join all parts into one mesh for easier point tracking/physics
    all_parts = [torso, head] + parts_l + parts_r
    
    # For a mechanical robot, rigid bone parenting is best.
    # We already set parent_type='BONE' in add_cube_bone.
    # So the rigging is ALREADY DONE and correct!
    
    # We just need to return the list of parts so the point tracker can track them all.
    # We DO NOT join them, because joining destroys the bone parenting.
    
    # Add material to all parts
    mat = bpy.data.materials.new(name=f"{name}_Mat")
    mat.diffuse_color = (0.8, 0.8, 0.9, 1.0)
    mat.metallic = 0.8
    mat.roughness = 0.2
    
    for part in all_parts:
        part.data.materials.append(mat)
    
    return armature, all_parts


def raycast_ground(scene, xy_point, start_height=10.0, ground_objects=None):
    """
    Find ground height at xy_point.
    """
    origin = Vector((xy_point[0], xy_point[1], start_height))
    direction = Vector((0, 0, -1))
    
    best_z = 0.0
    
    # Raycast scene
    # Note: ray_cast checks evaluated dependency graph in recent Blender versions
    depsgraph = bpy.context.evaluated_depsgraph_get()
    
    success, location, normal, index, object, matrix = scene.ray_cast(depsgraph, origin, direction)
    
    if success:
        # If we provided a filter list, check if object is in it
        if ground_objects is None or object in ground_objects:
            return location.z
    
    return 0.0 # Default floor


def evaluate_curve_at_t(curve_obj, t):
    """
    Evaluate position and tangent of a curve at factor t (0-1).
    Returns (position, tangent) vectors in world space.
    """
    # Use the curve's spline
    if not curve_obj.data.splines:
        return Vector((0,0,0)), Vector((0,1,0))
    
    spline = curve_obj.data.splines[0]
    
    # Map t to curve points
    # Simple linear interpolation between points for BEZIER or POLY
    # If it's a closed loop (cyclic), t=1 wraps to t=0
    
    # Better way: use mathutils.geometry.interpolate_bezier if we extracted points
    # But for now, let's just grab the calculated points from the evaluated mesh
    # This is robust for any curve type
    
    depsgraph = bpy.context.evaluated_depsgraph_get()
    curve_eval = curve_obj.evaluated_get(depsgraph)
    mesh = curve_eval.to_mesh()
    
    if len(mesh.vertices) < 2:
        curve_eval.to_mesh_clear()
        return curve_obj.location, Vector((0,1,0))
        
    total_verts = len(mesh.vertices)
    
    # Cyclic adjustment
    if spline.use_cyclic_u:
        idx_float = t * total_verts
    else:
        idx_float = t * (total_verts - 1)
        
    idx = int(idx_float)
    next_idx = (idx + 1) % total_verts
    fraction = idx_float - idx
    
    v1 = mesh.vertices[idx].co
    v2 = mesh.vertices[next_idx].co
    
    # Interpolate local position
    pos_local = v1.lerp(v2, fraction)
    
    # Calculate tangent (direction to next point)
    tangent_local = (v2 - v1).normalized()
    if tangent_local.length_squared == 0:
        tangent_local = Vector((0,1,0))
        
    # Transform to world
    pos_world = curve_obj.matrix_world @ pos_local
    
    # Transform tangent (rotation only)
    tangent_world = curve_obj.matrix_world.to_3x3() @ tangent_local
    tangent_world.normalize()
    
    curve_eval.to_mesh_clear()
    
    return pos_world, tangent_world


def animate_walk_cycle(armature, path_curve, ground_object, start_frame=1, end_frame=250, speed=1.0):
    """
    Animates the robot walking along a path on uneven ground.
    """
    scene = bpy.context.scene
    
    # Ensure in Pose Mode
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    bones = armature.pose.bones
    root = bones['Root']
    
    # Dimensions
    leg_length = 0.8
    hips_height = 1.3 # Lower than 1.6 to ensure knees bend
    stride_length = 1.2 * speed
    step_height = 0.5
    
    # Calculate path length approx to determine cycle count
    # Or just drive by speed
    cycle_length = 30 / speed # Frames per cycle
    
    # CREATE EXTERNAL IK TARGETS
    bpy.ops.object.mode_set(mode='OBJECT')
    
    target_l = bpy.data.objects.new("Target_L", None)
    target_r = bpy.data.objects.new("Target_R", None)
    target_pole_l = bpy.data.objects.new("Pole_L", None)
    target_pole_r = bpy.data.objects.new("Pole_R", None)
    
    for o in [target_l, target_r, target_pole_l, target_pole_r]:
        o.empty_display_type = 'SPHERE'
        o.empty_display_size = 0.1
        armature.users_collection[0].objects.link(o)
    
    # Update constraints
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    def update_constraint_target(bone_name, target_obj, pole_obj):
        bone = bones[bone_name]
        ik = bone.constraints.get("IK")
        if ik:
            ik.target = target_obj
            ik.subtarget = "" 
            ik.pole_target = pole_obj
            ik.pole_subtarget = ""
    
    update_constraint_target('Shin.L', target_l, target_pole_l)
    update_constraint_target('Shin.R', target_r, target_pole_r)
    
    # --- ANIMATION LOOP ---
    
    # State tracking for feet
    # We need to toggle between planted and moving
    # We'll calculate ideal positions and lerp
    
    # Previous frame positions
    last_root_pos = armature.location.copy()
    
    # Foot state: [position, is_planted, lift_progress]
    foot_state_l = {'pos': None, 'planted': True}
    foot_state_r = {'pos': None, 'planted': True}
    
    for frame in range(start_frame, end_frame + 1):
        scene.frame_set(frame)
        
        # 1. Move Armature along Curve
        t = (frame - start_frame) / (end_frame - start_frame)
        # Limit t to just under 1.0 to avoid index errors if not cyclic
        t = min(t, 0.999)
        
        pos_world, tangent_world = evaluate_curve_at_t(path_curve, t)
        
        # Update Armature Object Transform
        armature.location = pos_world
        armature.keyframe_insert(data_path="location", frame=frame)
        
        # Rotate to face tangent
        # Tangent is Y forward
        # Z is up
        rot_quat = tangent_world.to_track_quat('Y', 'Z')
        armature.rotation_euler = rot_quat.to_euler()
        armature.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        # Calculate vectors
        right_vec = tangent_world.cross(Vector((0, 0, 1))).normalized()
        
        # 2. Determine Root Height relative to Ground
        # Raycast from high up
        ground_z_root = raycast_ground(scene, pos_world, start_height=20.0, ground_objects=[ground_object])
        
        # If raycast missed (returned 0.0 and ground is lower), force a check? 
        # Assume ground is around -1.0 if 0.0 returned?
        # Let's trust raycast but verify in script
        
        # Base hip height
        bounce = math.sin(frame / cycle_length * 4 * math.pi) * 0.05
        final_root_z = ground_z_root + hips_height + bounce
        
        # Root bone is relative to Armature Object
        # Armature Object is at pos_world (on the path, likely Z=2.0)
        # So Root Bone Z = final_root_z - pos_world.z
        root.location.z = final_root_z - pos_world.z
        root.keyframe_insert(data_path="location", frame=frame)
        
        # 3. Animate Feet
        cycle_phase = (frame % cycle_length) / cycle_length
        
        def update_foot(target_obj, pole_obj, is_left, phase_offset):
            # Local cycle time 0-1
            ct = (cycle_phase + phase_offset) % 1.0
            
            side_sign = 1 if is_left else -1
            side_vec = right_vec * side_sign * 0.3 # 0.3 spacing from center
            
            # Pole (Knee) - always just in front/side of hips
            pole_pos = pos_world + side_vec + tangent_world * 0.5 + Vector((0, 0, 0.5))
            pole_obj.location = pole_pos
            pole_obj.keyframe_insert(data_path="location", frame=frame)
            
            # Foot Logic
            # Stance: 0.0 - 0.5
            # Swing: 0.5 - 1.0
            
            is_swing = ct > 0.5
            
            # Calculate "Ideal" planted spot for this moment if we were standing
            # It's where the hips are
            # But we need to plant AHEAD during swing, and stay BEHIND during stance
            
            if not is_swing:
                # Stance Phase - Foot should be PLANTED
                # If we don't have a planted position, find one
                state = foot_state_l if is_left else foot_state_r
                
                if state['pos'] is None or not state['planted']:
                    # Just landed! Plant it here.
                    # Where? Slightly ahead of root?
                    # At start of stance (t=0), foot is forward.
                    # Stride is roughly `stride_length`.
                    # So plant at Root + Forward * (Stride/2)
                    
                    plant_xy = pos_world + side_vec + tangent_world * (stride_length * 0.4)
                    g_z = raycast_ground(scene, plant_xy, start_height=20.0, ground_objects=[ground_object])
                    
                    state['pos'] = Vector((plant_xy.x, plant_xy.y, g_z))
                    state['planted'] = True
                
                # Keep target at planted pos
                target_obj.location = state['pos']
                
            else:
                # Swing Phase - Move from Back to Front
                state = foot_state_l if is_left else foot_state_r
                state['planted'] = False
                
                # Calculate trajectory
                # Start: position at t=0.5 (Back)
                # End: position at t=1.0 (Front)
                
                # Where were we at start of swing?
                # We were planted. Use that as start.
                if state['pos'] is None:
                     # Init
                     state['pos'] = pos_world + side_vec
                
                start_pos = state['pos']
                
                # Where do we want to land?
                # Future root pos? 
                # Approx: Current Root + Forward * (Stride/2) + Velocity * Time_Left?
                # Simpler: Target is Root + Forward * (Stride * 0.4)
                target_xy = pos_world + side_vec + tangent_world * (stride_length * 0.4)
                
                # Interpolate
                swing_progress = (ct - 0.5) / 0.5 # 0 to 1
                
                # XY Lerp
                current_xy = start_pos.lerp(target_xy, swing_progress)
                
                # Z Arc
                # Raycast current ground for safety
                g_z = raycast_ground(scene, current_xy, start_height=20.0, ground_objects=[ground_object])
                
                # Parabolic lift
                lift = math.sin(swing_progress * math.pi) * step_height
                
                final_pos = Vector((current_xy.x, current_xy.y, g_z + lift))
                target_obj.location = final_pos
                
            target_obj.keyframe_insert(data_path="location", frame=frame)

        # Update both feet
        update_foot(target_l, target_pole_l, True, 0.0)   # Left Phase 0
        update_foot(target_r, target_pole_r, False, 0.5)  # Right Phase 0.5

    return armature, [target_l, target_r, target_pole_l, target_pole_r]
