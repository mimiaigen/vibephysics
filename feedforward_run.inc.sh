# Shared CLI helpers for the unified feedforward runner.
# Source from run_feedforward.sh:  source "$SCRIPT_DIR/feedforward_run.inc.sh"

feedforward_usage_frame_args() {
    echo "  --max_frames N          Use at most N frames (see --max_frames_mode)"
    echo "  --max_frames_mode MODE  first (default) | spread"
    echo "                        first  = first N consecutive frames (default)"
    echo "                        spread = evenly across full input"
    echo "  --point_scale SIZE      Absolute point radius in the saved .blend (default from YAML)"
}

feedforward_parse_frame_args() {
    while [[ "$#" -gt 0 ]]; do
        case $1 in
            --max_frames) MAX_FRAMES="$2"; shift ;;
            --max_frames_mode) MAX_FRAMES_MODE="$2"; shift ;;
            *) break ;;
        esac
        shift
    done
}

feedforward_append_frame_args() {
    [ -n "${MAX_FRAMES:-}" ] && ARGS+=(--max_frames "$MAX_FRAMES")
    [ -n "${MAX_FRAMES_MODE:-}" ] && ARGS+=(--max_frames_mode "$MAX_FRAMES_MODE")
    [ -n "${POINT_SCALE:-}" ] && ARGS+=(--point_scale "$POINT_SCALE")
}

feedforward_print_frame_plan() {
    local config_path="$1"
    local input_path="$2"
    local engine_override="${3:-}"
    [ -z "${input_path:-}" ] && return 0
    local plan
    plan=$("$PYTHON" -c "
import sys
sys.path.insert(0, '${SCRIPT_DIR}/src')
try:
    from vibephysics.feedforward.config import (
        load_yaml_config,
        resolve_input_frame_limits,
        apply_video_frame_overrides,
    )
    from vibephysics.feedforward.common import get_vram_gb, preview_feedforward_input_plan
    cfg = load_yaml_config('${config_path}')
    cli_max = '${MAX_FRAMES:-}'
    cli_mode = '${MAX_FRAMES_MODE:-}'
    cfg = apply_video_frame_overrides(
        cfg,
        max_frames=int(cli_max) if cli_max else None,
        max_frames_mode=cli_mode or None,
    )
    engine = '${engine_override}' or cfg.get('engine', 'lingbot_map')
    mf, mode = resolve_input_frame_limits(cfg, engine)
    video = cfg.get('video') or {}
    lm = cfg.get('lingbot_map') or {}
    lingbot = engine == 'lingbot_map'
    print(preview_feedforward_input_plan(
        engine,
        '${input_path}',
        mode=lm.get('mode') if lingbot else None,
        keyframe_interval=lm.get('keyframe_interval') if lingbot else None,
        max_streaming_keyframes=lm.get('max_streaming_keyframes') if lingbot else None,
        vram_gb=get_vram_gb() if lingbot else None,
        max_frames=mf,
        max_frames_mode=mode,
        video_fps=video.get('fps', 2),
        window_size=lm.get('window_size', 64),
        overlap_size=lm.get('overlap_size', 16),
    ))
except Exception as exc:
    print(f'Frame plan preview unavailable: {exc}')
" 2>/dev/null) || return 0
    if [ -n "${plan:-}" ]; then
        echo "--- [${RUN_LABEL:-feedforward}] ${plan} ---"
    fi
}
