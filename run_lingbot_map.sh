#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${CONFIG:-$SCRIPT_DIR/src/vibephysics/feedforward/configs/feedforward_lingbot_map.yaml}"
RUN_LABEL="run_lingbot_map"
source "$SCRIPT_DIR/feedforward_run.inc.sh"

python_has() {
    "$1" -c "import $2" >/dev/null 2>&1
}

python_can_run() {
    python_has "$1" yaml && python_has "$1" bpy
}

collect_python_candidates() {
    local seen="|"
    local candidate

    add_candidate() {
        candidate="$1"
        [ -z "$candidate" ] && return
        [ ! -x "$candidate" ] && return
        case "$seen" in *"|$candidate|"*) return ;; esac
        seen="${seen}${candidate}|"
        printf '%s\n' "$candidate"
    }

    add_candidate "${VIBEPHYSICS_PYTHON:-}"
    add_candidate "${PYTHON:-}"
    add_candidate "${CONDA_PREFIX:+$CONDA_PREFIX/bin/python}"

    shopt -s nullglob
    for candidate in \
        "$HOME/anaconda3/envs/"*/bin/python \
        "$HOME/miniconda3/envs/"*/bin/python \
        "/opt/homebrew/anaconda3/envs/"*/bin/python \
        "/opt/homebrew/Caskroom/miniconda/base/envs/"*/bin/python; do
        add_candidate "$candidate"
    done
    shopt -u nullglob

    add_candidate "$(command -v python3.11 2>/dev/null)"
    add_candidate "$(command -v python 2>/dev/null)"
    add_candidate "$(command -v python3 2>/dev/null)"
}

diagnose_python() {
    local py="$1"
    local missing=()
    python_has "$py" yaml || missing+=("pyyaml")
    python_has "$py" bpy || missing+=("bpy")
    if ((${#missing[@]})); then
        echo "  $py (Python $($py -c 'import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")' 2>/dev/null || echo '?')) — missing: ${missing[*]}"
    fi
}

resolve_python() {
    while IFS= read -r candidate; do
        if python_can_run "$candidate"; then
            PYTHON="$candidate"
            return 0
        fi
    done < <(collect_python_candidates)
    return 1
}

if ! resolve_python; then
    echo "Error: no Python with vibephysics + bpy found." >&2
    echo "PyPI bpy 5.0 requires Python 3.11 (not 3.12+)." >&2
    echo "Checked:" >&2
    while IFS= read -r candidate; do diagnose_python "$candidate"; done < <(collect_python_candidates)
    echo "" >&2
    echo "Fix options:" >&2
    echo '  conda create -n vibephysics python=3.11 && conda activate vibephysics' >&2
    echo '  pip install vibephysics bpy' >&2
    echo "Or set VIBEPHYSICS_PYTHON=/path/to/python" >&2
    exit 1
fi

export PYTHONPATH="${SCRIPT_DIR}/src${PYTHONPATH:+:$PYTHONPATH}"
export KMP_DUPLICATE_LIB_OK=TRUE
export TQDM_DISABLE=0

"$PYTHON" -c "from vibephysics.feedforward.lingbot_map import ensure_dependencies; import sys; sys.exit(0 if ensure_dependencies() else 1)"

usage() {
    echo "Usage: $0 [--config <yaml>] [--input <path>] [--output_path <path>] [--point_scale SIZE] [--max_frames N] [--max_frames_mode first|spread]"
    echo ""
    feedforward_usage_frame_args
    echo ""
    echo "Frame limits apply via video.max_frames in config (shared by all engines)."
    echo "LingBot inference mode auto-adapts (lingbot_map.mode):"
    echo "  <=320 frames  -> streaming, every frame a keyframe"
    echo "  >320 frames   -> windowed with cross-window alignment"
    exit 1
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --config) CONFIG="$2"; shift ;;
        --input|--image_path) INPUT="$2"; shift ;;
        --output_path) OUTPUT_PATH="$2"; shift ;;
        --point_scale|--point-scale) POINT_SCALE="$2"; shift ;;
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

echo "--- [run_lingbot_map] Python: $PYTHON ---"
feedforward_print_frame_plan "$CONFIG" "${INPUT:-}"

exec "$PYTHON" -m vibephysics.feedforward.reconstruct "${ARGS[@]}"
