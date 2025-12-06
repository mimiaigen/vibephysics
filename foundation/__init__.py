"""
Foundation Module

Core physics simulation and scene setup utilities for Blender.
This module provides the building blocks for creating physics-based
simulations with water, ground, objects, and materials.

Modules:
- physics: Rigid body physics and force fields
- water: Water surface creation and dynamics
- ground: Terrain and seabed generation
- objects: Object creation and scattering
- materials: Material creation for various surfaces
- lighting: Lighting and camera setup
- robot: Robot loading and animation utilities
"""

# Import all submodules for convenient access
from . import physics
from . import water
from . import ground
from . import objects
from . import materials
from . import lighting
from . import robot
