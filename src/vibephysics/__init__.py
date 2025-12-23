"""
VibePhysics - Physics Simulation and Annotation Tools for Blender

A Python library for creating physics-based simulations in Blender,
with support for water dynamics, rigid body physics, robot animation,
and comprehensive annotation tools.

Usage:
    from vibephysics import foundation, annotation, setup
    
    # Or import specific modules
    from vibephysics.foundation import scene, physics, water
    from vibephysics.setup import scene, viewport  # scene also available here
    from vibephysics.annotation import AnnotationManager

Note: This package requires Blender 5.0's Python environment (bpy) for simulation.
"""

__version__ = "0.2.3"
__author__ = "Tsun-Yi Yang"

# Core modules (non-Blender)
from . import mapping

# Blender-dependent modules
try:
    import bpy
    from . import setup
    from . import foundation
    from . import annotation
    from .annotation import AnnotationManager, quick_annotate
    from .setup import init_simulation, setup_dual_viewport, clear_scene, load_asset, save_blend
    HAS_BPY = True
except ImportError:
    HAS_BPY = False
    setup = None
    foundation = None
    annotation = None

__all__ = [
    "__version__",
    "mapping",
]

if HAS_BPY:
    __all__ += [
        "setup",
        "foundation",
        "annotation",
        "AnnotationManager",
        "quick_annotate",
        "init_simulation",
        "setup_dual_viewport",
        "clear_scene",
        "load_asset",
        "save_blend",
    ]
