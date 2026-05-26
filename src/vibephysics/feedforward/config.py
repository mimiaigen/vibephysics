"""YAML config loading for feedforward reconstruction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .common import DEFAULT_LINGBOT_MAP_MODEL, DEFAULT_VIDEO_FPS

CONFIGS_DIR = Path(__file__).resolve().parent / "configs"
DEFAULT_FEEDFORWARD_CONFIG = CONFIGS_DIR / "feedforward.yaml"

FEEDFORWARD_ENGINES = ("lingbot_map", "vggt_omega")

MAX_FRAMES_MODES = ("spread", "first")


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    path = Path(path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open() as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a YAML mapping: {path}")
    return data


def _require(cfg: dict[str, Any], key: str, config_path: Path | None = None) -> Any:
    if key not in cfg or cfg[key] in (None, ""):
        prefix = f"{config_path}: " if config_path else ""
        raise ValueError(f"{prefix}missing required config key '{key}'")
    return cfg[key]


def _nested(cfg: dict[str, Any], key: str) -> dict[str, Any]:
    value = cfg.get(key) or {}
    if not isinstance(value, dict):
        raise ValueError(f"Config section '{key}' must be a mapping")
    return value


def apply_overrides(cfg: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = dict(cfg)
    for key, value in overrides.items():
        if value is not None:
            merged[key] = value
    return merged


def apply_video_frame_overrides(
    cfg: dict[str, Any],
    *,
    max_frames: int | None = None,
    max_frames_mode: str | None = None,
) -> dict[str, Any]:
    """Apply CLI overrides to the unified ``video`` input section."""
    if max_frames is None and max_frames_mode is None:
        return cfg
    video = dict(_nested(cfg, "video"))
    if max_frames is not None:
        video["max_frames"] = max_frames
    if max_frames_mode is not None:
        video["max_frames_mode"] = max_frames_mode
    merged = dict(cfg)
    merged["video"] = video
    return merged


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _normalize_max_frames_mode(mode: Any) -> str:
    normalized = str(mode).strip().lower()
    if normalized not in MAX_FRAMES_MODES:
        raise ValueError(
            f"Unknown max_frames_mode '{mode}'. Choose one of: {', '.join(MAX_FRAMES_MODES)}"
        )
    return normalized


def resolve_input_frame_limits(
    cfg: dict[str, Any],
    engine: str | None = None,
) -> tuple[int | None, str]:
    """
    Unified frame limits for all feedforward engines.

    Resolution order (first wins):
      1. ``video.max_frames`` / ``video.max_frames_mode``
      2. ``<engine>.max_frames`` / ``<engine>.max_frames_mode`` (legacy per-engine override)
      3. ``<engine>.batch_size`` (legacy alias for max_frames only)
    """
    video = cfg.get("video") or {}
    if not isinstance(video, dict):
        video = {}

    max_frames = _optional_int(video.get("max_frames"))
    mode_raw = video.get("max_frames_mode")

    if engine and max_frames is None:
        section = cfg.get(engine) or {}
        if isinstance(section, dict):
            max_frames = _optional_int(section.get("max_frames", section.get("batch_size")))
            if mode_raw in (None, ""):
                mode_raw = section.get("max_frames_mode")

    if max_frames is None and engine:
        section = cfg.get(engine) or {}
        if isinstance(section, dict):
            max_frames = _optional_int(section.get("batch_size"))

    mode = _normalize_max_frames_mode(mode_raw if mode_raw not in (None, "") else "first")
    return max_frames, mode


def _optional_path(value: Any) -> Any:
    if value in (None, ""):
        return None
    return value


def parse_feedforward_config(cfg: dict[str, Any], config_path: Path | None = None) -> dict[str, Any]:
    engine = _require(cfg, "engine", config_path)
    if engine not in FEEDFORWARD_ENGINES:
        raise ValueError(
            f"Invalid feedforward engine '{engine}'. Choose one of: {', '.join(FEEDFORWARD_ENGINES)}"
        )

    lingbot_map = _nested(cfg, "lingbot_map")
    vggt_omega = _nested(cfg, "vggt_omega")
    output = _nested(cfg, "output")
    video = _nested(cfg, "video")

    max_frames, max_frames_mode = resolve_input_frame_limits(cfg, engine)

    return {
        "image_path": _require(cfg, "image_path", config_path),
        "output_path": cfg.get("output_path"),
        "engine": engine,
        "verbose": cfg.get("verbose", True),
        "video_fps": video.get("fps", DEFAULT_VIDEO_FPS),
        "video_quality": video.get("quality", 2),
        "save_blend": output.get("save_blend", "scene.blend"),
        "min_confidence": output.get("min_confidence", 0.5),
        "filter_edges": output.get("filter_edges", True),
        "point_scale": output.get("point_scale", 1.0),
        "animate": output.get("animate", True),
        "animation_fps": output.get("animation_fps", 24),
        "align_ground": output.get("align_ground", True),
        "max_frames": max_frames,
        "max_frames_mode": max_frames_mode,
        "use_sdpa": lingbot_map.get("use_sdpa", False),
        "lingbot_map_mode": lingbot_map.get("mode"),
        "keyframe_interval": lingbot_map.get("keyframe_interval"),
        "window_size": lingbot_map.get("window_size", 64),
        "overlap_size": lingbot_map.get("overlap_size", 16),
        "overlap_keyframes": lingbot_map.get("overlap_keyframes"),
        "mask_sky": lingbot_map.get("mask_sky", False),
        "lingbot_map_image_size": lingbot_map.get("image_size", 518),
        "lingbot_map_model": lingbot_map.get("model", DEFAULT_LINGBOT_MAP_MODEL),
        "lingbot_map_checkpoint": _optional_path(lingbot_map.get("checkpoint")),
        "vggt_omega_checkpoint": _optional_path(vggt_omega.get("checkpoint")),
        "vggt_omega_checkpoint_name": vggt_omega.get("checkpoint_name", "vggt-omega-1b-512"),
        "vggt_omega_resolution": vggt_omega.get("resolution", 512),
        "vggt_omega_preprocess_mode": vggt_omega.get("preprocess_mode", "balanced"),
        "vggt_omega_enable_alignment": vggt_omega.get("enable_alignment", False),
        "vggt_omega_conf_percentile": vggt_omega.get("conf_percentile", 50.0),
        "vggt_omega_depth_edge_rtol": vggt_omega.get("depth_edge_rtol", 0.03),
    }
