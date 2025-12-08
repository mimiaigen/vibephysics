"""
Setup Module

Scene initialization, asset import/export, and viewport management utilities.
This module provides the core setup functionality for Blender scenes.

Modules:
- scene: Scene initialization, frame range, render settings
- importer: Load 3D assets (auto-detects format from extension)
- exporter: Save/export scenes and objects (auto-detects format)
- viewport: Viewport splitting and dual-view management
- gsplat: Gaussian Splatting (3DGS/4DGS) support

Usage:
    from vibephysics import setup
    
    # Smart functions (auto-detect format by file extension)
    setup.load_asset('model.glb')      # Loads GLB
    setup.load_asset('mesh.ply')       # Loads PLY
    setup.save_blend('output.blend')   # Saves blend file
    
    # Gaussian Splatting
    setup.load_gsplat('scene.ply')     # Single 3DGS
    setup.load_gsplat('frames/')       # 4DGS sequence (animated)
    
    # For format-specific control, use submodules directly:
    from vibephysics.setup import importer, exporter, gsplat
    importer.load_glb('model.glb', transform={'scale': 0.5})
    exporter.export_fbx('output.fbx', selected_only=True)
    gsplat.load_4dgs_sequence('frames/', prefix='frame_')
"""

from . import scene
from . import importer
from . import exporter
from . import viewport
from . import gsplat

# =============================================================================
# Scene Functions
# =============================================================================
from .scene import (
    # Initialization
    init_simulation,
    init_gsplat_scene,
    clear_scene,
    configure_physics_cache,
    # Frame range
    set_frame_range,
    get_frame_range,
    set_current_frame,
    get_current_frame,
    # Viewport
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
# Gaussian Splatting (3DGS/4DGS)
# =============================================================================
from .gsplat import (
    load_gsplat,
    load_3dgs,
    load_4dgs_sequence,
    load_4dgs_from_files,
    setup_sequence_animation,
    clear_sequence_animation,
    apply_geometry_nodes_from_blend,
    get_sequence_info,
    setup_gsplat_display,
    setup_gsplat_color,
    convert_sh_to_rgb,
    SH_C0,
    # Info utilities
    get_gsplat_info,
    print_gsplat_info,
    sigmoid,
)

# =============================================================================
# Viewport Functions
# =============================================================================
from .viewport import (
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
    setup_dual_viewport,
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
    'gsplat',
    
    # Scene functions
    'init_simulation',
    'init_gsplat_scene',
    'clear_scene',
    'configure_physics_cache',
    'set_frame_range',
    'get_frame_range',
    'set_current_frame',
    'get_current_frame',
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
    
    # Gaussian Splatting (3DGS/4DGS)
    'load_gsplat',
    'load_3dgs',
    'load_4dgs_sequence',
    'load_4dgs_from_files',
    'setup_sequence_animation',
    'clear_sequence_animation',
    'apply_geometry_nodes_from_blend',
    'get_sequence_info',
    'setup_gsplat_display',
    'setup_gsplat_color',
    'convert_sh_to_rgb',
    'SH_C0',
    'get_gsplat_info',
    'print_gsplat_info',
    'sigmoid',
    
    # Viewport functions
    'reset_viewport_single',
    'split_viewport_horizontal',
    'get_view3d_areas',
    'get_space_view3d',
    'configure_viewport_shading',
    'configure_viewport_overlays',
    'lock_viewport_to_camera',
    'sync_viewport_views',
    'setup_dual_viewport',
    'enter_local_view',
    'register_view_sync_handler',
    'register_viewport_restore_handler',
    'create_viewport_restore_script',
]
