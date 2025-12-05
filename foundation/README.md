# Physics Implementation Guide

This document bridges the gap between real-world physics concepts and their implementation within the VibePhysics framework.

## Module Structure

```
foundation/
├── physics.py    # Core physics: rigid body world, force fields
├── ground.py     # Terrain: seabed, uneven ground, containers
├── water.py      # Water: visual water, dynamic paint ripples
├── objects.py    # Floating objects: make any mesh floatable
├── materials.py  # Materials: water, ground, object shaders
└── lighting.py   # Lighting and camera setup
```

## Physics to Function Mapping

| Real Physics Concept | Equation / Principle | Module.Function | Implementation Details |
|----------------------|---------------------|-----------------|------------------------|
| **Newtonian Mechanics** | $F = ma$ (Second Law)<br>$F_g = mg$ (Gravity) | `physics.setup_rigid_body_world()` | **Engine:** Bullet Physics<br>**Config:** High substeps (60) to prevent tunneling of light objects ($0.001\text{kg}$). |
| **Buoyancy** | $F_b = \rho V g$ (Archimedes) | `physics.create_buoyancy_field()` | **Method:** Wind Force Field (+Z)<br>**Hack:** Constant upward force below $Z=0$ instead of exact volume calculation.<br>**Limit:** Bounded by `distance_max` at surface. |
| **Hydrodynamic Drag** | $F_d = -\frac{1}{2} \rho v^2 C_d A$ | `objects.make_object_floatable()` | **Method:** Adaptive Damping Driver<br>**Logic:** Python driver switches damping dynamically based on Z position. |
| **Turbulence** | Turbulent Flow (Chaotic) | `physics.create_underwater_currents()` | **Method:** Turbulence Force Field<br>**Math:** 3D Perlin Noise / Gradient Noise to generate random force vectors (Brownian motion). |
| **Wave Mechanics** (Ambient) | Spectral Synthesis (FFT) | `water.create_visual_water()` | **Method:** Ocean Modifier<br>**Tech:** Fourier Transform based surface displacement for realistic deep ocean swells. |
| **Wave Mechanics** (Ripples) | $\frac{\partial^2 u}{\partial t^2} = c^2 \nabla^2 u$ | `water.setup_dynamic_paint_interaction()` | **Method:** Dynamic Paint (Wave Surface)<br>**Tech:** Solves 2D Wave Equation on vertex grid.<br>**Coupling:** One-way (Objects $\to$ Waves). |

## Key Functions by Module

### `physics.py` - Core Physics
| Function | Description |
|----------|-------------|
| `setup_rigid_body_world()` | Initializes Bullet physics engine with optimized substeps |
| `create_buoyancy_field()` | Creates upward force field simulating water lift |
| `create_underwater_currents()` | Creates turbulence for natural water movement |

### `ground.py` - Terrain
| Function | Description |
|----------|-------------|
| `create_seabed()` | Flat ocean floor collision mesh |
| `create_uneven_ground()` | Procedural terrain with noise displacement |
| `create_bucket_container()` | Cylindrical container with physics walls |

### `water.py` - Water Visuals
| Function | Description |
|----------|-------------|
| `create_visual_water()` | Ocean Modifier based water surface (pool or open ocean) |
| `setup_dynamic_paint_interaction()` | Ripple effects from object interactions |

### `objects.py` - Floating Objects
| Function | Description |
|----------|-------------|
| `make_object_floatable()` | **Generic** - Makes ANY mesh object physics-enabled and floatable |
| `create_floating_sphere()` | Convenience - Creates and floats a sphere |
| `create_floating_cube()` | Convenience - Creates and floats a cube |
| `create_floating_mesh()` | Convenience - Creates various mesh types (sphere, cube, cylinder, cone, torus, monkey) |
| `generate_scattered_positions()` | Generates non-overlapping random positions |

### `materials.py` - Shaders
| Function | Description |
|----------|-------------|
| `create_water_material()` | Transparent water shader with caustics support |
| `create_seabed_material()` | Ground/dirt material |
| `create_mud_material()` | Wet mud material |
| `create_sphere_material()` | Colorful materials for objects |

### `lighting.py` - Scene Setup
| Function | Description |
|----------|-------------|
| `setup_lighting_and_camera()` | Complete scene lighting with caustics and volumetrics |
| `create_caustics_light()` | Animated caustic pattern projection |
| `create_underwater_volume()` | Volumetric god rays |

## Usage Example

```python
from foundation import physics, ground, water, objects, materials, lighting

# 1. Setup physics environment
physics.setup_rigid_body_world()
physics.create_buoyancy_field(z_bottom=-5, z_surface=0, strength=10.0)

# 2. Create terrain
ground.create_seabed(z_bottom=-5)

# 3. Create water
water_obj = water.create_visual_water(scale=1.0, wave_scale=1.0)
materials.create_water_material(water_obj)

# 4. Create floating objects (ANY mesh!)
import bpy
bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 5))
monkey = bpy.context.active_object
objects.make_object_floatable(monkey, mass=0.5, z_surface=0.0)

# 5. Setup ripple interactions
water.setup_dynamic_paint_interaction(water_obj, [monkey], ripple_strength=5.0)

# 6. Setup scene
lighting.setup_lighting_and_camera(...)
```
