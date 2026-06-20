"""YAML config loading for feedforward reconstruction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .common import DEFAULT_LINGBOT_MAP_MODEL, DEFAULT_VIDEO_FPS

CONFIGS_DIR = Path(__file__).resolve().parent / "configs"
DEFAULT_FEEDFORWARD_CONFIG = CONFIGS_DIR / "feedforward.yaml"

FEEDFORWARD_ENGINES = ("lingbot_map", "vggt_omega", "vgg_ttt", "map_anything", "r3", "dvlt")

MAX_FRAMES_MODES = ("spread", "first")
POINT_DISPLAY_MODES = ("pointcloud", "points", "spheres")
DEFAULT_POINT_SCALE = 0.004

# Keys under ``output`` in feedforward.yaml (same names in reconstruct_config.json).
OUTPUT_SETTING_KEYS = (
    "save_blend",
    "save_html",
    "save_frames",
    "split_files",
    "min_confidence",
    "filter_edges",
    "random_points_per_frame",
    "total_random_points",
    "point_cloud_3d_nms",
    "point_cloud_3d_nms_radius",
    "point_cloud_3d_nms_min_neighbors",
    "align_ground",
    "algo_3d_bbox",
    "only_start_frame_pose",
)

_LEGACY_OUTPUT_ALIASES = {
    "point_random_points_per_frame": "random_points_per_frame",
    "point_total_random_points": "total_random_points",
}

# Keys under ``output.blend`` (``.blend`` export / viewport only).
BLEND_OUTPUT_KEYS = (
    "point_scale",
    "point_display",
    "animate",
    "animation_fps",
    "animation_mode",
    "keep_start_frame_point_cloud",
)


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


def default_algo_3d_bbox_config() -> dict[str, Any]:
    """``algo_3d_bbox`` defaults from ``configs/feedforward.yaml``."""
    return _nested(load_yaml_config(DEFAULT_FEEDFORWARD_CONFIG), "algo_3d_bbox")


def default_detection_seg_config() -> dict[str, Any]:
    """``detection_seg`` defaults from ``configs/feedforward.yaml``."""
    return _nested(load_yaml_config(DEFAULT_FEEDFORWARD_CONFIG), "detection_seg")


def detection_seg_default(key: str) -> Any:
    section = default_detection_seg_config()
    if key not in section:
        raise ValueError(
            f"detection_seg.{key} missing in {DEFAULT_FEEDFORWARD_CONFIG}. "
            "Add it under the detection_seg section."
        )
    return section[key]


def _parse_rgba(value: Any) -> tuple[float, float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) < 3:
        raise ValueError(f"Expected [r, g, b] or [r, g, b, a], got {value!r}")
    nums = [float(v) for v in value[:4]]
    if len(nums) == 3:
        nums.append(1.0)
    if max(nums) > 1.0:
        nums = [c / 255.0 for c in nums]
    return (nums[0], nums[1], nums[2], nums[3])


_NAMED_COLORS: dict[str, tuple[float, float, float, float]] = {
    "cyan": (0.0, 0.85, 1.0, 1.0),
    "red": (1.0, 0.0, 0.0, 1.0),
    "green": (0.25, 0.9, 0.4, 1.0),
    "blue": (0.2, 0.45, 1.0, 1.0),
    "orange": (1.0, 0.45, 0.1, 1.0),
    "yellow": (1.0, 0.9, 0.2, 1.0),
    "magenta": (1.0, 0.2, 0.55, 1.0),
    "purple": (0.55, 0.35, 1.0, 1.0),
    "white": (1.0, 1.0, 1.0, 1.0),
    "black": (0.05, 0.05, 0.05, 1.0),
    "pink": (1.0, 0.5, 0.7, 1.0),
    "lime": (0.6, 1.0, 0.2, 1.0),
}

_CLASS_COLOR_DEFAULTS: dict[str, tuple[float, float, float, float]] = {
    "person": _NAMED_COLORS["cyan"],
    "oven": _NAMED_COLORS["red"],
    "microwave": _NAMED_COLORS["orange"],
    "toaster": _NAMED_COLORS["yellow"],
    "sink": _NAMED_COLORS["green"],
    "refrigerator": (0.69, 0.88, 1.0, 1.0),
    "dining table": _NAMED_COLORS["lime"],
    "bottle": _NAMED_COLORS["purple"],
    "cup": _NAMED_COLORS["blue"],
    "bowl": _NAMED_COLORS["magenta"],
    "chair": (0.55, 0.27, 0.07, 1.0),
    "couch": (0.27, 0.51, 0.71, 1.0),
    "bed": _NAMED_COLORS["pink"],
    "tv": _NAMED_COLORS["white"],
    "car": _NAMED_COLORS["magenta"],
}

_CLASS_COLOR_FALLBACK = (
    (1.0, 0.35, 0.35, 1.0),
    (0.35, 1.0, 0.45, 1.0),
    (0.35, 0.55, 1.0, 1.0),
    (1.0, 0.75, 0.3, 1.0),
    (0.85, 0.35, 1.0, 1.0),
)


def _normalize_detection_class_name(name: str) -> str:
    from .detection_seg import CLASS_ALIASES

    key = str(name).strip().lower()
    return CLASS_ALIASES.get(key, key)


def _resolve_color_token(token: str | None) -> tuple[float, float, float, float] | None:
    if token is None:
        return None
    key = str(token).strip().lower()
    if not key:
        return None
    if key in _NAMED_COLORS:
        return _NAMED_COLORS[key]
    if key.startswith("[") and key.endswith("]"):
        import ast

        try:
            parsed = ast.literal_eval(key)
            return _parse_rgba(parsed)
        except (SyntaxError, ValueError, TypeError):
            pass
    if key.replace(".", "", 1).isdigit() and "," in key:
        parts = [p.strip() for p in key.split(",")]
        if len(parts) >= 3:
            return _parse_rgba(parts)
    return None


def _parse_class_color_entry(item: Any) -> tuple[str, str | None]:
    """One YAML row: ``person``, ``person, cyan``, or ``[person, cyan]``."""
    if isinstance(item, (list, tuple)):
        parts = [str(x).strip() for x in item if str(x).strip()]
        if not parts:
            raise ValueError(f"Empty detection_seg class entry: {item!r}")
        name = _normalize_detection_class_name(parts[0])
        color = parts[1] if len(parts) > 1 else None
        return name, color

    text = str(item).strip()
    if not text:
        raise ValueError(f"Empty detection_seg class entry: {item!r}")
    if "," in text:
        name_part, color_part = text.split(",", 1)
        name = _normalize_detection_class_name(name_part)
        color = color_part.strip() or None
        return name, color
    return _normalize_detection_class_name(text), None


def _entries_from_flat_tokens(tokens: list[str]) -> list[tuple[str, str | None]]:
    """CLI ``person,cyan,oven,red`` -> pairs; ``person,oven,sink`` -> names only."""
    cleaned = [t.strip() for t in tokens if t.strip()]
    if not cleaned:
        return [("person", None)]
    if len(cleaned) >= 2 and len(cleaned) % 2 == 0:
        paired: list[tuple[str, str | None]] = []
        for i in range(0, len(cleaned), 2):
            paired.append(
                (_normalize_detection_class_name(cleaned[i]), cleaned[i + 1])
            )
        if all(_resolve_color_token(c) is not None for _, c in paired):
            return paired
    return [( _normalize_detection_class_name(t), None) for t in cleaned]


def parse_detection_seg_classes(
    raw: Any,
) -> tuple[list[str], dict[str, tuple[float, float, float, float]]]:
    """
    Parse ``classes`` from YAML/CLI.

    Each entry is a class name, optionally followed by a color after a comma
    (spaces optional): ``person, cyan``, ``oven,red``, or ``- [person, cyan]``.
    """
    entries: list[tuple[str, str | None]] = []
    if raw is None:
        entries = [("person", None)]
    elif isinstance(raw, str):
        entries = _entries_from_flat_tokens(raw.split(","))
    elif isinstance(raw, (list, tuple)):
        for item in raw:
            entries.append(_parse_class_color_entry(item))
    else:
        entries = [("person", None)]

    names: list[str] = []
    colors: dict[str, tuple[float, float, float, float]] = {}
    fallback_i = 0
    for name, color_token in entries:
        if not name or name in names:
            continue
        names.append(name)
        rgba = _resolve_color_token(color_token)
        if rgba is None:
            if name in _CLASS_COLOR_DEFAULTS:
                rgba = _CLASS_COLOR_DEFAULTS[name]
            else:
                rgba = _CLASS_COLOR_FALLBACK[
                    fallback_i % len(_CLASS_COLOR_FALLBACK)
                ]
                fallback_i += 1
        colors[name] = rgba
    if not names:
        names = ["person"]
        colors = {"person": _CLASS_COLOR_DEFAULTS["person"]}
    return names, colors


def format_detection_seg_class_entries(
    classes: list[str],
    colors: dict[str, tuple[float, float, float, float]],
) -> list[str]:
    """Serialize classes for YAML (``person, cyan`` when a named color matches)."""
    entries: list[str] = []
    for name in classes:
        rgba = colors.get(name)
        if rgba is None:
            entries.append(name)
            continue
        token: str | None = None
        for color_name, named in _NAMED_COLORS.items():
            if all(abs(a - b) < 1e-3 for a, b in zip(rgba[:3], named[:3])):
                token = color_name
                break
        if token is not None:
            entries.append(f"{name}, {token}")
        else:
            entries.append(
                f"{name}, [{int(rgba[0] * 255)}, {int(rgba[1] * 255)}, "
                f"{int(rgba[2] * 255)}, {int(rgba[3] * 255)}]"
            )
    return entries


def _detection_seg_classes_from_section(
    detection_seg: dict[str, Any],
) -> tuple[list[str], dict[str, tuple[float, float, float, float]]]:
    classes, colors = parse_detection_seg_classes(
        detection_seg.get("classes", detection_seg_default("classes"))
    )
    legacy = detection_seg.get("class_colors")
    if isinstance(legacy, dict):
        for key, value in legacy.items():
            colors[str(key)] = _parse_rgba(value)
    return classes, colors


def algo_3d_bbox_default(key: str) -> Any:
    """Read one ``algo_3d_bbox`` key from the packaged feedforward YAML."""
    section = default_algo_3d_bbox_config()
    if key not in section:
        raise ValueError(
            f"algo_3d_bbox.{key} missing in {DEFAULT_FEEDFORWARD_CONFIG}. "
            "Add it under the algo_3d_bbox section."
        )
    return section[key]


def default_output_config() -> dict[str, Any]:
    """``output`` defaults from ``configs/feedforward.yaml``."""
    return _nested(load_yaml_config(DEFAULT_FEEDFORWARD_CONFIG), "output")


def output_default(key: str) -> Any:
    """Read one ``output`` key from the packaged feedforward YAML."""
    section = default_output_config()
    if key not in section:
        raise ValueError(
            f"output.{key} missing in {DEFAULT_FEEDFORWARD_CONFIG}. "
            "Add it under the output section."
        )
    return section[key]


def default_blend_config() -> dict[str, Any]:
    """``output.blend`` defaults from ``configs/feedforward.yaml``."""
    output = default_output_config()
    blend = output.get("blend")
    if isinstance(blend, dict):
        return dict(blend)
    return {}


def blend_default(key: str) -> Any:
    """Read one Blender-only key from ``output.blend`` (legacy: top-level ``output``)."""
    if key not in BLEND_OUTPUT_KEYS:
        raise ValueError(f"Not a blend output key: {key!r}")
    blend = default_blend_config()
    if key in blend:
        return blend[key]
    output = default_output_config()
    if key in output:
        return output[key]
    raise ValueError(
        f"output.blend.{key} missing in {DEFAULT_FEEDFORWARD_CONFIG}. "
        "Add it under output.blend."
    )


def resolve_blend_settings(output: dict[str, Any]) -> dict[str, Any]:
    """Resolve Blender export settings from ``output.blend`` with legacy fallbacks."""
    nested = output.get("blend")
    nested = dict(nested) if isinstance(nested, dict) else {}
    packaged = default_blend_config()
    resolved: dict[str, Any] = {}
    for key in BLEND_OUTPUT_KEYS:
        if key in nested:
            resolved[key] = nested[key]
        elif key in output:
            resolved[key] = output[key]
        elif key in packaged:
            resolved[key] = packaged[key]
        else:
            raise ValueError(
                f"output.blend.{key} missing. Add it under output.blend in the config."
            )
    return resolved


def _read_saved_setting(config: dict[str, Any], key: str) -> Any | None:
    """Read one setting from reconstruct_config (nested ``output``/``blend`` or legacy flat)."""
    nested = config.get("output")
    if isinstance(nested, dict) and key in nested:
        return nested[key]
    if key in config:
        return config[key]
    for legacy, canon in _LEGACY_OUTPUT_ALIASES.items():
        if canon != key:
            continue
        if legacy in config:
            return config[legacy]
        if isinstance(nested, dict) and legacy in nested:
            return nested[legacy]
    return None


def output_settings_from_reconstruct_config(config: dict[str, Any]) -> dict[str, Any]:
    """Resolve ``output.*`` keys from a saved reconstruct_config (YAML names)."""
    packaged = default_output_config()
    resolved: dict[str, Any] = {}
    for key in OUTPUT_SETTING_KEYS:
        val = _read_saved_setting(config, key)
        if val is None and key in packaged:
            val = packaged[key]
        if val is not None:
            resolved[key] = val
    return resolved


def blend_settings_from_reconstruct_config(config: dict[str, Any]) -> dict[str, Any]:
    """Read blend settings saved in ``reconstruct_config.json`` (nested or legacy flat)."""
    nested = config.get("blend")
    if isinstance(nested, dict):
        base = dict(nested)
    else:
        base = {}
    for key in BLEND_OUTPUT_KEYS:
        if key not in base and key in config:
            base[key] = config[key]
    return base


def detection_seg_enabled(detection_seg_section: dict[str, Any] | None) -> bool:
    if not isinstance(detection_seg_section, dict):
        return False
    return bool(detection_seg_section.get("enabled", False))


def resolve_algo_3d_bbox_enabled(
    output: dict[str, Any],
    detection_seg_section: dict[str, Any] | None,
) -> bool:
    """Voxel-diff bboxes from ``output.algo_3d_bbox``, or always on when detection_seg is enabled."""
    return bool(output.get("algo_3d_bbox", False)) or detection_seg_enabled(
        detection_seg_section
    )


def _output_value(output: dict[str, Any], key: str) -> Any:
    """Read one ``output`` key from a config dict (legacy aliases + packaged default)."""
    if key in output:
        return output[key]
    for legacy, canon in _LEGACY_OUTPUT_ALIASES.items():
        if canon == key and legacy in output:
            return output[legacy]
    return output_default(key)


def normalize_point_display(value: Any) -> str:
    mode = str(value).strip().lower()
    if mode not in POINT_DISPLAY_MODES:
        raise ValueError(
            f"output.blend.point_display must be one of: {', '.join(POINT_DISPLAY_MODES)}"
        )
    return mode


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


def _optional_positive_int(value: Any) -> int | None:
    parsed = _optional_int(value)
    if parsed is None or parsed <= 0:
        return None
    return parsed


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
    vgg_ttt = _nested(cfg, "vgg_ttt")
    map_anything = _nested(cfg, "map_anything")
    r3 = _nested(cfg, "r3")
    dvlt = _nested(cfg, "dvlt")
    output = _nested(cfg, "output")
    video = _nested(cfg, "video")
    algo_3d_bbox = _nested(cfg, "algo_3d_bbox")
    detection_seg = _nested(cfg, "detection_seg")

    max_frames, max_frames_mode = resolve_input_frame_limits(cfg, engine)
    from .common import parse_random_points_limit

    random_points_per_frame = parse_random_points_limit(
        _output_value(output, "random_points_per_frame"),
        name="output.random_points_per_frame",
    )
    total_random_points = parse_random_points_limit(
        _output_value(output, "total_random_points"),
        name="output.total_random_points",
    )
    blend = resolve_blend_settings(output)

    return {
        "image_path": _require(cfg, "image_path", config_path),
        "output_path": cfg.get("output_path"),
        "engine": engine,
        "verbose": cfg.get("verbose", True),
        "video_fps": video.get("fps", DEFAULT_VIDEO_FPS),
        "video_quality": video.get("quality", 2),
        "save_blend": output.get("save_blend"),
        "save_html": output.get("save_html"),
        "save_frames": bool(output.get("save_frames", False)),
        "min_confidence": output.get("min_confidence", 2.0),
        "filter_edges": output.get("filter_edges", True),
        "point_scale": float(blend["point_scale"]),
        "point_display": normalize_point_display(blend["point_display"]),
        "random_points_per_frame": random_points_per_frame,
        "total_random_points": total_random_points,
        "split_files": bool(output.get("split_files", False)),
        "animate": bool(blend["animate"]),
        "animation_fps": int(blend["animation_fps"]),
        "animation_mode": str(blend["animation_mode"]),
        "align_ground": output.get("align_ground", True),
        "only_start_frame_pose": bool(output.get("only_start_frame_pose", False)),
        "keep_start_frame_point_cloud": bool(blend["keep_start_frame_point_cloud"]),
        "point_cloud_3d_nms": bool(
            output["point_cloud_3d_nms"]
            if output.get("point_cloud_3d_nms") is not None
            else output_default("point_cloud_3d_nms")
        ),
        "point_cloud_3d_nms_radius": float(
            output["point_cloud_3d_nms_radius"]
            if output.get("point_cloud_3d_nms_radius") is not None
            else output_default("point_cloud_3d_nms_radius")
        ),
        "point_cloud_3d_nms_min_neighbors": int(
            output["point_cloud_3d_nms_min_neighbors"]
            if output.get("point_cloud_3d_nms_min_neighbors") is not None
            else output_default("point_cloud_3d_nms_min_neighbors")
        ),
        "algo_3d_bbox": resolve_algo_3d_bbox_enabled(output, detection_seg),
        "detection_seg": detection_seg_enabled(detection_seg),
        "algo_3d_bbox_reference_frame": int(algo_3d_bbox.get("reference_frame", 0)),
        "algo_3d_bbox_voxel_size": float(algo_3d_bbox.get("voxel_size", 0.02)),
        "algo_3d_bbox_min_changed_voxels": int(algo_3d_bbox.get("min_changed_voxels", 12)),
        "algo_3d_bbox_min_change_fraction": float(algo_3d_bbox.get("min_change_fraction", 0.03)),
        "algo_3d_bbox_min_cluster_voxels": int(algo_3d_bbox.get("min_cluster_voxels", 8)),
        "algo_3d_bbox_cluster_gap_close": int(algo_3d_bbox.get("cluster_gap_close", 1)),
        "algo_3d_bbox_min_points_per_voxel": int(algo_3d_bbox.get("min_points_per_voxel", 1)),
        "algo_3d_bbox_shell_min_new_neighbors": int(algo_3d_bbox.get("shell_min_new_neighbors", 1)),
        "algo_3d_bbox_min_interior_voxels": int(algo_3d_bbox.get("min_interior_voxels", 2)),
        "algo_3d_bbox_min_interior_fraction": float(algo_3d_bbox.get("min_interior_fraction", 0.04)),
        "algo_3d_bbox_bbox_dense_min_neighbors": int(algo_3d_bbox.get("bbox_dense_min_neighbors", 3)),
        "algo_3d_bbox_bbox_min_dense_voxels": int(algo_3d_bbox.get("bbox_min_dense_voxels", 4)),
        "algo_3d_bbox_padding": float(algo_3d_bbox.get("padding", 0.01)),
        "algo_3d_bbox_min_visualize_changed_voxels": int(
            algo_3d_bbox.get(
                "min_visualize_changed_voxels",
                algo_3d_bbox_default("min_visualize_changed_voxels"),
            )
        ),
        "detection_seg_model": str(
            detection_seg.get("model", detection_seg_default("model"))
        ),
        **dict(
            zip(
                ("detection_seg_classes", "detection_seg_class_colors"),
                _detection_seg_classes_from_section(detection_seg),
            )
        ),
        "detection_seg_threshold": float(
            detection_seg.get("threshold", detection_seg_default("threshold"))
        ),
        "detection_seg_save_masks": bool(
            detection_seg.get("save_masks", detection_seg_default("save_masks"))
        ),
        "max_frames": max_frames,
        "max_frames_mode": max_frames_mode,
        "use_sdpa": lingbot_map.get("use_sdpa", False),
        "lingbot_map_mode": lingbot_map.get("mode"),
        "keyframe_interval": lingbot_map.get("keyframe_interval"),
        "lingbot_map_max_streaming_keyframes": lingbot_map.get("max_streaming_keyframes"),
        "window_size": lingbot_map.get("window_size", 64),
        "overlap_size": lingbot_map.get("overlap_size", 16),
        "overlap_keyframes": lingbot_map.get("overlap_keyframes"),
        "mask_sky": lingbot_map.get("mask_sky", False),
        "lingbot_map_image_size": lingbot_map.get("image_size", 518),
        "lingbot_map_preprocess_mode": lingbot_map.get("preprocess_mode", "center_square"),
        "lingbot_map_model": lingbot_map.get("model", DEFAULT_LINGBOT_MAP_MODEL),
        "lingbot_map_checkpoint": _optional_path(lingbot_map.get("checkpoint")),
        "vggt_omega_checkpoint": _optional_path(vggt_omega.get("checkpoint")),
        "vggt_omega_checkpoint_name": vggt_omega.get("checkpoint_name", "vggt-omega-1b-512"),
        "vggt_omega_resolution": vggt_omega.get("resolution", 512),
        "vggt_omega_preprocess_mode": vggt_omega.get("preprocess_mode", "balanced"),
        "vggt_omega_enable_alignment": vggt_omega.get("enable_alignment", False),
        "vggt_omega_conf_percentile": vggt_omega.get("conf_percentile", 50.0),
        "vggt_omega_depth_edge_rtol": vggt_omega.get("depth_edge_rtol", 0.03),
        "vgg_ttt_model_id": vgg_ttt.get("model_id", "nvidia/vgg-ttt"),
        "vgg_ttt_preprocess_mode": vgg_ttt.get("preprocess_mode", "crop"),
        "vgg_ttt_image_size": vgg_ttt.get("image_size", 518),
        "vgg_ttt_conf_percentile": vgg_ttt.get("conf_percentile", 50.0),
        "vgg_ttt_depth_edge_rtol": vgg_ttt.get("depth_edge_rtol", 0.03),
        "vgg_ttt_num_ttt_steps": vgg_ttt.get("num_ttt_steps", 1),
        "vgg_ttt_memory_efficient_inference": vgg_ttt.get("memory_efficient_inference", False),
        "map_anything_model": map_anything.get("model", "vggt"),
        "map_anything_model_kwargs": map_anything.get("model_kwargs"),
        "map_anything_install_all": map_anything.get("install_all", False),
        "map_anything_resolution": map_anything.get("resolution"),
        "map_anything_norm_type": map_anything.get("norm_type"),
        "map_anything_patch_size": map_anything.get("patch_size"),
        "map_anything_resize_mode": map_anything.get("resize_mode", "fixed_mapping"),
        "map_anything_size": map_anything.get("size"),
        "r3_checkpoint": _optional_path(r3.get("checkpoint")),
        "r3_model": r3.get("model", "r3_long"),
        "r3_config_name": r3.get("config_name", "r3-large"),
        "r3_mode": r3.get("mode", "local"),
        "r3_image_size": r3.get("image_size", 504),
        "r3_kv_backend": r3.get("kv_backend", "dense"),
        "r3_rel_pose_method": r3.get("rel_pose_method", "greedy"),
        "r3_metric_model_name": r3.get("metric_model_name", "depth-anything/DA3METRIC-LARGE"),
        "dvlt_checkpoint": dvlt.get("checkpoint") or "nvidia/dvlt",
        "dvlt_img_size": dvlt.get("img_size", 504),
        "dvlt_patch_size": dvlt.get("patch_size", 14),
        "dvlt_conf_percentile": dvlt.get("conf_percentile", 50.0),
        "dvlt_depth_edge_rtol": dvlt.get("depth_edge_rtol", 0.03),
    }
