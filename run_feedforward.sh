#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_LABEL="run_feedforward"
source "$SCRIPT_DIR/feedforward_run.inc.sh"

usage() {
    echo "Usage: $0 --method <method> --input <path> [common feedforward args]"
    echo ""
    echo "Examples:"
    echo "  $0 --method vggt_omega --input path/to/images"
    echo "  $0 --method lingbot_map --input test_recording.MOV --max_frames 50"
    echo "  $0 --method r3_long --input path/to/video.MOV"
    echo "  $0 --method da3 --input path/to/images"
    echo "  $0 --method mapanything --input path/to/images --blend"
    echo ""
    echo "Direct engines:"
    echo "  lingbot_map, vggt_omega, vgg_ttt, r3, r3_long, dvlt, map_anything"
    echo ""
    echo "Map-Anything factory methods (known examples; unknown methods route here too):"
    echo "  mapanything, mapanything_apache, mapanything_ablations, vggt, moge,"
    echo "  pi3, pi3x, dust3r, mast3r, must3r, modular_dust3r, pow3r, pow3r_ba,"
    echo "  anycalib, da3"
    echo ""
    echo "Common args are forwarded, including:"
    echo "  --input/--image_path, --output_path, --point_scale, --max_frames,"
    echo "  --max_frames_mode, --min_confidence, --random_points_per_frame, --total_random_points,"
    echo "  --split_files, --animation_mode, --only_start_frame_pose,"
    echo "  --keep_start_frame_point_cloud,"
    echo "  --point_cloud_3d_nms, --point_cloud_3d_nms_radius, --point_cloud_3d_nms_min_neighbors,"
    echo "  --detection_seg (masks + 3D bboxes + voxels), --detection_seg_classes,"
    echo "  --algo_3d_bbox (voxel-diff only, without RF-DETR),"
    echo "  --mode, --config,"
    echo "  --blend, --html, --frames, --no-install, --install-all"
    exit 1
}

METHOD=""
CONFIG="${CONFIG:-}"
INPUT=""
MAP_MODEL=""
MAP_MODEL_SET=0
INSTALL_ALL=0
BLEND=0
HTML=0
FRAMES=0
RANDOM_POINTS_PER_FRAME=""
TOTAL_RANDOM_POINTS=""
ARGS=()

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --method|-m)
            METHOD="$2"
            shift
            ;;
        --config)
            CONFIG="$2"
            shift
            ;;
        --input|--image_path)
            INPUT="$2"
            ARGS+=("$1" "$2")
            shift
            ;;
        --model)
            MAP_MODEL="$2"
            MAP_MODEL_SET=1
            ARGS+=("$1" "$2")
            shift
            ;;
        --install-all|--install_all|--map-anything-install-all|--map_anything_install_all)
            INSTALL_ALL=1
            ;;
        --blend)
            BLEND=1
            ;;
        --html)
            HTML=1
            ;;
        --frames)
            FRAMES=1
            ;;
        --random_points_per_frame|--random-points-per-frame)
            RANDOM_POINTS_PER_FRAME="$2"
            shift
            ;;
        --total_random_points|--total-random-points)
            TOTAL_RANDOM_POINTS="$2"
            shift
            ;;
        --no-install|--no_install)
            export VIBEPHYSICS_NO_AUTO_INSTALL=1
            ;;
        -h|--help)
            usage
            ;;
        *)
            ARGS+=("$1")
            ;;
    esac
    shift
done

if [ -z "$METHOD" ]; then
    echo "Error: --method is required." >&2
    usage
fi

normalize_method() {
    printf '%s' "$1" | tr '[:upper:]-' '[:lower:]_'
}

args_have_max_frames() {
    local arg
    for arg in "${ARGS[@]}"; do
        case "$arg" in
            --max_frames|--max-frames)
                return 0
                ;;
        esac
    done
    return 1
}

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

