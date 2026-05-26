# VibePhysics

![VibePhysics Teaser](assets/vibephysics_teaser.png)

**A lightweight Blender physics simulation framework for realistic robot animations, rigid body physics, water dynamics, and annotation tools — all running efficiently on CPU.**

<details>
<summary><strong>⚙️ Installation (macOS)</strong></summary>

```bash
# 1. Create environment
conda create -n vibephysics python=3.11
conda activate vibephysics

# 2. Install core package (includes COLMAP mapping & Blender simulation)
pip install vibephysics

# 3. (Optional) Install GLOMAP backend
# Linux users: refer to "Linux System Dependencies" below first
pip install git+https://github.com/shamangary/glomap.git

# 4. (Optional) Install feedforward backends from GitHub
# Or skip these — ./run_lingbot_map.sh / ./run_vggt_omega.sh auto-install on first run
pip install git+https://github.com/robbyant/lingbot-map.git
pip install git+https://github.com/facebookresearch/vggt-omega.git
```

</details>

<details>
<summary><strong>🐧 Linux (Ubuntu) System Dependencies</strong></summary>

If you are on Linux and want to use the **GLOMAP** or **COLMAP** backends, install these C++ development libraries before building:

```bash
sudo apt-get update
sudo apt-get install -y \
    libeigen3-dev \
    libceres-dev \
    libgoogle-glog-dev \
    libboost-all-dev \
    libsuitesparse-dev \
    libsqlite3-dev \
    libgflags-dev \
    libfreeimage-dev \
    libmetis-dev
```

</details>

<details>
<summary><strong>⚠️ Troubleshooting (Linker Errors)</strong></summary>

If you are using **Anaconda** on Linux and see an error like `relocation R_X86_64_TPOFF32 ... can not be used when making a shared object`, it is due to a conflict with the Anaconda linker. Fix it by forcing the compiler to use the global-dynamic TLS model:

```bash
export CXXFLAGS="$CXXFLAGS -fPIC -ftls-model=global-dynamic"
export CFLAGS="$CFLAGS -fPIC"
pip install git+https://github.com/shamangary/glomap.git
```

</details>

<details>
<summary><strong>🗺️ Mapping & Reconstruction</strong></summary>

Convert image sequences into 3D reconstructions with sparse SfM (GLOMAP/COLMAP) or dense feedforward models.

![GLOMAP Demo](assets/glomap_pointcloud_demo.gif)

