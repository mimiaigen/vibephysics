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

    parser = argparse.ArgumentParser(description="Demo of GLOMAP pipeline + BPY Visualization")
    parser.add_argument("--images", type=str, default="/Users/shamangary/codeDemo/data/da3/output/20251220_201123", help="Path to input images directory")
    parser.add_argument("--output", type=str, default="output/glomap_demo", help="Output directory for reconstruction")
    parser.add_argument("--save-blend", type=str, default="output/glomap_demo/scene.blend", help="Path to save result .blend file")
    parser.add_argument("--skip-pipeline", action="store_true", help="Skip reconstruction, only visualize existing sparse model")
    parser.add_argument("--sparse", type=str, help="Direct path to sparse model folder (containing cameras.bin)")
    parser.add_argument("--point-size", type=float, default=0.01, help="Size of points in the reconstruction")
    parser.add_argument("--camera-model", type=str, default="PINHOLE", help="Camera model for reconstruction (e.g. PINHOLE, SIMPLE_RADIAL)")
    parser.add_argument("--rotation", type=float, nargs=3, default=[0, 0, 0], help="Global rotation in degrees (Euler XYZ)")
    
    args = parser.parse_args(argv)

    output_path = Path(args.output).absolute()
    
    # 2. Locate Sparse Model
    sparse_path = None
    if args.sparse:
        sparse_path = Path(args.sparse)
    else:
        # 1. Run Pipeline
        if not args.skip_pipeline:
            if not Path(args.images).exists():
                print(f"Error: Image path {args.images} not found.")
                # If images not found, maybe it's already a sparse path?
                if (Path(args.images) / "cameras.bin").exists():
                    print("Found cameras.bin in image path, using it as sparse path.")
                    sparse_path = Path(args.images)
                else:
                    return

            if sparse_path is None:
                print(f"Running GLOMAP pipeline on {args.images}...")
                ret = mapping.glomap_pipeline(
                    image_path=args.images,
                    output_path=output_path,
                    camera_model=args.camera_model,
                    verbose=True
                )
                if ret != 0:
                    print("Pipeline failed.")
                    return
        
        # Search for sparse output
        if sparse_path is None:
            potential_paths = [
                output_path / "sparse" / "0",
                output_path / "sparse",
                Path(args.images) / "sparse" / "0",
                Path(args.images) / "sparse",
                Path(args.images) # sometimes images folder IS the sparse folder
            ]
            
            for p in potential_paths:
                if (p / "cameras.bin").exists() or (p / "cameras.txt").exists():
                    sparse_path = p
                    break
            
    if sparse_path is None:
        print(f"Could not find valid Colmap/Glomap sparse model.")
        return

    # 3. Visualization
    print(f"Visualizing model from {sparse_path}...")
    reset_scene()
    
    mapping.load_colmap_reconstruction(str(sparse_path), collection_name="GLOMAP_Result", point_size=args.point_size, rotation=args.rotation)
    
    # 4. Save
    save_path = Path(args.save_blend)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(save_path))
    print(f"Saved .blend file to {save_path}")

if __name__ == "__main__":
    main()
