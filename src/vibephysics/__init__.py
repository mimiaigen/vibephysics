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
Run scripts through Blender:
    blender -b -P your_script.py
"""

__version__ = "0.1.0"
__author__ = "Your Name"

# Check if running inside Blender
def _check_blender_environment():
    """Check if bpy is available and provide helpful error if not."""
    try:
        import bpy
        return True
    except ImportError:
        import sys
        
        error_message = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                     VibePhysics - Blender 5.0 Required                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  This package requires Blender 5.0's Python environment (bpy module).        ║
║                                                                              ║
║  ⚠️  You are running Python outside of Blender!                              ║
║                                                                              ║
║  To use vibephysics, run your scripts through Blender:                       ║
║                                                                              ║
║    # Run in background mode:                                                 ║
║    blender -b -P your_script.py                                              ║
║                                                                              ║
║    # Run with GUI:                                                           ║
║    blender -P your_script.py                                                 ║
║                                                                              ║
║    # Pass arguments to your script:                                          ║
║    blender -b -P your_script.py -- --your-arg value                          ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  REQUIREMENTS:                                                               ║
║    • Blender 5.0                                                             ║
║    • Download: https://www.blender.org/download/                             ║
║    • Install guide: https://docs.blender.org/manual/en/latest/               ║
║                     getting_started/installing/                              ║
║                                                                              ║
║  Verify Blender is installed:                                                ║
║    blender --version                                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        print(error_message, file=sys.stderr)
        raise ImportError(
            "vibephysics requires Blender 5.0's Python environment. "
            "Run your script with: blender -b -P your_script.py"
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