- **GLOMAP** – Global SfM, 1–2 orders of magnitude faster than incremental COLMAP.
- **COLMAP** – Industry-standard incremental SfM.
- **Feedforward** – Dense reconstruction via [LingBot-Map](https://github.com/robbyant/lingbot-map) and [VGGT-Omega](https://github.com/facebookresearch/vggt-omega).
- **GSplat ready** – GLOMAP/COLMAP outputs use standard `sparse/0` + `images/` layout for 3D Gaussian Splatting.

---

### GLOMAP

Set `engine: glomap` in `src/vibephysics/mapping/configs/sfm.yaml`.

**Config:**
```yaml
engine: glomap
image_path: path/to/images
output_path: null
matcher: exhaustive
camera_model: SIMPLE_RADIAL
verbose: true
```

**Command line:**
```bash
./run_glomap.sh --image_path path/to/images
./run_glomap.sh --config my_sfm.yaml --image_path path/to/images
```

**Python API:**
```python
from vibephysics import mapping

mapping.run_sfm_from_config("src/vibephysics/mapping/configs/sfm.yaml", image_path="path/to/images")
mapping.glomap_pipeline(image_path="path/to/images")
```

GLOMAP writes a COLMAP-format sparse model under `output/.../sparse/0/`. Use the [COLMAP visualization](#colmap-visualization) steps below to inspect it in Blender.

---

### COLMAP

Set `engine: colmap` in `src/vibephysics/mapping/configs/sfm.yaml` (same fields as GLOMAP; only `engine` changes).

**Command line:**
```bash
./run_glomap.sh --config src/vibephysics/mapping/configs/sfm.yaml --image_path path/to/images
# with engine: colmap in the yaml
```

**Python API:**
```python
from vibephysics import mapping

mapping.run_sfm_from_config("src/vibephysics/mapping/configs/sfm.yaml", image_path="path/to/images")
mapping.colmap_pipeline(image_path="path/to/images")
```

Output layout matches standard COLMAP: `sparse/0/` with `cameras.bin`, `images.bin`, `points3D.bin`, etc.

#### COLMAP visualization {#colmap-visualization}

Load a sparse reconstruction (COLMAP or GLOMAP output) into Blender as a colored point cloud with camera frustums. Blender is a **viewer only** — the sparse folder on disk is the source of truth.

**Command line:**
```bash
./run_glomap_visual.sh --sparse path/to/sparse/0 --output result.blend
```

**Python API:**
```python
from vibephysics import mapping

mapping.load_colmap_reconstruction(
    input_path="output/mapping_output/sparse/0",
    point_size=0.03,
    rotation=(-90, 0, 0),  # optional global rotation on import
)
```

---

### Dense feedforward reconstruction

![Feedforward Comparison](assets/feedforward_comparison.gif)

Install feedforward backends (Python 3.11 + `bpy`). Pre-install from GitHub (see Installation) or let run scripts auto-install on first use:

```bash
pip install vibephysics bpy
./run_lingbot_map.sh --input test_recording.MOV
./run_vggt_omega.sh --input path/to/images
```

Per-engine configs: `src/vibephysics/feedforward/configs/`

| Config | Engine | Notes |
|--------|--------|-------|
| `feedforward.yaml` | `lingbot_map` (default) | Generic template |
| `feedforward_lingbot_map.yaml` | `lingbot_map` | Demo defaults (`min_confidence: 1.5`) |
| `feedforward_vggt_omega.yaml` | `vggt_omega` | Requires [gated HF access](https://huggingface.co/facebook/VGGT-Omega) |

**Config (`feedforward.yaml`):**
```yaml
engine: lingbot_map       # lingbot_map | vggt_omega
image_path: path/to/images
output_path: null

video:
  fps: 2
  max_frames: null
  max_frames_mode: first   # first | spread

output:
  save_blend: scene.blend
  min_confidence: 0.5
  align_ground: true
  animate: true
  animation_fps: 24

lingbot_map:
  model: lingbot-map
  image_size: 518
  mode: auto
  window_size: 64
  overlap_size: 16

vggt_omega:
  checkpoint_name: vggt-omega-1b-512
  resolution: 512
  conf_percentile: 50.0
```

**Input:** folder, single image, or video (`.mov`/`.mp4`). Videos extract frames at `video.fps` into `output/<video_stem>/` and reuse cached frames on reruns.

**Command line:**
```bash
./run_lingbot_map.sh --input test_recording.MOV
./run_vggt_omega.sh --input path/to/images

./run_compare_blend.sh \
  --left  feedforward_output/vggt_omega_test/predictions.npz \
  --right feedforward_output/lingbot_map_test/predictions.npz \
  --output feedforward_output/compare.blend
```

**Python API:**
```python
from vibephysics import feedforward

output_dir = feedforward.reconstruct_from_config(
    "src/vibephysics/feedforward/configs/feedforward_lingbot_map.yaml",
    image_path="test_recording.MOV",
)
pred = feedforward.load_prediction(output_dir / "predictions.npz")
```

| Engine | Best for | Frames |
|--------|----------|--------|
| **LingBot-Map** | Long video, streaming | 100–25,000+ |
| **VGGT-Omega** | High-quality batches | 10–100 |
| **GLOMAP/COLMAP** | Sparse SfM, GSplat | any |

**Output layout:**
```
feedforward_output/{engine}_{timestamp}/
  predictions.npz          # canonical Z-up arrays (depth, conf, poses, world_points)
  reconstruct_config.json
  scene.blend              # optional viewer export
```

`predictions.npz` is ground truth: Blender Z-up coordinates (`metadata.world_coordinates: blender_z_up`), ground-aligned when `align_ground: true`. Blender import does not re-run alignment or axis conversion on new NPZ files.

</details>

<details>
<summary><strong>🎬 Simulation Results</strong> — <code>sh run_robot.sh</code></summary>

![Result Demo](assets/result_demo.gif)

Robot walking with rigid body physics, uneven ground, puddles, and annotation overlay.

</details>

<details>
<summary><strong>📊 Annotation Tools Demo</strong> — <code>sh run_basics.sh</code></summary>

![Annotation Demo](assets/annotation_demo.gif)

Bounding boxes, motion trails, and point cloud tracking for vision datasets.

</details>

<details>
<summary><strong>🎯 Dynamic Frustum Culling Demo</strong> — <code>sh run_basics.sh</code></summary>

![Frustum Demo](assets/frustum_demo.gif)

Per-point frustum culling with a mounted camera; in-frustum points turn red in real time.

</details>

<details>
<summary><strong>💧 Water Simulation Demo</strong> — <code>sh run_water.sh</code></summary>

![Water Float Demo](assets/water_float_demo.gif)

Water physics with buoyancy, ripples, and point cloud tracking.

</details>

<details>
<summary><strong>🐕 Go2 Simulation Demo</strong> — <code>python examples/go2/go2_waypoint_walk.py</code></summary>

![Go2 Demo](assets/go2_water_sphere_demo.gif)

Unitree Go2 walking with water puddles and falling debris.

</details>

<details>
<summary><strong>✨ Highlights</strong></summary>

- **🚀 No GPU Required** – Efficient on CPU-only machines; GPU optional for rendering.
- **🤖 Robot Simulation** – IK walking with Open Duck and Unitree Go2.
- **💧 Water Physics** – Puddles, ripples, buoyancy.
- **📊 Annotation Tools** – Bboxes, motion trails, point tracking.
- **🗺️ SfM Mapping** – COLMAP and GLOMAP sparse reconstruction.
- **🧠 Feedforward** – LingBot-Map and VGGT-Omega dense reconstruction.
- **🔧 Developer Friendly** – Pure Python, `bpy` as a module, no GUI required.

Perfect for researchers, animators, and robotics engineers who need physics without dedicated GPU hardware.

</details>

<details>
<summary><strong>Requirements</strong></summary>

### For running simulations
- **Python 3.11** (required for `bpy`; **3.12+ not supported**)
- **bpy** (Blender as a Python module)

### For viewing results (optional)
- **Blender 5.0** – [blender.org](https://www.blender.org/download/)
- Only needed to open generated `.blend` files; not required to run simulations

> ⚠️ PyPI `bpy` 5.0 ships cp311 wheels only.

### Third-party assets
- **Open Duck**: [Open Duck Blender model](https://github.com/pollen-robotics/Open_Duck_Blender) (demo only; see upstream license).
- **Unitree Go2**: [Unitree model dataset](https://huggingface.co/datasets/unitreerobotics/unitree_model) (auto-downloaded for Go2 examples).

</details>

<details>
<summary><strong>Quick Start</strong></summary>

```bash
# Annotation demos (bbox, trails, tracking, frustum culling)
sh ./run_basics.sh

# Open Duck robot simulation
sh ./run_robot.sh
sh ./run_robot.sh mounted    # POV (default)
sh ./run_robot.sh center     # overview
sh ./run_robot.sh following  # third-person

# Unitree Go2
python examples/go2/go2_waypoint_walk.py
python examples/go2/go2_waypoint_walk.py --end-frame 150 --num-spheres 50

# Forest walk
sh ./run_forest.sh
sh ./run_forest.sh --frustum-mode highlight
sh ./run_forest.sh --no-physics

# Water
sh ./run_water.sh
```

</details>

<details>
<summary><strong>Visualizing simulation results</strong></summary>

Simulations write `.blend` files under `output/`.

**Download Blender 5.0** (free): [blender.org/download](https://www.blender.org/download/)

**Open results:**
```bash
# macOS
open output/robot_waypoint.blend

# Linux
blender output/robot_waypoint.blend

# Windows
start output/robot_waypoint.blend
```

Press **Spacebar** in Blender to play the animation.

</details>

<details>
<summary><strong>Camera system</strong></summary>

| Camera type | Description | Best for |
|-------------|-------------|----------|
| **Center** | Cameras in a circle, looking at scene center | Overview, multi-angle |
| **Mounted** | Cameras on an object (e.g. robot head) | First-person POV |
| **Following** | Camera tracks a target | Third-person |

```python
from vibephysics.camera import CameraManager

cam_manager = CameraManager()
center_rig = cam_manager.add_center_pointing('center', num_cameras=4, radius=25, height=12)
center_rig.create(target_location=(0, 0, 0))

mounted_rig = cam_manager.add_object_mounted('mounted', num_cameras=4, distance=0.15)
mounted_rig.create(parent_object=robot_head, lens=10)

follow_rig = cam_manager.add_following('following', height=12, look_angle=60)
follow_rig.create(target=robot_armature)

cam_manager.activate_rig('mounted', camera_index=0)
```

**Shell:**
```bash
sh run_robot.sh mounted
sh run_robot.sh center
sh run_robot.sh following
```

**Switch cameras in Blender:** all rigs exist in every `.blend`; use the green camera icon in the Outliner or `Ctrl+Numpad 0` on the selected camera.

</details>

<details>
<summary><strong>Setup module</strong></summary>

Scene initialization, import/export, and viewport helpers:

```python
from vibephysics import setup

setup.init_simulation(start_frame=1, end_frame=250)
setup.load_asset('robot.glb')
setup.save_blend('output/scene.blend')

from vibephysics.setup import importer, exporter
objects = importer.load_glb('model.glb', transform={'scale': 0.5})
exporter.export_fbx('output.fbx', selected_only=True)
```

| Import | Export |
|--------|--------|
| GLB/GLTF | Blend |
| FBX | GLB/GLTF |
| PLY | FBX |
| OBJ | OBJ |
| STL | PLY |
| DAE | STL |
| USD/USDA/USDC | USD |
| Blend (append) | |

</details>

<details>
<summary><strong>Gaussian Splatting (3DGS) — BETA</strong></summary>

3D Gaussian Splatting viewer support (under development):

```bash
sh run_3dgs_viewer.sh
```

</details>

<details>
<summary><strong>License</strong></summary>

**© 2025 MIMI AI LTD, UK. All rights reserved.**

### Academic & student use (free)
Free for students, academic research, and education.

### Commercial use
Contact: **tsunyi@mimiaigen.com**

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

</details>
