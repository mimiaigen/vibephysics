"""
Inspect the duck rig's IK setup
"""
import sys
import os
import bpy

def load_duck_robot(filepath):
    """Loads the duck robot."""
    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        data_to.objects = data_from.objects

    armature = None
    for obj in data_to.objects:
        if obj:
            if "Background" in obj.name:
                continue
            if obj.name not in bpy.context.scene.objects:
                bpy.context.scene.collection.objects.link(obj)
            if obj.type == 'ARMATURE':
                armature = obj
        
    return armature

def inspect_ik(armature):
    """Inspect IK setup."""
    print("\n" + "="*60)
    print("DUCK RIG IK INSPECTION")
    print("="*60)
    
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    bones = armature.pose.bones
    
    # Find all bones with IK constraints
    print("\n--- BONES WITH IK CONSTRAINTS ---")
    ik_bones = []
    for bone in bones:
        for constraint in bone.constraints:
            if constraint.type == 'IK':
                ik_bones.append(bone)
                print(f"\nBone: {bone.name}")
                print(f"  IK Target: {constraint.target.name if constraint.target else 'None'}")
                print(f"  IK Subtarget: {constraint.subtarget}")
                print(f"  Chain Length: {constraint.chain_count}")
                print(f"  Influence: {constraint.influence}")
    
    if not ik_bones:
        print("No IK constraints found!")
    
    # Find leg-related bones
    print("\n--- LEG-RELATED BONES ---")
    leg_bones = [b for b in bones if 'leg' in b.name.lower() or 'knee' in b.name.lower() 
                 or 'ankle' in b.name.lower() or 'hip' in b.name.lower() or 'foot' in b.name.lower()]
    for bone in leg_bones:
        constraints_str = ", ".join([c.type for c in bone.constraints]) if bone.constraints else "None"
        print(f"  {bone.name}: constraints=[{constraints_str}]")
    
    # Check fk_ik_controller if exists
    print("\n--- FK/IK CONTROLLER ---")
    if 'fk_ik_controller' in bones:
        ctrl = bones['fk_ik_controller']
        print(f"Found fk_ik_controller bone")
        print(f"  Location: {ctrl.location}")
        # Check for custom properties
        for key in ctrl.keys():
            if key != '_RNA_UI':
                print(f"  Property '{key}': {ctrl[key]}")
    else:
        print("No fk_ik_controller found")
    
    bpy.ops.object.mode_set(mode='OBJECT')

def main():
    # Cleanup
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Load duck
    duck_path = "/Users/shamangary/codeDemo/Open_Duck_Blender/open-duck-mini.blend"
    armature = load_duck_robot(duck_path)
    
    if armature:
        inspect_ik(armature)
    else:
        print("Failed to load duck!")

if __name__ == "__main__":
    main()
