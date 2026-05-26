"""YAML config for the mapping CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CONFIGS_DIR = Path(__file__).resolve().parent / "configs"
DEFAULT_SFM_CONFIG = CONFIGS_DIR / "sfm.yaml"
SFM_ENGINES = ("glomap", "colmap")


def load_sfm_config(
    config_path: str | Path,
    image_path: str | Path | None = None,
    output_path: str | Path | None = None,
    save_blend: bool | None = None,
    blend_path: str | Path | None = None,
    point_size: float | None = None,
    rotation: tuple[float, float, float] | None = None,
) -> dict[str, Any]:
    path = Path(config_path).expanduser().resolve()
    with path.open() as handle:
        cfg = yaml.safe_load(handle)
    if not isinstance(cfg, dict):
        raise ValueError(f"Config must be a YAML mapping: {path}")

    if image_path is not None:
        cfg["image_path"] = image_path
    if output_path is not None:
        cfg["output_path"] = output_path
    if not cfg.get("image_path"):
        raise ValueError(f"{path}: missing required config key 'image_path'")

    engine = cfg.get("engine", "glomap")
    if engine not in SFM_ENGINES:
        raise ValueError(f"Invalid engine '{engine}'. Choose: {', '.join(SFM_ENGINES)}")

    video = cfg.get("video") or {}
    visualize = cfg.get("visualize") or {}
    rot = rotation if rotation is not None else visualize.get("rotation", [-90, 0, 0])

    return {
        "image_path": cfg["image_path"],
        "output_path": cfg.get("output_path"),
        "mapper": engine,
        "matcher": cfg.get("matcher", "sequential"),
        "camera_model": cfg.get("camera_model", "SIMPLE_RADIAL"),
        "verbose": cfg.get("verbose", True),
        "video_fps": video.get("fps", 2.0),
        "video_quality": video.get("quality", 2),
        "save_blend": save_blend if save_blend is not None else visualize.get("save_blend", True),
        "blend_path": blend_path if blend_path is not None else visualize.get("blend_path"),
        "point_size": point_size if point_size is not None else visualize.get("point_size", 0.03),
        "rotation": tuple(rot),
        "animate": visualize.get("animate", True),
        "animation_fps": visualize.get("animation_fps", 24),
    }
