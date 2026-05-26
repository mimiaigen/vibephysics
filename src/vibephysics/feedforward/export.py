"""Export feedforward predictions.npz to .blend (single or side-by-side compare)."""

from __future__ import annotations

import argparse
import json
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
        min_confidence = defaults.get("min_confidence", 0.5)

    point_scale = args.point_scale
    if point_scale == 1.0 and defaults.get("point_scale") is not None:
        point_scale = float(defaults["point_scale"])

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
    setup_compare_dual_viewport(left_collection, right_collection)
    bpy.context.scene.frame_set(0)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_blend_file(str(args.output))
    print(
        f"[vibephysics] Saved compare Blender scene to {args.output} "
        f"(left={left_collection}, right={right_collection}, shared timeline)"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Export feedforward predictions to Blender .blend files.")
    sub = parser.add_subparsers(dest="command", required=True)

    single = sub.add_parser("blend", help="Export one predictions.npz to a .blend file")
    single.add_argument("--predictions", type=Path, required=True, help="Path to predictions.npz")
    single.add_argument("--output", type=Path, required=True, help="Output .blend path")
    single.add_argument("--min_confidence", type=float, default=None)
    single.add_argument("--point_scale", type=float, default=1.0)
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
    compare.add_argument("--point_scale", type=float, default=1.0)
    compare.add_argument("--point-size", type=float, default=0.03, dest="point_size")
    compare.add_argument("--animate", action=argparse.BooleanOptionalAction, default=True)
    compare.add_argument("--align-ground", action=argparse.BooleanOptionalAction, default=True)
    compare.add_argument("--animation_fps", type=int, default=None)
    compare.add_argument("--video_fps", type=float, default=None)

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


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[ERROR] Blend export failed: {exc}", file=sys.stderr)
        sys.exit(1)
