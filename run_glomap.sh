#!/bin/bash

# Default values
ENGINE="glomap"
MATCHER="exhaustive"
CAMERA_MODEL="PINHOLE"

# Function to show usage
usage() {
    echo "Usage: $0 --image_path <path> [--engine <glomap|colmap>] [--output_path <path>] [--matcher <exhaustive|sequential>] [--camera_model <model>]"
    echo ""
    echo "Arguments:"
    echo "  --image_path    Path to the folder containing raw images (Required)"
    echo "  --engine        SfM engine to use (default: glomap)"
    echo "  --output_path   Directory to save the reconstruction results"
    echo "  --matcher       Matching method (default: exhaustive)"
    echo "  --camera_model  Camera model (default: SIMPLE_RADIAL)"
    exit 1
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --image_path) IMAGE_PATH="$2"; shift ;;
        --engine) ENGINE="$2"; shift ;;
        --output_path) OUTPUT_PATH="$2"; shift ;;
        --matcher) MATCHER="$2"; shift ;;
        --camera_model) CAMERA_MODEL="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

# Check required parameters
if [ -z "$IMAGE_PATH" ]; then
    echo "Error: --image_path is required."
    usage
fi

# Run the pipeline
python -m vibephysics.mapping.pipeline \
    --image_path "$IMAGE_PATH" \
    --engine "$ENGINE" \
    ${OUTPUT_PATH:+--output_path "$OUTPUT_PATH"} \
    --matcher "$MATCHER" \
    --camera_model "$CAMERA_MODEL"
