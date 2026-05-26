import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
src_path = (current_dir / ".." / ".." / "src").resolve()
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import argparse
import bpy
from vibephysics import feedforward
from vibephysics.feedforward.config import DEFAULT_FEEDFORWARD_CONFIG
from vibephysics.setup.exporter import save_blend


def reset_scene():
    if sys.path[0] != str(src_path):
        if str(src_path) in sys.path:
            sys.path.remove(str(src_path))
        sys.path.insert(0, str(src_path))
    bpy.ops.wm.read_factory_settings(use_empty=True)


def main():
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1 :]
    else:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Run or visualize feedforward reconstruction in Blender")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_FEEDFORWARD_CONFIG,
        help="Feedforward YAML config file",
    )
    parser.add_argument("--image_path", type=str, help="Override config image_path")
    parser.add_argument("--predictions", type=str, help="Visualize saved predictions.npz instead of running inference")
    parser.add_argument("--output_path", type=str, default=None, help="Override config output_path")
    args = parser.parse_args(argv)

    if args.image_path:
        output_path = feedforward.reconstruct_from_config(
            args.config,
            image_path=args.image_path,
            output_path=args.output_path,
        )
        print(f"Output directory: {output_path}")
        return

    if args.predictions:
        from vibephysics.feedforward.config import load_yaml_config
        from vibephysics.feedforward.ground_align import align_prediction_ground
        from vibephysics.feedforward.schema import load_prediction

        cfg = load_yaml_config(args.config)
        output = cfg.get("output") or {}
        predictions_path = Path(args.predictions).absolute()
        if not predictions_path.exists():
            print(f"Error: predictions file not found: {predictions_path}")
            return
        prediction = load_prediction(predictions_path)
        if output.get("align_ground", True) and not prediction.metadata.get("ground_align_applied"):
            align_prediction_ground(prediction)
        from vibephysics.feedforward.common import convert_prediction_to_blender_zup

        convert_prediction_to_blender_zup(prediction)
        reset_scene()
        feedforward.load_reconstruction(
            prediction,
            min_confidence=output.get("min_confidence", 0.5),
            point_scale=output.get("point_scale", 1.0),
        )
        save_path = Path(output.get("save_blend", "output/feedforward_scene.blend")).absolute()
        save_blend(str(save_path))
        print(f"Saved .blend file to {save_path}")
        return

    parser.error("Provide either --image_path or --predictions")


if __name__ == "__main__":
    main()
