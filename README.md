# VibePhysics

![VibePhysics Teaser](vibephysics_teaser.png)

**A lightweight Blender physics simulation framework for creating realistic robot animations, rigid body physics, water dynamics, and comprehensive annotation tools — all running efficiently on CPU.**

## ✨ Highlights

- **🚀 No GPU Required** – Runs efficiently on CPU-only machines (MacBook Pro, laptops, standard workstations). GPU accelerates rendering but is not mandatory.
- **🤖 Robot Simulation** – Realistic IK-based walking animations with the Open Duck robot
- **💧 Water Physics** – Dynamic water surfaces, puddles, ripples, and buoyancy simulation
- **📊 Annotation Tools** – Bounding boxes, motion trails, and point cloud tracking for vision datasets
- **🎯 Production Ready** – Clean API, modular architecture, and extensive examples
- **🔧 Developer Friendly** – Pure Python, works with Blender as a module (bpy), no GUI needed

Perfect for researchers, animators, and robotics engineers who need physics simulations without expensive GPU hardware.

## Requirements

### For Running Simulations
- **Python 3.11** (required for bpy compatibility - **Python 3.12+ is not supported**)
- **bpy** (Blender as a Python module)

### For Viewing Results (Optional)
- **Blender 5.0** - Free download from [blender.org](https://www.blender.org/download/)
- Only needed to view/render the generated `.blend` files
- Not required to run simulations

> ⚠️ **Important**: This package requires Python 3.11. Python 3.12 and later versions are not compatible with the current version of bpy.

### Dependency
We use the [Open Duck blender model](https://github.com/pollen-robotics/Open_Duck_Blender) as demo purpose. We do not own the model. Please refer to the original github repo.

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
# Run annotation demo
sh ./run_annotation.sh

# Run robot simulation
sh ./run_robot.sh

# Run water simulations
sh ./run_water.sh
```

## Visualizing Results

All simulations generate `.blend` files in the `output/` directory. To view and interact with these results:

**Download Blender 5.0** (Free & Open Source)
- 🔗 **[Download Blender](https://www.blender.org/download/)**
- Compatible with Windows, macOS (Intel/Apple Silicon), and Linux
- No installation required for VibePhysics to run – Blender is only needed to view results
- GPU accelerates viewport and rendering performance, but CPU-only works fine

**Opening Results:**
```bash
# macOS
open output/robot_waypoint.blend

# Linux
blender output/robot_waypoint.blend

# Windows
start output/robot_waypoint.blend
```

Once in Blender, press **Spacebar** to play the animation and view your physics simulation!

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
│   │   ├── robot.py        # Generic robot control
│   │   ├── open_duck.py    # Open Duck robot integration
│   │   ├── trajectory.py   # Waypoint paths
│   │   └── scene.py        # Scene initialization
│   └── annotation/         # Visualization tools
│       ├── base.py         # Base annotation classes
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

## License

**© 2025 MIMI AI LTD, UK. All rights reserved.**

### Academic & Student Use (Free)
This software is **free to use** for:
- Students
- Academic research
- Educational purposes

### Commercial Use
For business or enterprise use, please contact: **tsunyi@mimiaigen.com**
We have separate license for business/enterprise users.


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