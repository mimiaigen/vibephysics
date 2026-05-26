import sys
from pathlib import Path

from .colmap import sfm_pipeline
from .config import DEFAULT_SFM_CONFIG, load_sfm_config


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run sparse SfM (GLOMAP or COLMAP).")
    parser.add_argument("--config", type=Path, default=DEFAULT_SFM_CONFIG, help="YAML config.")
    parser.add_argument("--image_path", "--input", dest="image_path", default=None)
    parser.add_argument("--output_path", default=None)
    parser.add_argument("--no-blend", action="store_true", help="Skip saving visualize.blend.")
    parser.add_argument("--blend-path", default=None, help="Custom .blend output path.")
    parser.add_argument("--point-size", type=float, default=None)
    parser.add_argument("--rotation", type=float, nargs=3, default=None, metavar=("X", "Y", "Z"))
    parser.add_argument("--no-animate", action="store_true", help="Disable timeline animation in .blend.")
    parser.add_argument("--animation-fps", type=int, default=None, help="Blender playback fps (default: 24).")
    args = parser.parse_args()

    try:
        params = load_sfm_config(
            args.config,
            args.image_path,
            args.output_path,
            save_blend=False if args.no_blend else None,
            blend_path=args.blend_path,
            point_size=args.point_size,
            rotation=tuple(args.rotation) if args.rotation is not None else None,
        )
        if args.no_animate:
            params["animate"] = False
        if args.animation_fps is not None:
            params["animation_fps"] = args.animation_fps
        sys.exit(sfm_pipeline(**params))
    except (ValueError, FileNotFoundError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
