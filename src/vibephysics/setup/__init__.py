"""
Setup Module

Scene initialization, asset import/export, and viewport management utilities.
This module provides the core setup functionality for Blender scenes.

Modules:
- scene: Scene initialization, frame range, render settings
- importer: Load 3D assets (auto-detects format from extension)
- exporter: Save/export scenes and objects (auto-detects format)
- viewport: Viewport splitting and dual-view management

Usage:
    from vibephysics import setup
    
    # Smart functions (auto-detect format by file extension)
    setup.load_asset('model.glb')      # Loads GLB
    setup.load_asset('mesh.ply')       # Loads PLY
    setup.save_blend('output.blend')   # Saves blend file
    
    # For format-specific control, use submodules directly:
    from vibephysics.setup import importer, exporter
    importer.load_glb('model.glb', transform={'scale': 0.5})
    exporter.export_fbx('output.fbx', selected_only=True)
"""

from . import scene
from . import importer
from . import exporter
from . import viewport

# =============================================================================
# Scene Functions
# =============================================================================
from .scene import (
    # Initialization
    init_simulation,
    clear_scene,
    configure_physics_cache,
    # Frame range
    set_frame_range,
    get_frame_range,
    set_current_frame,
    get_current_frame,
    # Viewport
    setup_dual_viewport,
    reset_viewport,
    # Render settings
    set_render_resolution,
    set_render_engine,
    set_output_path,
)

# =============================================================================
# Smart Import/Export (auto-detect format)
# =============================================================================
from .importer import load_asset, move_to_collection, ensure_collection
from .exporter import save_blend, export_selected, ensure_output_dir, get_output_path

# =============================================================================
# Viewport Functions
# =============================================================================
from .viewport import (
    # Simple dual viewport (scene-level)
    setup_dual_viewport_simple,
    reset_viewport_single,
    # Viewport utilities
    split_viewport_horizontal,
    get_view3d_areas,
    get_space_view3d,
    configure_viewport_shading,
    configure_viewport_overlays,
    lock_viewport_to_camera,
    sync_viewport_views,
    # Local view dual viewport (for annotations)
    setup_dual_viewport as setup_dual_viewport_local,
    enter_local_view,
    register_view_sync_handler,
    register_viewport_restore_handler,
    create_viewport_restore_script,
)

__all__ = [
    # Modules (for format-specific access)
    'scene',
    'importer',
    'exporter',
    'viewport',
    
    # Scene functions
    'init_simulation',
    'clear_scene',
    'configure_physics_cache',
    'set_frame_range',
    'get_frame_range',
    'set_current_frame',
    'get_current_frame',
    'setup_dual_viewport',
    'reset_viewport',
    'set_render_resolution',
    'set_render_engine',
    'set_output_path',
    
    # Smart import/export (auto-detect format)
    'load_asset',
    'move_to_collection',
    'ensure_collection',
    'save_blend',
    'export_selected',
    'ensure_output_dir',
    'get_output_path',
    
    # Viewport functions
    'setup_dual_viewport_simple',
    'reset_viewport_single',
    'split_viewport_horizontal',
    'get_view3d_areas',
    'get_space_view3d',
    'configure_viewport_shading',
    'configure_viewport_overlays',
    'lock_viewport_to_camera',
    'sync_viewport_views',
    'setup_dual_viewport_local',
    'enter_local_view',
    'register_view_sync_handler',
    'register_viewport_restore_handler',
    'create_viewport_restore_script',
]
