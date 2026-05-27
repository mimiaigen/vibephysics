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
    echo "Usage: $0 --input <scene.blend> [--output <clean.blend>] [--point_scale SIZE] [options]"
    echo ""
    echo "Cleans a .blend by removing trajectory/path helpers and target-cross helpers,"
    echo "setting a pure black background, and disabling viewport grid overlays."
    echo ""
    echo "Options:"
    echo "  --point_scale SIZE      Set existing point clouds to an absolute point radius"
    echo "  --keep-traj           Keep trajectory/path helper objects"
    echo "  --keep-target-cross   Keep target cross helper objects"
    echo "  --keep-grid           Keep viewport grid overlays"
    echo "  --keep-background     Keep existing world/background settings"
    echo "  --compress            Compress the saved .blend"
    echo ""
    echo "Example:"
    echo "  $0 --input feedforward_output/run/scene.blend --output feedforward_output/run/scene_clean.blend"
    exit 1
}

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --input|-i) INPUT="$2"; shift ;;
        --output|-o) OUTPUT="$2"; shift ;;
        --point_scale|--point-scale) POINT_SCALE="$2"; shift ;;
        --keep-traj|--keep_traj) KEEP_TRAJ=1 ;;
        --keep-target-cross|--keep_target_cross) KEEP_TARGET_CROSS=1 ;;
        --keep-grid|--keep_grid) KEEP_GRID=1 ;;
        --keep-background|--keep_background) KEEP_BACKGROUND=1 ;;
        --compress) COMPRESS=1 ;;
        -h|--help) usage ;;
        *) echo "Unknown parameter: $1"; usage ;;
    esac
    shift
done

if [[ -z "$INPUT" ]]; then
    usage
fi

if ! resolve_python; then
    echo "Error: no Python with PyPI bpy found." >&2
    echo "Use Python 3.11 with: pip install vibephysics bpy" >&2
    echo "Or set VIBEPHYSICS_PYTHON=/path/to/python" >&2
    exit 1
fi

export PYTHONPATH="${SCRIPT_DIR}/src${PYTHONPATH:+:$PYTHONPATH}"

ARGS=(--input "$INPUT")
[ -n "${OUTPUT:-}" ] && ARGS+=(--output "$OUTPUT")
[ -n "${POINT_SCALE:-}" ] && ARGS+=(--point_scale "$POINT_SCALE")
[ -n "${KEEP_TRAJ:-}" ] && ARGS+=(--keep-traj)
[ -n "${KEEP_TARGET_CROSS:-}" ] && ARGS+=(--keep-target-cross)
[ -n "${KEEP_GRID:-}" ] && ARGS+=(--keep-grid)
[ -n "${KEEP_BACKGROUND:-}" ] && ARGS+=(--keep-background)
[ -n "${COMPRESS:-}" ] && ARGS+=(--compress)

echo "--- [run_postprocess_blend] Python: $PYTHON ---"
exec "$PYTHON" -m vibephysics.setup.postprocess_blend "${ARGS[@]}"
