#!/bin/bash
# Run 3DGS Viewer Demo
# Usage: sh run_3dgs_viewer.sh [path_to_ply]
#
# Options:
#   --mesh-type: IcoSphere (default), Circle (flat disk), DualIcoSphere, Cube
#   --shader-mode: Gaussian (default, transparent falloff), Ring, Wireframe, Freestyle
#   --point-scale: Anisotropic (default, ellipsoids), Max (spheres), Auto, Fix
#   --geo-size: 3.0 (default) - mesh is Nx larger than visible Gaussian
#   --use-simple: Use solid colors (no transparency)
#   --no-rotate: Skip default Z-up to Y-up rotation

PLY_PATH="${1:-/Users/shamangary/codeDemo/marble/almond tree/almond_tree_marble.ply}"

echo "=========================================="
echo "  3D Gaussian Splatting Viewer"
echo "=========================================="
echo "Input: $PLY_PATH"
echo ""

# Anisotropic mode creates ELLIPSOID shapes (can be thin as needles!)
# - Uses (scale_0, scale_1, scale_2) as separate X, Y, Z scales
# - Uses quaternion (rot_0, rot_1, rot_2, rot_3) for rotation
# - This is the correct way to render 3D Gaussian Splats
python examples/gsplat/demo_3dgs_viewer.py --input "$PLY_PATH" \
    --mesh-type IcoSphere \
    --point-scale Anisotropic \
    --shader-mode Gaussian \
    --geo-size 3.0 \
    --output-channel "Final color"
