# VibePhysics

A Blender physics simulation framework for creating realistic water dynamics, robot animations, and comprehensive annotation tools.

## Requirements

- **Python 3.11** (required for bpy compatibility)
- **bpy** (Blender as a Python module)

## Installation

```bash
# Create conda environment with Python 3.11
conda create -n vibephysics python=3.11
conda activate vibephysics

# Install bpy (Blender as Python module)
pip install bpy

# Install vibephysics
pip install vibephysics

# Or install from source
pip install -e .
```

## Quick Start

```bash
# Run water simulation
python examples/water/water_float.py --output output/water_float.blend

# Run robot simulation
./run_robot.sh

# Run all simulations
./run_water.sh
```

## Project Structure

```
vibephysics/
├── src/vibephysics/
│   ├── foundation/         # Core simulation modules
│   │   ├── physics.py      # Rigid body world, force fields
│   │   ├── ground.py       # Terrain generation
│   │   ├── water.py        # Water surfaces, ripples
│   │   ├── objects.py      # Floating objects
│   │   ├── materials.py    # Shaders (water, mud, etc.)
│   │   ├── lighting.py     # Lighting and camera
│   │   ├── open_duck.py    # Open Duck robot integration
│   │   ├── trajectory.py   # Waypoint paths
│   │   └── scene.py        # Scene initialization
│   └── annotation/         # Visualization tools
│       ├── bbox.py         # Bounding box annotations
│       ├── motion_trail.py # Motion path visualization
│       ├── point_tracking.py # Point cloud tracking
│       ├── viewport.py     # Dual viewport setup
│       └── manager.py      # Unified annotation API
├── examples/
│   ├── basics/             # Annotation demos
│   ├── water/              # Water simulations
│   └── robot/              # Robot simulations
├── run_water.sh            # Run water examples
├── run_robot.sh            # Run robot examples
└── run_annotation.sh       # Run annotation demos
```

## Examples

### Water Simulations

```bash
# Floating objects
python examples/water/water_float.py --output output/water_float.blend

# Rising water
python examples/water/water_rise.py --output output/water_rise.blend

# Storm with debris
python examples/water/storm.py --output output/storm.blend

# Water puddles
python examples/water/water_puddles.py --output output/water_puddles.blend
```

### Robot Simulations

```bash
# Robot walking through puddles
python examples/robot/robot_walking_water_puddle.py --output output/robot_walk.blend

# Duck following waypoints
python examples/robot/duck_waypoint_walk.py --waypoint-pattern exploration --output output/duck.blend
```

### Annotation Demos

```bash
# Bounding boxes
python examples/basics/demo_bbox.py

# Motion trails
python examples/basics/demo_motion_trail.py

# Point tracking
python examples/basics/demo_point_tracking.py

# All annotations combined
python examples/basics/demo_all_annotations.py
```

## Annotation System

VibePhysics includes a unified annotation system for visualizing simulations:

```python
from vibephysics.annotation import AnnotationManager

mgr = AnnotationManager()

# Add bounding boxes
mgr.add_bbox(cube, color=(1.0, 0.0, 0.0, 1.0))

# Add motion trails
mgr.add_motion_trail(sphere, color=(0.0, 1.0, 0.0, 1.0))

# Add point tracking
mgr.add_point_tracking([cube, sphere], points_per_object=50)

# Finalize (registers handlers, creates scripts)
mgr.finalize()
```

## Foundation Modules

### `physics.py` - Core Physics
- `setup_rigid_body_world()` - Initialize Bullet physics
- `create_buoyancy_field()` - Upward force for floating
- `create_underwater_currents()` - Turbulence forces

### `water.py` - Water Visuals
- `create_flat_surface()` - Flat water plane
- `setup_robot_water_interaction()` - Ripple effects

### `objects.py` - Objects
- `create_falling_spheres()` - Physics-enabled spheres
- `generate_scattered_positions()` - Random non-overlapping positions

### `open_duck.py` - Robot Integration
- `load_open_duck()` - Load Open Duck robot model
- `animate_duck_walking()` - Walking animation along path
- `setup_duck_collision()` - Physics collision setup

## Shell Scripts

```bash
# Run all water simulations
./run_water.sh

# Run robot simulations (auto-downloads Open Duck model)
./run_robot.sh

# Run annotation demos
./run_annotation.sh
```

## Common Arguments

| Argument | Description |
|----------|-------------|
| `--output` | Output .blend file path |
| `--start-frame` | Animation start frame |
| `--end-frame` | Animation end frame |
| `--num-spheres` | Number of floating objects |
| `--wave-scale` | Wave intensity |
| `--no-annotations` | Disable annotations |

## License

See LICENSE file.
