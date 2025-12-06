import sys
import os
import bpy
import math

# Add parent directory to path to import foundation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from annotation import point_tracking

def setup_demo_scene():
    # Clear existing objects
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Create object
    bpy.ops.mesh.primitive_monkey_add(size=2.0, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "Suzanne"
    
    # Animate Rotation
    obj.rotation_euler = (0, 0, 0)
    obj.keyframe_insert(data_path="rotation_euler", frame=1)
    obj.rotation_euler = (0, 0, math.radians(360))
    obj.keyframe_insert(data_path="rotation_euler", frame=100)
    
    # Setup Camera
    bpy.ops.object.camera_add(location=(0, -8, 4))
    cam = bpy.context.active_object
    cam.rotation_euler = (math.radians(75), 0, 0)
    bpy.context.scene.camera = cam
    
    return [obj]

def run():
    print("Running Point Tracking Annotation Demo...")
    objects = setup_demo_scene()
    
    # Add Point Tracking
    # setup_viewport=False because we are running in background usually,
    # but it will create the scripts for UI mode.
    point_tracking.setup_point_tracking_visualization(objects, points_per_object=200, setup_viewport=True)
    
    # Save
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output'))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_file = os.path.join(output_dir, "demo_point_tracking.blend")
    bpy.ops.wm.save_as_mainfile(filepath=output_file)
    print(f"✅ Saved to {output_file}")

if __name__ == "__main__":
    run()
