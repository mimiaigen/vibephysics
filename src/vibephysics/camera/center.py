"""
Center Pointing Camera Rig

Creates N cameras arranged in a circle, all pointing at a center target.
"""

import bpy
import math
from .base import BaseCamera


class CenterPointingCameraRig(BaseCamera):
    """
    Creates N cameras arranged in a circle, all pointing at a center target.
    
    Default: 4 cameras evenly distributed around a circle at 0°, 90°, 180°, 270°.
    Default active camera is Camera_3_Angle_270 (viewing from -Y direction).
    
    Usage:
        from vibephysics.camera import CenterPointingCameraRig
        
        rig = CenterPointingCameraRig(num_cameras=4, radius=15, height=8)
        cameras = rig.create(target_object=water_surface)
        rig.set_active(3)  # Set camera at 270° as active (default)
    """
    
    def __init__(self, num_cameras=4, radius=15.0, height=8.0, name_prefix="Camera", 
                 default_angle=270):
        """
        Initialize center-pointing camera rig.
        
        Args:
            num_cameras: Number of cameras to create (default: 4)
            radius: Distance from center (default: 15)
            height: Height above ground (default: 8)
            name_prefix: Prefix for camera names
            default_angle: Angle of the default active camera in degrees (default: 270)
        """
        super().__init__(name_prefix)
        self.num_cameras = num_cameras
        self.radius = radius
        self.height = height
        self.default_angle = default_angle
        
    def create(self, target_object=None, target_location=None, lens=35):
        """
        Create the camera rig.
        
        Args:
            target_object: Object for cameras to track (uses TRACK_TO constraint)
            target_location: Fallback location if no target object (creates empty)
            lens: Camera lens focal length (mm)
            
        Returns:
            List of created camera objects
        """
        self.cameras = []
        
        # Determine target
        target = target_object
        if target is None:
            # Create an empty target at specified location or origin
            loc = target_location if target_location else (0, 0, 0)
            if not bpy.data.objects.get("Camera_Target_Center"):
                bpy.ops.object.empty_add(type='PLAIN_AXES', location=loc)
                target = bpy.context.active_object
                target.name = "Camera_Target_Center"
                target.empty_display_size = 0.5
                target.hide_render = True
            else:
                target = bpy.data.objects.get("Camera_Target_Center")
        
        # Create cameras
        for i in range(self.num_cameras):
            angle_deg = i * (360.0 / self.num_cameras)
            angle_rad = math.radians(angle_deg)
            
            # Calculate position on circle
            cam_x = self.radius * math.cos(angle_rad)
            cam_y = self.radius * math.sin(angle_rad)
            cam_z = self.height
            
            bpy.ops.object.camera_add(location=(cam_x, cam_y, cam_z))
            cam = bpy.context.active_object
            cam.name = f"{self.name_prefix}_{i}_Angle_{int(angle_deg)}"
            
            # Configure camera
            self.setup_camera_data(cam, lens=lens)
            
            # Add tracking constraint
            constraint = cam.constraints.new(type='TRACK_TO')
            constraint.target = target
            constraint.track_axis = 'TRACK_NEGATIVE_Z'
            constraint.up_axis = 'UP_Y'
            
            self.cameras.append(cam)
        
        # Set default camera based on default_angle
        if self.cameras:
            # Find camera closest to default_angle
            default_index = 0
            for i in range(self.num_cameras):
                angle = i * (360.0 / self.num_cameras)
                if abs(angle - self.default_angle) < 0.1:  # Close enough match
                    default_index = i
                    break
            bpy.context.scene.camera = self.cameras[default_index]
            
        return self.cameras
    
    def set_active_by_angle(self, angle):
        """
        Set the active camera by its angle.
        
        Args:
            angle: Angle in degrees (0, 90, 180, 270, etc.)
            
        Returns:
            The activated camera or None if not found
        """
        for i, cam in enumerate(self.cameras):
            cam_angle = i * (360.0 / self.num_cameras)
            if abs(cam_angle - angle) < 0.1:
                bpy.context.scene.camera = cam
                return cam
        return None


def create_center_cameras(num_cameras=4, radius=15.0, height=8.0, target=None):
    """
    Quick function to create center-pointing cameras.
    
    Args:
        num_cameras: Number of cameras
        radius: Distance from center
        height: Height above ground
        target: Target object (or None for origin)
        
    Returns:
        List of camera objects
    """
    rig = CenterPointingCameraRig(num_cameras=num_cameras, radius=radius, height=height)
    return rig.create(target_object=target)
