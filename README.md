# VibePhysics

![VibePhysics Teaser](vibephysics_teaser.png)

**A lightweight Blender physics simulation framework for creating realistic robot animations, rigid body physics, water dynamics, and comprehensive annotation tools — all running efficiently on CPU.**

## ✨ Highlights

- **🚀 No GPU Required** – Runs smoothly on CPU-only machines (MacBook Pro, laptops, standard workstations)
- **🤖 Robot Simulation** – Realistic IK-based walking animations with the Open Duck robot
- **💧 Water Physics** – Dynamic water surfaces, puddles, ripples, and buoyancy simulation
- **📊 Annotation Tools** – Bounding boxes, motion trails, and point cloud tracking for vision datasets
- **🎯 Production Ready** – Clean API, modular architecture, and extensive examples
- **🔧 Developer Friendly** – Pure Python, works with Blender as a module (bpy), no GUI needed

Perfect for researchers, animators, and robotics engineers who need physics simulations without expensive GPU hardware.

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

### Robot Simulations

```bash
# Robot walking through puddles
python examples/robot/robot_walking_water_puddle.py --output output/duck_walk.blend

# Duck following waypoints
python examples/robot/duck_waypoint_walk.py --waypoint-pattern exploration --output output/duck.blend
```

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

**© 2025 MIMI AI LTD, UK. All rights reserved.**

### Academic & Student Use (Free)
This software is **free to use** for:
- Students
- Academic research
- Educational purposes

### Commercial Use
For business or enterprise use, please contact: **tsunyi@mimiaigen.com**
We have seperate license for business/enterprise users.


### Dependency
We use the [Open Duck blender model](https://github.com/pollen-robotics/Open_Duck_Blender) as demo purpose. We do not own the model. Please refer to the original github repo.


### Citation
```
@misc{VibePhysics,
  author = {Tsun-Yi Yang},
  title = {VibePhysics: Physics and Robotics Simulation in Blender Without GPU Requirements},
  month = {December},
  year = {2025},
  url = {https://github.com/mimiaigen/vibephysics}
}
```