make_runtime_config() {
    local r3_model="$1"
    local source_config="${CONFIG:-$DEFAULT_CONFIG}"
    local tmp_config
    tmp_config="$(mktemp "${TMPDIR:-/tmp}/vibephysics_feedforward.XXXXXX.yaml")"
    "$PYTHON" - "$source_config" "$tmp_config" "$ENGINE" "$r3_model" "$BLEND" "$HTML" "$FRAMES" "$RANDOM_POINTS_PER_FRAME" "$TOTAL_RANDOM_POINTS" <<'PY'
import sys
from pathlib import Path

import yaml

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
engine = sys.argv[3]
r3_model = sys.argv[4]
blend = sys.argv[5] == "1"
html = sys.argv[6] == "1"
frames = sys.argv[7] == "1"
random_points_per_frame = sys.argv[8]
total_random_points = sys.argv[9]

cfg = yaml.safe_load(src.read_text())
if not isinstance(cfg, dict):
    raise SystemExit(f"Config is not a YAML mapping: {src}")
output = cfg.setdefault("output", {})
if not isinstance(output, dict):
    raise SystemExit("Config section 'output' must be a mapping")
cfg["engine"] = engine
output["save_blend"] = "scene.blend" if blend else None
output["save_html"] = "visual.html" if html else None
output["save_frames"] = frames
if random_points_per_frame.lower() not in {"", "none", "null"}:
    output["random_points_per_frame"] = (
        None if random_points_per_frame == "0" else float(random_points_per_frame)
    )
if total_random_points.lower() not in {"", "none", "null"}:
    output["total_random_points"] = (
        None if total_random_points == "0" else float(total_random_points)
    )

if r3_model:
    section = cfg.setdefault("r3", {})
    if not isinstance(section, dict):
        raise SystemExit("Config section 'r3' must be a mapping")
    section["model"] = r3_model
dst.write_text(yaml.safe_dump(cfg, sort_keys=False))
PY
    printf '%s' "$tmp_config"
}

METHOD_NORM="$(normalize_method "$METHOD")"
ENGINE=""
DEFAULT_CONFIG="$SCRIPT_DIR/src/vibephysics/feedforward/configs/feedforward.yaml"
R3_MODEL=""

case "$METHOD_NORM" in
    lingbot|lingbot_map)
        ENGINE="lingbot_map"
        ;;
    vggt_omega|vggtomega)
        ENGINE="vggt_omega"
        ;;
    vgg_ttt|vggttt)
        ENGINE="vgg_ttt"
        ;;
    r3)
        ENGINE="r3"
        R3_MODEL="r3"
        ;;
    r3_long|r3long)
        ENGINE="r3"
        R3_MODEL="r3_long"
        ;;
    dvlt|deja_view|dejaview|deja-view)
        ENGINE="dvlt"
        ;;
    map_anything|mapanything_engine)
        ENGINE="map_anything"
        ;;
    *)
        # Treat remaining methods as Map-Anything factory keys. This keeps the
        # unified CLI forward-compatible when Map-Anything adds new model names.
        ENGINE="map_anything"
        if [ "$MAP_MODEL_SET" -eq 0 ]; then
            MAP_MODEL="$METHOD_NORM"
        fi
        ;;
esac

if ! resolve_python; then
    echo "Error: no Python with vibephysics + bpy found." >&2
    echo "PyPI bpy 5.0 requires Python 3.11 (not 3.12+)." >&2
    echo "Checked:" >&2
    while IFS= read -r candidate; do diagnose_python "$candidate"; done < <(collect_python_candidates)
    echo "" >&2
    echo "Fix options:" >&2
    echo '  conda create -n vibephysics python=3.11 && conda activate vibephysics' >&2
    echo '  pip install "numpy<2" vibephysics bpy' >&2
    echo "Or set VIBEPHYSICS_PYTHON=/path/to/python" >&2
    exit 1
fi

export PYTHONPATH="${SCRIPT_DIR}/src${PYTHONPATH:+:$PYTHONPATH}"
export KMP_DUPLICATE_LIB_OK=TRUE
export TQDM_DISABLE="${TQDM_DISABLE:-0}"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"
export TORCHDYNAMO_DISABLE="${TORCHDYNAMO_DISABLE:-1}"

[ -z "$CONFIG" ] && CONFIG="$DEFAULT_CONFIG"

TMP_CONFIG=""
TMP_CONFIG="$(make_runtime_config "$R3_MODEL")"
trap 'rm -f "$TMP_CONFIG"' EXIT
CONFIG="$TMP_CONFIG"

