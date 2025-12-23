import sys
import os
from pathlib import Path

# Ensure src is in path if running from examples
# This allows running the script directly without installing the package
current_dir = Path(__file__).resolve().parent
src_path = (current_dir / ".." / ".." / "src").resolve()
if str(src_path) not in sys.path:
    # We use index 0 and potentially re-insert if bpy moves it
    sys.path.insert(0, str(src_path))

import bpy
import argparse
from vibephysics import mapping

def reset_scene():
    """Clear existing objects in the scene."""
    # Ensure src is still first (Blender sometimes prefix paths)
    if sys.path[0] != str(src_path):
        if str(src_path) in sys.path: sys.path.remove(str(src_path))
        sys.path.insert(0, str(src_path))
    
    bpy.ops.wm.read_factory_settings(use_empty=True)

def main():
    # Helper to parse args even when run via blender
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1:]
    else:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Visualize GLOMAP/COLMAP reconstruction in Blender")
    parser.add_argument("--sparse", type=str, required=True, help="Path to sparse model folder (containing cameras.bin/txt)")
    parser.add_argument("--save-blend", type=str, default="output/visualize.blend", help="Path to save result .blend file")
    parser.add_argument("--point-size", type=float, default=0.01, help="Size of points in the reconstruction")
    parser.add_argument("--rotation", type=float, nargs=3, default=[0, 0, 0], help="Global rotation in degrees (Euler XYZ)")
    
    args = parser.parse_args(argv)

    sparse_path = Path(args.sparse).absolute()
    if not (sparse_path / "cameras.bin").exists() and not (sparse_path / "cameras.txt").exists():
        print(f"Error: Could not find cameras.bin or cameras.txt in {sparse_path}")
        return

    # Visualization
    print(f"Visualizing model from {sparse_path}...")
    reset_scene()
    
    mapping.load_colmap_reconstruction(
        str(sparse_path), 
        collection_name="GLOMAP_Result", 
        point_size=args.point_size, 
        rotation=args.rotation
    )
    
    # Save
    save_path = Path(args.save_blend).absolute()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(save_path))
    print(f"Saved .blend file to {save_path}")

if __name__ == "__main__":
    main()
