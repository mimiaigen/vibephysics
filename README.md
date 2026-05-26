# VibePhysics

![VibePhysics Teaser](assets/vibephysics_teaser.png)

**A lightweight Blender physics simulation framework for realistic robot animations, rigid body physics, water dynamics, and annotation tools — all running efficiently on CPU.**

---

## ⚙️ Installation (macOS)

Conda + `pip install vibephysics`; optional feedforward backends.

<details>
<summary>Installation steps</summary>

```bash
# 1. Create environment
conda create -n vibephysics python=3.11
conda activate vibephysics

# 2. Install core package (includes COLMAP/GLOMAP mapping & Blender simulation)
pip install vibephysics

# 3. (Optional) Install feedforward backends from GitHub
# Or skip these — ./run_lingbot_map.sh / ./run_vggt_omega.sh auto-install on first run
pip install git+https://github.com/robbyant/lingbot-map.git
pip install git+https://github.com/facebookresearch/vggt-omega.git
```

</details>

---

## 🗺️ Sparse mapping (GLOMAP & COLMAP)

![GLOMAP Demo](assets/glomap_pointcloud_demo.gif)

Structure-from-Motion: sparse point clouds and camera poses, GSplat-ready `sparse/0` layout.

<details>
<summary>GLOMAP & COLMAP usage</summary>

### GLOMAP (global mapper)

Set `engine: glomap` in `src/vibephysics/mapping/configs/sfm.yaml`.

GLOMAP is built into COLMAP 4.0+ and runs via `pycolmap.global_mapping` (included with `pip install vibephysics`). It is typically faster than incremental COLMAP on large image sets. The global pipeline uses view-graph calibration for intrinsics, which may differ slightly from incremental self-calibration.

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

GLOMAP writes COLMAP-format output under `output/.../sparse/0/`. Visualize with the [COLMAP visualization](#colmap-visualization) steps below.

---

### COLMAP

Set `engine: colmap` in the same `sfm.yaml` (only `engine` changes).

**Command line:**
```bash
./run_glomap.sh --config src/vibephysics/mapping/configs/sfm.yaml --image_path path/to/images
```

**Python API:**
```python
from vibephysics import mapping

mapping.run_sfm_from_config("src/vibephysics/mapping/configs/sfm.yaml", image_path="path/to/images")
mapping.colmap_pipeline(image_path="path/to/images")
```

Output: `sparse/0/` with `cameras.bin`, `images.bin`, `points3D.bin`, etc.

#### COLMAP visualization {#colmap-visualization}

Load sparse reconstruction (COLMAP or GLOMAP) in Blender. Blender is **viewer only** — `sparse/0` on disk is ground truth.

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
    rotation=(-90, 0, 0),
)
```

</details>

---

## 🧠 Feedforward reconstruction

![Feedforward Comparison](assets/feedforward_comparison.gif)

Dense depth, poses, and world points from video or images via LingBot-Map and VGGT-Omega. `predictions.npz` is Z-up ground truth; Blender only visualizes it.

<details>
<summary>Feedforward setup & usage</summary>

Install backends (Python 3.11 + `bpy`). Pre-install from GitHub (see Installation) or let run scripts auto-install on first use:

```bash
pip install vibephysics bpy
./run_lingbot_map.sh --input test_recording.MOV
./run_vggt_omega.sh --input path/to/images
```

Configs: `src/vibephysics/feedforward/configs/`

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

**Output layout:**
```
feedforward_output/{engine}_{timestamp}/
  predictions.npz          # Z-up arrays (depth, conf, poses, world_points)
  reconstruct_config.json
  scene.blend              # optional viewer export
