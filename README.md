# VibePhysics

![VibePhysics Teaser](assets/vibephysics_teaser.png)

**A lightweight framework for turning real-world videos and images into 3D maps, Blender scenes, and physical simulations — bridging feedforward reconstruction, sparse mapping, robotics, and physics in one CPU-friendly workflow.**

**Current release:** [v0.3.7 on PyPI](https://pypi.org/project/vibephysics/0.3.7/)

---

## Changelog

- **v0.3.7** (2026-05-31) — PyPI; feedforward ground align (frame-0 camera up, 1D Hough multi-floor → bottom floor, bumpy-depth tilt); fixed-size Blender camera frustums/trajectory; point cloud icosphere instancing in blend export; `SKILL.md` ground-align docs.
- **v0.3.6** (2026-05-31) — PyPI; [DVLT](https://github.com/nv-tlabs/dvlt) feedforward (`--method dvlt`); `.vibephysics/feedforward/` weight caches; Plotly trajectory aligned with saved poses; feedforward `SKILL.md` for agents; GPU dependency fixes.
- **v0.3.5** (2026-05-31) — PyPI; feedforward stage timing/RSS; compact NPZ defaults (`min_confidence`, per-frame/global sampling); Plotly frame-balanced sampling; R3 Mac/MPS kill warning.
- **2026-05-30** — [R3](https://github.com/KevinXu02/R3) / R3-Long; unified `run_feedforward.sh` + `feedforward.yaml`; opt-in `--blend` / `--html` / `--frames`.
- **2026-05-29** — [Map-Anything](https://github.com/facebookresearch/map-anything), [VGG-TTT](https://github.com/nv-dvl/vgg-ttt).
- **2026-05-28** — [VGGT-Omega](https://github.com/facebookresearch/vggt-omega); [LingBot-Map](https://github.com/robbyant/lingbot-map) long video; Blender Z-up `predictions.npz`.
- **2026-05-27** — GLOMAP/COLMAP mapping viz; Plotly HTML export.

---

## ⚙️ Installation (macOS)

Conda + `pip install vibephysics` (latest: **0.3.7**); optional feedforward backends.

<details>
<summary>Installation steps</summary>

```bash
# 1. Create environment
conda create -n vibephysics python=3.11
conda activate vibephysics

# 2. Install core package (includes COLMAP/GLOMAP mapping & Blender simulation)
pip install "vibephysics>=0.3.7"

# 3. (Optional) Install feedforward backends from GitHub
# Or skip these — run_feedforward.sh auto-installs on first run
pip install git+https://github.com/robbyant/lingbot-map.git
pip install git+https://github.com/facebookresearch/vggt-omega.git
pip install "mapanything @ git+https://github.com/facebookresearch/map-anything.git"
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

Feedforward 3D reconstruction from video or images via LingBot-Map, VGGT-Omega, VGG-TTT, Map-Anything, R3/R3-Long, and DVLT. By default, `predictions.npz` stores a compact colored point cloud plus camera poses; dense depth/world-point tensors are opt-in.

<details>
<summary>Feedforward setup & usage</summary>

Install backends (Python 3.11 + `bpy`). Pre-install from GitHub (see Installation) or let `run_feedforward.sh` auto-install on first use. The default output is compact `predictions.npz` only (~4k points/frame); add `--frames`, `--html`, and `--blend` as needed.

Examples below build up step by step on the same base command — each step adds one thing.

```bash
pip install vibephysics bpy

# 1. Simplest — compact predictions.npz only (~4k pts/frame)
./run_feedforward.sh --method lingbot_map --input test_recording.MOV

# 2. + preprocessed RGB frames folder
./run_feedforward.sh \
  --method lingbot_map \
  --input test_recording.MOV \
  --frames

# 3. + Plotly browser viewer (uses frames/ for source-frame preview)
./run_feedforward.sh \
  --method lingbot_map \
  --input test_recording.MOV \
  --frames \
  --html

# 4. + Blender scene export
./run_feedforward.sh \
  --method lingbot_map \
  --input test_recording.MOV \
  --frames \
  --html \
  --blend

# 5. + limit frame count (quick test on a short clip)
./run_feedforward.sh \
  --method lingbot_map \
  --input test_recording.MOV \
  --max_frames 12 \
  --max_frames_mode first \
  --frames \
  --html \
  --blend

# 6. + lighter point cloud (faster HTML / smaller npz)
./run_feedforward.sh \
  --method lingbot_map \
  --input test_recording.MOV \
  --random_points_per_frame 1000 \
  --frames \
  --html

# 7. + denser compact cloud for Blender
./run_feedforward.sh \
  --method lingbot_map \
  --input test_recording.MOV \
  --random_points_per_frame 20000 \
  --compact \
  --point_scale 0.02 \
  --frames \
  --blend

# 8. Long input — spread sampling + global point cap
./run_feedforward.sh \
  --method vggt_omega \
  --input path/to/images \
  --max_frames 30 \
  --max_frames_mode spread \
  --random_points_per_frame 5000 \
  --total_random_points 120000 \
  --frames \
  --html

# 9. Dense legacy arrays — full depth/conf/world_points (not compact sampling)
./run_feedforward.sh \
  --method lingbot_map \
  --input test_recording.MOV \
  --random_points_per_frame 0 \
  --min_confidence 1.5

# 10. Alternate engine — R3 on Mac/MPS (small batch)
./run_feedforward.sh \
  --method r3 \
  --input test_recording.MOV \
  --max_frames 4 \
  --random_points_per_frame 2000 \
  --frames

# 11. Map-Anything factory method — e.g. Depth Anything 3
./run_feedforward.sh \
  --method da3 \
  --input path/to/images \
  --random_points_per_frame 6000 \
  --blend

# 12. Full custom — custom output dir, caps, all exports
./run_feedforward.sh \
  --method r3_long \
  --input test_recording.MOV \
  --output_path output/r3_long_demo \
  --max_frames 24 \
  --max_frames_mode first \
  --random_points_per_frame 4000 \
  --total_random_points 200000 \
  --frames \
  --html \
  --blend
```

Configs: `src/vibephysics/feedforward/configs/`

`feedforward.yaml` is the single feedforward config. It includes sections for all engines; `run_feedforward.sh --method ...` selects the active engine and patches runtime output flags.

**Config (`feedforward.yaml`):** one file for all engines. `run_feedforward.sh` sets `engine` from `--method` and patches `output.save_blend`, `output.save_html`, `output.save_frames`, `output.random_points_per_frame`, `output.total_random_points`, and `output.compact` from CLI flags. For R3, `--method r3` / `r3_long` also sets `r3.model`.

```yaml
engine: lingbot_map       # lingbot_map | vggt_omega | vgg_ttt | map_anything | r3 | dvlt
image_path: path/to/images
output_path: null
verbose: true

video:
  fps: 2                   # extraction rate; cached in .vibephysics_extract_fps
  quality: 2
  max_frames: null         # null = all frames; N limits count
  max_frames_mode: first   # first | spread

output:
  save_blend: null         # scene.blend path, or set by --blend
  save_html: null          # e.g. visual.html, or set by --html
  save_frames: false       # true = save model-preprocessed RGB frames
  min_confidence: 2.0
  filter_edges: true
  point_scale: 0.001
  random_points_per_frame: 4000  # per-frame random sample after confidence filter; null/0 = dense
  total_random_points: null      # optional global random cap after per-frame sampling
  compact: false           # true = force compact points + poses only
  animate: true
  animation_fps: 24
  align_ground: true       # frame-0 camera up + Hough floor peaks → bottom floor (OpenCV, pre-save)

lingbot_map:
  model: lingbot-map
  checkpoint: null
  image_size: 518
  mode: auto               # auto | streaming | batch
  keyframe_interval: null
  max_streaming_keyframes: null
  window_size: 64
  overlap_size: 16
  overlap_keyframes: null
  use_sdpa: false
  mask_sky: false

vggt_omega:
  checkpoint: null
  checkpoint_name: vggt-omega-1b-512
  resolution: 512
  preprocess_mode: balanced
  enable_alignment: false
  conf_percentile: 50.0
  depth_edge_rtol: 0.03

vgg_ttt:
  model_id: nvidia/vgg-ttt
  preprocess_mode: crop
  image_size: 518
  conf_percentile: 50.0
  depth_edge_rtol: 0.03
  num_ttt_steps: 1
  memory_efficient_inference: false

map_anything:
  model: vggt              # model_factory key; see table below
  model_kwargs: null
  install_all: false
  resolution: 518
  norm_type: identity      # vggt/pi3/moge=identity; mapanything/da3=dinov2; dust3r=dust3r
  patch_size: 14
  resize_mode: fixed_mapping # fixed_mapping | longest_side | square | fixed_size
  size: null               # required for longest_side / square / fixed_size

r3:
  checkpoint: null         # null = auto-download KevinXu02/R3
  model: r3_long           # r3 | r3_long (--method r3_long sets this)
  config_name: r3-large
  mode: local              # test | local | long | strided
  image_size: 504
  kv_backend: dense        # dense | paged (paged needs flashinfer)
  rel_pose_method: greedy  # greedy | pgo
  metric_model_name: depth-anything/DA3METRIC-LARGE
```

**Input:** folder, single image, or video (`.mov`/`.mp4`). Videos extract frames at `video.fps` into `output/<video_stem>/` and reuse cached frames on reruns.

`run_feedforward.sh` routes direct engines (`lingbot_map`, `vggt_omega`, `vgg_ttt`, `r3`, `r3_long`, `dvlt`) and Map-Anything factory model keys (`da3`, `mapanything`, `vggt`, `mast3r`, `pi3`, etc.) through one CLI. Unknown method names are treated as Map-Anything model keys so new factory methods can be tried without changing the script.

**Saved output defaults:** `predictions.npz` is compact by default because `--random_points_per_frame` defaults to `4000`, with `min_confidence: 2.0` filtering low-confidence points first. It stores `points`, `colors`, `conf`, `frame_ids`, camera `extrinsic`/`intrinsic`, `trajectory`, `engine`, and `metadata`. Filtering order is: first apply `--min_confidence`, then randomly keep up to `--random_points_per_frame K` points within each frame, then apply `--total_random_points K` globally if provided. Set `--random_points_per_frame 0` to disable per-frame random sampling and save dense legacy arrays (`depth`, `conf`, `world_points`, etc.) unless `--compact` or `--total_random_points` is set. Pass `--blend` to additionally export `scene.blend`, `--html` to export `visual.html`, and `--frames` to save the model-preprocessed RGB frames folder.

**Map-Anything model keys:**

`run_feedforward.sh --method <map-anything-key>` uses the Map-Anything unified loader and converts outputs into the same `FeedforwardPrediction` format as LingBot-Map and VGGT-Omega.

| Model key | Default preprocessing | Notes |
|-----------|-----------------------|-------|
| `mapanything` | `resolution: 518`, `norm_type: dinov2`, `patch_size: 14` | Official `facebook/map-anything` checkpoint via `MapAnything.from_pretrained()` |
| `mapanything_apache` | `518`, `dinov2`, `14` | Apache-licensed `facebook/map-anything-apache` checkpoint |
| `mapanything_ablations` | `518`, `dinov2`, `14` | Map-Anything ablation model key when available in the installed package |
| `vggt` | `518`, `identity`, `14` | Default VibePhysics Map-Anything backend |
| `moge` | `518`, `identity`, `14` | MoGe wrapper defaults to `Ruicheng/moge-vitl` |
| `pi3` | `518`, `identity`, `14` | Pi3 wrapper |
| `pi3x` | `518`, `identity`, `14` | Pi3x wrapper; auto-installs the `pi3` extra when needed |
| `dust3r` | `512`, `dust3r`, `16` | Downloads the official DUSt3R checkpoint if no `ckpt_path` is supplied |
| `mast3r` | `512`, `dust3r`, `16` | Downloads the official MASt3R checkpoint if no `ckpt_path` is supplied |
| `must3r` | `512`, `dust3r`, `16` | Downloads official MUSt3R checkpoints if paths are not supplied |
| `modular_dust3r` | `512`, `dust3r`, `16` | Modular DUSt3R key when available in the installed package |
| `pow3r` | `512`, `dust3r`, `16` | Requires `model_kwargs.ckpt_path` for the Pow3R checkpoint |
| `pow3r_ba` | `512`, `dust3r`, `16` | Pow3R with bundle adjustment; requires `model_kwargs.ckpt_path` |
| `anycalib` | `518`, `dinov2`, `14` | AnyCalib wrapper; auto-installs the `anycalib` extra when needed |
| `da3` | `504`, `dinov2`, `14` | Depth Anything 3 wrapper; auto-installs `depth-anything-3` extra when needed |

For model-specific arguments, set `map_anything.model_kwargs` in YAML. The run script auto-installs the selected model extra with `numpy<2` pinned for `bpy` compatibility; use `--install-all` to install all Map-Anything extras or `--no-install` / `VIBEPHYSICS_NO_AUTO_INSTALL=1` if you manage dependencies manually.

See [Time-sync comparison](#-time-sync-comparison-glomap-vs-feedforward) for side-by-side `.blend` export (e.g. GLOMAP vs LingBot-Map).

**Python API:**
```python
from vibephysics import feedforward

output_dir = feedforward.reconstruct_from_config(
    "src/vibephysics/feedforward/configs/feedforward.yaml",
    image_path="test_recording.MOV",
)
pred = feedforward.load_prediction(output_dir / "predictions.npz")

map_output_dir = feedforward.reconstruct_from_config(
    "src/vibephysics/feedforward/configs/feedforward.yaml",
    image_path="test_recording.MOV",
    map_anything_model="vggt",
)
```

| Engine | Best for | Frames |
|--------|----------|--------|
| **LingBot-Map** | Long video, streaming | 100–25,000+ |
| **VGGT-Omega** | High-quality batches | 10–100 |
| **VGG-TTT** | Test-time training experiments | Small batches |
| **Map-Anything** | Trying many feedforward models behind one interface | Model-dependent |
| **R3 / R3-Long** | Online/streaming relative-pose reconstruction | Long videos; use small `--max_frames` on Mac/MPS |

**Output layout:**
```
feedforward_output/{engine}_{timestamp}/
  predictions.npz          # compact points+poses by default; dense arrays if --random_points_per_frame 0
  reconstruct_config.json
  frames/                  # optional, only when --frames is passed
  visual.html              # optional, only when --html is passed
  scene.blend              # optional, only when --blend is passed
```

`predictions.npz` uses Blender Z-up (`metadata.world_coordinates: blender_z_up`). **Ground align** (`align_ground: true`, default) runs in OpenCV space **before** Z-up save: frame-0 camera pose sets rough up, **1D Hough voting** along that axis finds multiple floor heights, and the **lowest floor below the camera** is leveled (works on bumpy depth, not a flat-plane assumption). Metadata may include `ground_align_floor_count` and `ground_align_floor_heights`. Blender import does not re-align or re-axis-convert. Post-process an existing `.blend` with `run_postprocess_blend.sh --point_scale SIZE`.

Compact predictions are best when you only need a colored 3D point cloud, trajectory, and camera poses; dense mode is best when you need full per-pixel depth/confidence/world-point maps.

**Plotly HTML point cloud:**

```bash
./run_feedforward.sh --method lingbot_map --input test_recording.MOV --html

python -m vibephysics.feedforward.export plotly \
  --predictions output/feedforward_output/lingbot_map_20260528_144552/predictions.npz \
  --output output/feedforward_output/lingbot_map_20260528_144552/pointcloud_plotly.html \
  --trajectory
```

The HTML viewer renders all valid points saved in `predictions.npz`; point count is normally controlled by `random_points_per_frame` and `total_random_points` during reconstruction. For manual ad-hoc export, you can still pass `--max-points` to downsample a large existing prediction. It draws the camera trajectory as red dots connected by a red line and includes Play/Pause buttons (`1x` to `16x`) plus a frame slider. Install Plotly if needed:

```bash
pip install plotly
```

</details>

---

## 🔀 Time-sync comparison (GLOMAP vs feedforward)

![GLOMAP vs LingBot-Map comparison](assets/glomap_vs_lingbot_comparison.gif)

Side-by-side `.blend` with a **shared timeline** — scrub once, both reconstructions play in sync. Use the same input video and the same extraction fps (`video.fps: 2` in both mapping and feedforward configs).

<details>
<summary>Compare workflow</summary>

**1. Run both pipelines on the same input**

```bash
./run_glomap.sh --input test_home.mp4 --output_path mapping_output/test_home_glomap
./run_feedforward.sh --method lingbot_map --input test_home.mp4 --output_path feedforward_output/lingbot_map_test_home
```

**2. Combine into one compare `.blend`**

```bash
./run_compare_blend.sh \
  --left  mapping_output/test_home_glomap/sparse/0 \
  --right feedforward_output/lingbot_map_test_home/predictions.npz \
  --output compare_output/glomap_vs_lingbot.blend
```

Each side can be:
- `predictions.npz` (LingBot-Map, VGGT-Omega, VGG-TTT, Map-Anything, ...)
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
- **🧠 Feedforward** – LingBot-Map, VGGT-Omega, VGG-TTT, and Map-Anything.
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
./run_feedforward.sh --method lingbot_map --input test_recording.MOV
./run_feedforward.sh --method vggt --input test_recording.MOV
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
