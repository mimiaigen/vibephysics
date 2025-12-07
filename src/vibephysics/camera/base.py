"""
Base Camera Module

Provides the base class for all camera configurations.
"""

import bpy


class BaseCamera:
    """
    Base class for camera configurations.
    
    All camera rigs (CenterPointing, Following, ObjectMounted) inherit from this.
    Provides common functionality for camera creation and management.
    """
    
    def __init__(self, name_prefix="Camera"):
        """
        Initialize base camera.
        
        Args:
            name_prefix: Prefix for camera names
        """
        self.name_prefix = name_prefix
        self.cameras = []
        
    def create(self, **kwargs):
        """Create the camera(s). Override in subclasses."""
        raise NotImplementedError
        
    def set_active(self, index=0):
        """
        Set a specific camera as the active scene camera.
        
        Args:
            index: Index of camera to activate (0-based)
            
        Returns:
            The activated camera object, or None if index out of range
        """
        if 0 <= index < len(self.cameras):
            bpy.context.scene.camera = self.cameras[index]
            return self.cameras[index]
        return None
    
    def get_cameras(self):
        """Return list of all cameras created by this rig."""
        return self.cameras
    
    def setup_camera_data(self, cam_obj, lens=35, clip_start=0.1, clip_end=1000):
        """
        Configure camera data settings.
        
        Args:
            cam_obj: The camera object to configure
            lens: Focal length in mm (default: 35)
            clip_start: Near clipping distance (default: 0.1)
            clip_end: Far clipping distance (default: 1000)
        """
        cam_obj.data.lens = lens
        cam_obj.data.clip_start = clip_start
        cam_obj.data.clip_end = clip_end
    
    def hide_all(self, hide=True):
        """
        Hide or show all cameras in this rig.
        
        Args:
            hide: True to hide, False to show
        """
        for cam in self.cameras:
            if cam:
                cam.hide_viewport = hide
                cam.hide_render = hide
    
    def delete_all(self):
        """Delete all cameras created by this rig."""
        for cam in self.cameras:
            if cam and cam.name in bpy.data.objects:
                bpy.data.objects.remove(cam, do_unlink=True)
        self.cameras = []
