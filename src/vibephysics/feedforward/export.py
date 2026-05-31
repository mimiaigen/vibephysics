"""Export feedforward predictions.npz to .blend (single or side-by-side compare)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def _script_argv() -> list[str]:
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1 :]
    return sys.argv[1:]


def _load_output_defaults(predictions_path: Path) -> dict:
    config_path = predictions_path.parent / "reconstruct_config.json"
    if not config_path.is_file():
        return {}
    try:
        return json.loads(config_path.read_text())
    except json.JSONDecodeError:
        return {}


def _blend_load_settings(predictions_path: Path, args: argparse.Namespace) -> dict:
    """Match reconstruct.py / export blend kwargs from reconstruct_config.json when present."""
    defaults = _load_output_defaults(predictions_path)

    animation_fps = args.animation_fps
    if animation_fps is None:
        animation_fps = int(defaults.get("animation_fps", 24))

    video_fps = args.video_fps
    if video_fps is None and defaults.get("video_fps") is not None:
        video_fps = float(defaults["video_fps"])

    min_confidence = getattr(args, "min_confidence", None)
    if min_confidence is None:
        min_confidence = defaults.get("min_confidence", 2.0)

    point_scale = args.point_scale
    if point_scale is None:
        point_scale = float(defaults.get("point_scale", 0.001))

    return {
        "min_confidence": float(min_confidence),
        "point_scale": float(point_scale),
        "animate": bool(args.animate),
        "animation_fps": int(animation_fps),
        "video_fps": video_fps,
    }


def _prepare_prediction_for_blend(
    predictions_path: Path,
    *,
    align_ground: bool,
):
    from vibephysics.feedforward.ground_align import align_prediction_ground
    from vibephysics.feedforward.schema import load_prediction

    from vibephysics.feedforward.common import convert_prediction_to_blender_zup

    prediction = load_prediction(predictions_path)
    if align_ground and not prediction.metadata.get("ground_align_applied"):
        align_prediction_ground(prediction)
    convert_prediction_to_blender_zup(prediction)
    return prediction


def export_blend(args: argparse.Namespace) -> None:
    import bpy

    from vibephysics.feedforward.visual import load_reconstruction
    from vibephysics.setup.exporter import save_blend as save_blend_file

    prediction = _prepare_prediction_for_blend(args.predictions, align_ground=args.align_ground)
    load_kwargs = _blend_load_settings(args.predictions, args)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    load_reconstruction(
        prediction,
        global_indices=prediction.metadata.get("selected_indices"),
        frame_viewports=True,
        **load_kwargs,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_blend_file(str(args.output))
    print(f"[vibephysics] Saved Blender scene to {args.output}")


def _reconstruction_kind(path: Path) -> str:
    path = path.expanduser().resolve()
    if path.is_file() and path.suffix == ".npz":
        return "npz"
    if path.is_dir() and (
        (path / "cameras.bin").exists() or (path / "cameras.txt").exists()
    ):
        return "sparse"
    raise ValueError(
        f"Unsupported reconstruction path: {path}. "
        "Provide predictions.npz or a COLMAP sparse model folder (with cameras.bin)."
    )


def _sparse_frames_dir(sparse_path: Path) -> Path | None:
    images_link = sparse_path.parent.parent / "images"
    if images_link.exists():
        return images_link.resolve()
    return None


def _load_compare_side(
    path: Path,
    *,
    side: str,
    load_kwargs: dict,
    align_ground: bool,
    point_size: float,
) -> str:
    kind = _reconstruction_kind(path)
    if kind == "npz":
        from vibephysics.feedforward.visual import ENGINE_COLLECTION_NAMES, load_reconstruction

        prediction = _prepare_prediction_for_blend(path, align_ground=align_ground)
        col_name = ENGINE_COLLECTION_NAMES.get(prediction.engine, f"{prediction.engine.upper()}_Result")
        load_reconstruction(
            prediction,
            global_indices=prediction.metadata.get("selected_indices"),
            frame_viewports=False,
            **load_kwargs,
        )
        return col_name

    from vibephysics.mapping.map_visual import load_colmap_reconstruction

    parent_name = path.parent.parent.name.lower()
    if "glomap" in parent_name:
        col_name = "GLOMAP_Result"
    elif "colmap" in parent_name:
        col_name = "COLMAP_Result"
    else:
        col_name = f"{side}_Result"
    load_colmap_reconstruction(
        str(path),
        collection_name=col_name,
        point_size=point_size,
        animate=load_kwargs.get("animate", True),
        animation_fps=load_kwargs.get("animation_fps", 24),
        video_fps=load_kwargs.get("video_fps"),
        frames_dir=_sparse_frames_dir(path),
    )
    return col_name


def export_compare_blend(args: argparse.Namespace) -> None:
    import bpy

    from vibephysics.setup.exporter import save_blend as save_blend_file
    from vibephysics.setup.viewport import setup_compare_dual_viewport

    bpy.ops.wm.read_factory_settings(use_empty=True)

    collection_names: list[str] = []
    align_ground = getattr(args, "align_ground", True)
    point_size = getattr(args, "point_size", 0.03)
    left_path, right_path = args.inputs

    for side, path in zip(("LEFT", "RIGHT"), (left_path, right_path)):
        load_kwargs = _blend_load_settings(path, args) if _reconstruction_kind(path) == "npz" else {
            "animate": bool(args.animate),
            "animation_fps": int(args.animation_fps or 24),
            "video_fps": args.video_fps,
        }
        collection_names.append(
            _load_compare_side(
                path,
                side=side,
                load_kwargs=load_kwargs,
                align_ground=align_ground,
                point_size=point_size,
            )
        )

    left_collection, right_collection = collection_names
    setup_compare_dual_viewport(left_collection, right_collection, layout=args.layout)
    bpy.context.scene.frame_set(0)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_blend_file(str(args.output))
    print(
        f"[vibephysics] Saved compare Blender scene to {args.output} "
        f"(left={left_collection}, right={right_collection}, shared timeline)"
    )


def _select_plotly_compact_indices(
    selected_idx: "np.ndarray",
    conf_all: "np.ndarray",
    max_points: int | None,
    rng: "np.random.Generator",
    frame_ids: "np.ndarray | None" = None,
) -> "np.ndarray":
    """Downsample compact points without biasing toward the first stored frames."""
    import numpy as np

    if max_points is None:
        return selected_idx
    if len(selected_idx) <= max_points:
        return selected_idx

    if frame_ids is None:
        return rng.choice(selected_idx, size=max_points, replace=False)

    selected_frame_ids = frame_ids[selected_idx]
    unique_frames = np.unique(selected_frame_ids)
    if len(unique_frames) == 0:
        return selected_idx[:max_points]

    per_frame = max(max_points // len(unique_frames), 1)
    chosen_chunks: list[np.ndarray] = []
    chosen_mask = np.zeros(len(selected_idx), dtype=bool)

    for frame in unique_frames:
        local = np.flatnonzero(selected_frame_ids == frame)
        if len(local) <= per_frame:
            keep_local = local
        else:
            order = np.argsort(conf_all[selected_idx[local]])[::-1]
            keep_local = local[order[:per_frame]]
        chosen_mask[keep_local] = True
        chosen_chunks.append(selected_idx[keep_local])

    chosen = np.concatenate(chosen_chunks) if chosen_chunks else selected_idx[:0]
    if len(chosen) < max_points:
        remaining = selected_idx[~chosen_mask]
        if len(remaining):
            fill_count = min(max_points - len(chosen), len(remaining))
            fill_order = np.argsort(conf_all[remaining])[::-1][:fill_count]
            chosen = np.concatenate([chosen, remaining[fill_order]])
    elif len(chosen) > max_points:
        order = np.argsort(conf_all[chosen])[::-1][:max_points]
        chosen = chosen[order]

    return chosen


def export_plotly(args: argparse.Namespace) -> None:
    """Export a sampled interactive Plotly point cloud from predictions.npz."""
    import numpy as np
    import plotly.graph_objects as go
    from PIL import Image

    defaults = _load_output_defaults(args.predictions)
    min_confidence = args.min_confidence
    if min_confidence is None:
        min_confidence = float(defaults.get("min_confidence", 2.0))
    video_fps = args.video_fps
    if video_fps is None:
        video_fps = float(defaults.get("video_fps") or 2.0)

    with np.load(args.predictions, allow_pickle=True) as data:
        extrinsic = data["extrinsic"]
        metadata = data["metadata"][0] if "metadata" in data.files and len(data["metadata"]) else {}
        frames_dir = args.frames_dir
        if frames_dir is None:
            frames_dir = Path(metadata.get("preprocessed_frames_dir") or (args.predictions.parent / "frames"))
        else:
            frames_dir = Path(frames_dir)
        if not frames_dir.is_absolute():
            frames_dir = args.predictions.parent / frames_dir
        frame_paths = sorted(frames_dir.glob("frame_*.jpg"))
        is_compact = "points" in data.files and "colors" in data.files
        if is_compact:
            points_all = data["points"].astype(np.float32)
            conf_all = data["conf"].reshape(-1).astype(np.float32)
            mask = (conf_all >= min_confidence) & np.isfinite(conf_all) & np.isfinite(points_all).all(axis=1)
            if not np.any(mask):
                raise ValueError(f"No finite compact points found at confidence >= {min_confidence:g}")
            selected_idx = np.flatnonzero(mask)
            frame_ids = data["frame_ids"] if "frame_ids" in data.files else None
            selected_idx = _select_plotly_compact_indices(
                selected_idx,
                conf_all,
                args.max_points,
                np.random.default_rng(args.seed),
                frame_ids=frame_ids,
            )
            points = points_all[selected_idx]
            conf_values = conf_all[selected_idx]
            colors = data["colors"][selected_idx].astype(np.uint8)
            marker_color = [f"rgb({r},{g},{b})" for r, g, b in colors]
            colorbar = None
            colorscale = None
        else:
            world_points = data["world_points"]
            confidence = data["conf"]
            num_frames, height, width = confidence.shape
            flat_points = world_points.reshape(-1, 3)
            flat_conf = confidence.reshape(-1)
            total_points = flat_conf.size

            if args.max_points is None:
                mask = (flat_conf >= min_confidence) & np.isfinite(flat_conf) & np.isfinite(flat_points).all(axis=1)
                if not np.any(mask):
                    raise ValueError(f"No finite points found at confidence >= {min_confidence:g}")
                sampled_idx = np.flatnonzero(mask)
            else:
                rng = np.random.default_rng(args.seed)
                sampled_chunks: list[np.ndarray] = []
                chunk_size = min(2_000_000, total_points)
                for _ in range(args.sample_rounds):
                    idx = rng.integers(0, total_points, size=chunk_size, endpoint=False)
                    pts = flat_points[idx]
                    conf = flat_conf[idx]
                    mask = (conf >= min_confidence) & np.isfinite(conf) & np.isfinite(pts).all(axis=1)
                    if not np.any(mask):
                        continue
                    sampled_chunks.append(idx[mask])
                    if sum(len(chunk) for chunk in sampled_chunks) >= args.max_points:
                        break
                if not sampled_chunks:
                    raise ValueError(f"No finite points found at confidence >= {min_confidence:g}")
                sampled_idx = np.concatenate(sampled_chunks)[: args.max_points]
            points = flat_points[sampled_idx].astype(np.float32)
            conf_values = flat_conf[sampled_idx].astype(np.float32)

            marker_color = conf_values
            colorbar = {"title": "confidence"}
            colorscale = "Viridis"
            if len(frame_paths) >= num_frames:
                frame_idx = sampled_idx // (height * width)
                rem = sampled_idx % (height * width)
                yy = rem // width
                xx = rem % width
                rgb_values = np.empty((len(sampled_idx), 3), dtype=np.uint8)
                for frame in np.unique(frame_idx):
                    image = Image.open(frame_paths[int(frame)]).convert("RGB")
                    if image.size != (width, height):
                        image = image.resize((width, height), Image.Resampling.BICUBIC)
                    rgb = np.asarray(image, dtype=np.uint8)
                    selected = frame_idx == frame
                    rgb_values[selected] = rgb[yy[selected], xx[selected]]
                marker_color = [f"rgb({r},{g},{b})" for r, g, b in rgb_values]
                colorbar = None
                colorscale = None

    figure_data = [
        go.Scatter3d(
            x=points[:, 0],
            y=points[:, 1],
            z=points[:, 2],
            mode="markers",
            marker={
                "size": args.point_size,
                "color": marker_color,
                "opacity": args.opacity,
                "colorbar": colorbar,
                "colorscale": colorscale,
            },
            text=[f"conf={value:.2f}" for value in conf_values],
            hovertemplate="x=%{x:.3f}<br>y=%{y:.3f}<br>z=%{z:.3f}<br>%{text}<extra></extra>",
            name="Point cloud",
        )
    ]

    trajectory_js = ""
    if args.trajectory:
        trajectory = extrinsic[:, :3, 3].astype(np.float32)
        trajectory = trajectory[np.isfinite(trajectory).all(axis=1)]
        tx, ty, tz = trajectory[:, 0], trajectory[:, 1], trajectory[:, 2]
        figure_data.extend(
            [
                go.Scatter3d(
                    x=tx,
                    y=ty,
                    z=tz,
                    mode="lines+markers",
                    line={"color": "red", "width": 5},
                    marker={"color": "red", "size": 3},
                    name="Camera trajectory",
                ),
                go.Scatter3d(
                    x=[tx[0]],
                    y=[ty[0]],
                    z=[tz[0]],
                    mode="lines+markers",
                    line={"color": "yellow", "width": 8},
                    marker={"color": "yellow", "size": 5},
                    name="Visited trajectory",
                    hoverinfo="skip",
                ),
                go.Scatter3d(
                    x=[tx[0]],
                    y=[ty[0]],
                    z=[tz[0]],
                    mode="markers",
                    marker={"color": "yellow", "size": 8, "line": {"color": "red", "width": 3}},
                    text=["frame=0"],
                    name="Current frame",
                    hovertemplate="current %{text}<br>x=%{x:.3f}<br>y=%{y:.3f}<br>z=%{z:.3f}<extra></extra>",
                ),
            ]
        )
        trajectory_js = _plotly_trajectory_controls_script(
            tx.tolist(),
            ty.tolist(),
            tz.tolist(),
            [
                os.path.relpath(path, args.output.parent).replace(os.sep, "/")
                for path in frame_paths[: len(trajectory)]
            ],
            base_duration_ms=max(int(1000 / max(video_fps, 1e-6)), 1),
        )

    fig = go.Figure(data=figure_data)

    layout = {
        "title": f"Point cloud: {len(points):,} sampled points (conf >= {min_confidence:g})",
        "scene": {"xaxis_title": "X", "yaxis_title": "Y", "zaxis_title": "Z", "aspectmode": "data"},
        "margin": {"l": 0, "r": 0, "b": 64, "t": 56},
        "template": "plotly_dark",
        "hoverlabel": {"align": "left", "bgcolor": "rgba(20,20,20,0.92)"},
    }
    fig.update_layout(**layout)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(
        args.output,
        include_plotlyjs="cdn",
        full_html=True,
        post_script=trajectory_js or None,
    )
    print(f"[vibephysics] Saved Plotly point cloud to {args.output}")


def _plotly_trajectory_controls_script(
    x: list[float],
    y: list[float],
    z: list[float],
    frame_urls: list[str],
    *,
    base_duration_ms: int,
) -> str:
    payload = {
        "x": x,
        "y": y,
        "z": z,
        "frameUrls": frame_urls,
        "baseDurationMs": base_duration_ms,
    }
    data_json = json.dumps(payload)
    return f"""
