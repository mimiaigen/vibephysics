#!/bin/bash
# Run 3DGS Viewer Demo
# Usage: sh run_3dgs_viewer.sh [path_to_ply]
#
# Options:
#   --mesh-type: IcoSphere (default), DualIcoSphere, Cube
#   --shader-mode: Gaussian (default, transparent falloff), Ring, Wireframe, Freestyle
#   --point-scale: Anisotropic (default, ellipsoids), Max (spheres)
#   --geo-size: 3.0 (default) - mesh is Nx larger than visible Gaussian
#   --opacity-scale: 1.0 (default) - < 1.0 transparent, > 1.0 opaque
#   --use-simple: Use solid colors (no transparency)
#   --no-rotate: Skip default Z-up to Y-up rotation

PLY_PATH="${1:-/Users/shamangary/codeDemo/marble/almond tree/almond_tree_marble.ply}"
shift 2>/dev/null || true

echo "=========================================="
echo "  3D Gaussian Splatting Viewer"
echo "=========================================="
echo "Input: $PLY_PATH"
echo ""

# Avoid leaking Conda/site-packages numpy into Blender's Python (can cause NumPy ABI mismatches)
export PYTHONNOUSERSITE=1
unset PYTHONPATH

# Recommended default preset (good visuals, stable):
# - DualIcoSphere: nicer coverage than a sphere
# - Anisotropic: faithful 3DGS ellipsoids (we auto-normalize global size in gsplat.py)
# - Gaussian + geo-size 2.0: Sharper clip
# - Opacity-scale 10.0: Stronger solid core for "sharper" look
#
# You can pass extra args after the ply path, e.g.:
#   sh run_3dgs_viewer.sh /path/to.ply --opacity-scale 1.0
python examples/gsplat/demo_3dgs_viewer.py --input "$PLY_PATH" \
    --shader-mode Gaussian \
    --point-scale Anisotropic \
    --opacity-scale 10.0 \
    --geo-size 2.5 \
    "$@"