```

`predictions.npz` uses Blender Z-up (`metadata.world_coordinates: blender_z_up`). Ground align runs before save when `align_ground: true`; Blender does not re-align or re-axis-convert on load.

</details>

---

## 🎬 Simulation results

![Result Demo](assets/result_demo.gif)

Robot walking with rigid body physics, uneven ground, puddles, and annotation overlay — `sh run_robot.sh`.

<details>
<summary>Run robot simulation</summary>

```bash
sh ./run_robot.sh
sh ./run_robot.sh mounted    # POV (default)
sh ./run_robot.sh center     # overview
sh ./run_robot.sh following  # third-person
```

</details>

## 📊 Annotation tools

![Annotation Demo](assets/annotation_demo.gif)

Bounding boxes, motion trails, and point cloud tracking — `sh run_basics.sh`.

<details>
<summary>Annotation demos</summary>

```bash
sh ./run_basics.sh
```

</details>

## 🎯 Frustum culling

![Frustum Demo](assets/frustum_demo.gif)

Per-point frustum culling; in-frustum points turn red in real time — `sh run_basics.sh`.

<details>
<summary>Frustum options</summary>

```bash
sh ./run_forest.sh --frustum-mode highlight
sh ./run_forest.sh --frustum-mode frustum_only
```

</details>

## 💧 Water simulation

![Water Float Demo](assets/water_float_demo.gif)

Buoyancy, ripples, and point tracking — `sh run_water.sh`.

<details>
<summary>Water demo</summary>

```bash
sh ./run_water.sh
```

</details>

## 🐕 Go2 simulation

![Go2 Demo](assets/go2_water_sphere_demo.gif)

Unitree Go2 with water and debris — `python examples/go2/go2_waypoint_walk.py`.

<details>
<summary>Go2 commands</summary>

```bash
python examples/go2/go2_waypoint_walk.py
python examples/go2/go2_waypoint_walk.py --end-frame 150 --num-spheres 50
```

</details>

---

## ✨ Highlights

CPU-friendly physics, robots, water, annotations, sparse mapping, and dense feedforward in one package.

<details>
<summary>Feature list</summary>

- **🚀 No GPU Required** – Efficient on CPU-only machines; GPU optional for rendering.
- **🤖 Robot Simulation** – IK walking with Open Duck and Unitree Go2.
- **💧 Water Physics** – Puddles, ripples, buoyancy.
- **📊 Annotation Tools** – Bboxes, motion trails, point tracking.
- **🗺️ Sparse Mapping** – COLMAP incremental and GLOMAP global SfM (via pycolmap 4.0+).
- **🧠 Feedforward** – LingBot-Map and VGGT-Omega.
- **🔧 Developer Friendly** – Pure Python, `bpy` as a module, no GUI required.

</details>

## Requirements

Python 3.11 + `bpy`; Blender 5.0 optional for viewing `.blend` files.

<details>
<summary>Details & third-party assets</summary>

### For running simulations
- **Python 3.11** (required for `bpy`; **3.12+ not supported**)
- **bpy** (Blender as a Python module)

### For viewing results (optional)
- **Blender 5.0** – [blender.org](https://www.blender.org/download/)

> ⚠️ PyPI `bpy` 5.0 ships cp311 wheels only.

### Third-party assets
- **Open Duck**: [Open Duck Blender model](https://github.com/pollen-robotics/Open_Duck_Blender)
- **Unitree Go2**: [Unitree model dataset](https://huggingface.co/datasets/unitreerobotics/unitree_model)

</details>

## Quick start

One-liner entry points for demos and simulations.

<details>
<summary>All quick-start commands</summary>

```bash
sh ./run_basics.sh
sh ./run_robot.sh
sh ./run_forest.sh
sh ./run_water.sh
python examples/go2/go2_waypoint_walk.py
./run_lingbot_map.sh --input test_recording.MOV
./run_glomap.sh --image_path path/to/images
```

</details>

## Visualizing simulation results

Open `output/*.blend` in Blender 5.0 and press Spacebar to play.

<details>
<summary>Platform commands</summary>

```bash
open output/robot_waypoint.blend      # macOS
blender output/robot_waypoint.blend   # Linux
start output/robot_waypoint.blend    # Windows
```

</details>

## Camera system

Center, mounted, and following camera rigs; switch active camera in the Outliner.

<details>
<summary>Camera API & shell options</summary>

| Camera type | Description | Best for |
|-------------|-------------|----------|
| **Center** | Circle around scene center | Overview |
| **Mounted** | On object (e.g. robot head) | POV |
| **Following** | Tracks target | Third-person |

```python
from vibephysics.camera import CameraManager

cam_manager = CameraManager()
cam_manager.add_center_pointing('center', num_cameras=4, radius=25, height=12).create(target_location=(0, 0, 0))
cam_manager.add_object_mounted('mounted', num_cameras=4, distance=0.15).create(parent_object=robot_head, lens=10)
cam_manager.add_following('following', height=12, look_angle=60).create(target=robot_armature)
cam_manager.activate_rig('mounted', camera_index=0)
```

```bash
sh run_robot.sh mounted | center | following
```

Use the green camera icon in the Outliner or `Ctrl+Numpad 0` to switch cameras in Blender.

</details>

## Setup module

Import/export assets and initialize simulation scenes.

<details>
<summary>Setup API & formats</summary>

```python
from vibephysics import setup

setup.init_simulation(start_frame=1, end_frame=250)
setup.load_asset('robot.glb')
setup.save_blend('output/scene.blend')
```

| Import | Export |
|--------|--------|
| GLB/GLTF, FBX, PLY, OBJ, STL, DAE, USD, Blend | Blend, GLB, FBX, OBJ, PLY, STL, USD |

</details>

## Gaussian Splatting (3DGS) — BETA

Viewer for 3D Gaussian splats (under development).

<details>
<summary>3DGS viewer</summary>

```bash
sh run_3dgs_viewer.sh
```

</details>

## License

Licensed under the [Apache License, Version 2.0](LICENSE).

<details>
<summary>License & citation</summary>

Copyright 2025 MIMI AI LTD

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full text.

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
