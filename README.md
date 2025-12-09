# VibePhysics

![VibePhysics Teaser](vibephysics_teaser.png)

**A lightweight Blender physics simulation framework for creating realistic robot animations, rigid body physics, water dynamics, and comprehensive annotation tools — all running efficiently on CPU.**

## 🎬 Example Results

![Result Demo](result_demo.gif)

*Robot walking simulation with rigid body physics, interacting with uneven ground, puddles, and real-time annotation overlay.*

## 📊 Annotation Tools Demo

![Annotation Demo](annotation_demo.gif)

*Comprehensive annotation system featuring bounding boxes, motion trails, and point cloud tracking for computer vision datasets.*

## 💧 Water Simulation Demo

![Water Float Demo](water_float_demo.gif)

*Water physics simulation with floating objects, buoyancy forces, dynamic ripples, and point cloud tracking.*

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
pip install tqdm

# Install vibephysics
pip install vibephysics

# Or install from source
pip install -e .
```

## Quick Start

```bash
# Run annotation demo
sh ./run_annotation.sh

# Run robot simulation (with mounted POV camera by default)
sh ./run_robot.sh

# Run robot simulation with different camera views
sh ./run_robot.sh mounted    # First-person POV (default)
sh ./run_robot.sh center     # Overview from multiple angles
sh ./run_robot.sh following  # Third-person tracking shot

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

## Camera System

VibePhysics includes a flexible multi-camera system with three camera rig types:

| Camera Type | Description | Best For |
|-------------|-------------|----------|
| **Center** | Multiple cameras arranged in a circle, pointing at scene center | Overview shots, multi-angle captures |
| **Mounted** | Cameras attached directly to an object (e.g., robot head) | First-person POV, onboard views |
| **Following** | Single camera that follows and tracks a target object | Third-person view, tracking shots |

### Usage Example

```python
from vibephysics.camera import CameraManager

cam_manager = CameraManager()

# Center-pointing cameras (fixed position, looking at origin)
center_rig = cam_manager.add_center_pointing('center', num_cameras=4, radius=25, height=12)
center_rig.create(target_location=(0, 0, 0))

# Mounted cameras (attached to robot head for POV shots)
mounted_rig = cam_manager.add_object_mounted('mounted', num_cameras=4, distance=0.15)
mounted_rig.create(parent_object=robot_head, lens=10)

# Following camera (tracks a moving object)
follow_rig = cam_manager.add_following('following', height=12, look_angle=60)
follow_rig.create(target=robot_armature)

# Activate a specific camera
cam_manager.activate_rig('mounted', camera_index=0)  # Front camera
```

### Command Line Options

Robot simulations support camera selection via shell script or Python:

```bash
# Via shell script (recommended)
sh run_robot.sh mounted    # First-person POV (default)
sh run_robot.sh center     # Overview from multiple angles
sh run_robot.sh following  # Third-person tracking shot

# Via Python directly
python examples/robot/robot_waypoint_walk.py --active-camera mounted
python examples/robot/robot_waypoint_walk.py --active-camera center
python examples/robot/robot_waypoint_walk.py --active-camera following
```

### Switching Cameras in Blender

**All three camera rigs are created in every `.blend` file** — the command line option only sets which one is active by default. You can manually switch between any camera directly in Blender:

1. **Open the `.blend` file** in Blender
2. **Press `Numpad 0`** to view through the active camera
3. **Switch cameras** using one of these methods:
   - **Outliner (Easiest)**: In the top-right Outliner panel, find camera objects (e.g., `MountedCam_0`, `CenterCam_0`, `FollowingCam`) → Click the **green camera icon** 🎥 next to the camera name to make it active
   - **Right-click Menu**: Right-click a camera in Outliner → **Set Active Camera**
   - **Keyboard**: Select a camera → Press `Ctrl + Numpad 0` to make it active
   - **View Menu**: View → Cameras → Set Active Object as Camera

> 💻 **Mac Users**: Simply click the **green camera icon** 🎥 in the Outliner (see above) to switch active cameras.

This means you can generate a single `.blend` file and render from any camera angle without re-running the simulation.

## Project Structure

```
vibephysics/
├── src/vibephysics/
│   ├── setup/              # Scene & asset management
│   │   ├── scene.py        # Scene initialization, frame range
│   │   ├── importer.py     # Asset loading (GLB, FBX, PLY, etc.)
│   │   ├── exporter.py     # Save/export (blend, FBX, OBJ, etc.)
│   │   ├── viewport.py     # Viewport splitting, dual-view
│   │   └── gsplat.py       # Gaussian Splatting (3DGS)
│   ├── foundation/         # Core simulation modules
│   │   ├── physics.py      # Rigid body world, force fields
│   │   ├── ground.py       # Terrain generation
│   │   ├── water.py        # Water surfaces, ripples
│   │   ├── objects.py      # Floating objects
│   │   ├── materials.py    # Shaders (water, mud, etc.)
│   │   ├── lighting.py     # Lighting and camera
│   │   ├── robot.py        # Generic robot control
│   │   ├── open_duck.py    # Open Duck robot integration
│   │   └── trajectory.py   # Waypoint paths
│   ├── annotation/         # Visualization tools
│   │   ├── base.py         # Base annotation classes
│   │   ├── bbox.py         # Bounding box annotations
│   │   ├── motion_trail.py # Motion path visualization
│   │   ├── point_tracking.py # Point cloud tracking
│   │   └── manager.py      # Unified annotation API
│   └── camera/             # Camera system
│       ├── base.py         # Base camera classes
│       ├── center.py       # Center-pointing cameras
│       ├── following.py    # Following camera rig
│       ├── mounted.py      # Object-mounted cameras
│       └── manager.py      # Camera manager API
├── examples/
│   ├── basics/             # Annotation demos
│   ├── water/              # Water simulations
│   └── robot/              # Robot simulations
├── run_water.sh            # Run water examples
├── run_robot.sh            # Run robot examples
└── run_annotation.sh       # Run annotation demos
```

## Setup Module

The `setup` module provides scene initialization, asset import/export, and viewport management:

```python
from vibephysics import setup

# Initialize a simulation scene
setup.init_simulation(start_frame=1, end_frame=250)

# Load assets (auto-detects format from file extension)
setup.load_asset('robot.glb')           # GLB/GLTF
setup.load_asset('mesh.fbx')            # FBX
setup.load_asset('points.ply')          # PLY

# Save/export (auto-detects format)
setup.save_blend('output/scene.blend')  # Creates directories automatically

# For format-specific options, use submodules directly:
from vibephysics.setup import importer, exporter

objects = importer.load_glb('model.glb', transform={'scale': 0.5})
exporter.export_fbx('output.fbx', selected_only=True)
```

### Supported Formats

| Import | Export |
|--------|--------|
| GLB/GLTF | Blend |
| FBX | GLB/GLTF |
| PLY | FBX |
| OBJ | OBJ |
| STL | PLY |
| DAE (Collada) | STL |
| USD/USDA/USDC | USD |
| Blend (append) | |

## Gaussian Splatting (3DGS)

VibePhysics supports loading 3D Gaussian Splatting data:

```
sh run_3dgs_viewer.sh
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