(function() {{
  const plot = document.getElementById('{{plot_id}}');
  const data = {data_json};
  const trajX = data.x;
  const trajY = data.y;
  const trajZ = data.z;
  const frameUrls = data.frameUrls || [];
  const n = trajX.length;
  let frame = 0;
  let progress = 0;
  let timer = null;
  let playing = false;
  let playStartedAt = 0;
  let playStartProgress = 0;
  let pendingRender = null;
  let renderScheduled = false;

  const controls = document.createElement('div');
  controls.style.cssText = [
    'position:absolute',
    'z-index:10',
    'left:16px',
    'bottom:16px',
    'display:flex',
    'gap:8px',
    'align-items:center',
    'flex-wrap:wrap',
    'max-width:calc(100% - 360px)',
    'background:rgba(0,0,0,0.65)',
    'color:white',
    'padding:8px 10px',
    'border-radius:6px',
    'font:13px sans-serif',
    'box-shadow:0 2px 12px rgba(0,0,0,0.35)'
  ].join(';');
  controls.innerHTML = `
    <button id="vp-play-pause" type="button">Play</button>
    <label>Speed
      <select id="vp-speed">
        <option value="1">1x</option>
        <option value="2">2x</option>
        <option value="4">4x</option>
        <option value="8">8x</option>
        <option value="16">16x</option>
      </select>
    </label>
    <label>Frame
      <input id="vp-frame" type="range" min="0" max="${{Math.max(n - 1, 0)}}" value="0" step="1" style="width:220px">
    </label>
    <span id="vp-frame-label">0.00/${{Math.max(n - 1, 0)}}</span>
  `;
  plot.parentElement.style.position = 'relative';
  plot.parentElement.appendChild(controls);

  const framePanel = document.createElement('div');
  framePanel.style.cssText = [
    'position:absolute',
    'z-index:9',
    'right:16px',
    'bottom:16px',
    'width:min(320px, 32vw)',
    'background:rgba(0,0,0,0.65)',
    'color:white',
    'padding:8px',
    'border-radius:6px',
    'font:13px sans-serif',
    'box-shadow:0 2px 12px rgba(0,0,0,0.35)',
    'display:none'
  ].join(';');
  framePanel.innerHTML = `
    <div style="margin-bottom:6px">Source frame</div>
    <img id="vp-frame-image" alt="source frame" style="display:block;width:100%;max-height:38vh;object-fit:contain;border:1px solid rgba(255,255,255,0.35);border-radius:4px;background:#111">
  `;
  plot.parentElement.appendChild(framePanel);

  const playPause = controls.querySelector('#vp-play-pause');
  const speedSelect = controls.querySelector('#vp-speed');
  const frameSlider = controls.querySelector('#vp-frame');
  const frameLabel = controls.querySelector('#vp-frame-label');
  const frameImage = framePanel.querySelector('#vp-frame-image');
  if (frameUrls.length) {{
    framePanel.style.display = 'block';
  }}

  function speedMultiplier() {{
    return Math.max(Number(speedSelect.value || 1), 1);
  }}

  function interpolateAt(value) {{
    const clamped = Math.max(0, Math.min(Number(value), n - 1));
    const lo = Math.floor(clamped);
    const hi = Math.min(lo + 1, n - 1);
    const t = clamped - lo;
    return {{
      progress: clamped,
      frame: lo,
      x: trajX[lo] + (trajX[hi] - trajX[lo]) * t,
      y: trajY[lo] + (trajY[hi] - trajY[lo]) * t,
      z: trajZ[lo] + (trajZ[hi] - trajZ[lo]) * t
    }};
  }}

  function renderProgressNow(nextProgress) {{
    const pos = interpolateAt(nextProgress);
    progress = pos.progress;
    frame = pos.frame;
    const visitedX = trajX.slice(0, frame + 1);
    const visitedY = trajY.slice(0, frame + 1);
    const visitedZ = trajZ.slice(0, frame + 1);
    if (progress > frame || frame === 0) {{
      visitedX.push(pos.x);
      visitedY.push(pos.y);
      visitedZ.push(pos.z);
    }}
    Plotly.restyle(plot, {{
      x: [visitedX, [pos.x]],
      y: [visitedY, [pos.y]],
      z: [visitedZ, [pos.z]],
      text: [null, ['frame=' + progress.toFixed(2)]]
    }}, [2, 3]);
    frameSlider.value = String(frame);
    frameLabel.textContent = progress.toFixed(2) + '/' + (n - 1);
    if (frameUrls.length) {{
      const imageFrame = Math.max(0, Math.min(Math.round(progress), frameUrls.length - 1));
      if (frameImage.getAttribute('src') !== frameUrls[imageFrame]) {{
        frameImage.setAttribute('src', frameUrls[imageFrame]);
      }}
    }}
  }}

  function renderProgress(nextProgress) {{
    pendingRender = nextProgress;
    if (renderScheduled) return;
    renderScheduled = true;
    requestAnimationFrame(function() {{
      renderScheduled = false;
      renderProgressNow(pendingRender);
    }});
  }}

  function stop() {{
    if (timer !== null) {{
      clearTimeout(timer);
      timer = null;
    }}
    playing = false;
    playPause.textContent = 'Play';
  }}

  function tick() {{
    if (!playing) return;
    const elapsed = performance.now() - playStartedAt;
    const advancedFrames = (elapsed / data.baseDurationMs) * speedMultiplier();
    const nextProgress = Math.min(playStartProgress + advancedFrames, n - 1);
    if (nextProgress !== progress) {{
      renderProgress(nextProgress);
    }}
    if (progress >= n - 1) {{
      stop();
      return;
    }}
    timer = setTimeout(tick, 16);
  }}

  function start() {{
    stop();
    playing = true;
    playPause.textContent = 'Pause';
    playStartedAt = performance.now();
    playStartProgress = progress;
    tick();
  }}

  playPause.addEventListener('click', function() {{
    if (playing) {{
      stop();
    }} else {{
      start();
    }}
  }});
  speedSelect.addEventListener('change', function() {{
    if (playing) {{
      playStartedAt = performance.now();
      playStartProgress = progress;
      tick();
    }}
  }});
  frameSlider.addEventListener('input', function() {{
    stop();
    const value = Number(frameSlider.value);
    frame = Math.max(0, Math.min(value, n - 1));
    progress = frame;
    frameLabel.textContent = frame.toFixed(2) + '/' + (n - 1);
    renderProgress(value);
  }});

  renderProgressNow(0);
}})();
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Export feedforward predictions to Blender .blend files.")
    sub = parser.add_subparsers(dest="command", required=True)

    single = sub.add_parser("blend", help="Export one predictions.npz to a .blend file")
    single.add_argument("--predictions", type=Path, required=True, help="Path to predictions.npz")
    single.add_argument("--output", type=Path, required=True, help="Output .blend path")
    single.add_argument("--min_confidence", type=float, default=None)
    single.add_argument(
        "--point_scale",
        "--point-scale",
        type=float,
        default=None,
        help="Absolute point radius for feedforward points. Defaults to reconstruct_config.json or 0.001.",
    )
    single.add_argument("--animate", action=argparse.BooleanOptionalAction, default=True)
    single.add_argument("--align-ground", action=argparse.BooleanOptionalAction, default=True)
    single.add_argument("--animation_fps", type=int, default=24)
    single.add_argument("--video_fps", type=float, default=None)

    compare = sub.add_parser(
        "compare",
        help="Combine two reconstructions into one time-synced compare .blend",
    )
    compare.add_argument(
        "--inputs",
        "--predictions",
        type=Path,
        nargs=2,
        metavar=("LEFT", "RIGHT"),
        required=True,
        dest="inputs",
        help="Left/right paths: predictions.npz and/or COLMAP sparse/0 folder",
    )
    compare.add_argument("--output", type=Path, required=True, help="Output .blend path")
    compare.add_argument(
        "--point_scale",
        "--point-scale",
        type=float,
        default=None,
        help="Absolute point radius for feedforward points. Defaults to reconstruct_config.json or 0.001.",
    )
    compare.add_argument("--point-size", type=float, default=0.03, dest="point_size")
    compare.add_argument("--animate", action=argparse.BooleanOptionalAction, default=True)
    compare.add_argument("--align-ground", action=argparse.BooleanOptionalAction, default=True)
    compare.add_argument("--animation_fps", type=int, default=None)
    compare.add_argument("--video_fps", type=float, default=None)
    compare.add_argument(
        "--layout",
        choices=("left-right", "top-down"),
        default="left-right",
        help="Compare viewport layout: side-by-side (left-right) or stacked (top-down)",
    )

    plotly = sub.add_parser("plotly", help="Export predictions.npz to an interactive Plotly HTML point cloud")
    plotly.add_argument("--predictions", type=Path, required=True, help="Path to predictions.npz")
    plotly.add_argument("--output", type=Path, required=True, help="Output .html path")
    plotly.add_argument("--min_confidence", "--min-confidence", type=float, default=None)
    plotly.add_argument(
        "--max-points",
        type=int,
        default=None,
        help="Optional manual cap for ad-hoc HTML export; default embeds all saved/valid points",
    )
    plotly.add_argument("--point-size", type=float, default=1.2)
    plotly.add_argument("--opacity", type=float, default=0.85)
    plotly.add_argument("--seed", type=int, default=42)
    plotly.add_argument("--sample-rounds", type=int, default=80)
    plotly.add_argument("--frames-dir", type=Path, default=None, help="Optional frame directory for RGB coloring")
    plotly.add_argument("--video-fps", type=float, default=None, help="Trajectory animation fps")
    plotly.add_argument("--trajectory", action=argparse.BooleanOptionalAction, default=True)

    args = parser.parse_args(_script_argv())

    if args.command == "blend":
        if not args.predictions.is_file():
            parser.error(f"Predictions file not found: {args.predictions}")
        export_blend(args)
    elif args.command == "compare":
        for path in args.inputs:
            try:
                _reconstruction_kind(path)
            except ValueError as exc:
                parser.error(str(exc))
            if not path.exists():
                parser.error(f"Input not found: {path}")
        export_compare_blend(args)
    elif args.command == "plotly":
        if not args.predictions.is_file():
            parser.error(f"Predictions file not found: {args.predictions}")
        export_plotly(args)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[ERROR] Feedforward export failed: {exc}", file=sys.stderr)
        sys.exit(1)
