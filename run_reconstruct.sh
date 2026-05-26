#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${CONFIG:-$SCRIPT_DIR/src/vibephysics/feedforward/configs/feedforward.yaml}"
RUN_LABEL="run_reconstruct"
source "$SCRIPT_DIR/feedforward_run.inc.sh"

usage() {
    echo "Usage: $0 [--config <yaml>] [--input <path>] [--output_path <path>] [--max_frames N] [--max_frames_mode first|spread]"
    echo ""
    echo "  --config        Feedforward YAML config (default: feedforward.yaml)"
    echo "  --input         Video (.mov/.mp4), image folder, or single image"
    echo "  --output_path   Override output_path in config"
    echo ""
    feedforward_usage_frame_args
    echo ""
    echo "Frame limits apply via video.max_frames in config (shared by all engines)."
    exit 1
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --config) CONFIG="$2"; shift ;;
        --input|--image_path) INPUT="$2"; shift ;;
        --output_path) OUTPUT_PATH="$2"; shift ;;
        --max_frames) MAX_FRAMES="$2"; shift ;;
        --max_frames_mode) MAX_FRAMES_MODE="$2"; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

ARGS=(--config "$CONFIG")
[ -n "${INPUT:-}" ] && ARGS+=(--input "$INPUT")
[ -n "${OUTPUT_PATH:-}" ] && ARGS+=(--output_path "$OUTPUT_PATH")
feedforward_append_frame_args

feedforward_print_frame_plan "$CONFIG" "${INPUT:-}"

python -m vibephysics.feedforward.reconstruct "${ARGS[@]}"
