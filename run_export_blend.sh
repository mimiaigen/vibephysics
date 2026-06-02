#!/bin/bash
# Export an existing predictions.npz to scene.blend (no re-inference).
# Uses reconstruct_config.json beside the NPZ for blend settings (pointcloud, scale, …).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
        "$HOME/miniconda3/envs/"*/bin/python; do
        add_candidate "$candidate"
    done
    shopt -u nullglob

    add_candidate "$(command -v python3.11 2>/dev/null)"
    add_candidate "$(command -v python 2>/dev/null)"
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

usage() {
    echo "Usage: $0 --predictions <predictions.npz> [--output <scene.blend>] [export args]"
    echo ""
    echo "Examples:"
    echo "  $0 --predictions output/feedforward_output/lingbot_map_20260602_205324/predictions.npz"
    echo "  $0 --predictions out/predictions.npz --output out/scene_pointcloud.blend"
    exit 1
}

PREDICTIONS=""
OUTPUT=""
EXTRA=()

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --predictions|-p) PREDICTIONS="$2"; shift ;;
        --output|-o) OUTPUT="$2"; shift ;;
        -h|--help) usage ;;
        *) EXTRA+=("$1") ;;
    esac
    shift
done

[ -z "$PREDICTIONS" ] && usage
[ ! -f "$PREDICTIONS" ] && echo "Error: not found: $PREDICTIONS" >&2 && exit 1

if ! resolve_python; then
    echo "Error: no Python with bpy found (Python 3.11 + bpy required)." >&2
    exit 1
fi

export PYTHONPATH="${SCRIPT_DIR}/src${PYTHONPATH:+:$PYTHONPATH}"
export KMP_DUPLICATE_LIB_OK=TRUE

PREDICTIONS="$(cd "$(dirname "$PREDICTIONS")" && pwd)/$(basename "$PREDICTIONS")"
if [ -z "$OUTPUT" ]; then
    OUTPUT="$(dirname "$PREDICTIONS")/scene_pointcloud.blend"
fi

echo "--- [run_export_blend] Python: $PYTHON ---"
echo "--- [run_export_blend] Input:  $PREDICTIONS ---"
echo "--- [run_export_blend] Output: $OUTPUT ---"

"$PYTHON" -m vibephysics.feedforward.export blend \
    --predictions "$PREDICTIONS" \
    --output "$OUTPUT" \
    --no-align-ground \
    "${EXTRA[@]}"
