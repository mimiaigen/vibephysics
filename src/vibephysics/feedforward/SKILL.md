# Feedforward reconstruction

Dense reconstruction from video, image folders, or single images. Each engine runs inference in its own package folder; shared orchestration, I/O, alignment, and export live at the feedforward root.

## Layout

```
feedforward/
  lingbot_map/__init__.py   # LingBot-Map
  vggt_omega/__init__.py    # VGGT-Omega
  vgg_ttt/__init__.py       # VGG-TTT
  map_anything/__init__.py  # Map-Anything factory (many model keys)
  r3/__init__.py            # R3
  dvlt/__init__.py          # Déjà View (DVLT) — https://github.com/nv-tlabs/dvlt

  schema.py                 # FeedforwardPrediction + predictions.npz I/O
  reconstruct.py            # orchestrator, video→frames, CLI, profiling
  config.py                 # YAML loading, FEEDFORWARD_ENGINES
  configs/feedforward.yaml  # default config (all engines)

  common.py                 # images, geometry, caches, point clouds, Blender Z-up
  deps.py                   # ensure_engine_dependencies() per engine
  ground_align.py           # ground plane align (all engines, OpenCV space)
  visual.py                 # Blender import (Z-up NPZ; no second coord pass)
  export.py                 # npz → .blend / compare / Plotly HTML
```

**Rule:** engine folders contain only that method’s inference + weight download. Do not duplicate ground align, Z-up convert, compact save, blend, or Plotly logic in engine code.

## Weight and cache paths (`.vibephysics`)

All engines store weights under the repo (or override), not in arbitrary `~/.cache` defaults:

| Helper | Path |
|--------|------|
| `feedforward_cache_root()` | `{repo}/.vibephysics/feedforward` (or `VIBEPHYSICS_FEEDFORWARD_CACHE`) |
| `feedforward_engine_dir("<engine>")` | `.vibephysics/feedforward/<engine>/` — per-engine `.pt`, `checkpoints/`, clones |
| `feedforward_hf_hub_cache()` | `.vibephysics/feedforward/huggingface/hub/` — shared HF snapshots (R3, VGGT-Omega, Map-Anything, …) |
| `feedforward_torch_hub_cache("<engine>")` | `.vibephysics/feedforward/<engine>/torch_hub/` — `torch.hub` checkouts (e.g. DINOv2) |

**New engine checklist for caches:**

1. `DEFAULT_CACHE = feedforward_engine_dir("my_engine")` in `my_engine/__init__.py`.
2. Download checkpoints into `DEFAULT_CACHE` (or `DEFAULT_CACHE / "checkpoints"`).
3. For Hugging Face: set `cache_dir` / `HF_HOME` / `HUGGINGFACE_HUB_CACHE` via `feedforward_hf_hub_cache()` (see `map_anything._map_anything_weight_cache`, `vggt_omega._hf_hub_download`, `r3`).
4. For `torch.hub`: call `feedforward_torch_hub_cache("my_engine")` and `torch.hub.set_dir(...)` inside a context manager during load.
5. Register pip/git deps in `deps.py` (`_PYPI_DEPS`, `_ENGINE_GIT`, `ensure_engine_dependencies`).

Never hard-code `~/.cache/huggingface` or system torch hub paths in a new engine.

## Unified CLI (`run_feedforward.sh`)

Preferred entry point. Sources `feedforward_run.inc.sh` for shared frame/plan helpers.

```bash
./run_feedforward.sh --method lingbot_map --input path/to/video.MOV
./run_feedforward.sh --method vggt_omega --input path/to/images
./run_feedforward.sh --method vgg_ttt --input path/to/images
./run_feedforward.sh --method r3_long --input path/to/video.MOV
./run_feedforward.sh --method mapanything --input path/to/images --blend --html
./run_feedforward.sh --method da3 --input path/to/images   # Map-Anything factory key
./run_feedforward.sh --method dvlt --input path/to/video.MOV --html
```

**What the shell script does:**

