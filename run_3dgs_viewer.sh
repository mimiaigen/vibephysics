#!/bin/bash
# Run 3DGS Viewer Demo
# Usage: sh run_3dgs_viewer.sh [path_to_ply]

PLY_PATH="${1:-/Users/shamangary/codeDemo/marble/almond tree/almond_tree_marble.ply}"

echo "=========================================="
echo "  3D Gaussian Splatting Viewer"
echo "=========================================="
echo "Input: $PLY_PATH"
echo ""

python examples/gsplat/demo_3dgs_viewer.py --input "$PLY_PATH"

