#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python_has() {
    "$1" -c "import $2" >/dev/null 2>&1
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

resolve_python() {
    local candidate
    while IFS= read -r candidate; do
        if python_has "$candidate" bpy; then
            PYTHON="$candidate"
            return 0
        fi
    done < <(collect_python_candidates)
    return 1
}

usage() {
    echo "Usage: $0 --left <predictions.npz> --right <predictions.npz> [--output <path.blend>]"
    echo ""
    echo "Example:"
    echo "  $0 \\"
    echo "    --left  feedforward_output/vggt_omega_test/predictions.npz \\"
    echo "    --right feedforward_output/lingbot_map_test/predictions.npz \\"
    echo "    --output feedforward_output/compare_vggt_lingbot.blend"
    exit 1
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --left) LEFT="$2"; shift ;;
        --right) RIGHT="$2"; shift ;;
        --output) OUTPUT="$2"; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown parameter: $1"; usage ;;
    esac
    shift
done

if [[ -z "$LEFT" || -z "$RIGHT" ]]; then
    usage
fi

if ! resolve_python; then
    echo "Error: no Python with PyPI bpy found." >&2
    echo "Use Python 3.11 or 3.13 with: pip install bpy" >&2
    echo "Or set VIBEPHYSICS_PYTHON=/path/to/python" >&2
    exit 1
fi

OUTPUT="${OUTPUT:-$SCRIPT_DIR/feedforward_output/compare.blend}"
export PYTHONPATH="${SCRIPT_DIR}/src${PYTHONPATH:+:$PYTHONPATH}"

echo "--- [run_compare_blend] Python: $PYTHON ---"
exec "$PYTHON" -m vibephysics.feedforward.export compare \
    --predictions "$LEFT" "$RIGHT" \
    --output "$OUTPUT"
