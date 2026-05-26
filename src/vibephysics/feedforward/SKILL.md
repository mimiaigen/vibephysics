# Feedforward reconstruction

Dense reconstruction from video, image folders, or single images. Each engine runs inference in its own folder; everything else is shared.

## Layout

```
feedforward/
  lingbot_map/__init__.py   # LingBot-Map only (pip package + checkpoint, → FeedforwardPrediction)
  vggt_omega/__init__.py    # VGGT-Omega only (pip package + checkpoint, → FeedforwardPrediction)

  schema.py                 # FeedforwardPrediction + predictions.npz I/O
  reconstruct.py            # orchestrator, video→frames I/O, CLI, run profiling
  config.py                 # YAML loading
  configs/                  # feedforward*.yaml per engine

  common.py                 # images, geometry, point cloud collection, confidence filtering
  ground_align.py           # ground plane align (single path, all engines)
  visual.py                 # Blender import (no align — data already in npz)
  export.py                 # npz → .blend (single or compare subcommands)
```

**Rule:** engine folders contain only that method’s inference code. Shared steps live at the feedforward root.

## Input

- `.mp4`, `.mov`, image folder, or single image (`reconstruct.py` extracts frames from video)

## Output (per run)

```
feedforward_output/{engine}_{timestamp}/
  predictions.npz          # canonical arrays (aligned if align_ground: true)
  reconstruct_config.json
  scene.blend               # optional
```

## Canonical layer

All engines produce `FeedforwardPrediction` → saved as `predictions.npz`:

- `world_points`, `depth`, `conf`, `extrinsic`, `intrinsic`, `image_paths`
- Saved NPZ uses Blender Z-up (`world_coordinates: blender_z_up`); engines infer in OpenCV, then convert before save
- Metadata flags: `ground_align_applied`, `w2c_as_camera_pose` (LingBot), `extrinsic_is_matrix_world`

## Pipeline

1. **Engine** (`lingbot_map/` or `vggt_omega/`) — run upstream model → `FeedforwardPrediction` (OpenCV)
2. **Ground align** (`ground_align.py`) — if enabled, mutates arrays in OpenCV
3. **Z-up convert** (`common.convert_prediction_to_blender_zup`) — world_points + extrinsic → Blender coords
4. **Save** — `predictions.npz`, optional `.blend` via `visual.py` (viewer only; no coord convert on Z-up NPZ)

Legacy NPZ without `world_coordinates` still get OpenCV→Blender at load time.

## Commands

```bash
./run_lingbot_map.sh --input path/to/video.MOV
./run_vggt_omega.sh --input path/to/images
./run_reconstruct.sh --config src/vibephysics/feedforward/configs/feedforward.yaml --input ...
./run_compare_blend.sh --left a/predictions.npz --right b/predictions.npz

python -m vibephysics.feedforward.reconstruct --config ... --input ...
python -m vibephysics.feedforward.export blend --predictions out/predictions.npz --output scene.blend
python -m vibephysics.feedforward.export compare --predictions left.npz right.npz --output compare.blend
```

## Adding an engine

1. Add `feedforward/my_engine/__init__.py` with `is_available()` and `run_my_engine(...) -> FeedforwardPrediction`
2. Register in `config.py` `FEEDFORWARD_ENGINES` and YAML config section
3. Wire in `reconstruct.py` — do not duplicate ground align, points, or visual logic in the engine folder
