import sys
import os
import bpy
import math

# Add parent directory to path to import foundation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from annotation import motion_trail

def setup_demo_scene():
    # Clear existing objects
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Create object
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.5, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.name = "BouncingBall"
    
    # Animate (Bouncing motion)
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 100
    
    for frame in range(1, 101):
        t = frame / 20.0
        x = t * 2.0 - 5.0
        z = abs(math.sin(t * 2.0)) * 3.0
        
        obj.location = (x, 0, z)
        obj.keyframe_insert(data_path="location", frame=frame)
        
    # Setup Camera
    bpy.ops.object.camera_add(location=(0, -10, 5))
    cam = bpy.context.active_object
    cam.rotation_euler = (math.radians(75), 0, 0)
    bpy.context.scene.camera = cam
    
    return obj

def run():
    print("Running Motion Trail Annotation Demo...")
    obj = setup_demo_scene()
    
    # Add Motion Trail
    motion_trail.create_motion_trail(obj, start_frame=1, end_frame=100, step=1)
    
    # Create viewport restore script (runs when file is opened in UI mode)
    from annotation import viewport
    viewport.create_viewport_restore_script("AnnotationViz")
    
    # Save
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output'))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_file = os.path.join(output_dir, "demo_motion_trail.blend")
    bpy.ops.wm.save_as_mainfile(filepath=output_file)
    print(f"✅ Saved to {output_file}")

if __name__ == "__main__":
    run()
