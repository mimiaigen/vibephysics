"""
Camera Module

Provides various camera setup configurations for scene visualization.

Camera Types:
1. CenterPointingCameraRig - N cameras pointing at a center target
2. FollowingCamera - Camera that follows an object from above (sky view)
3. ObjectMountedCameraRig - N cameras attached to object, pointing outward

Usage:
    from vibephysics.camera import (
        CenterPointingCameraRig,
        FollowingCamera,
        ObjectMountedCameraRig,
        CameraManager,
    )
    
    # 6 cameras pointing at center
    rig = CenterPointingCameraRig(num_cameras=6, radius=15, height=8)
    cameras = rig.create(target_object=my_obj)
    
    # Following camera (bird's eye view)
    cam = FollowingCamera(height=10, look_angle=45)
    cam.create(target=robot_armature)
    
    # Object-mounted cameras (e.g., robot POV)
    mounted = ObjectMountedCameraRig(num_cameras=4)
    mounted.create(parent_object=robot)
    
    # Use CameraManager to manage multiple rigs
    manager = CameraManager()
    manager.add_center_pointing('center', num_cameras=6, radius=15)
    manager.add_following('follow', height=10)
    manager.add_object_mounted('mounted', num_cameras=4)
"""

# Base class
from .base import BaseCamera

# Camera rig types
from .center import CenterPointingCameraRig, create_center_cameras
from .following import FollowingCamera, create_following_camera
from .mounted import ObjectMountedCameraRig, create_mounted_cameras

# Camera manager
from .manager import CameraManager, setup_all_camera_types

__all__ = [
    # Base class
    'BaseCamera',
    
    # Camera rig types
    'CenterPointingCameraRig',
    'FollowingCamera',
    'ObjectMountedCameraRig',
    
    # Camera manager
    'CameraManager',
    
    # Convenience functions
    'create_center_cameras',
    'create_following_camera',
    'create_mounted_cameras',
    'setup_all_camera_types',
]
