"""
Simple straight walk test - now with FK/IK switch enabled!
"""
import sys
import os
import bpy
import math
from mathutils import Vector, Matrix

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def load_duck_robot(filepath):
    """Loads the duck robot."""
    if not os.path.exists(filepath):
        print(f"Error: Duck file not found at {filepath}")
        return None, []

    print(f"Loading duck from {filepath}...")
    
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
        armature.location = (0, 0, 0)
        armature.rotation_euler = (0, 0, 0)
        armature.scale = (1.0, 1.0, 1.0)
        
    return armature, robot_parts

def simple_walk_test(armature, start_frame=1, end_frame=100):
    """
    Simple walk animation with IK mode enabled.
    """
    scene = bpy.context.scene
    
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    bones = armature.pose.bones
    
    # CRITICAL: Enable IK mode!
    if 'fk_ik_controller' in bones:
        fk_ik_ctrl = bones['fk_ik_controller']
        if 'fk_ik' in fk_ik_ctrl:
            print(f"Setting FK/IK to IK mode (1.0)")
            fk_ik_ctrl['fk_ik'] = 1.0
            fk_ik_ctrl.keyframe_insert(data_path='["fk_ik"]', frame=start_frame)
    else:
        print("WARNING: No fk_ik_controller found!")
    
    # Get IK foot bones
    bone_l = bones.get('leg_ik.l')
    bone_r = bones.get('leg_ik.r')
    
    if not bone_l or not bone_r:
        print("ERROR: IK foot bones not found!")
        return
    
    print(f"IK bones found: leg_ik.l, leg_ik.r")
    
    # Walking parameters
    walk_speed = 0.3
    step_length = 1.5
    step_height = 0.8
    frames_per_cycle = 20
    
    print(f"Walk speed: {walk_speed}, Step length: {step_length}, Step height: {step_height}")
    
    for frame in range(start_frame, end_frame + 1):
        scene.frame_set(frame)
        
        # Move armature forward
        y_pos = (frame - start_frame) * walk_speed
        armature.location = Vector((0, y_pos, 0))
        armature.keyframe_insert(data_path="location", frame=frame)
        
        # Cycle phase
        cycle_phase = ((frame - start_frame) % frames_per_cycle) / frames_per_cycle
        
        # Root bounce
        if 'root' in bones:
            bounce = math.sin(cycle_phase * 4 * math.pi) * 0.1
            bones['root'].location.z = bounce
            bones['root'].keyframe_insert(data_path="location", frame=frame)
        
        def calc_foot_offset(phase_offset):
            foot_phase = (cycle_phase + phase_offset) % 1.0
            
            if foot_phase < 0.5:
                t = foot_phase / 0.5
                forward = step_length * (0.5 - t)
                height = 0.0
            else:
                t = (foot_phase - 0.5) / 0.5
                forward = step_length * (-0.5 + t)
                height = math.sin(t * math.pi) * step_height
            
            return forward, height
        
        left_forward, left_height = calc_foot_offset(0.0)
        right_forward, right_height = calc_foot_offset(0.5)
        
        # Set IK target positions (Y=forward, Z=height)
        bone_l.location = Vector((0, left_forward, left_height))
        bone_l.keyframe_insert(data_path="location", frame=frame)
        
        bone_r.location = Vector((0, right_forward, right_height))
        bone_r.keyframe_insert(data_path="location", frame=frame)
        
        if frame <= 21:
            print(f"F{frame}: phase={cycle_phase:.2f} L=({left_forward:.1f},{left_height:.1f}) R=({right_forward:.1f},{right_height:.1f})")
    
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"\nAnimation complete! Frames {start_frame}-{end_frame}")

def setup_scene():
    """Setup test scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Ground
    bpy.ops.mesh.primitive_plane_add(size=50, location=(0, 25, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    
    # Camera
    bpy.ops.object.camera_add(location=(15, 15, 8))
    camera = bpy.context.active_object
    camera.rotation_euler = (math.radians(70), 0, math.radians(135))
    bpy.context.scene.camera = camera
    
    # Light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 20))
    
    return ground

def main():
    print("\n" + "="*50)
    print("WALK TEST WITH IK MODE ENABLED")
    print("="*50 + "\n")
    
    ground = setup_scene()
    
    duck_path = "/Users/shamangary/codeDemo/Open_Duck_Blender/open-duck-mini.blend"
    armature, robot_parts = load_duck_robot(duck_path)
    
    if not armature:
        print("Failed to load duck!")
        return
    
    print(f"Loaded: {armature.name} + {len(robot_parts)} parts")
    
    simple_walk_test(armature, start_frame=1, end_frame=150)
    
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 150
    bpy.context.scene.frame_set(1)
    
    output_path = os.path.abspath("debug_walk.blend")
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"\nSaved to: {output_path}")

if __name__ == "__main__":
    main()
