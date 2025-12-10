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

__version__ = "0.1.9"
__author__ = "Tsun-Yi Yang"

# Import subpackages for convenient access
from . import setup
from . import foundation
from . import annotation

# Quick access to commonly used classes
from .annotation import AnnotationManager, quick_annotate

# Scene setup
from .setup import init_simulation, setup_dual_viewport, clear_scene

# Asset import/export (smart functions that auto-detect format)
from .setup import load_asset, save_blend

__all__ = [
    "__version__",
    # Modules
    "setup",
    "foundation",
    "annotation",
    # Annotation
    "AnnotationManager",
    "quick_annotate",
    # Scene setup
    "init_simulation",
    "setup_dual_viewport",
    "clear_scene",
    # Import/Export (auto-detect format)
    "load_asset",
    "save_blend",
]
