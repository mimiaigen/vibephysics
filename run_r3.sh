#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${CONFIG:-$SCRIPT_DIR/src/vibephysics/feedforward/configs/feedforward_r3.yaml}"
RUN_LABEL="run_r3"
source "$SCRIPT_DIR/feedforward_run.inc.sh"

python_has() {
    "$1" -c "import $2" >/dev/null 2>&1
}

python_can_run() {
    "$1" - <<'PY' >/dev/null 2>&1
import sys
try:
    import yaml  # noqa: F401
    import numpy as np
    if int(np.__version__.split(".", 1)[0]) >= 2:
        raise RuntimeError(f"bpy requires numpy<2, found numpy {np.__version__}")
    import bpy  # noqa: F401
except Exception:
    sys.exit(1)
PY
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
    if ! "$py" - <<'PY' >/dev/null 2>&1
import sys
try:
    import numpy as np
    if int(np.__version__.split(".", 1)[0]) >= 2:
        raise RuntimeError
except Exception:
    sys.exit(1)
PY
    then
        missing+=("numpy<2")
    fi
    if ! "$py" - <<'PY' >/dev/null 2>&1
import sys
try:
    import bpy  # noqa: F401
except Exception:
    sys.exit(1)
PY
    then
        missing+=("bpy")
    fi
    if ((${#missing[@]})); then
        echo "  $py (Python $($py -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo '?')) — missing: ${missing[*]}"
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
    echo '  pip install "numpy<2" vibephysics bpy' >&2
    echo "First run will auto-install R3 and download checkpoints from Hugging Face (KevinXu02/R3)." >&2
    echo "On macOS this uses an experimental no-xformers install and MPS/CPU fallback." >&2
    echo "Or set VIBEPHYSICS_PYTHON=/path/to/python" >&2
    exit 1
fi

export PYTHONPATH="${SCRIPT_DIR}/src${PYTHONPATH:+:$PYTHONPATH}"
export KMP_DUPLICATE_LIB_OK=TRUE
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"

if ! "$PYTHON" -c "from vibephysics.feedforward.r3 import ensure_dependencies; import sys; sys.exit(0 if ensure_dependencies() else 1)"; then
    echo "--- [run_r3] R3 dependencies unavailable on this machine (see message above). ---" >&2
    echo "--- [run_r3] Linux + NVIDIA CUDA is the upstream-supported path; macOS is experimental. ---" >&2
    exit 1
fi

usage() {
    echo "Usage: $0 [--config <yaml>] [--input <path>] [--output_path <path>] [--point_scale SIZE] [--max_frames N] [--max_frames_mode first|spread]"
    echo ""
    feedforward_usage_frame_args
    echo ""
    echo "Frame limits apply via video.max_frames in config (shared by all engines)."
    echo "R3 mode preset (r3.mode): test | local | long | strided"
    echo "  local  -> indoor / small-coverage scenes (default)"
    echo "  long   -> outdoor / long trajectories (uses r3_long + metric scale)"
    echo "  macOS  -> experimental no-xformers install; prefer small max_frames and mode=test/local"
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

echo "--- [run_r3] Python: $PYTHON ---"
feedforward_print_frame_plan "$CONFIG" "${INPUT:-}"

exec "$PYTHON" -m vibephysics.feedforward.reconstruct "${ARGS[@]}"
