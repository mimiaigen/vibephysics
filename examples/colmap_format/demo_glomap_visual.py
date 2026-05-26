import sys
from pathlib import Path

import bpy
import argparse

current_dir = Path(__file__).resolve().parent
src_path = (current_dir / ".." / ".." / "src").resolve()
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from vibephysics.mapping.map_visual import save_reconstruction_blend


def main():
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1:]
    else:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Visualize GLOMAP/COLMAP reconstruction in Blender")
    parser.add_argument("--sparse", type=str, required=True, help="Path to sparse model folder")
    parser.add_argument("--save-blend", type=str, default="output/visualize.blend", help="Path to save .blend")
    parser.add_argument("--point-size", type=float, default=0.03)
    parser.add_argument("--rotation", type=float, nargs=3, default=[-90, 0, 0])
    parser.add_argument("--no-animate", action="store_true")
    parser.add_argument("--animation-fps", type=int, default=24)
    parser.add_argument("--video-fps", type=float, default=None)
    args = parser.parse_args(argv)

    sys.exit(
        save_reconstruction_blend(
            args.sparse,
            args.save_blend,
            point_size=args.point_size,
            rotation=tuple(args.rotation),
            animate=not args.no_animate,
            animation_fps=args.animation_fps,
            video_fps=args.video_fps,
            frames_dir=Path(args.sparse).parent.parent / "images",
        )
    )


if __name__ == "__main__":
    main()
