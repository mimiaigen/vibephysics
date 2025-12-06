"""
Scene management and initialization utilities.
Hides low-level Blender API calls for scene setup.
"""
import bpy

def init_simulation(start_frame=1, end_frame=250, physics_config=None, clear=True):
    """
    Universal scene initialization for all examples.
    
    Args:
        start_frame: First frame of animation
        end_frame: Last frame of animation
        physics_config: Dict with physics settings (substeps, solver_iters, cache_buffer)
        clear: Whether to clear existing scene objects
    """
    if clear:
        clear_scene()
    
    # Setup physics
    from . import physics
    physics.setup_rigid_body_world()
    
    # Configure physics cache if requested
    if physics_config:
        configure_physics_cache(start_frame, end_frame, **physics_config)

def clear_scene():
    """Remove all objects from scene and clear handlers."""
    # Clear frame handlers to avoid duplicates
    bpy.app.handlers.frame_change_pre.clear()
    
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