1. Normalizes `--method` → `engine` (`lingbot_map`, `vggt_omega`, `vgg_ttt`, `r3`, `dvlt`, `map_anything`). Aliases: `deja_view`, `dejaview` → `dvlt`.
2. Unknown method names → `engine=map_anything` with `--model` set to that name (forward-compatible factory keys).
3. Resolves Python 3.11 + `bpy` + `numpy<2`; sets `PYTHONPATH="${repo}/src"`.
4. Builds a temp YAML from `configs/feedforward.yaml` (`save_blend`, `save_html`, `compact`, R3 model, …).
5. Calls `ensure_dependencies()` on the engine module (unless `VIBEPHYSICS_NO_AUTO_INSTALL=1` / `--no-install`).
6. Prints frame plan via `feedforward_print_frame_plan` in `feedforward_run.inc.sh` (`preview_feedforward_input_plan`).
7. Runs `python -m vibephysics.feedforward.reconstruct --config <tmp> ...` with forwarded args (`--input`, `--max_frames`, `--point_scale`, …).

**`feedforward_run.inc.sh` helpers:** `feedforward_parse_frame_args`, `feedforward_append_frame_args`, `feedforward_print_frame_plan` — reuse these if you add another top-level runner; do not fork duplicate plan-preview logic.

**Direct Python (same pipeline, no shell):**

```bash
export PYTHONPATH=src
python -m vibephysics.feedforward.reconstruct --config src/vibephysics/feedforward/configs/feedforward.yaml --input ...
python -m vibephysics.feedforward.export blend --predictions out/predictions.npz --output scene.blend
python -m vibephysics.feedforward.export plotly --predictions out/predictions.npz --output visual.html
```

## Input

- `.mp4`, `.mov`, image folder, or single image (`reconstruct.py` extracts frames from video)
- Video FPS from config (`video.fps`); written beside frames as `.vibephysics_extract_fps` for animation

## Output (per run)

Default directory (when `output_path` is null):

```
{input_parent}/feedforward_output/{engine}_{timestamp}/
  predictions.npz
  reconstruct_config.json
  frames/              # optional (save_frames)
  scene.blend          # optional (--blend / output.save_blend)
  visual.html          # optional (--html / output.save_html)
```

## Canonical layer

All engines return `FeedforwardPrediction` → saved as `predictions.npz`:

- Dense: `world_points`, `depth`, `conf`, `extrinsic`, `intrinsic`, `image_paths`
- Compact (optional): `points`, `colors`, `conf`, `frame_ids` — fewer points for blend/HTML
- Saved layout: Blender Z-up (`metadata.world_coordinates: blender_z_up`); engines infer in OpenCV first
- Metadata: `ground_align_applied`, `w2c_as_camera_pose` (per-engine; see below), `extrinsic_is_matrix_world`, `preprocessed_frames_dir`, `video_fps`

## Coordinates, extrinsics, and Plotly (do not break)

Saved `predictions.npz` is the single source of truth for blend, Plotly, and compare. **Do not add a second coordinate pass in `export.py`** (no `plotly_points_in_scene_space`, no `camera_trajectory_positions`, no OpenCV→Blender helpers in the Plotly path). Plotly must keep reading arrays exactly as written at save time.

### Save-time Z-up (`convert_prediction_to_blender_zup`)

Runs once in `reconstruct.py` before `save_prediction` / `save_compact_prediction`. It converts `world_points` and `extrinsic` together and sets `metadata.world_coordinates = blender_z_up` and `metadata.extrinsic_is_matrix_world = true`.

`extrinsic[:, :3, 3]` after save is the camera path Plotly plots. It must stay consistent with `world_points` / compact `points` from the same convert.

### `w2c_as_camera_pose` (easy to break Plotly)

`common.convert_prediction_to_blender_zup` uses this flag when building Blender `matrix_world` from each 3×4 `extrinsic` row:

| `w2c_as_camera_pose` | `convert_prediction_to_blender_zup` uses |
|----------------------|------------------------------------------|
| `true` | the stored 3×4 matrix as the pose (no `inv`) |
| `false` | `inv(stored 3×4)` as c2w, then Z-up |

**LingBot-Map:** `FeedforwardPrediction.extrinsic` is built with `c2w_to_w2c(...)`, but metadata must stay **`w2c_as_camera_pose: true`**. Do not set it to `false` because the local variable is named `extrinsic_w2c` — that “fix” changes the saved trajectory and misaligns Plotly from the point cloud. Other engines: set the flag to match how their 3×4 rows are defined; grep existing engines before changing.

### Plotly contract (`export.export_plotly`)

