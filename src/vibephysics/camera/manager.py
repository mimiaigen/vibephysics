"""
Camera Manager Module

Provides unified management for all camera rigs in a scene.
"""

import bpy
from .center import CenterPointingCameraRig
from .following import FollowingCamera
from .mounted import ObjectMountedCameraRig


class CameraManager:
    """
    Unified manager for all camera rigs in a scene.
    
    Usage:
        from vibephysics.camera import CameraManager
        
        manager = CameraManager()
        
        # Add different camera setups
        center_rig = manager.add_center_pointing(num_cameras=6, radius=15)
        follow_cam = manager.add_following(target=robot)
        mounted_rig = manager.add_object_mounted(parent=robot, num_cameras=4)
        
        # Switch between rigs
        manager.activate_rig('center_pointing')
        manager.set_camera(0)
    """
    
    def __init__(self):
        """Initialize camera manager."""
        self.rigs = {}
        self.active_rig_name = None
        
    def add_center_pointing(self, name='center_pointing', **kwargs):
        """
        Add a center-pointing camera rig.
        
        Args:
            name: Name for this rig
            **kwargs: Arguments passed to CenterPointingCameraRig
            
        Returns:
            The created rig (not yet created, call .create() on it)
        """
        rig = CenterPointingCameraRig(**kwargs)
        self.rigs[name] = rig
        return rig
    
    def add_following(self, name='following', **kwargs):
        """
        Add a following camera.
        
        Args:
            name: Name for this rig
            **kwargs: Arguments passed to FollowingCamera
            
        Returns:
            The created rig (not yet created, call .create() on it)
        """
        rig = FollowingCamera(**kwargs)
        self.rigs[name] = rig
        return rig
    
    def add_object_mounted(self, name='object_mounted', **kwargs):
        """
        Add an object-mounted camera rig.
        
        Args:
            name: Name for this rig
            **kwargs: Arguments passed to ObjectMountedCameraRig
            
        Returns:
            The created rig (not yet created, call .create() on it)
        """
        rig = ObjectMountedCameraRig(**kwargs)
        self.rigs[name] = rig
        return rig
    
    def get_rig(self, name):
        """
        Get a camera rig by name.
        
        Args:
            name: Name of the rig
            
        Returns:
            The rig or None if not found
        """
        return self.rigs.get(name)
    
    def activate_rig(self, name, camera_index=0):
        """
        Activate a camera rig and set a specific camera as active.
        
        Args:
            name: Name of the rig to activate
            camera_index: Which camera in the rig to make active
            
        Returns:
            The activated camera or None
        """
        rig = self.rigs.get(name)
        if rig:
            self.active_rig_name = name
            rig.set_active(camera_index)
            return rig.cameras[camera_index] if rig.cameras else None
        return None
    
    def get_all_cameras(self):
        """
        Get all cameras from all rigs.
        
        Returns:
            List of all camera objects
        """
        all_cams = []
        for rig in self.rigs.values():
            all_cams.extend(rig.get_cameras())
        return all_cams
    
    def cycle_camera(self, within_rig=True):
        """
        Cycle to the next camera.
        
        Args:
            within_rig: If True, cycle within active rig; if False, cycle through all
            
        Returns:
            The newly active camera
        """
        if within_rig and self.active_rig_name:
            rig = self.rigs[self.active_rig_name]
            if hasattr(rig, 'cycle_camera'):
                return rig.cycle_camera()
            else:
                cameras = rig.get_cameras()
                current = bpy.context.scene.camera
                if current in cameras:
                    idx = (cameras.index(current) + 1) % len(cameras)
                else:
                    idx = 0
                bpy.context.scene.camera = cameras[idx]
                return cameras[idx]
        else:
            # Cycle through all cameras
            all_cams = self.get_all_cameras()
            if not all_cams:
                return None
            current = bpy.context.scene.camera
            if current in all_cams:
                idx = (all_cams.index(current) + 1) % len(all_cams)
            else:
                idx = 0
            bpy.context.scene.camera = all_cams[idx]
            return all_cams[idx]
    
    def delete_all(self):
        """Delete all cameras from all rigs."""
        for rig in self.rigs.values():
            rig.delete_all()
        self.rigs = {}
        self.active_rig_name = None


def setup_all_camera_types(target_object, parent_for_mounted=None):
    """
    Demo function to create all three camera types at once.
    
    Args:
        target_object: Object to track/follow
        parent_for_mounted: Object for mounted cameras (uses target if None)
        
    Returns:
        CameraManager with all rigs configured
    """
    manager = CameraManager()
    
    # 1. Center pointing (6 cameras)
    rig1 = manager.add_center_pointing('center', num_cameras=6, radius=15, height=8)
    rig1.create(target_object=target_object)
    
    # 2. Following camera
    rig2 = manager.add_following('follow', height=12, look_angle=60)
    rig2.create(target=target_object)
    
    # 3. Object mounted (4 directions)
    parent = parent_for_mounted or target_object
    if parent.type == 'MESH':
        rig3 = manager.add_object_mounted('mounted', num_cameras=4, distance=2.0)
        rig3.create(parent_object=parent)
    
    # Activate center pointing by default
    manager.activate_rig('center')
    
    return manager
