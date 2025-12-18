"""
Go2 Robot Simulation Test

Demonstrates loading a Go2 robot from USD, rigging it, 
and making it walk on uneven ground.
"""

import sys
import os
import bpy
import argparse

# Setup imports
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(_root, 'src'))

from vibephysics.foundation import scene, ground, materials, lighting, trajectory, go2
from vibephysics.setup import save_blend

def run_go2_simulation(usd_path, output_path):
    print("=" * 60)
    print("  🐕 Go2 Robot Simulation")
    print("=" * 60)
    
    start_frame = 1
    end_frame = 150
    
    # 1. Init scene
    scene.init_simulation(start_frame=start_frame, end_frame=end_frame)
    
    # 2. Create ground
    terrain = ground.create_uneven_ground(
        z_base=0.0,
        size=20.0,
        noise_scale=2.0,
        strength=0.3
    )
    materials.create_mud_material(terrain)
    
    # 3. Load Go2
    # The user provided the path: /Users/shamangary/codeDemo/unitree_model/Go2/usd/go2.usd
    base_obj, robot_parts, robot_meshes = go2.load_go2(usd_path)
    
    if not base_obj:
        print("Failed to load Go2!")
        return

    # 4. Rig Go2
    armature = go2.rig_go2(base_obj)
    
    # 5. Create Path
    path = trajectory.create_circular_path(radius=4.0, z_location=1.0)
    
    # 6. Animate
    go2.animate_go2_walking(
        armature=armature,
        path_curve=path,
        ground_object=terrain,
        start_frame=start_frame,
        end_frame=end_frame,
        speed=1.0 # Normal speed, foundation now uses 0.8s cycle which is slower
    )
    
    # 7. Lighting
    lighting.setup_lighting(
        resolution_x=1920, 
        resolution_y=1080, 
        start_frame=start_frame, 
        end_frame=end_frame
    )
    
    # Set active camera to follow the robot
    cam = bpy.data.objects.get('Camera')
    if cam:
        # Create constraint
        const = cam.constraints.new('COPY_LOCATION')
        const.target = armature
        const.use_offset = True
        cam.location = (8, -8, 5)
        
        # Track to
        track = cam.constraints.new('TRACK_TO')
        track.target = armature
        track.track_axis = 'TRACK_NEGATIVE_Z'
        track.up_axis = 'UP_Y'

    # Save
    save_blend(output_path)
    print(f"\n✅ Simulation saved to {output_path}")

if __name__ == "__main__":
    # Get USD path (auto-downloads if needed)
    usd_path = go2.get_go2_usd_path()
    output_path = "output/go2_walk.blend"
    
    # Create output dir
    os.makedirs("output", exist_ok=True)
    
    run_go2_simulation(usd_path, output_path)
