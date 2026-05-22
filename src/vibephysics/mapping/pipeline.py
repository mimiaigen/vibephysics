import sys
from pathlib import Path

from .config import DEFAULT_SFM_CONFIG, run_sfm_from_config


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run sparse SfM mapping pipeline (GLOMAP or COLMAP).")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_SFM_CONFIG,
        help=f"YAML config file (default: {DEFAULT_SFM_CONFIG.name})",
    )
    parser.add_argument("--image_path", "--input", default=None, dest="image_path", help="Override config image_path (video, image folder, or single image).")
    parser.add_argument("--output_path", default=None, help="Override config output_path.")
    args = parser.parse_args()

    try:
        sys.exit(run_sfm_from_config(args.config, args.image_path, args.output_path))
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
