"""
VibePhysics - Physics Simulation and Annotation Tools for Blender

A Python library for creating physics-based simulations in Blender,
with support for water dynamics, rigid body physics, robot animation,
and comprehensive annotation tools.

Usage:
    from vibephysics import foundation, annotation
    
    # Or import specific modules
    from vibephysics.foundation import scene, physics, water
    from vibephysics.annotation import AnnotationManager

Note: This package requires Blender 5.0's Python environment (bpy).
"""

__version__ = "0.1.3"
__author__ = "Your Name"

# Check if running inside Blender
def _check_blender_environment():
    """Check if bpy is available and provide helpful error if not."""
    try:
        import bpy
        return True
    except ImportError:
        import sys
        
        raise ImportError(
            "vibephysics requires python=3.11 and Blender 5.0's Python environment. "
        )

# Check environment before importing submodules
_check_blender_environment()

# Import subpackages for convenient access
from . import foundation
from . import annotation

# Quick access to commonly used classes
from .annotation import AnnotationManager, quick_annotate

__all__ = [
    "__version__",
    "foundation",
    "annotation",
    "AnnotationManager",
    "quick_annotate",
]
