#!/bin/bash

# Default values
SPARSE_PATH="<your_folder>/mapping_output/glomap_20251223_120214/sparse/0"
POINT_SIZE=0.03
OUTPUT_PATH="<your_folder>/mapping_output/glomap_20251223_120214/visualize_color.blend"
ROTATION="-90 0 0"

# Function to show usage
usage() {
    echo "Usage: $0 [--sparse <path/to/sparse/0>] [--output <path/to/save.blend>] [--point_size <float>] [--rotation <x y z>]"
    echo ""
    echo "Arguments:"
    echo "  --sparse        Path to the folder containing cameras.bin, points3D.bin, etc. (Default: $SPARSE_PATH)"
    echo "  --output        Where to save the .blend file (Default: $OUTPUT_PATH)"
    echo "  --point_size    Size of the points in the visualization (Default: $POINT_SIZE)"
    echo "  --rotation      Global rotation in degrees Euler XYZ (Default: $ROTATION)"
    exit 1
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --sparse) SPARSE_PATH="$2"; shift ;;
        --output) OUTPUT_PATH="$2"; shift ;;
        --point_size) POINT_SIZE="$2"; shift ;;
        --rotation) ROTATION="$2 $3 $4"; shift; shift; shift ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

# Run the visualization script
python examples/colmap_format/demo_glomap_visual.py \
    --sparse "$SPARSE_PATH" \
    --save-blend "$OUTPUT_PATH" \
    --point-size "$POINT_SIZE" \
    --rotation $ROTATION
