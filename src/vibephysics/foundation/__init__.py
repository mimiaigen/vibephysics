"""
Foundation Module

Core physics simulation and scene setup utilities for Blender.
This module provides the building blocks for creating physics-based
simulations with water, ground, objects, and materials.

Modules:
- scene: Scene initialization and cleanup utilities
- physics: Rigid body physics and force fields
- water: Water surface creation and dynamics
- ground: Terrain and seabed generation
- objects: Object creation and scattering
- materials: Material creation for various surfaces
- lighting: Lighting and camera setup
- trajectory: Path and trajectory generation (general)
- robot: General rigged character control (model-agnostic)
- open_duck: Open Duck robot specific control
"""

# Import all submodules for convenient access
from . import scene
from . import physics
from . import water
from . import ground
from . import objects
from . import materials
from . import lighting
from . import trajectory
from . import robot
from . import open_duck
