"""
Demo: Dynamic Frustum Culling

Demonstrates frustum-based point tracking with:
- Scattered cubes as tracked objects
- Moving carrier with mounted camera (circular motion)
- Three frustum modes: all, highlight, frustum_only

Simplified version of robot_forest_walk.py for showcasing frustum culling.
"""

import sys
import os
import bpy
import math
import random

# Setup imports (works with both pip install and local development)
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(_root, 'src'))

from vibephysics.annotation import AnnotationManager, point_tracking
from vibephysics.camera import CameraManager
from vibephysics.setup import save_blend


def setup_demo_scene():
    """Create scene with scattered cubes and moving carrier."""
    # Clear existing objects
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 200
    
    # ==========================================================================
    # Ground & Lighting
    # ==========================================================================
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    bpy.context.active_object.name = "Ground"
    
    bpy.ops.object.light_add(type='SUN', location=(10, 10, 20))
    bpy.context.active_object.data.energy = 3.0
    
    # ==========================================================================
    # Scattered Cubes (objects to track)
    # ==========================================================================
    random.seed(42)
    tracked_objects = []
    
    for i in range(30):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(3, 12)
        x, y = dist * math.cos(angle), dist * math.sin(angle)
        z = random.uniform(0.3, 1.5)
        
        bpy.ops.mesh.primitive_cube_add(size=0.4, location=(x, y, z))
        cube = bpy.context.active_object
        cube.name = f"Cube_{i:03d}"
        cube.scale = (random.uniform(0.5, 1.2),) * 3
        tracked_objects.append(cube)
    
    # ==========================================================================
    # Moving Carrier (animated in circle - camera mounts here)
    # ==========================================================================
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(8, 0, 1.0))
    carrier = bpy.context.active_object
    carrier.name = "CameraCarrier"
    
    # Animate carrier in circular motion (like demo_all_annotations.py style)
    radius = 8.0
    for f in range(1, 201):
        t = (f / 200) * 2 * math.pi  # Full circle over 200 frames
        carrier.location.x = radius * math.cos(t)
        carrier.location.y = radius * math.sin(t)
        carrier.location.z = 1.0
        # Point carrier in direction of motion
        carrier.rotation_euler.z = t + math.pi / 2
        carrier.keyframe_insert(data_path="location", frame=f)
        carrier.keyframe_insert(data_path="rotation_euler", frame=f)
    
    return tracked_objects, carrier


def setup_camera_system(carrier):
    """Setup mounted camera on the carrier."""
    print("\n📷 Setting up Camera System...")
    
    cam_manager = CameraManager()
    
    # Object-mounted camera on carrier
    mounted_rig = cam_manager.add_object_mounted(
        name='mounted',
        num_cameras=1,
        distance=0.5,
        height_offset=0.3,
        forward_axis='X'
    )
    mounted_rig.create(parent_object=carrier, lens=35)
    cam_manager.activate_rig('mounted', camera_index=0)
    
    print("  📷 Mounted camera on carrier (moves with carrier)")
    print(f"  Total cameras: {len(cam_manager.get_all_cameras())}")
    
    return cam_manager


def run():
    """Main entry point - demonstrates frustum culling with point tracking."""
    print("=" * 60)
    print("Running Dynamic Frustum Culling Demo")
    print("=" * 60)
    
    # ==========================================================================
    # Scene Setup
    # ==========================================================================
    tracked_objects, carrier = setup_demo_scene()
    print(f"\n🎲 Created {len(tracked_objects)} cubes")
    print("🚀 Created moving carrier (circular path)")
    
    # ==========================================================================
    # Camera System
    # ==========================================================================
    cam_manager = setup_camera_system(carrier)
    
    # ==========================================================================
    # Annotations with Frustum Culling
    # ==========================================================================
    print("\n🎯 Adding Point Tracking with Frustum Culling...")
    
    mgr = AnnotationManager(collection_name="AnnotationViz")
    
    # Add point tracking with frustum culling
    # NOTE: show_frustum=False - frustum created AFTER camera setup
    mgr.add_point_tracking(
        tracked_objects=tracked_objects,
        points_per_object=50,
        point_size=0.06,
        # frustum_mode options:
        #   - 'all': Show all points (no culling)
        #   - 'highlight': All visible, in-frustum points turn RED
        #   - 'frustum_only': Only show points inside frustum
        frustum_mode='highlight',      # Points in frustum turn red
        frustum_distance=15.0,         # Frustum distance in meters
        show_frustum=False             # Frustum created separately below
    )
    
    mgr.finalize(setup_viewport=False)
    
    # Create frustum wireframe AFTER camera is set up
    point_tracking.setup_frustum_visualization(
        camera=bpy.context.scene.camera,
        collection_name="AnnotationViz"
    )
    
    print("  - Mode: highlight (in-frustum points turn red)")
    print("  - Frustum distance: 15m")
    print("  - Points per object: 50")
    
    # ==========================================================================
    # Save
    # ==========================================================================
    output_dir = os.path.abspath(os.path.join(_root, 'output'))
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "demo_frustum_culling.blend")
    save_blend(output_file)
    
    print("\n" + "=" * 60)
    print("✅ Demo Complete!")
    print("=" * 60)
    print("\nSummary:")
    print(f"   - {len(tracked_objects)} tracked cubes")
    print(f"   - {len(mgr.point_clouds)} point cloud tracker")
    print("   - Mounted camera on moving carrier")
    print("\nFrustum Modes (edit frustum_mode in script to change):")
    print("   - 'all': Show all points (no culling)")
    print("   - 'highlight': All visible, in-frustum points turn RED")
    print("   - 'frustum_only': Only show points inside frustum")
    print("\nTo view in Blender:")
    print("   1. Open output/demo_frustum_culling.blend")
    print("   2. Press Space to play animation")
    print("   3. Watch points change color as camera moves!")


if __name__ == "__main__":
    run()
