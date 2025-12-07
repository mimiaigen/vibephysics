"""
Following Camera Module

Creates a camera that follows a target object from above (bird's eye view).
"""

import bpy
import math
from .base import BaseCamera


class FollowingCamera(BaseCamera):
    """
    Creates a camera that follows a target object from above (bird's eye view).
    
    The camera maintains a fixed height above the target and looks down at it.
    Can be configured to follow with an offset or track at an angle.
    
    Usage:
        from vibephysics.camera import FollowingCamera
        
        cam = FollowingCamera(height=12, offset=(0, -5, 0))
        cam.create(target=robot_armature)
    """
    
    def __init__(self, height=10.0, offset=(0, 0, 0), look_angle=45, name="FollowCamera"):
        """
        Initialize following camera.
        
        Args:
            height: Height above target (default: 10)
            offset: (x, y, z) offset from target position
            look_angle: Angle from vertical in degrees (0=straight down, 90=horizontal)
            name: Camera name
        """
        super().__init__(name)
        self.height = height
        self.offset = offset
        self.look_angle = look_angle
        
    def create(self, target, use_constraint=True, lens=35):
        """
        Create the following camera.
        
        Args:
            target: Object to follow (typically armature or mesh)
            use_constraint: If True, uses TRACK_TO constraint; if False, parents camera
            lens: Camera lens focal length
            
        Returns:
            The camera object
        """
        # Calculate initial position
        target_loc = target.location
        cam_loc = (
            target_loc.x + self.offset[0],
            target_loc.y + self.offset[1] - self.height * math.tan(math.radians(90 - self.look_angle)),
            target_loc.z + self.offset[2] + self.height
        )
        
        bpy.ops.object.camera_add(location=cam_loc)
        cam = bpy.context.active_object
        cam.name = self.name_prefix
        
        self.setup_camera_data(cam, lens=lens)
        
        if use_constraint:
            # Use TRACK_TO constraint for smooth following
            constraint = cam.constraints.new(type='TRACK_TO')
            constraint.target = target
            constraint.track_axis = 'TRACK_NEGATIVE_Z'
            constraint.up_axis = 'UP_Y'
            
            # Add COPY_LOCATION for following (with offset)
            loc_constraint = cam.constraints.new(type='COPY_LOCATION')
            loc_constraint.target = target
            loc_constraint.use_offset = True
        else:
            # Parent directly (simpler but less flexible)
            cam.parent = target
            cam.matrix_parent_inverse = target.matrix_world.inverted()
            
            # Set rotation to look at target
            cam.rotation_euler = (math.radians(self.look_angle), 0, 0)
        
        self.cameras = [cam]
        bpy.context.scene.camera = cam
        
        return cam


def create_following_camera(target, height=10.0, look_angle=45):
    """
    Quick function to create a following camera.
    
    Args:
        target: Object to follow
        height: Height above target
        look_angle: Angle from vertical
        
    Returns:
        Camera object
    """
    cam = FollowingCamera(height=height, look_angle=look_angle)
    return cam.create(target=target)
