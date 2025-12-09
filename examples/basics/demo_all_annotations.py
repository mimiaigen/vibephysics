"""
Demo: All Annotations Combined

Demonstrates the unified annotation system with:
- Bounding boxes (animated)
- Motion trails (baked paths)
- Point tracking (surface point cloud)
- Camera systems (center-pointing, following, object-mounted)

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
from vibephysics.camera import CameraManager
from vibephysics.setup import save_blend


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

    # Camera setup is handled separately to demonstrate different camera systems
    return objects


def setup_camera_systems(objects):
    """
    Demonstrate the three camera system types.
    
    Camera Types:
    1. CenterPointingCameraRig: 6 cameras pointing at scene center
    2. FollowingCamera: Camera following the bouncing sphere
    3. ObjectMountedCameraRig: 4 cameras attached to the cube (front/right/back/left)
    """
    cube, sphere, torus = objects
    
    print("\n📷 Setting up Camera Systems...")
    
    # Create camera manager to organize all camera rigs
    cam_manager = CameraManager()
    
    # ==========================================================================
    # Camera Type 1: Center-Pointing Cameras (4 cameras around scene)
    # ==========================================================================
    print("  📷 Type 1: Center-pointing cameras (4 cameras)")
    center_rig = cam_manager.add_center_pointing(
        name='center', 
        num_cameras=4, 
        radius=15.0, 
        height=8.0
    )
    center_rig.create(target_location=(0, 0, 1))  # Point at scene center, slightly elevated
    
    # ==========================================================================
    # Camera Type 2: Following Camera (bird's eye view following sphere)
    # ==========================================================================
    print("  📷 Type 2: Following camera (tracks sphere)")
    follow_rig = cam_manager.add_following(
        name='follow',
        height=10.0,
        look_angle=50  # 50 degrees from vertical
    )
    follow_rig.create(target=sphere)  # Follow the bouncing sphere
    
    # ==========================================================================
    # Camera Type 3: Object-Mounted Cameras (4 cameras on cube, looking outward)
    # ==========================================================================
    print("  📷 Type 3: Object-mounted cameras (4 POV cameras on cube)")
    mounted_rig = cam_manager.add_object_mounted(
        name='mounted',
        num_cameras=4,
        distance=3.0,  # Distance from cube center
        height_offset=0.5,
        directions=['front', 'right', 'back', 'left']
    )
    mounted_rig.create(parent_object=cube)  # Cameras move with the cube!
    
    # ==========================================================================
    # Set default active camera (center pointing, camera at 270°)
    # ==========================================================================
    cam_manager.activate_rig('center', camera_index=3)  # Camera_3_Angle_270
    
    print(f"\n  Total cameras created: {len(cam_manager.get_all_cameras())}")
    print("    - 4 center-pointing cameras (fixed positions, track center)")
    print("    - 1 following camera (bird's eye view, tracks sphere)")
    print("    - 4 mounted cameras (attached to cube, move with it)")
    
    return cam_manager


def run():
    """Main entry point - demonstrates the unified annotation API."""
    print("=" * 60)
    print("Running Combined Annotation Demo (Unified API)")
    print("=" * 60)
    
    objects = setup_demo_scene()
    cube, sphere, torus = objects
    
    # ==========================================================================
    # Camera Systems Setup
    # ==========================================================================
    # Demonstrate all three camera types before annotations
    cam_manager = setup_camera_systems(objects)
    
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
    
    # ==========================================================================
    # Save
    # ==========================================================================
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output'))
    output_file = os.path.join(output_dir, "demo_all_annotations.blend")
    save_blend(output_file)
    
    print("\n" + "=" * 60)
    print("✅ Demo Complete!")
    print("=" * 60)
    print("\nAnnotation Summary:")
    print(f"   - {len(mgr.bboxes)} bounding boxes (cube, sphere, torus)")
    print(f"   - {len(mgr.trails)} motion trails (cube, sphere, torus)")
    print(f"   - {len(mgr.point_clouds)} point cloud tracker")
    print("\nCamera Summary:")
    print(f"   - {len(cam_manager.get_all_cameras())} total cameras")
    print("   - Type 1: 4 center-pointing cameras (fixed, track center)")
    print("   - Type 2: 1 following camera (bird's eye, tracks sphere)")
    print("   - Type 3: 4 object-mounted cameras (attached to cube)")
    print("   - Default view: Camera_3_Angle_270")
    print("\nTo view in Blender:")
    print("   1. Open the .blend file")
    print("   2. Run 'restore_point_tracking_viewport.py' from Text Editor")
    print("   3. Press Space to play animation")
    print("   4. Use Numpad 0 to view through active camera")
    print("   5. Switch cameras in Properties > Scene > Camera")


if __name__ == "__main__":
    run()
