"""
Demo: All Annotations Combined

Demonstrates the unified annotation system with:
- Bounding boxes (animated)
- Motion trails (baked paths)
- Point tracking (surface point cloud)

Uses the new AnnotationManager for simplified API.
"""

import sys
import os
import bpy
import math
import random

# Setup imports (works with both pip install and local development)
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(_root, 'src'))

from vibephysics.annotation import AnnotationManager, bbox, motion_trail, point_tracking, viewport


def setup_demo_scene():
    """Create animated demo objects."""
    # Clear existing objects
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 150
    
    objects = []
    
    # 1. Cube (Boxy) - rotating spiral motion
    bpy.ops.mesh.primitive_cube_add(location=(-4, 0, 0))
    cube = bpy.context.active_object
    cube.name = "Boxy"
    objects.append(cube)
    
    for f in range(1, 151):
        t = f / 20.0
        cube.location.x = -4 + math.sin(t) * 2
        cube.location.y = math.cos(t) * 2
        cube.rotation_euler.z = t
        cube.keyframe_insert(data_path="location", frame=f)
        cube.keyframe_insert(data_path="rotation_euler", frame=f)
        
    # 2. Sphere (Roundy) - bouncing motion
    bpy.ops.mesh.primitive_uv_sphere_add(location=(4, 0, 0))
    sphere = bpy.context.active_object
    sphere.name = "Roundy"
    objects.append(sphere)
    
    for f in range(1, 151):
        t = f / 15.0
        sphere.location.z = abs(math.sin(t)) * 3
        sphere.scale = (1 + math.sin(t)*0.2, 1 + math.sin(t)*0.2, 1 - math.sin(t)*0.2)
        sphere.keyframe_insert(data_path="location", frame=f)
        sphere.keyframe_insert(data_path="scale", frame=f)

    # 3. Torus (Donut) - sweeping motion with rotation
    bpy.ops.mesh.primitive_torus_add(location=(0, 5, 2))
    torus = bpy.context.active_object
    torus.name = "Donut"
    objects.append(torus)
    
    for f in range(1, 151):
        t = f / 25.0
        torus.location.x = math.sin(t * 2) * 5
        torus.rotation_euler.x = t * 2
        torus.keyframe_insert(data_path="location", frame=f)
        torus.keyframe_insert(data_path="rotation_euler", frame=f)

    # Setup Camera
    bpy.ops.object.camera_add(location=(0, -12, 8))
    cam = bpy.context.active_object
    cam.rotation_euler = (math.radians(60), 0, 0)
    bpy.context.scene.camera = cam
    
    return objects


def run():
    """Main entry point - demonstrates the unified annotation API."""
    print("=" * 60)
    print("Running Combined Annotation Demo (Unified API)")
    print("=" * 60)
    
    objects = setup_demo_scene()
    cube, sphere, torus = objects
    
    # ==========================================================================
    # Method 1: Using AnnotationManager (Recommended)
    # ==========================================================================
    # This is the new unified API that simplifies annotation management.
    
    mgr = AnnotationManager(collection_name="AnnotationViz")
    
    # Add bounding boxes with distinct colors
    print("\n📦 Adding Bounding Boxes...")
    mgr.add_bbox(cube, color=(1.0, 0.2, 0.0, 1.0))    # Orange
    mgr.add_bbox(sphere, color=(0.0, 1.0, 0.2, 1.0))  # Green
    mgr.add_bbox(torus, color=(0.2, 0.4, 1.0, 1.0))   # Blue
    
    # Add motion trails for ALL objects (this was the missing trail for sphere!)
    print("\n🌀 Adding Motion Trails...")
    mgr.add_motion_trail(cube, color=(1.0, 0.5, 0.0, 1.0))    # Orange trail
    mgr.add_motion_trail(sphere, color=(0.0, 1.0, 0.5, 1.0))  # Green trail (was missing!)
    mgr.add_motion_trail(torus, color=(0.5, 0.5, 1.0, 1.0))   # Blue trail
    
    # Add point tracking
    print("\n🎯 Adding Point Tracking...")
    mgr.add_point_tracking(objects, points_per_object=100)
    
    # Finalize - registers all handlers and creates embedded scripts
    mgr.finalize(setup_viewport=False)
    
    # Create viewport restore script for when file is re-opened
    viewport.create_viewport_restore_script("AnnotationViz")
    
    # ==========================================================================
    # Alternative: Quick API (one-liner)
    # ==========================================================================
    # For even simpler usage, you can use:
    #
    #   from annotation import quick_annotate
    #   quick_annotate(objects, bbox=True, trail=True, point_tracking=True)
    #
    # This automatically creates all annotations with auto-generated colors.
    
    # ==========================================================================
    # Alternative: Individual Module Usage (Original API)
    # ==========================================================================
    # You can still use the individual modules directly:
    #
    #   bbox.create_bbox_annotation(cube, color=(1, 0, 0, 1))
    #   bbox.register()
    #   
    #   motion_trail.create_motion_trail(cube, start_frame=1, end_frame=150)
    #   
    #   point_tracking.setup_point_tracking_visualization(objects, points_per_object=50)
    
    # ==========================================================================
    # Save
    # ==========================================================================
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output'))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_file = os.path.join(output_dir, "demo_all_annotations.blend")
    bpy.ops.wm.save_as_mainfile(filepath=output_file)
    
    print("\n" + "=" * 60)
    print("✅ Demo Complete!")
    print(f"   Saved to: {output_file}")
    print("=" * 60)
    print("\nAnnotation Summary:")
    print(f"   - {len(mgr.bboxes)} bounding boxes (cube, sphere, torus)")
    print(f"   - {len(mgr.trails)} motion trails (cube, sphere, torus)")
    print(f"   - {len(mgr.point_clouds)} point cloud tracker")
    print("\nTo view in Blender:")
    print("   1. Open the .blend file")
    print("   2. Run 'restore_point_tracking_viewport.py' from Text Editor")
    print("   3. Press Space to play animation")


if __name__ == "__main__":
    run()
