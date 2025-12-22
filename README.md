# VibePhysics

![VibePhysics Teaser](assets/vibephysics_teaser.png)

**A lightweight Blender physics simulation framework for creating realistic robot animations, rigid body physics, water dynamics, and comprehensive annotation tools — all running efficiently on CPU.**

## 🎬 Example Results (`sh run_robot.sh`)

![Result Demo](assets/result_demo.gif)

*Robot walking simulation with rigid body physics, interacting with uneven ground, puddles, and real-time annotation overlay.*

## 📊 Annotation Tools Demo (`sh run_basics.sh`)

![Annotation Demo](assets/annotation_demo.gif)

*Comprehensive annotation system featuring bounding boxes, motion trails, and point cloud tracking for computer vision datasets.*

## 🎯 Dynamic Frustum Culling Demo (`sh run_basics.sh`)

![Frustum Demo](assets/frustum_demo.gif)

*Per-point frustum culling with mounted camera. Points inside the camera frustum turn red in real-time as the camera moves.*

## 💧 Water Simulation Demo (`sh run_water.sh`)

![Water Float Demo](assets/water_float_demo.gif)

*Water physics simulation with floating objects, buoyancy forces, dynamic ripples, and point cloud tracking.*

## 🐕 Go2 Simulation Demo (`python examples/go2/go2_waypoint_walk.py`)

![Go2 Demo](assets/go2_water_sphere_demo.gif)

*Unitree Go2 robot walking through a physics-enabled environment with water puddles and falling debris.*

## ✨ Highlights

- **🚀 No GPU Required** – Runs efficiently on CPU-only machines (MacBook Pro, laptops, standard workstations). GPU accelerates rendering but is not mandatory.
- **🤖 Robot Simulation** – Realistic IK-based walking animations with Open Duck and Unitree Go2 robots
- **💧 Water Physics** – Dynamic water surfaces, puddles, ripples, and buoyancy simulation
- **📊 Annotation Tools** – Bounding boxes, motion trails, and point cloud tracking for vision datasets
- **🎯 Production Ready** – Clean API, modular architecture, and extensive examples
- **🗺️ SfM Mapping** – Integrated COLMAP and GLOMAP pipelines for high-speed 3D reconstruction
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
- **Open Duck**: We use the [Open Duck blender model](https://github.com/pollen-robotics/Open_Duck_Blender) as demo. We do not own the model. Please refer to the original github repo.
- **Unitree Go2**: We use the [Unitree Go2 USD model](https://huggingface.co/datasets/unitreerobotics/unitree_model). The model is auto-downloaded when running Go2 examples. We do not own the model.

## ⚙️ Installation

```bash
# 1. Create environment
conda create -n vibephysics python=3.11
conda activate vibephysics

# 2. Install core package (includes COLMAP mapping & Blender simulation)
pip install vibephysics

# 3. (Optional) Install GLOMAP backend
pip install git+https://github.com/shamangary/glomap.git
```

## Quick Start

```bash
# Run basic annotation demos (bbox, motion trail, point tracking, frustum culling)
sh ./run_basics.sh

# Run Open Duck robot simulation (with mounted POV camera by default)
sh ./run_robot.sh

# Run robot simulation with different camera views
sh ./run_robot.sh mounted    # First-person POV (default)
sh ./run_robot.sh center     # Overview from multiple angles
sh ./run_robot.sh following  # Third-person tracking shot

# Run Unitree Go2 robot simulation (auto-downloads model on first run)
python examples/go2/go2_waypoint_walk.py

# Go2 with custom settings
python examples/go2/go2_waypoint_walk.py --end-frame 150 --num-spheres 50

# Run forest walk simulation (robot walking through dense forest)
sh ./run_forest.sh

# Run forest with frustum culling options
sh ./run_forest.sh --frustum-mode highlight    # In-frustum points turn red
sh ./run_forest.sh --frustum-mode frustum_only # Only show in-frustum points
sh ./run_forest.sh --no-physics                # Fastest playback

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

## 🗺️ Mapping & Reconstruction

VibePhysics integrates high-performance Structure-from-Motion (SfM) engines to convert image sequences into 3D reconstructions.

- **GLOMAP Engine** – Global SfM that is 1-2 orders of magnitude faster than traditional methods.
- **COLMAP Engine** – Industry-standard incremental SfM for robust reconstruction.
- **GSplat Ready** – Automatically generates standard output structures (`sparse/0` and `images/` symlink) ready for instant GSplat training.

### 💻 Usage (Command Line)

```bash
# Run GLOMAP pipeline (Fastest - Default)
./run_glomap.sh --image_path path/to/images

# Run COLMAP pipeline (Most Robust)
./run_glomap.sh --image_path path/to/images --engine colmap

# Advanced options
./run_glomap.sh --image_path path/to/images --matcher sequential --camera_model PINHOLE
```

### 🐍 Usage (Python API)

```python
from vibephysics import mapping

# 1. Simple Usage (Only image_path is REQUIRED)
# Defaults: glomap engine, exhaustive matcher, SIMPLE_RADIAL camera
mapping.glomap_pipeline(image_path="path/to/images")

# 2. COLMAP Incremental Pipeline
mapping.colmap_pipeline(image_path="path/to/images")

# 3. Full Configuration (All parameters except image_path are OPTIONAL)
mapping.glomap_pipeline(
    image_path="path/to/images",          # REQUIRED
    output_path="output/dir",             # Optional: Defaults to image_path/../mapping_output/
    database_path="path/to/database.db",  # Optional: Defaults to output_path/sparse/database.db
    matcher="exhaustive",                 # Optional: "exhaustive" (default) or "sequential"
    camera_model="SIMPLE_RADIAL",         # Optional: "PINHOLE", "SIMPLE_RADIAL" (default), "OPENCV", etc.
    verbose=True                          # Optional: Set to False to suppress logs
)
```

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| **`image_path`** | **Yes** | - | Path to the folder containing raw images. |
| **`output_path`** | No | `mapping_output/` | Directory for results. Creates `sparse/0` and symlinked `images/`. |
| **`database_path`** | No | `database.db` | Optional path to an existing COLMAP database. |
| **`matcher`** | No | `exhaustive` | Matching algorithm: `exhaustive` or `sequential`. |
| **`camera_model`** | No | `SIMPLE_RADIAL` | COLMAP camera model (e.g., `PINHOLE`, `OPENCV`). |

## Gaussian Splatting (3DGS) (BETA)

VibePhysics supports loading 3D Gaussian Splatting data.
[Warning] Currently it's under development

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