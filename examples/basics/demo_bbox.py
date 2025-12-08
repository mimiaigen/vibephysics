import sys
import os
import bpy
import math

# Setup imports (works with both pip install and local development)
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(_root, 'src'))

from vibephysics.annotation import bbox
from vibephysics.setup import save_blend

def setup_demo_scene():
    # Clear existing objects
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    # Create objects
    bpy.ops.mesh.primitive_cube_add(location=(-3, 0, 0))
    cube = bpy.context.active_object
    cube.name = "MovingCube"
    
    bpy.ops.mesh.primitive_uv_sphere_add(location=(3, 0, 0))
    sphere = bpy.context.active_object
    sphere.name = "RotatingSphere"
    
    # Animate Cube (Location)
    cube.keyframe_insert(data_path="location", frame=1)
    cube.location.y = 5
    cube.keyframe_insert(data_path="location", frame=50)
    cube.location.y = 0
    cube.keyframe_insert(data_path="location", frame=100)
    
    # Animate Sphere (Rotation)
    sphere.rotation_euler = (0, 0, 0)
    sphere.keyframe_insert(data_path="rotation_euler", frame=1)
    sphere.rotation_euler = (math.pi, math.pi, 0)
    sphere.keyframe_insert(data_path="rotation_euler", frame=100)
    
    # Setup Camera
    bpy.ops.object.camera_add(location=(0, -10, 5))
    cam = bpy.context.active_object
    cam.rotation_euler = (math.radians(60), 0, 0)
    bpy.context.scene.camera = cam
    
    return [cube, sphere]

def run():
    print("Running BBox Annotation Demo...")
    objects = setup_demo_scene()
    
    # Add BBox Annotations
    for i, obj in enumerate(objects):
        color = (1.0, 0.2 * i, 0.0, 1.0) # Orange-ish
        bbox.create_bbox_annotation(obj, color=color)
    
    # Register handler
    bbox.register()
    
    # Create viewport restore script (runs when file is opened in UI mode)
    from vibephysics.annotation import viewport
    viewport.create_viewport_restore_script("AnnotationViz")
    
    # Save
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output'))
    save_blend(os.path.join(output_dir, "demo_bbox.blend"))

if __name__ == "__main__":
    run()
