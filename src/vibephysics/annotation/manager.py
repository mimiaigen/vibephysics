"""
Annotation Manager Module

Provides a unified interface to manage all annotation types.
Handles registration, updates, and persistence of annotations.
"""

import bpy
from . import base
from . import bbox as bbox_module
from . import motion_trail as trail_module
from . import point_tracking as tracking_module
from . import viewport as viewport_module


class AnnotationManager:
    """
    Central manager for all annotation types.
    
    This class provides a unified API to:
    - Create annotations of any type
    - Register frame handlers for animated annotations
    - Create embedded scripts for persistence
    - Manage annotation collections and viewport setup
    
    Usage:
        manager = AnnotationManager()
        manager.add_bbox(cube, color=(1, 0, 0, 1))
        manager.add_motion_trail(cube)
        manager.add_point_tracking([sphere, cube])
        manager.finalize()  # Registers handlers and creates scripts
    """
    
    def __init__(self, collection_name=None):
        """
        Initialize the annotation manager.
        
        Args:
            collection_name: Name of collection for all annotations
        """
        self.collection_name = collection_name or base.DEFAULT_COLLECTION_NAME
        self.collection = base.ensure_collection(self.collection_name)
        
        # Track created annotations
        self.bboxes = []
        self.trails = []
        self.point_clouds = []
        
        # Track which handlers are registered
        self._handlers_registered = set()
        
    # =========================================================================
    # Bounding Box Annotations
    # =========================================================================
    
    def add_bbox(self, target_obj, color=(1.0, 0.6, 0.0, 1.0), thickness=2.0):
        """
        Add a bounding box annotation to an object.
        
        Args:
            target_obj: Object to annotate
            color: RGBA color tuple
            thickness: Line thickness
            
        Returns:
            The bbox visualization object
        """
        bbox_obj = bbox_module.create_bbox_annotation(
            target_obj, 
            color=color, 
            thickness=thickness
        )
        if bbox_obj:
            self.bboxes.append(bbox_obj)
        return bbox_obj
    
    def add_bboxes(self, objects, colors=None, thickness=2.0):
        """
        Add bounding box annotations to multiple objects.
        
        Args:
            objects: List of objects to annotate
            colors: List of RGBA colors (or single color for all, or None for auto)
            thickness: Line thickness
            
        Returns:
            List of bbox visualization objects
        """
        if colors is None:
            # Auto-generate distinct colors
            from mathutils import Color
            colors = []
            for i, _ in enumerate(objects):
                c = Color()
                c.hsv = ((i * 0.618033988749895) % 1.0, 0.8, 0.9)
                colors.append((c.r, c.g, c.b, 1.0))
        elif not isinstance(colors, list):
            colors = [colors] * len(objects)
            
        results = []
        for obj, color in zip(objects, colors):
            bbox = self.add_bbox(obj, color=color, thickness=thickness)
            results.append(bbox)
        return results
    
    # =========================================================================
    # Motion Trail Annotations
    # =========================================================================
    
    def add_motion_trail(self, target_obj, start_frame=None, end_frame=None, 
                         step=1, color=(0.0, 0.8, 1.0, 1.0)):
        """
        Add a motion trail annotation to an object.
        
        Args:
            target_obj: Object to track
            start_frame: Start frame (None = scene start)
            end_frame: End frame (None = scene end)
            step: Frame step for sampling
            color: RGBA color for the trail
            
        Returns:
            The trail curve object
        """
        trail_obj = trail_module.create_motion_trail(
            target_obj,
            start_frame=start_frame,
            end_frame=end_frame,
            step=step,
            color=color,
            collection_name=self.collection_name
        )
        if trail_obj:
            self.trails.append(trail_obj)
        return trail_obj
    
    def add_motion_trails(self, objects, start_frame=None, end_frame=None, 
                          step=1, colors=None):
        """
        Add motion trail annotations to multiple objects.
        
        Args:
            objects: List of objects to track
            start_frame: Start frame (None = scene start)
            end_frame: End frame (None = scene end)
            step: Frame step for sampling
            colors: List of RGBA colors (or None for auto)
            
        Returns:
            List of trail curve objects
        """
        if colors is None:
            from mathutils import Color
            colors = []
            for i, _ in enumerate(objects):
                c = Color()
                c.hsv = ((i * 0.618033988749895 + 0.5) % 1.0, 0.7, 0.95)
                colors.append((c.r, c.g, c.b, 1.0))
        elif not isinstance(colors, list):
            colors = [colors] * len(objects)
            
        results = []
        for obj, color in zip(objects, colors):
            trail = self.add_motion_trail(
                obj, 
                start_frame=start_frame, 
                end_frame=end_frame, 
                step=step, 
                color=color
            )
            results.append(trail)
        return results
    
    # =========================================================================
    # Point Tracking Annotations
    # =========================================================================
    
    def add_point_tracking(self, tracked_objects, points_per_object=30, 
                           point_size=0.05, setup_viewport=False):
        """
        Add point tracking visualization to objects.
        
        Args:
            tracked_objects: List of objects to track
            points_per_object: Number of surface sample points per object
            point_size: Size of each tracking point
            setup_viewport: Whether to create dual viewport setup
            
        Returns:
            The point cloud tracker object
        """
        point_cloud = tracking_module.setup_point_tracking_visualization(
            tracked_objects,
            points_per_object=points_per_object,
            setup_viewport=setup_viewport,
            collection_name=self.collection_name
        )
        if point_cloud:
            self.point_clouds.append(point_cloud)
        return point_cloud
    
    # =========================================================================
    # Quick Setup Methods
    # =========================================================================
    
    def annotate_all(self, objects, bbox=True, trail=True, point_tracking=True,
                     bbox_colors=None, trail_colors=None, points_per_object=30):
        """
        Apply all annotation types to a list of objects.
        
        Args:
            objects: List of objects to annotate
            bbox: Whether to add bounding boxes
            trail: Whether to add motion trails
            point_tracking: Whether to add point tracking
            bbox_colors: Colors for bboxes (auto if None)
            trail_colors: Colors for trails (auto if None)
            points_per_object: Points per object for tracking
            
        Returns:
            Dict with 'bboxes', 'trails', 'point_cloud' keys
        """
        results = {
            'bboxes': [],
            'trails': [],
            'point_cloud': None
        }
        
        if bbox:
            results['bboxes'] = self.add_bboxes(objects, colors=bbox_colors)
            
        if trail:
            results['trails'] = self.add_motion_trails(objects, colors=trail_colors)
            
        if point_tracking:
            results['point_cloud'] = self.add_point_tracking(
                objects, 
                points_per_object=points_per_object
            )
            
        return results
    
    def annotate_with_config(self, all_objects, center_object=None, config=None,
                             start_frame=None, end_frame=None, trail_step=2,
                             points_per_object=30, bbox_colors=None, trail_colors=None):
        """
        Apply annotations using a TrackingConfig for fine-grained control.
        
        This method gives you control over what objects to track for each
        annotation type (bbox, trail, point tracking).
        
        Args:
            all_objects: List of all objects that could be tracked
            center_object: The main/center object (e.g., armature for robots)
            config: TrackingConfig instance (defaults to robot_default)
            start_frame: Start frame for trails (None = scene start)
            end_frame: End frame for trails (None = scene end)
            trail_step: Frame step for trail sampling
            points_per_object: Points per object for tracking
            bbox_colors: Colors for bboxes (auto if None)
            trail_colors: Colors for trails (auto if None)
            
        Returns:
            Dict with 'bboxes', 'trails', 'point_cloud' keys
            
        Example:
            from annotation import AnnotationManager, TrackingConfig, TrackingTarget
            
            mgr = AnnotationManager()
            
            # Track bbox for all, trail for center only, points for all
            config = TrackingConfig(
                bbox=TrackingTarget.ALL,
                trail=TrackingTarget.CENTER,
                points=TrackingTarget.ALL
            )
            
            mgr.annotate_with_config(
                all_objects=robot_parts + debris,
                center_object=armature,
                config=config
            )
        """
        # Default to robot-friendly config
        if config is None:
            config = base.TrackingConfig.robot_default()
        
        results = {
            'bboxes': [],
            'trails': [],
            'point_cloud': None
        }
        
        # Get objects for each annotation type
        bbox_objects = config.get_bbox_objects(all_objects, center_object)
        trail_objects = config.get_trail_objects(all_objects, center_object)
        points_objects = config.get_points_objects(all_objects, center_object)
        
        # Apply bounding boxes
        if bbox_objects:
            results['bboxes'] = self.add_bboxes(bbox_objects, colors=bbox_colors)
        
        # Apply motion trails
        if trail_objects:
            results['trails'] = self.add_motion_trails(
                trail_objects,
                start_frame=start_frame,
                end_frame=end_frame,
                step=trail_step,
                colors=trail_colors
            )
        
        # Apply point tracking
        if points_objects:
            # Filter to mesh objects only
            mesh_objects = [obj for obj in points_objects if obj.type == 'MESH']
            if mesh_objects:
                results['point_cloud'] = self.add_point_tracking(
                    mesh_objects,
                    points_per_object=points_per_object
                )
        
        return results
    
    def annotate_robot(self, robot_parts, center_object, debris_objects=None,
                       bbox_robot=True, bbox_debris=True,
                       trail_center=True, trail_debris=False,
                       point_tracking=True,
                       start_frame=None, end_frame=None, trail_step=2,
                       points_per_object=30):
        """
        Convenience method for annotating robot simulations.
        
        Provides explicit control over what to track for robots vs debris.
        
        Args:
            robot_parts: List of robot mesh parts
            center_object: Robot center/armature for trail tracking
            debris_objects: Optional list of debris/environment objects
            bbox_robot: Add bbox to robot parts
            bbox_debris: Add bbox to debris objects
            trail_center: Add trail to center object
            trail_debris: Add trails to debris objects
            point_tracking: Add point tracking to all objects
            start_frame: Start frame for trails
            end_frame: End frame for trails
            trail_step: Frame step for trail sampling
            points_per_object: Points per object for tracking
            
        Returns:
            Dict with 'bboxes', 'trails', 'point_cloud' keys
        """
        from mathutils import Color
        
        debris_objects = debris_objects or []
        
        results = {
            'bboxes': [],
            'trails': [],
            'point_cloud': None
        }
        
        # Bounding boxes
        if bbox_robot and robot_parts:
            print(f"  - Adding {len(robot_parts)} robot bboxes...")
            # Warm colors for robot (orange to yellow)
            robot_colors = []
            for i in range(len(robot_parts)):
                hue = 0.05 + (i / max(len(robot_parts), 1)) * 0.15
                c = Color()
                c.hsv = (hue, 0.9, 0.95)
                robot_colors.append((c.r, c.g, c.b, 1.0))
            results['bboxes'].extend(self.add_bboxes(robot_parts, colors=robot_colors))
        
        if bbox_debris and debris_objects:
            print(f"  - Adding {len(debris_objects)} debris bboxes...")
            # Cool colors for debris (cyan to blue)
            debris_colors = []
            for i in range(len(debris_objects)):
                hue = 0.5 + (i / max(len(debris_objects), 1)) * 0.2
                c = Color()
                c.hsv = (hue, 0.7, 0.9)
                debris_colors.append((c.r, c.g, c.b, 1.0))
            results['bboxes'].extend(self.add_bboxes(debris_objects, colors=debris_colors))
        
        # Motion trails
        if trail_center and center_object:
            print(f"  - Adding center trail...")
            trail = self.add_motion_trail(
                center_object,
                start_frame=start_frame,
                end_frame=end_frame,
                step=trail_step,
                color=(1.0, 0.8, 0.2, 1.0)  # Golden yellow
            )
            if trail:
                results['trails'].append(trail)
        
        if trail_debris and debris_objects:
            print(f"  - Adding {len(debris_objects)} debris trails...")
            debris_trails = self.add_motion_trails(
                debris_objects,
                start_frame=start_frame,
                end_frame=end_frame,
                step=trail_step
            )
            results['trails'].extend(debris_trails)
        
        # Point tracking
        if point_tracking:
            all_mesh_objects = []
            if robot_parts:
                all_mesh_objects.extend([p for p in robot_parts if p.type == 'MESH'])
            if debris_objects:
                all_mesh_objects.extend([d for d in debris_objects if d.type == 'MESH'])
            
            if all_mesh_objects:
                print(f"  - Adding point tracking for {len(all_mesh_objects)} objects...")
                pts_per = max(5, points_per_object // len(all_mesh_objects))
                results['point_cloud'] = self.add_point_tracking(
                    all_mesh_objects,
                    points_per_object=pts_per
                )
        
        return results
    
    # =========================================================================
    # Handler & Script Registration
    # =========================================================================
    
    def register_handlers(self):
        """Register all necessary frame change handlers."""
        if self.bboxes and 'bbox' not in self._handlers_registered:
            bbox_module.register()
            self._handlers_registered.add('bbox')
            
        # Point tracking handlers are registered automatically in setup_point_tracking_visualization
        # but we track it here for consistency
        if self.point_clouds:
            self._handlers_registered.add('point_tracking')
            
        # Motion trails don't need handlers (they're baked)
        
    def create_embedded_scripts(self):
        """Create all embedded scripts for persistence."""
        if self.bboxes:
            bbox_module.create_embedded_bbox_script()
            
        if self.point_clouds:
            tracking_module.create_embedded_tracking_script()
            
        # Create viewport restore script
        viewport_module.create_viewport_restore_script(self.collection_name)
        
    def setup_viewport(self, dual_viewport=True):
        """
        Setup viewport configuration.
        
        Args:
            dual_viewport: Whether to create dual viewport (annotation vs scene)
        """
        if dual_viewport and not bpy.app.background:
            annotation_objects = list(self.collection.objects)
            viewport_module.setup_dual_viewport(annotation_objects, self.collection_name)
            viewport_module.register_viewport_restore_handler(self.collection_name)
    
    def finalize(self, register_handlers=True, create_scripts=True, 
                 setup_viewport=False, sync_frame=True):
        """
        Finalize annotation setup.
        
        Call this after adding all annotations to register handlers
        and create persistence scripts.
        
        Args:
            register_handlers: Whether to register frame handlers
            create_scripts: Whether to create embedded scripts
            setup_viewport: Whether to setup dual viewport
            sync_frame: Whether to sync annotations to frame 1 before saving
        """
        if register_handlers:
            self.register_handlers()
            
        if create_scripts:
            self.create_embedded_scripts()
            
        if setup_viewport:
            self.setup_viewport()
        
        # Sync to frame 1 so annotations match when file is opened
        if sync_frame:
            self.sync_to_frame(bpy.context.scene.frame_start)
            
        print(f"✅ Annotation Manager finalized:")
        print(f"   - {len(self.bboxes)} bounding boxes")
        print(f"   - {len(self.trails)} motion trails")
        print(f"   - {len(self.point_clouds)} point clouds")
    
    def sync_to_frame(self, frame=1):
        """
        Sync all annotations to a specific frame.
        
        This ensures bboxes and point clouds match their targets
        at the specified frame. Call before saving to ensure
        correct initial state when file is reopened.
        
        Args:
            frame: Frame number to sync to
        """
        scene = bpy.context.scene
        
        # Set frame
        scene.frame_set(frame)
        
        # Force depsgraph update
        depsgraph = bpy.context.evaluated_depsgraph_get()
        
        # Update all bboxes
        for bbox_obj in self.bboxes:
            if bbox_obj:
                bbox_module.update_bbox(bbox_obj, depsgraph)
        
        # Update point clouds
        for pc_obj in self.point_clouds:
            if pc_obj:
                tracking_module.update_point_cloud_positions(pc_obj, scene)
        
    # =========================================================================
    # Utilities
    # =========================================================================
    
    def get_all_annotation_objects(self):
        """Get all annotation visualization objects."""
        return self.bboxes + self.trails + self.point_clouds
    
    def clear(self):
        """Remove all annotations created by this manager."""
        for obj in self.get_all_annotation_objects():
            if obj and obj.name in bpy.data.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
                
        self.bboxes.clear()
        self.trails.clear()
        self.point_clouds.clear()
        
    def hide_annotations(self, hide=True):
        """Show or hide all annotation objects."""
        for obj in self.get_all_annotation_objects():
            if obj:
                obj.hide_viewport = hide
                obj.hide_render = hide
                
    def set_collection_visibility(self, viewport=True, render=False):
        """
        Set visibility for the annotation collection.
        
        Args:
            viewport: Visible in viewport
            render: Visible in render
        """
        if self.collection:
            # Find layer collection
            layer_coll = base.find_layer_collection(
                bpy.context.view_layer.layer_collection,
                self.collection_name
            )
            if layer_coll:
                layer_coll.exclude = not viewport
            self.collection.hide_render = not render


# =============================================================================
# Convenience Functions
# =============================================================================

_default_manager = None

def get_manager(collection_name=None):
    """
    Get or create the default annotation manager.
    
    Args:
        collection_name: Collection name (only used if creating new manager)
        
    Returns:
        AnnotationManager instance
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = AnnotationManager(collection_name)
    return _default_manager


def reset_manager():
    """Reset the default manager (for new scenes)."""
    global _default_manager
    _default_manager = None


def quick_annotate(objects, bbox=True, trail=True, point_tracking=False, 
                   collection_name=None, finalize=True):
    """
    Quick function to annotate objects with minimal code.
    
    Args:
        objects: Object or list of objects to annotate
        bbox: Add bounding boxes
        trail: Add motion trails
        point_tracking: Add point tracking
        collection_name: Collection for annotations
        finalize: Whether to finalize (register handlers/scripts)
        
    Returns:
        The AnnotationManager instance
        
    Example:
        from annotation import manager
        manager.quick_annotate([cube, sphere], bbox=True, trail=True)
    """
    if not isinstance(objects, (list, tuple)):
        objects = [objects]
        
    mgr = AnnotationManager(collection_name)
    mgr.annotate_all(
        objects, 
        bbox=bbox, 
        trail=trail, 
        point_tracking=point_tracking
    )
    
    if finalize:
        mgr.finalize()
        
    return mgr
