#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    echo "Usage: $0 [--sparse <path/to/sparse/0>] [--output <path/to/save.blend>] [--point_size <float>] [--rotation <x y z>]"
    exit 1
}

SPARSE_PATH=""
OUTPUT_PATH=""
POINT_SIZE=0.03
ROTATION="-90 0 0"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --sparse) SPARSE_PATH="$2"; shift ;;
        --output) OUTPUT_PATH="$2"; shift ;;
        --point_size) POINT_SIZE="$2"; shift ;;
        --rotation) ROTATION="$2 $3 $4"; shift; shift; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

if [[ -z "$SPARSE_PATH" || -z "$OUTPUT_PATH" ]]; then
    echo "Error: --sparse and --output are required."
    usage
fi

python "$SCRIPT_DIR/examples/colmap_format/demo_glomap_visual.py" \
    --sparse "$SPARSE_PATH" \
    --save-blend "$OUTPUT_PATH" \
    --point-size "$POINT_SIZE" \
    --rotation $ROTATION
