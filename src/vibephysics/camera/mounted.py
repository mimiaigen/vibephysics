"""
Object Mounted Camera Rig

Creates N cameras attached to an object, pointing outward (POV cameras).
Cameras are positioned in the parent object's LOCAL coordinate space,
so they correctly follow the object's orientation.
"""

import bpy
import math
from mathutils import Euler, Vector, Matrix
from .base import BaseCamera


class ObjectMountedCameraRig(BaseCamera):
    """
    Creates N cameras attached to an object, pointing outward.
    
    Cameras move and rotate with the parent object, providing
    first-person or surround views from the object's perspective.
    
    IMPORTANT: Cameras are positioned relative to the parent's LOCAL axes:
    - 'front' = parent's local +Y direction
    - 'right' = parent's local +X direction
    - 'back' = parent's local -Y direction
    - 'left' = parent's local -X direction
    
    This means if the parent object is rotated, the cameras will be
    positioned and oriented correctly relative to the object's facing direction.
    
    Default: 4 cameras (front, right, back, left)
    
    Usage:
        from vibephysics.camera import ObjectMountedCameraRig
        
        # 4 cameras on robot looking outward
        rig = ObjectMountedCameraRig(num_cameras=4, distance=2.0)
        cameras = rig.create(parent_object=robot_mesh)
        
        # Custom directions
        rig = ObjectMountedCameraRig(
            num_cameras=4,
            directions=['front', 'right', 'back', 'left']
        )
    """
    
    # Predefined directions with LOCAL rotation (Euler angles in radians)
    # These rotations are applied in the parent's local space
    # Camera -Z axis points in viewing direction, +Y axis points up
    DIRECTION_ROTATIONS = {
        'front':  (math.radians(90), 0, 0),           # Looking forward (+Y local)
        'back':   (math.radians(90), 0, math.pi),     # Looking backward (-Y local)
        'left':   (math.radians(90), 0, math.radians(90)),   # Looking left (-X local)
        'right':  (math.radians(90), 0, math.radians(-90)),  # Looking right (+X local)
        'up':     (0, 0, 0),                           # Looking up (+Z local)
        'down':   (math.pi, 0, 0),                     # Looking down (-Z local)
        'front_left':  (math.radians(90), 0, math.radians(45)),
        'front_right': (math.radians(90), 0, math.radians(-45)),
        'back_left':   (math.radians(90), 0, math.radians(135)),
        'back_right':  (math.radians(90), 0, math.radians(-135)),
    }
    
    # Predefined direction offsets (unit vectors in LOCAL space)
    DIRECTION_OFFSETS = {
        'front':  (0, 1, 0),
        'back':   (0, -1, 0),
        'left':   (-1, 0, 0),
        'right':  (1, 0, 0),
        'up':     (0, 0, 1),
        'down':   (0, 0, -1),
        'front_left':  (-0.707, 0.707, 0),
        'front_right': (0.707, 0.707, 0),
        'back_left':   (-0.707, -0.707, 0),
        'back_right':  (0.707, -0.707, 0),
    }
    
    def __init__(self, num_cameras=4, distance=1.0, height_offset=0.5, 
                 directions=None, name_prefix="MountedCam", forward_axis='+Y',
                 rotation_offset=0.0):
        """
        Initialize object-mounted camera rig.
        
        Args:
            num_cameras: Number of cameras (default: 4, ignored if directions specified)
            distance: Distance from parent object center
            height_offset: Vertical offset from object center
            directions: List of direction names ('front', 'right', etc.) or None for auto
            name_prefix: Prefix for camera names
            forward_axis: Which local axis is "forward" for the parent object.
                         '+Y' (default), '-Y' (Open Duck), '+X', '-X'
            rotation_offset: Additional rotation offset in DEGREES around Z axis.
                            Use this to fine-tune camera orientation if forward_axis
                            doesn't match exactly. Positive = counter-clockwise.
        """
        super().__init__(name_prefix)
        self.num_cameras = num_cameras
        self.distance = distance
        self.height_offset = height_offset
        self.forward_axis = forward_axis
        self.rotation_offset = math.radians(rotation_offset)  # Convert to radians
        
        # Set up directions
        if directions:
            self.directions = directions
            self.num_cameras = len(directions)
        else:
            # Default: evenly distributed around horizontal plane
            if num_cameras == 4:
                self.directions = ['front', 'right', 'back', 'left']
            elif num_cameras == 6:
                self.directions = ['front', 'front_right', 'back_right', 
                                   'back', 'back_left', 'front_left']
            elif num_cameras == 8:
                self.directions = ['front', 'front_right', 'right', 'back_right',
                                   'back', 'back_left', 'left', 'front_left']
            else:
                # Generate evenly spaced directions
                self.directions = [f"angle_{int(i * 360 / num_cameras)}" 
                                   for i in range(num_cameras)]
    
    def _get_forward_axis_rotation(self):
        """
        Get total rotation offset based on forward_axis setting plus user rotation_offset.
        Returns rotation in radians around Z axis.
        """
        # Base rotation for forward axis
        # These values rotate the camera directions so 'front' faces the robot's forward
        axis_rotations = {
            '+Y': 0,                    # Default, no rotation needed
            '-Y': -math.pi / 2,         # -90° rotation (Open Duck faces -Y)
            '+X': math.pi,              # 180° rotation
            '-X': 0,                    # No rotation
        }
        base_rot = axis_rotations.get(self.forward_axis, 0)
        # Add user-specified rotation offset
        return base_rot + self.rotation_offset
    
    def create(self, parent_object, lens=35, use_parent=True):
        """
        Create the mounted camera rig.
        
        Cameras are positioned in the parent object's LOCAL coordinate space.
        The 'front' direction is determined by the forward_axis parameter.
        
        Args:
            parent_object: Object to attach cameras to (mesh, armature, or empty)
            lens: Camera lens focal length
            use_parent: If True, parent cameras to object; if False, use constraints
            
        Returns:
            List of created camera objects
        """
        self.cameras = []
        self.parent_object = parent_object
        
        # Get parent's world matrix for transforming local positions to world
        parent_matrix = parent_object.matrix_world
        
        # Get rotation offset for forward axis
        axis_rot = self._get_forward_axis_rotation()
        axis_rot_matrix = Euler((0, 0, axis_rot)).to_matrix()
        
        for i, direction in enumerate(self.directions):
            # Calculate offset based on direction (in LOCAL space)
            if direction in self.DIRECTION_OFFSETS:
                local_offset = Vector(self.DIRECTION_OFFSETS[direction])
            else:
                # Parse angle from direction name (e.g., "angle_45")
                try:
                    angle = float(direction.split('_')[1])
                    angle_rad = math.radians(angle)
                    local_offset = Vector((math.cos(angle_rad), math.sin(angle_rad), 0))
                except:
                    local_offset = Vector((0, 1, 0))  # Default to front
            
            # Apply forward axis rotation to offset
            local_offset = axis_rot_matrix @ local_offset
            
            # Calculate camera LOCAL position (relative to parent)
            local_pos = Vector((
                local_offset.x * self.distance,
                local_offset.y * self.distance,
                local_offset.z * self.distance + self.height_offset
            ))
            
            # Get LOCAL rotation for this direction
            if direction in self.DIRECTION_ROTATIONS:
                base_rotation = Euler(self.DIRECTION_ROTATIONS[direction])
            else:
                # Calculate rotation for custom angle
                try:
                    angle = float(direction.split('_')[1])
                    angle_rad = math.radians(angle)
                    base_rotation = Euler((math.radians(90), 0, angle_rad))
                except:
                    base_rotation = Euler((math.radians(90), 0, 0))
            
            # Apply forward axis rotation to camera rotation
            # Add axis_rot to Z component of rotation
            local_rotation = Euler((base_rotation.x, base_rotation.y, base_rotation.z + axis_rot))
            
            # Transform local position to world position for initial camera creation
            world_pos = parent_matrix @ local_pos
            
            # Transform local rotation to world rotation
            # Combine parent's rotation with camera's local rotation
            local_rot_matrix = local_rotation.to_matrix().to_4x4()
            world_rot_matrix = parent_matrix.to_3x3().to_4x4() @ local_rot_matrix
            world_rotation = world_rot_matrix.to_euler()
            
            # Create camera at world position with world rotation
            bpy.ops.object.camera_add(location=world_pos)
            cam = bpy.context.active_object
            cam.name = f"{self.name_prefix}_{direction}"
            cam.rotation_euler = world_rotation
            
            self.setup_camera_data(cam, lens=lens)
            
            # Ensure camera is visible and selectable
            cam.hide_viewport = False
            cam.hide_render = False
            cam.hide_select = False
            
            if use_parent:
                # Parent camera to object
                # After parenting, the camera's local transform will be relative to parent
                cam.parent = parent_object
                
                # Set matrix_parent_inverse to identity so camera uses local coordinates
                # This makes the camera's location/rotation be local to the parent
                cam.matrix_parent_inverse = Matrix.Identity(4)
                
                # Now set the camera's local position and rotation
                cam.location = local_pos
                cam.rotation_euler = local_rotation
                
                # Compensate for parent's scale to keep camera at normal size
                # Get the parent's world scale and set camera scale to inverse
                parent_scale = parent_object.matrix_world.to_scale()
                if parent_scale.x != 0 and parent_scale.y != 0 and parent_scale.z != 0:
                    cam.scale = (1.0 / parent_scale.x, 1.0 / parent_scale.y, 1.0 / parent_scale.z)
            else:
                # Use constraints instead
                # Copy location with offset
                loc_constraint = cam.constraints.new(type='COPY_LOCATION')
                loc_constraint.target = parent_object
                loc_constraint.use_offset = True
                
                # Copy rotation and add local rotation
                rot_constraint = cam.constraints.new(type='COPY_ROTATION')
                rot_constraint.target = parent_object
                rot_constraint.mix_mode = 'ADD'
            
            self.cameras.append(cam)
        
        # Set first camera as active
        if self.cameras:
            bpy.context.scene.camera = self.cameras[0]
            
        return self.cameras
    
    def cycle_camera(self):
        """Cycle to the next camera in the rig."""
        if not self.cameras:
            return None
            
        current = bpy.context.scene.camera
        if current in self.cameras:
            idx = (self.cameras.index(current) + 1) % len(self.cameras)
        else:
            idx = 0
            
        bpy.context.scene.camera = self.cameras[idx]
        return self.cameras[idx]


def create_mounted_cameras(parent, num_cameras=4, distance=1.0, directions=None):
    """
    Quick function to create object-mounted cameras.
    
    Args:
        parent: Object to attach cameras to
        num_cameras: Number of cameras (ignored if directions specified)
        distance: Distance from parent center
        directions: List of direction names
        
    Returns:
        List of camera objects
    """
    rig = ObjectMountedCameraRig(num_cameras=num_cameras, distance=distance, directions=directions)
    return rig.create(parent_object=parent)
