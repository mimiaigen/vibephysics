"""
Demo: Motion Trail with Camera Systems

Demonstrates motion trail annotation combined with different camera views.
Shows how object-mounted cameras can provide dynamic POV perspectives.
"""

import sys
import os
import bpy
import math

# Setup imports (works with both pip install and local development)
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(_root, 'src'))

from vibephysics.annotation import motion_trail
from vibephysics.camera import CameraManager
from vibephysics.setup import save_blend

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
    
    return obj


def setup_camera_systems(obj):
    """
    Setup camera systems to view the bouncing ball from different perspectives.
    
    Camera Types demonstrated:
    1. Center-pointing: Fixed cameras looking at scene center
    2. Following: Camera that tracks the ball from above
    3. Object-mounted: Cameras attached to the ball (POV view)
    """
    print("\n📷 Setting up Camera Systems...")
    
    cam_manager = CameraManager()
    
    # ==========================================================================
    # Type 1: Center-pointing cameras (4 cameras, smaller scene)
    # ==========================================================================
    print("  📷 Type 1: Center-pointing cameras (4 cameras)")
    center_rig = cam_manager.add_center_pointing(
        name='center',
        num_cameras=4,
        radius=10.0,
        height=5.0
    )
    center_rig.create(target_location=(0, 0, 1.5))
    
    # ==========================================================================
    # Type 2: Following camera (bird's eye tracking the ball)
    # ==========================================================================
    print("  📷 Type 2: Following camera (tracks ball)")
    follow_rig = cam_manager.add_following(
        name='follow',
        height=8.0,
        look_angle=60
    )
    follow_rig.create(target=obj)
    
    # ==========================================================================
    # Type 3: Object-mounted cameras (4 cameras on the ball, looking outward)
    # ==========================================================================
    print("  📷 Type 3: Object-mounted POV cameras (4 on ball)")
    mounted_rig = cam_manager.add_object_mounted(
        name='mounted',
        num_cameras=4,
        distance=2.0,
        height_offset=0.0,
        directions=['front', 'right', 'back', 'left']
    )
    mounted_rig.create(parent_object=obj)
    
    # Set default to center camera at 270° for this demo
    cam_manager.activate_rig('center', camera_index=3)  # Camera_3_Angle_270
    
    print(f"\n  Total cameras: {len(cam_manager.get_all_cameras())}")
    
    return cam_manager

def run():
    print("=" * 60)
    print("Running Motion Trail + Camera Systems Demo")
    print("=" * 60)
    
    obj = setup_demo_scene()
    
    # Setup camera systems
    cam_manager = setup_camera_systems(obj)
    
    # Add Motion Trail
    print("\n🌀 Adding Motion Trail...")
    motion_trail.create_motion_trail(obj, start_frame=1, end_frame=100, step=1,
                                     color=(0.0, 1.0, 0.8, 1.0))  # Cyan trail
    
    # Create viewport restore script (runs when file is opened in UI mode)
    from vibephysics.annotation import viewport
    viewport.create_viewport_restore_script("AnnotationViz")
    
    # Save
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output'))
    output_file = os.path.join(output_dir, "demo_motion_trail.blend")
    save_blend(output_file)
    
    print("\n" + "=" * 60)
    print("✅ Demo Complete!")
    print("=" * 60)
    print("\nCamera Summary:")
    print(f"   - {len(cam_manager.get_all_cameras())} total cameras")
    print("   - 4 center-pointing cameras (fixed positions)")
    print("   - 1 following camera (tracks ball from above)")
    print("   - 4 object-mounted POV cameras (move with ball)")
    print("\nTry switching cameras to see different views!")
    print("   - Following camera shows the ball with motion trail")
    print("   - Object-mounted cameras show dynamic POV as ball bounces")

if __name__ == "__main__":
    run()
