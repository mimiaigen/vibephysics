"""
Annotation Utilities

Point tracking, bounding boxes, motion trails, and visualization tools 
for annotating Blender simulations.

Unified API:
    from annotation import manager
    mgr = manager.AnnotationManager()
    mgr.add_bbox(cube)
    mgr.add_motion_trail(cube)
    mgr.add_point_tracking([cube, sphere])
    mgr.finalize()

Or use the quick API:
    from annotation import manager
    manager.quick_annotate([cube, sphere], bbox=True, trail=True)

Individual modules:
    from annotation import bbox, motion_trail, point_tracking, viewport
"""

# Base utilities (for extension)
from .base import (
    DEFAULT_COLLECTION_NAME,
    ensure_collection,
    create_emission_material,
    create_vertex_color_material,
    register_frame_handler,
    unregister_frame_handler,
    create_embedded_script,
    get_object_world_bounds,
    get_evaluated_object,
    get_depsgraph,
    BaseAnnotation,
    AnnotationType,
    create_annotation,
    # Tracking configuration
    TrackingTarget,
    TrackingConfig,
)

# Individual annotation modules
from .point_tracking import (
    setup_point_tracking_visualization,
    create_point_cloud_tracker,
    register_frame_handler as register_point_tracking_handler,
    create_embedded_tracking_script,
    sample_mesh_surface_points,
    generate_distinct_colors,
)

from .bbox import (
    create_bbox_annotation,
    update_bbox,
    update_all_bboxes,
    register as register_bbox,
    create_embedded_bbox_script,
)

from .motion_trail import (
    create_motion_trail,
    create_motion_trails,
)

from .viewport import (
    setup_dual_viewport,
    split_viewport_horizontal,
    configure_viewport_shading,
    configure_viewport_overlays,
    enter_local_view,
    register_viewport_restore_handler,
    create_viewport_restore_script,
)

# Manager (unified API)
from .manager import (
    AnnotationManager,
    get_manager,
    reset_manager,
    quick_annotate,
)

__all__ = [
    # Constants
    'DEFAULT_COLLECTION_NAME',
    
    # Base utilities
    'ensure_collection',
    'create_emission_material',
    'create_vertex_color_material',
    'register_frame_handler',
    'unregister_frame_handler',
    'create_embedded_script',
    'get_object_world_bounds',
    'get_evaluated_object',
    'get_depsgraph',
    'BaseAnnotation',
    'AnnotationType',
    'create_annotation',
    
    # Tracking configuration
    'TrackingTarget',
    'TrackingConfig',
    
    # BBox
    'create_bbox_annotation',
    'update_bbox',
    'update_all_bboxes',
    'register_bbox',
    'create_embedded_bbox_script',
    
    # Motion Trail
    'create_motion_trail',
    'create_motion_trails',
    
    # Point Tracking
    'setup_point_tracking_visualization',
    'create_point_cloud_tracker',
    'register_point_tracking_handler',
    'create_embedded_tracking_script',
    'sample_mesh_surface_points',
    'generate_distinct_colors',
    
    # Viewport
    'setup_dual_viewport',
    'split_viewport_horizontal',
    'configure_viewport_shading',
    'configure_viewport_overlays',
    'enter_local_view',
    'register_viewport_restore_handler',
    'create_viewport_restore_script',
    
    # Manager (unified API)
    'AnnotationManager',
    'get_manager',
    'reset_manager',
    'quick_annotate',
]
