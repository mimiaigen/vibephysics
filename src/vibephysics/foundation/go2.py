"""
Go2 Robot Foundation Module

Model-specific control for the Unitree Go2 robot dog.
Provides functionality to load, rig (USD to Armature), and animate the Go2.
"""

import bpy
import math
import os
import subprocess
from mathutils import Vector, Matrix, Euler
from . import robot
from . import trajectory

try:
    from tqdm import tqdm
except ImportError:
    # Fallback if tqdm not installed
    def tqdm(iterable, **kwargs):
        return iterable


def get_go2_usd_path():
    """
    Get the path to the Go2 USD file.
    If the unitree_model repository is not found, automatically clone it.
    
    The model is expected to be at: {vibephysics_parent}/unitree_model/Go2/usd/go2.usd
    
    Returns:
        str: Path to the go2.usd file
    """
    # Get the vibephysics root directory (parent of src/vibephysics/foundation)
    foundation_dir = os.path.dirname(os.path.abspath(__file__))
    vibephysics_root = os.path.dirname(os.path.dirname(os.path.dirname(foundation_dir)))
    
    # unitree_model should be at the same level as vibephysics
    parent_dir = os.path.dirname(vibephysics_root)
    unitree_model_dir = os.path.join(parent_dir, "unitree_model")
    usd_path = os.path.join(unitree_model_dir, "Go2", "usd", "go2.usd")
    
    # Check if the USD file exists
    if os.path.exists(usd_path):
        return usd_path
    
    # Check if unitree_model directory exists but USD is missing
    if os.path.exists(unitree_model_dir):
        raise FileNotFoundError(
            f"unitree_model directory exists but Go2 USD not found at: {usd_path}\n"
            f"Please check the repository structure."
        )
    
    # Auto-download using git clone
    print(f"  📥 Go2 model not found. Downloading from Hugging Face...")
    print(f"     Target: {parent_dir}")
    
    try:
        result = subprocess.run(
            ["git", "clone", "https://huggingface.co/datasets/unitreerobotics/unitree_model"],
            cwd=parent_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Git clone failed: {result.stderr}")
        
        print(f"  ✅ Successfully downloaded unitree_model")
        
        # Verify the file exists now
        if os.path.exists(usd_path):
            return usd_path
        else:
            raise FileNotFoundError(f"Downloaded but USD file not found at: {usd_path}")
            
    except FileNotFoundError:
        raise RuntimeError(
            "Git is not installed. Please install git and try again, or manually clone:\n"
            f"  cd {parent_dir}\n"
            "  git clone https://huggingface.co/datasets/unitreerobotics/unitree_model"
        )

def fix_robot_materials(mesh_objects):
    """
    Replace USD materials with simple, visible red materials.
    
    Args:
        mesh_objects: List of mesh objects to fix materials for
    """
    print("  - Simplifying robot materials for visibility...")
    
    replaced_count = 0
    robot_color = (0.8, 0.2, 0.2, 1.0)  # Red
    
    for mesh_obj in mesh_objects:
        # Clear all existing materials
        mesh_obj.data.materials.clear()
        
        # Create and assign a simple visible material
        mat = _create_simple_robot_material(mesh_obj.name, robot_color)
        mesh_obj.data.materials.append(mat)
        replaced_count += 1
    
    print(f"    Replaced {replaced_count} materials with simple red materials")


def _create_simple_robot_material(name, color):
    """
    Creates a super simple material for maximum visibility.
    No metallic, no complex reflections - just diffuse color.
    """
    mat = bpy.data.materials.new(name=f"SimpleRobot_{name}")
    mat.use_nodes = True
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # Create minimal node setup
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (200, 0)
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    
    # Simple diffuse settings - no metallic, moderate roughness
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Metallic'].default_value = 0.0  # Pure diffuse
    bsdf.inputs['Roughness'].default_value = 0.6  # Matte finish
    
    # Handle different Blender versions for Specular
    if 'Specular' in bsdf.inputs:
        bsdf.inputs['Specular'].default_value = 0.3  # Minimal specular
    elif 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.3
    
    # Connect nodes
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

# Go2 bone/joint names from USD structure
LEG_PREFIXES = ['FL', 'FR', 'RL', 'RR']
JOINT_SUFFIXES = ['hip', 'thigh', 'calf', 'foot']

# Proportions for animation
GO2_PROPORTIONS = {
    'base_height': 0.45,
    'stride_length': 0.25,
    'step_height': 0.08,
    'cycle_duration': 0.6, # seconds
}

def load_go2(usd_path, transform=None):
    """
    Import Go2 from USD file.
    """
    if not os.path.exists(usd_path):
        raise FileNotFoundError(f"Go2 USD not found at {usd_path}")
    
    # Track existing objects before import
    existing_objects = set(bpy.data.objects.keys())
    
    # Import USD
    bpy.ops.wm.usd_import(filepath=usd_path)
    
    # Find new objects from USD import
    new_objects = [obj for obj in bpy.data.objects if obj.name not in existing_objects]
    robot_meshes = [obj for obj in new_objects if obj.type == 'MESH']
    
    # Find the base object
    base_obj = bpy.data.objects.get('base')
    if not base_obj:
        # Check for any object named 'base' (sometimes USD imports with prefixes)
        for obj in bpy.data.objects:
            if obj.name.endswith('base') and obj.type == 'EMPTY':
                base_obj = obj
                break
    
    if not base_obj:
        print("Warning: 'base' object not found in USD import.")
        return None, [], []

    # Get all related parts
    robot_parts = []
    def get_children(obj):
        for child in obj.children:
            robot_parts.append(child)
            get_children(child)
    
    robot_parts.append(base_obj)
    get_children(base_obj)
    
    if transform:
        if 'location' in transform:
            base_obj.location = transform['location']
        if 'rotation' in transform:
            base_obj.rotation_euler = transform['rotation']
        if 'scale' in transform:
            s = transform['scale']
            base_obj.scale = (s, s, s) if isinstance(s, (int, float)) else s

    # Fix dark/black materials from USD import (only on robot meshes)
    fix_robot_materials(robot_meshes)
    
    # Hide Empty axes display (not the object itself, as children depend on it)
    for obj in new_objects:
        if obj.type == 'EMPTY':
            obj.empty_display_size = 0.0

    return base_obj, robot_parts, robot_meshes

def rig_go2(base_obj):
    """
    Creates a Blender Armature from the USD hierarchy and sets up IK.
    """
    print("  - Rigging Go2...")
    
    # Create armature
    armature_data = bpy.data.armatures.new("Go2_Armature")
    armature_obj = bpy.data.objects.new("Go2_Rig", armature_data)
    bpy.context.scene.collection.objects.link(armature_obj)
    
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Create Root bone
    root_bone = armature_data.edit_bones.new("root")
    root_bone.head = (0, 0, 0)
    root_bone.tail = (0, 0.1, 0)
    
    # Create leg bones
    for side in LEG_PREFIXES:
        last_bone = root_bone
        for joint in JOINT_SUFFIXES:
            obj_name = f"{side}_{joint}"
            target_obj = bpy.data.objects.get(obj_name)
            
            if not target_obj:
                continue
                
            bone_name = f"{side}_{joint}_bone"
            bone = armature_data.edit_bones.new(bone_name)
            
            # Get world location
            world_loc = target_obj.matrix_world.to_translation()
            
            bone.head = world_loc
            # Tail is next joint or a bit further
            next_joint_idx = JOINT_SUFFIXES.index(joint) + 1
            if next_joint_idx < len(JOINT_SUFFIXES):
                next_obj_name = f"{side}_{JOINT_SUFFIXES[next_joint_idx]}"
                next_obj = bpy.data.objects.get(next_obj_name)
                if next_obj:
                    bone.tail = next_obj.matrix_world.to_translation()
                else:
                    bone.tail = world_loc + Vector((0, 0, -0.1))
            else:
                bone.tail = world_loc + Vector((0, 0, -0.05))
            
            if joint == 'hip':
                bone.parent = root_bone
            else:
                bone.parent = last_bone
            
            last_bone = bone
            
        # Create IK target bone
        ik_name = f"{side}_IK"
        ik_bone = armature_data.edit_bones.new(ik_name)
        foot_obj = bpy.data.objects.get(f"{side}_foot")
        if foot_obj:
            foot_loc = foot_obj.matrix_world.to_translation()
            ik_bone.head = foot_loc
            ik_bone.tail = foot_loc + Vector((0, 0.05, 0))
            ik_bone.use_deform = False

    bpy.ops.object.mode_set(mode='POSE')
    
    # Add IK constraints
    for side in LEG_PREFIXES:
        calf_bone = armature_obj.pose.bones.get(f"{side}_calf_bone")
        if calf_bone:
            ik_const = calf_bone.constraints.new('IK')
            ik_const.target = armature_obj
            ik_const.subtarget = f"{side}_IK"
            ik_const.chain_count = 2 # calf and thigh
            
    # Parent USD parts to bones
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Map USD objects to bones
    # We parent the major empties to bones. 
    # Since meshes are children of these empties, they will follow.
    for side in LEG_PREFIXES:
        for joint in JOINT_SUFFIXES:
            obj_name = f"{side}_{joint}"
            obj = bpy.data.objects.get(obj_name)
            bone_name = f"{side}_{joint}_bone"
            
            if obj and bone_name in armature_obj.pose.bones:
                # Store matrix world to restore it after parenting
                mw = obj.matrix_world.copy()
                obj.parent = armature_obj
                obj.parent_type = 'BONE'
                obj.parent_bone = bone_name
                obj.matrix_world = mw

    # Also parent 'base' to root bone
    if base_obj:
        mw = base_obj.matrix_world.copy()
        base_obj.parent = armature_obj
        base_obj.parent_type = 'BONE'
        base_obj.parent_bone = "root"
        base_obj.matrix_world = mw

    return armature_obj

def animate_go2_walking(armature, path_curve, ground_object, 
                       start_frame=1, end_frame=250, speed=1.0):
    """
    Animate Go2 walking with a trot gait.
    """
    print("  - Animating Go2 trot cycle...")
    scene = bpy.context.scene
    
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    # Trot gait: FL/RR move together, FR/RL move together
    GAIT_OFFSETS = {
        'FL': 0.0,
        'RR': 0.0,
        'FR': 0.5,
        'RL': 0.5
    }
    
    stride = GO2_PROPORTIONS['stride_length']
    step_h = GO2_PROPORTIONS['step_height']
    # Adjust base height for natural stance
    base_h = 0.30 
    
    # Faster trot: 0.4s per cycle was too fast.
    fps = scene.render.fps
    cycle_duration = 0.8 # seconds (Slower, more natural)
    frames_per_cycle = int(fps * cycle_duration / speed)
    frames_per_cycle = max(1, frames_per_cycle)
    
    # Pre-calculate rest locations of IK bones (in World/Armature space)
    
    # Pre-calculate stride/step for consistency
    
    total_frames = end_frame - start_frame + 1
    for frame in tqdm(range(start_frame, end_frame + 1), desc="Animating Go2", total=total_frames):
        scene.frame_set(frame)
        
        # Calculate path position (center of robot projected on path)
        t = (frame - start_frame) / (end_frame - start_frame)
        t = min(t, 0.9999)
        
        path_pos_world, tangent_world = trajectory.evaluate_curve_at_t(path_curve, t)
        
        # Track orientation first to get the rotation matrix
        # Robot is X-forward
        rot_quat = tangent_world.to_track_quat('X', 'Z')
        mat_rot = rot_quat.to_matrix().to_4x4()
        
        # Calculate Cycle Phase
        cycle_phase = ((frame - start_frame) % frames_per_cycle) / frames_per_cycle
        
        # 1. Determine where feet *want* to be (XY) to raycast ground
        #    We need the ground heights of all 4 feet to decide Body Height
        
        foot_ground_heights = {}
        foot_ik_targets_xy = {} # Store xy offsets (world) for later
        
        for side in LEG_PREFIXES:
            # We need the rest position relative to the armature center (to apply rotation)
            # We can get this from the bone's head in Pose Mode (which is essentially local to armature)
            bone = armature.pose.bones.get(f"{side}_IK")
            if not bone: continue
            
            rest_head = bone.bone.head
            
            # Calculate stride phase offset
            phase = (cycle_phase + GAIT_OFFSETS[side]) % 1.0
            
            # Use continuous sinusoidal functions for smooth motion
            # Forward/Backward (X): Full sine wave over the cycle
            # phase 0.0: foot at back (-stride/2) but moving
            # phase 0.5: foot at front (+stride/2) but moving
            # We want to avoid static "rest" look.
            # Shift phase slightly if needed, but Sine is continuous.
            # The issue might be that rest_head position is added to offset.
            # If offset is 0, we are at "rest". 
            # Sine is 0 at phase 0, 0.5, 1.0. This corresponds to center of stride.
            # At center of stride (mid-swing or mid-stance), legs are together.
            # To avoid "standing still" look, ensure legs are always split.
            # With gait offsets (0, 0.5), when one pair is at 0 (center), other is at 0.5 (center).
            # This means at phase 0.0 and 0.5, ALL legs are centered. This looks like "Standing".
            # FIX: Use Cosine for Forward/Backward so extremes are at 0.0 and 0.5.
            # Cos(0) = 1 (Front), Cos(pi) = -1 (Back).
            # Then at phase 0.0, legs are at EXTENSION limits, not center.
            fwd_offset = (stride / 2.0) * math.cos(phase * 2 * math.pi)
            
            # Vertical (Z): Lift during swing (second half of cycle)
            # We want the foot to lift only during "swing" (roughly phase 0.5-1.0)
            # But use smooth transitions
            if phase < 0.5:
                # Stance phase - foot on ground
                up_offset = 0.0
            else:
                # Swing phase - smooth lift and return
                # Map phase 0.5-1.0 to 0-1
                swing_t = (phase - 0.5) * 2.0
                # Use sine for smooth up and down
                up_offset = math.sin(swing_t * math.pi) * step_h
            
            # Local offset vector (Armature Space)
            # fwd_offset is along local X (Robot Forward)
            local_offset_vec = Vector((fwd_offset, 0, 0))
            
            # Rotate to World Space (orientation)
            world_offset_vec = mat_rot @ local_offset_vec
            
            # Approximate Foot World XY is Path_Pos + Rotated_Rest + Rotated_Offset
            # (ignoring Body Z for now, just need XY for raycast)
            
            # Rotated Rest Position (relative to un-rotated path pos)
            rotated_rest = mat_rot @ rest_head
            
            foot_xy_candidate = path_pos_world + rotated_rest + world_offset_vec
            
            # Raycast
            z_ground = robot.raycast_ground(
                scene, 
                foot_xy_candidate, 
                start_height=10.0,
                ground_objects=[ground_object]
            )
            
            foot_ground_heights[side] = z_ground
            foot_ik_targets_xy[side] = fwd_offset # Store local fwd offset for later step
        
        # 2. Determine Adaptive Body Height
        # Average the 4 ground heights
        if foot_ground_heights:
            avg_ground_z = sum(foot_ground_heights.values()) / len(foot_ground_heights)
        else:
            avg_ground_z = 0.0
            
        # Add body bounce
        bounce = math.sin(cycle_phase * 4 * math.pi) * 0.01
        
        # Set Armature Location
        # Z = Average Foot Ground + Base Height + Bounce
        armature_z = avg_ground_z + base_h + bounce
        armature_world_loc = Vector((path_pos_world.x, path_pos_world.y, armature_z))
        
        armature.location = armature_world_loc
        armature.keyframe_insert(data_path="location", frame=frame)
        
        # Determine Body Rotation
        # 1. Orientation (Yaw) from Path
        armature.rotation_euler = rot_quat.to_euler()
        armature.keyframe_insert(data_path="rotation_euler", frame=frame)
        
        # 3. Animate Legs to Reach Targets
        for side in LEG_PREFIXES:
            bone = armature.pose.bones.get(f"{side}_IK")
            if not bone: continue
            
            # Retrieve pre-calcs
            ground_z = foot_ground_heights.get(side, 0.0)
            fwd_offset = foot_ik_targets_xy.get(side, 0.0)
            rest_head = bone.bone.head
            
            phase = (cycle_phase + GAIT_OFFSETS[side]) % 1.0
            
            # Calculate Up Offset (Swing Height)
            if phase >= 0.5:
                t_p = (phase - 0.5) / 0.5
                up_offset = math.sin(t_p * math.pi) * step_h
            else:
                up_offset = 0.0
                
            # Target World Z
            # Add small offset for foot radius so mesh sits ON ground, not IN ground
            foot_radius = 0.022  # approx 2.2cm buffer
            target_z = ground_z + up_offset + foot_radius
            
            # IK Target Local Z (relative to Rest Pose)
            # Logic: Armature_Z + Rest_Z + Pose_Z = Target_Z
            # Pose_Z = Target_Z - Armature_Z - Rest_Z
            # Note: Rest_Z is local. If Robot is flat (no pitch/roll), this holds.
            pose_z = target_z - armature_z - rest_head.z
            
            # Ensure we're never below ground (even if rest pose was)
            # pose_z is relative to (armature_z + rest_head.z)
            # World_Z = armature_z + rest_head.z + pose_z
            # If World_Z < ground_z + radius, clamp it.
            
            bone.location = Vector((fwd_offset, 0, pose_z))
            bone.keyframe_insert(data_path="location", frame=frame)
            
        # Root bone animation is removed/merged into Armature location
        # because the whole armature now floats adaptively. 
        # But if we want 'root' bone functionality (wobble independent of legs?), we can keep it.
        # Here we used Armature Object for main transport, so root bone can stay static or minor wobble.
        # We already added 'bounce' to armature_z, so no need for root bone bounce.
        root_bone = armature.pose.bones.get("root")
        if root_bone:
            root_bone.location = Vector((0,0,0))
            root_bone.keyframe_insert(data_path="location", frame=frame)

    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Hide armature bones in viewport (after animation is complete)
    armature.hide_viewport = True


def setup_go2_collision(robot_meshes, kinematic=True, friction=0.8, restitution=0.1):
    """
    Sets up collision physics for Go2 robot meshes.
    
    Only adds rigid body to meshes that are NOT parented to other meshes.
    This avoids dependency cycles that break physics simulation.
    
    For kinematic mode, the mesh follows animation but can push active rigid bodies.
    
    Args:
        robot_meshes: List of Go2 mesh objects from load_go2()
        kinematic: If True, meshes follow animation but collide with active objects
        friction: Collision friction coefficient
        restitution: Bounciness coefficient
    
    Returns:
        Number of meshes with collision added
    """
    print(f"  - Setting up Go2 collision physics ({len(robot_meshes)} meshes)...")
    count = 0
    skipped = 0
    
    # Create a set of mesh names for quick lookup
    mesh_names = {m.name for m in robot_meshes if m and m.type == 'MESH'}
    
    for mesh in robot_meshes:
        if not mesh or mesh.type != 'MESH':
            continue
        
        # Skip meshes that are parented to other meshes in our list
        # Only add rigid body to "root" meshes to avoid dependency cycles
        parent = mesh.parent
        if parent and parent.type == 'MESH' and parent.name in mesh_names:
            skipped += 1
            continue
        
        # Add rigid body
        bpy.ops.object.select_all(action='DESELECT')
        mesh.select_set(True)
        bpy.context.view_layer.objects.active = mesh
        
        try:
            if not mesh.rigid_body:
                bpy.ops.rigidbody.object_add(type='ACTIVE')
            
            rb = mesh.rigid_body
            rb.kinematic = kinematic
            rb.collision_shape = 'CONVEX_HULL'
            rb.friction = friction
            rb.restitution = restitution
            rb.collision_margin = 0.001
            
            count += 1
        except Exception as e:
            print(f"    Warning: Could not add rigid body to {mesh.name}: {e}")
    
    if skipped > 0:
        print(f"    Added collision to {count} mesh parts (skipped {skipped} children)")
    else:
        print(f"    Added collision to {count} mesh parts")
    return count
