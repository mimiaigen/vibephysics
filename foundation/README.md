# Physics Implementation Guide

This document bridges the gap between real-world physics concepts and their implementation within the VibePhysics framework.

## Module Structure

```
foundation/
├── scene.py       # Universal scene initialization and cleanup
├── physics.py     # Core physics: rigid body world, force fields
├── ground.py      # Terrain: seabed, uneven ground, containers
├── water.py       # Water: visual water, dynamic paint ripples
├── objects.py     # Object creation: spheres, cubes, debris
├── materials.py   # Materials: water, ground, object shaders
├── lighting.py    # Lighting and camera setup
├── trajectory.py  # Path and trajectory generation (general)
├── robot.py       # General rigged character control (model-agnostic)
└── open_duck.py   # Open Duck robot specific control
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
| `setup_camera_tracking()` | Make camera follow a target object |
| `create_caustics_light()` | Animated caustic pattern projection |
| `create_underwater_volume()` | Volumetric god rays |

### `trajectory.py` - Paths and Trajectories
| Function | Description |
|----------|-------------|
| `create_circular_path()` | Circle or oval path for any object |
| `create_linear_path()` | Straight line path |
| `create_figure_eight_path()` | Figure-8 pattern |
| `create_waypoint_path()` | Custom path through waypoints |
| `evaluate_curve_at_t()` | Get position/tangent on curve |

### `robot.py` - General Character Control
| Function | Description |
|----------|-------------|
| `load_rigged_robot()` | Load ANY rigged model from .blend file |
| `animate_walking()` | Generic IK-based walking animation |
| `setup_collision_meshes()` | Add physics collision to rigged parts |
| `raycast_ground()` | Detect ground height for foot placement |

### `open_duck.py` - Duck-Specific Control
| Function | Description |
|----------|-------------|
| `load_open_duck()` | Load Open Duck with duck-specific defaults |
| `create_duck_walk_path()` | Duck-appropriate walking path |
| `animate_duck_walking()` | Duck waddle animation |
| `setup_duck_collision()` | Duck-specific collision physics |
| `setup_duck_simulation()` | **Complete recipe** - all duck setup in one call |

## Model-Specific Control

### Architecture
The foundation separates **general control** from **model-specific control**:

- **General modules** (`robot.py`, `trajectory.py`) work with ANY rigged model
- **Model-specific modules** (`open_duck.py`) provide specialized control with model constants

### Creating New Model Controllers

See `foundation/MODEL_GUIDE.md` for complete guide.

**Quick example:**
```python
# foundation/your_model.py

from . import robot, trajectory

YOUR_MODEL_PROPORTIONS = {
    'hips_height_ratio': 0.33,
    'stride_ratio': 1.6,
    # ... model-specific constants
}

def setup_your_model_simulation(terrain, **kwargs):
    """Complete recipe for your model."""
    armature, parts = robot.load_rigged_robot(filepath, transform)
    path = trajectory.create_circular_path(radius=10.0)
    robot.animate_walking(armature, path, terrain, **YOUR_MODEL_PROPORTIONS)
    robot.setup_collision_meshes(parts)
    return {'armature': armature, 'parts': parts, 'path': path}
```

Then import and use: `from foundation import your_model`

## Usage Examples

### Water Physics Simulation
```python
from foundation import scene, physics, ground, water, objects, materials, lighting

# 1. Universal scene setup
scene.init_simulation(start_frame=1, end_frame=250)

# 2. Create terrain
terrain = ground.create_seabed(z_bottom=-5)

# 3. Create water
water_obj = water.create_visual_water(scale=1.0, wave_scale=1.0)
materials.create_water_material(water_obj)

# 4. Add physics
physics.create_buoyancy_field(z_bottom=-5, z_surface=0, strength=10.0)

# 5. Create floating objects
import bpy
bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 5))
monkey = bpy.context.active_object
objects.make_object_floatable(monkey, mass=0.5, z_surface=0.0)

# 6. Setup ripples
water.setup_dynamic_paint_interaction(water_obj, [monkey], ripple_strength=5.0)

# 7. Lighting & render
lighting.setup_lighting_and_camera(...)

# 8. Bake physics
physics.bake_all()
```

### Robot Walking Simulation
```python
from foundation import scene, ground, open_duck, water, lighting, physics

# 1. Universal setup
scene.init_simulation(start_frame=1, end_frame=250)

# 2. Terrain
terrain = ground.create_uneven_ground(z_base=-1.0, size=25.0)

# 3. Water surface
water_obj = water.create_flat_surface(size=20.0, z_level=-0.9)

# 4. Duck (all setup in one call!)
duck_result = open_duck.setup_duck_simulation(
    terrain=terrain,
    terrain_size=25.0,
    start_frame=1,
    end_frame=250,
    walk_speed=1.0
)

# 5. Water interactions
water.setup_robot_water_interaction(
    water_obj, 
    duck_result['parts'], 
    [], 
    ripple_strength=15.0
)

# 6. Camera and render
lighting.setup_lighting_and_camera(...)
lighting.setup_camera_tracking(duck_result['armature'])

# 7. Bake
physics.bake_all()
```
