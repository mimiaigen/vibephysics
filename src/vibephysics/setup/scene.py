"""
Scene Management Module

Core scene initialization and configuration utilities.
Provides a clean API for setting up Blender scenes with physics and viewports.

For asset loading, see: importer.py (use load_asset() - auto-detects format)
For scene export, see: exporter.py (use save_blend() or export_asset())
"""
import bpy

# Re-export only the smart functions (auto-detect format by extension)
from .importer import load_asset, move_to_collection, ensure_collection
from .exporter import save_blend, export_selected
from .gsplat import load_gsplat, load_3dgs, load_4dgs_sequence


# =============================================================================
# Scene Initialization
# =============================================================================

def init_simulation(start_frame=1, end_frame=250, physics_config=None, clear=True):
    """
    Universal scene initialization for all examples.
    
    Args:
        start_frame: First frame of animation
        end_frame: Last frame of animation
        physics_config: Dict with physics settings (substeps, solver_iters, cache_buffer)
        clear: Whether to clear existing scene objects
    
    Example:
        # Basic initialization
        init_simulation(start_frame=1, end_frame=250)
        
        # With physics config
        init_simulation(
            physics_config={'substeps': 20, 'solver_iters': 20}
        )
    """
    if clear:
        clear_scene()
    
    # Setup frame range
    scene = bpy.context.scene
    scene.frame_start = start_frame
    scene.frame_end = end_frame
    scene.frame_set(start_frame)
    
    # Setup physics
    from ..foundation import physics
    physics.setup_rigid_body_world()
    
    # Configure physics cache if requested
    if physics_config:
        configure_physics_cache(start_frame, end_frame, **physics_config)


def init_gsplat_scene(
    gsplat_path,
    start_frame=1,
    collection_name="GaussianSplat",
    clear=True
):
    """
    Initialize a scene for Gaussian Splatting playback.
    
    Automatically detects 3DGS (single file) vs 4DGS (folder sequence).
    Sets up frame range based on sequence length for 4DGS.
    
    Args:
        gsplat_path: Path to .ply file (3DGS) or folder with PLY sequence (4DGS)
        start_frame: Starting frame number
        collection_name: Collection name for the splat(s)
        clear: Whether to clear existing scene
    
    Returns:
        Object (3DGS) or Collection (4DGS), or None if failed
    
    Example:
        # Load single Gaussian splat
        obj = init_gsplat_scene('scene.ply')
        
        # Load animated 4DGS sequence
        collection = init_gsplat_scene('frames/')
        # Frame range automatically set to match sequence length
    """
    import os
    
    if clear:
        clear_scene()
    
    scene = bpy.context.scene
    scene.frame_start = start_frame
    scene.frame_set(start_frame)
    
    # Load Gaussian splat(s)
    from . import gsplat
    result = gsplat.load_gsplat(
        gsplat_path,
        collection_name=collection_name,
        frame_start=start_frame,
        setup_animation=True
    )
    
    # For 4DGS sequences, adjust frame range based on loaded frames
    if result and isinstance(result, bpy.types.Collection):
        num_frames = len(result.objects)
        scene.frame_end = start_frame + num_frames - 1
        print(f"📊 Frame range set: {start_frame} to {scene.frame_end} ({num_frames} frames)")
    
    return result


def clear_scene():
    """
    Remove all objects from scene and clear handlers.
    
    This clears:
    - All objects in the scene
    - Frame change handlers (pre and post)
    """
    # Clear frame handlers to avoid duplicates
    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_post.clear()
    
    # Remove all objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()


def configure_physics_cache(start_frame, end_frame, substeps=20, solver_iters=20, cache_buffer=50):
    """
    Configure rigid body simulation parameters.
    
    Args:
        start_frame: First frame for physics cache
        end_frame: Last frame for physics cache
        substeps: Physics substeps per frame (higher = more accurate)
        solver_iters: Solver iterations (higher = more stable)
        cache_buffer: Extra frames beyond end_frame for cache
    """
    scene = bpy.context.scene
    if scene.rigidbody_world:
        scene.rigidbody_world.substeps_per_frame = substeps
        scene.rigidbody_world.solver_iterations = solver_iters
        scene.rigidbody_world.point_cache.frame_start = start_frame
        scene.rigidbody_world.point_cache.frame_end = end_frame + cache_buffer


# =============================================================================
# Frame Range Utilities
# =============================================================================

def set_frame_range(start_frame, end_frame):
    """
    Set the animation frame range.
    
    Args:
        start_frame: First frame
        end_frame: Last frame
    """
    scene = bpy.context.scene
    scene.frame_start = start_frame
    scene.frame_end = end_frame


def get_frame_range():
    """
    Get the current frame range.
    
    Returns:
        Tuple of (start_frame, end_frame)
    """
    scene = bpy.context.scene
    return scene.frame_start, scene.frame_end


def set_current_frame(frame):
    """Set the current frame."""
    bpy.context.scene.frame_set(frame)


def get_current_frame():
    """Get the current frame."""
    return bpy.context.scene.frame_current


def reset_viewport():
    """
    Reset viewport to single view (undo dual viewport split).
    """
    if bpy.app.background:
        return
    
    from . import viewport as vp
    vp.reset_viewport_single()


# =============================================================================
# Render Settings
# =============================================================================

def set_render_resolution(width, height, percentage=100):
    """
    Set render resolution.
    
    Args:
        width: Render width in pixels
        height: Render height in pixels
        percentage: Resolution percentage (default 100%)
    """
    scene = bpy.context.scene
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = percentage


def set_render_engine(engine='CYCLES'):
    """
    Set the render engine.
    
    Args:
        engine: 'CYCLES', 'BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT', or 'BLENDER_WORKBENCH'
    """
    bpy.context.scene.render.engine = engine


def set_output_path(path):
    """
    Set the render output path.
    
    Args:
        path: Output path for rendered frames
    """
    bpy.context.scene.render.filepath = path
