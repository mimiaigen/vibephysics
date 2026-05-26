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

## 🗺️ Sparse mapping

![GLOMAP Demo](assets/glomap_pointcloud_demo.gif)

Sparse point clouds and camera poses in GSplat-ready `sparse/0/` layout. Built on `pycolmap` 4.0+ (GLOMAP global mapper is integrated into COLMAP).

<details>
<summary>Usage</summary>

**Python API** (video, image folder, or single image):

```python
from vibephysics import mapping

# GLOMAP — fast global mapper (default)
mapping.glomap_pipeline("test_home.mp4", output_path="mapping_output/test_home_glomap", matcher="sequential")

# COLMAP — incremental mapper
mapping.colmap_pipeline("path/to/images")
```

**CLI** (reads `src/vibephysics/mapping/configs/sfm.yaml`, saves animated `visualize.blend` by default):

```bash
./run_glomap.sh --input test_home.mp4 --output_path mapping_output/test_home_glomap
./run_glomap.sh --input test_home.mp4 --no-blend          # sparse only
./run_glomap.sh --input test_home.mp4 --no-animate        # static .blend
```

Press Spacebar in Blender to play the camera path animation (same style as feedforward `.blend` files).

Set `engine: glomap` or `engine: colmap` in the YAML. Use `matcher: sequential` for videos.

**Visualize separately** (if you used `--no-blend`):

```bash
bash run_glomap_visual.sh --sparse mapping_output/test_home_glomap/sparse/0 --output result.blend
```

```python
mapping.load_colmap_reconstruction("mapping_output/test_home_glomap/sparse/0", point_size=0.03, rotation=(-90, 0, 0))
```

Output: `sparse/0/` plus `visualize.blend` (unless `--no-blend`).

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
```

See [Time-sync comparison](#-time-sync-comparison-glomap-vs-feedforward) for side-by-side `.blend` export (e.g. GLOMAP vs LingBot-Map).

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

## 🔀 Time-sync comparison (GLOMAP vs feedforward)

Side-by-side `.blend` with a **shared timeline** — scrub once, both reconstructions play in sync. Use the same input video and the same extraction fps (`video.fps: 2` in both mapping and feedforward configs).

<details>
<summary>Compare workflow</summary>

**1. Run both pipelines on the same input**

```bash
./run_glomap.sh --input test_home.mp4 --output_path mapping_output/test_home_glomap
./run_lingbot_map.sh --input test_home.mp4 --output_path feedforward_output/lingbot_map_test_home
```

**2. Combine into one compare `.blend`**

```bash
./run_compare_blend.sh \
  --left  mapping_output/test_home_glomap/sparse/0 \
  --right feedforward_output/lingbot_map_test_home/predictions.npz \
  --output compare_output/glomap_vs_lingbot.blend
```

Each side can be:
- `predictions.npz` (LingBot-Map, VGGT-Omega, …)
- `sparse/0/` folder from GLOMAP/COLMAP mapping

**3. View in Blender**

Open the compare `.blend` — split viewport (left vs right), shared timeline. Press **Spacebar** to play both animations together.

**Feedforward vs feedforward** works the same way:

```bash
./run_compare_blend.sh \
  --left  feedforward_output/vggt_omega_test/predictions.npz \
  --right feedforward_output/lingbot_map_test/predictions.npz \
  --output compare_output/vggt_vs_lingbot.blend
```

**Python API:**

```python
python -m vibephysics.feedforward.export compare \
  --inputs mapping_output/test_home_glomap/sparse/0 \
           feedforward_output/lingbot_map_test_home/predictions.npz \
  --output compare_output/glomap_vs_lingbot.blend \
  --video_fps 2
```

**Timing notes**
- Both sides use the same animation model: duration ≈ `(num_frames - 1) / video_fps`
- For a fair comparison, use the **same video** and **same `video.fps`** when extracting frames
- GLOMAP may register fewer cameras than extracted frames → its animation can be shorter than the source video

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
- **🗺️ Sparse Mapping** – GLOMAP global and COLMAP incremental SfM via pycolmap 4.0+.
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