- Points: `points` (compact) or sampled `world_points` — **no transform in export**
- Trajectory: `extrinsic[:, :3, 3]` — **no transform in export**
- Do not re-run `convert_prediction_to_blender_zup` inside Plotly export

Blend CLI may load NPZ and call convert only for legacy OpenCV files (`export._prepare_prediction_for_blend`); that path must not be copied into Plotly.

### If trajectory looks wrong

1. Check whether `w2c_as_camera_pose` (or engine extrinsic layout) changed — **re-run reconstruction**; old NPZ keep the old transform.
2. Confirm Plotly still uses `extrinsic[:, :3, 3]` only — not a new helper.
3. Confirm Z-up still runs once before save, not twice on the same arrays.

## Pipeline (`reconstruct.py`)

1. **Engine** — upstream model → `FeedforwardPrediction` (OpenCV world)
2. **Ground align** (`ground_align.py`) — if `align_ground: true`, still in OpenCV
3. **Z-up** (`common.convert_prediction_to_blender_zup`) — in place before save
4. **Save** — `predictions.npz` (+ optional compact), `reconstruct_config.json`
5. **Plotly** (`export.export_plotly` via `_export_plotly_html`) — reads NPZ as saved (see **Coordinates, extrinsics, and Plotly**)
6. **Blend** (`visual.load_reconstruction`) — Z-up NPZ; optional ground align only when exporting blend from CLI with `--align-ground`

Legacy NPZ without `world_coordinates` are still treated as OpenCV at load/visual time.

## Engines (`config.FEEDFORWARD_ENGINES`)

`lingbot_map`, `vggt_omega`, `vgg_ttt`, `map_anything`, `r3`, `dvlt`

**DVLT** ([nv-tlabs/dvlt](https://github.com/nv-tlabs/dvlt)): recurrent multi-view model; default checkpoint `nvidia/dvlt` on Hugging Face (NVIDIA license on weights). Installed with `pip install --no-deps` + a numpy&lt;2 runtime (see `deps.install_dvlt_from_git`) so it coexists with `bpy`. Outputs OpenCV c2w → stored as w2c with `w2c_as_camera_pose: false`. CUDA strongly recommended.

Map-Anything: one engine module; `map_anything.model` / `--model` selects factory keys (`vggt`, `da3`, `pi3`, …). Extra pip specs live in `deps.MAP_ANYTHING_EXTRA_SPECS`.

## Adding an engine

1. **`feedforward/my_engine/__init__.py`**
   - `is_available()`, `ensure_dependencies()` → `deps.ensure_engine_dependencies("my_engine")`
   - `run_...(...) -> FeedforwardPrediction`
   - `DEFAULT_CACHE = feedforward_engine_dir("my_engine")`; downloads/HF/torch.hub as above

2. **`deps.py`** — add `_PYPI_DEPS`, `_ENGINE_MODULES`, `_ENGINE_GIT` entries; wire `ensure_engine_dependencies`

3. **`config.py`** — append to `FEEDFORWARD_ENGINES`

4. **`configs/feedforward.yaml`** — new top-level `my_engine:` section with defaults

5. **`reconstruct.py`** — branch in engine dispatch + `_engine_available` / `_ensure_engine` / install hint

6. **`run_feedforward.sh`** — `case` arm for `--method` alias → `engine=my_engine`; dependency block before reconstruct (mirror existing engines)

7. **Do not duplicate** ground align, `convert_prediction_to_blender_zup`, compact/dense save, blend, or Plotly in the engine folder

8. **Set `w2c_as_camera_pose` correctly** for how your engine’s `extrinsic` rows must be interpreted by `convert_prediction_to_blender_zup` (see **Coordinates, extrinsics, and Plotly**). Wrong flag → wrong saved trajectory vs points. **Do not copy LingBot’s `true` flag to other engines** unless their 3×4 rows use the same convention.

9. **DVLT pattern:** `feedforward/dvlt/__init__.py` → `run_dvlt()` using upstream `DVLT` + `preprocess_images`; HF weights via `feedforward_hf_hub_cache()`; git install via `deps.ensure_dvlt_package()` (no upstream `[all]` extra).

Optional: extend `common.engine_preview_label` / `preview_feedforward_input_plan` if the engine needs a custom frame-plan line in `feedforward_print_frame_plan`.
