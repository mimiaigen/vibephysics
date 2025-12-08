"""
Annotation Utilities

Point tracking, bounding boxes, motion trails, and visualization tools 
for annotating Blender simulations.

Unified API:
    from vibephysics.annotation import AnnotationManager
    mgr = AnnotationManager()
    mgr.add_bbox(cube)
    mgr.add_motion_trail(cube)
    mgr.add_point_tracking([cube, sphere])
    mgr.finalize()

Or use the quick API:
    from vibephysics.annotation import quick_annotate
    quick_annotate([cube, sphere], bbox=True, trail=True)

Individual modules:
    from vibephysics.annotation import bbox, motion_trail, point_tracking

Viewport utilities (now in setup module):
    from vibephysics.setup import viewport
    from vibephysics.annotation import viewport  # backward compatible alias

Camera systems:
    from vibephysics.camera import CameraManager, CenterPointingCameraRig
"""

# =============================================================================
# Base utilities
# =============================================================================
from .base import (
    DEFAULT_COLLECTION_NAME,
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
    TrackingTarget,
    TrackingConfig,
)

# Collection utilities (from setup module)
from ..setup.importer import ensure_collection
from ..setup.viewport import find_layer_collection

# =============================================================================
# Annotation modules
# =============================================================================
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

from .point_tracking import (
    setup_point_tracking_visualization,
    create_point_cloud_tracker,
    register_frame_handler as register_point_tracking_handler,
    create_embedded_tracking_script,
    sample_mesh_surface_points,
    generate_distinct_colors,
)

# =============================================================================
# Manager (unified API)
# =============================================================================
from .manager import (
    AnnotationManager,
    get_manager,
    reset_manager,
    quick_annotate,
)

# =============================================================================
# Viewport (re-exported from setup for backward compatibility)
# =============================================================================
from ..setup import viewport
from ..setup.viewport import (
    setup_dual_viewport_simple,
    reset_viewport_single,
    setup_dual_viewport,
    create_viewport_restore_script,
    register_viewport_restore_handler,
)

__all__ = [
    # Constants
    'DEFAULT_COLLECTION_NAME',
    
    # Collection utilities (from setup)
    'ensure_collection',
    'find_layer_collection',
    
    # Base utilities
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
    
    # Manager (unified API)
    'AnnotationManager',
    'get_manager',
    'reset_manager',
    'quick_annotate',
    
    # Viewport (from setup module)
    'viewport',
    'setup_dual_viewport_simple',
    'reset_viewport_single',
    'setup_dual_viewport',
    'create_viewport_restore_script',
    'register_viewport_restore_handler',
]
