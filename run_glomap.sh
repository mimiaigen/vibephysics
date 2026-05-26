#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${CONFIG:-$SCRIPT_DIR/src/vibephysics/mapping/configs/sfm.yaml}"

usage() {
    echo "Usage: $0 [--config <yaml>] [--input <path>] [--output_path <path>] [options]"
    echo ""
    echo "  --config        SfM YAML config (default: sfm.yaml)"
    echo "  --input         Video (.mov/.mp4), image folder, or single image"
    echo "  --output_path   Override output_path in config"
    echo "  --no-blend      Skip saving visualize.blend (blend export is on by default)"
  echo "  --no-animate    Save a static .blend without timeline animation"
  echo "  --animation-fps Blender playback fps for animation (default: 24)"
    echo "  --blend-path    Custom .blend output path"
    echo "  --point-size    Point size in Blender visualization (default: 0.03)"
    echo "  --rotation X Y Z  Global rotation in degrees (default: -90 0 0)"
    echo ""
    echo "Set engine: glomap or engine: colmap in the YAML config."
    exit 1
}

NO_BLEND=""
NO_ANIMATE=""
BLEND_PATH=""
POINT_SIZE=""
ROTATION=""
ANIMATION_FPS=""

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --config) CONFIG="$2"; shift ;;
        --input|--image_path) INPUT="$2"; shift ;;
        --output_path) OUTPUT_PATH="$2"; shift ;;
        --no-blend) NO_BLEND="1" ;;
        --no-animate) NO_ANIMATE="1" ;;
        --blend-path) BLEND_PATH="$2"; shift ;;
        --point-size) POINT_SIZE="$2"; shift ;;
        --rotation) ROTATION="$2 $3 $4"; shift; shift; shift ;;
        --animation-fps) ANIMATION_FPS="$2"; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

python -m vibephysics.mapping.pipeline \
    --config "$CONFIG" \
    ${INPUT:+--input "$INPUT"} \
    ${OUTPUT_PATH:+--output_path "$OUTPUT_PATH"} \
    ${NO_BLEND:+--no-blend} \
    ${NO_ANIMATE:+--no-animate} \
    ${BLEND_PATH:+--blend-path "$BLEND_PATH"} \
    ${POINT_SIZE:+--point-size "$POINT_SIZE"} \
    ${ROTATION:+--rotation $ROTATION} \
    ${ANIMATION_FPS:+--animation-fps "$ANIMATION_FPS"}
