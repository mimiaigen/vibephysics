#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${CONFIG:-$SCRIPT_DIR/src/vibephysics/feedforward/configs/feedforward.yaml}"

usage() {
    echo "Usage: $0 [--config <yaml>] [--input <path>] [--output_path <path>]"
    echo ""
    echo "  --config        Feedforward YAML config (default: feedforward.yaml)"
    echo "  --input         Video (.mov/.mp4), image folder, or single image"
    echo "  --output_path   Override output_path in config"
    exit 1
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --config) CONFIG="$2"; shift ;;
        --input|--image_path) INPUT="$2"; shift ;;
        --output_path) OUTPUT_PATH="$2"; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

python -m vibephysics.feedforward.reconstruct \
    --config "$CONFIG" \
    ${INPUT:+--input "$INPUT"} \
    ${OUTPUT_PATH:+--output_path "$OUTPUT_PATH"}
