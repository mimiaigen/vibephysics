# Foundation Module
# Organized by functionality

from . import physics        # Core physics: rigid body world, force fields
from . import ground         # Terrain: seabed, uneven ground, containers
from . import water          # Water: visual water, dynamic paint ripples
from . import objects        # Floating objects: make any mesh floatable
from . import materials      # Materials: water, ground, object shaders
from . import lighting       # Lighting and camera setup
from . import robot          # Robot character and procedural animation
from . import viewport       # Viewport management: dual viewport, view sync
from . import point_tracking # Point cloud tracking visualization
