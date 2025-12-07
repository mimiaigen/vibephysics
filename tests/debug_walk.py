"""
Simple straight walk test using Open Duck foundation classes.
"""
import sys
import os
import bpy
import math
from mathutils import Vector

# Add src to path so we can import vibephysics
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from vibephysics.foundation import open_duck, trajectory

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
    print("WALK TEST WITH OPEN DUCK FOUNDATION")
    print("="*50 + "\n")
    
    ground = setup_scene()
    
    # 1. Load Duck
    try:
        # Use default path handling in open_duck
        armature, robot_parts = open_duck.load_open_duck()
    except Exception as e:
        print(f"Failed to load duck: {e}")
        return
    
    print(f"Loaded: {armature.name} + {len(robot_parts)} parts")
    
    # 2. Create Path (Straight line)
    # Create a straight path using trajectory waypoints
    waypoints = [
        (0, 0, 0),
        (0, 30, 0)
    ]
    path = trajectory.create_waypoint_path(waypoints, name="WalkPath")
    
    # 3. Animate Walking
    # animate_duck_walking handles the IK/FK setup and animation loop
    open_duck.animate_duck_walking(
        armature=armature,
        path_curve=path,
        ground_object=ground,
        start_frame=1,
        end_frame=150,
        speed=1.0
    )
    
    # 4. Setup Collision (Optional but good for completeness)
    open_duck.setup_duck_collision(robot_parts, kinematic=True)

    # Save result
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 150
    bpy.context.scene.frame_set(1)
    
    output_path = os.path.abspath("debug_walk.blend")
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"\nSaved to: {output_path}")

if __name__ == "__main__":
    main()
