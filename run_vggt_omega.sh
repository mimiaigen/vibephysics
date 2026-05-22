#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${CONFIG:-$SCRIPT_DIR/src/vibephysics/feedforward/configs/feedforward_vggt_omega.yaml}"

python_has() {
    "$1" -c "import $2" >/dev/null 2>&1
}

python_can_run_vggt_omega() {
    python_has "$1" yaml && python_has "$1" torch && python_has "$1" cv2 && python_has "$1" bpy
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
    add_candidate "$(command -v python3.13 2>/dev/null)"
    add_candidate "$(command -v python 2>/dev/null)"
    add_candidate "$(command -v python3 2>/dev/null)"
}

diagnose_python() {
    local py="$1"
    local missing=()
    python_has "$py" yaml || missing+=("pyyaml")
    python_has "$py" torch || missing+=("torch")
    python_has "$py" cv2 || missing+=("opencv-python")
    python_has "$py" bpy || missing+=("bpy")
    python_has "$py" vggt_omega || missing+=("vggt-omega")
    if ((${#missing[@]})); then
        echo "  $py (Python $($py -c 'import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")' 2>/dev/null || echo '?')) — missing: ${missing[*]}"
    fi
}

resolve_python() {
    local candidate
    local with_vggt=""

    while IFS= read -r candidate; do
        if ! python_can_run_vggt_omega "$candidate"; then
            continue
        fi
        if python_has "$candidate" vggt_omega; then
            PYTHON="$candidate"
            return 0
        fi
        if [ -z "$with_vggt" ]; then
            with_vggt="$candidate"
        fi
    done < <(collect_python_candidates)

    if [ -n "$with_vggt" ]; then
        PYTHON="$with_vggt"
        return 0
    fi
    return 1
}

if ! resolve_python; then
    echo "Error: no Python with PyPI bpy found for VGGT-Omega reconstruction." >&2
    echo "PyPI bpy on macOS supports Python 3.11 or 3.13 (not 3.12)." >&2
    echo "Checked:" >&2
    while IFS= read -r candidate; do diagnose_python "$candidate"; done < <(collect_python_candidates)
    echo "" >&2
    echo "Fix options:" >&2
    echo '  conda activate py311   # or another 3.11/3.13 env with bpy' >&2
    echo '  pip install "vibephysics[vggt_omega]"' >&2
    echo "First run will auto-download the checkpoint (gated HF model)." >&2
    echo "Or set VIBEPHYSICS_PYTHON=/path/to/python" >&2
    exit 1
fi

if ! python_has "$PYTHON" vggt_omega; then
    echo "--- [run_vggt_omega] Installing vggt-omega ---"
    "$PYTHON" -m pip install "vggt-omega @ git+https://github.com/facebookresearch/vggt-omega.git"
fi

if ! python_has "$PYTHON" huggingface_hub; then
    echo "--- [run_vggt_omega] Installing huggingface_hub (auto checkpoint download) ---"
    "$PYTHON" -m pip install huggingface_hub
fi

export PYTHONPATH="${SCRIPT_DIR}/src${PYTHONPATH:+:$PYTHONPATH}"
export KMP_DUPLICATE_LIB_OK=TRUE

"$PYTHON" -c "import torch" 2>/dev/null || true

usage() {
    echo "Usage: $0 [--config <yaml>] [--input <path>] [--output_path <path>] [--mode balanced|max_size]"
    exit 1
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --config) CONFIG="$2"; shift ;;
        --input|--image_path) INPUT="$2"; shift ;;
        --output_path) OUTPUT_PATH="$2"; shift ;;
        --mode) MODE="$2"; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown parameter passed: $1"; usage ;;
    esac
    shift
done

if [ -n "${MODE:-}" ]; then
    case "$MODE" in
        balanced|max_size) ;;
        *) echo "Error: --mode must be balanced or max_size (got: $MODE)" >&2; exit 1 ;;
    esac
fi

ARGS=(--config "$CONFIG")
[ -n "${INPUT:-}" ] && ARGS+=(--input "$INPUT")
[ -n "${OUTPUT_PATH:-}" ] && ARGS+=(--output_path "$OUTPUT_PATH")
[ -n "${MODE:-}" ] && ARGS+=(--mode "$MODE")

echo "--- [run_vggt_omega] Python: $PYTHON ---"
exec "$PYTHON" -m vibephysics.feedforward.reconstruct "${ARGS[@]}"