DETECTION_SEG=0
for arg in "${ARGS[@]}"; do
    if [ "$arg" = "--detection_seg" ]; then
        DETECTION_SEG=1
        break
    fi
done

if ! "$PYTHON" - "$ENGINE" "$CONFIG" "$MAP_MODEL" "$INSTALL_ALL" "$DETECTION_SEG" <<'PY'
import sys
from pathlib import Path

engine, config_path, map_model, install_all_raw, detection_seg_raw = sys.argv[1:6]
install_all = install_all_raw == "1"
detection_seg = detection_seg_raw == "1"

if engine == "lingbot_map":
    from vibephysics.feedforward.lingbot_map import ensure_dependencies

    ok = ensure_dependencies()
elif engine == "vggt_omega":
    from vibephysics.feedforward.vggt_omega import ensure_dependencies

    ok = ensure_dependencies()
elif engine == "vgg_ttt":
    from vibephysics.feedforward.vgg_ttt import ensure_dependencies

    ok = ensure_dependencies()
elif engine == "r3":
    from vibephysics.feedforward.r3 import ensure_dependencies

    ok = ensure_dependencies()
elif engine == "dvlt":
    from vibephysics.feedforward.dvlt import ensure_dependencies

    ok = ensure_dependencies()
elif engine == "map_anything":
    from vibephysics.feedforward.config import load_yaml_config
    from vibephysics.feedforward.map_anything import ensure_dependencies

    cfg = load_yaml_config(Path(config_path))
    model = map_model or (cfg.get("map_anything") or {}).get("model") or "vggt"
    ok = ensure_dependencies(model_name=model, install_all=install_all)
else:
    raise SystemExit(f"Unknown feedforward engine: {engine}")

if ok:
    if not detection_seg:
        from vibephysics.feedforward.config import detection_seg_enabled, load_yaml_config

        cfg = load_yaml_config(Path(config_path))
        detection_seg = detection_seg_enabled(cfg.get("detection_seg"))
    if detection_seg:
        from vibephysics.feedforward.detection_seg import ensure_detection_seg_dependencies

        ensure_detection_seg_dependencies(verbose=True)

raise SystemExit(0 if ok else 1)
PY
then
    echo "--- [run_feedforward] Dependencies unavailable for method '$METHOD'. ---" >&2
    exit 1
fi

RECON_ARGS=(--config "$CONFIG")
RECON_ARGS+=("${ARGS[@]}")
if [ "$ENGINE" = "map_anything" ]; then
    if [ "$MAP_MODEL_SET" -eq 0 ] && [ -n "$MAP_MODEL" ]; then
        RECON_ARGS+=(--model "$MAP_MODEL")
    fi
    [ "$INSTALL_ALL" -eq 1 ] && RECON_ARGS+=(--map-anything-install-all)
fi

echo "--- [run_feedforward] Method: $METHOD_NORM (engine=$ENGINE) ---"
echo "--- [run_feedforward] Python: $PYTHON ---"
if [ "$(uname -s)" = "Darwin" ] && [ "$ENGINE" = "r3" ]; then
    if [ "$R3_MODEL" = "r3_long" ] && ! args_have_max_frames; then
        echo "--- [run_feedforward] Warning: r3_long on Mac/MPS can be killed by memory pressure on longer clips. Use --max_frames N or --method r3 for the smaller checkpoint. ---"
    fi
fi
feedforward_print_frame_plan "$CONFIG" "${INPUT:-}" "$ENGINE"

"$PYTHON" -m vibephysics.feedforward.reconstruct "${RECON_ARGS[@]}"
status=$?
if [ "$status" -eq 137 ] || [ "$status" -eq 9 ]; then
    echo "--- [run_feedforward] Process was killed by the OS (SIGKILL), usually memory pressure. ---" >&2
    if [ "$ENGINE" = "r3" ]; then
        echo "--- [run_feedforward] For R3 on Mac/MPS, retry with: --method r3 --max_frames 4 (or another small N). r3_long is best on Linux + CUDA. ---" >&2
    fi
fi
exit "$status"
