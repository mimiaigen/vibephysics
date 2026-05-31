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

__version__ = "0.3.7"
__author__ = "Tsun-Yi Yang"

try:
    import bpy

    HAS_BPY = True
except ImportError:
    HAS_BPY = False

__all__ = [
    "__version__",
    "feedforward",
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


def __getattr__(name: str):
    if name == "mapping":
        import importlib

        return importlib.import_module(".mapping", __name__)
    if name == "feedforward":
        import importlib

        return importlib.import_module(".feedforward", __name__)
    if not HAS_BPY:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    if name == "setup":
        from . import setup

        return setup
    if name == "foundation":
        from . import foundation

        return foundation
    if name == "annotation":
        from . import annotation

        return annotation
    if name == "AnnotationManager":
        from .annotation import AnnotationManager

        return AnnotationManager
    if name == "quick_annotate":
        from .annotation import quick_annotate

        return quick_annotate
    if name == "init_simulation":
        from .setup import init_simulation

        return init_simulation
    if name == "setup_dual_viewport":
        from .setup import setup_dual_viewport

        return setup_dual_viewport
    if name == "clear_scene":
        from .setup import clear_scene

        return clear_scene
    if name == "load_asset":
        from .setup import load_asset

        return load_asset
    if name == "save_blend":
        from .setup import save_blend

        return save_blend
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
