"""YAML config loading for sparse SfM mapping pipelines."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .utils import resolve_mapping_input

CONFIGS_DIR = Path(__file__).resolve().parent / "configs"
DEFAULT_SFM_CONFIG = CONFIGS_DIR / "sfm.yaml"

SFM_ENGINES = ("glomap", "colmap")


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


def parse_sfm_config(cfg: dict[str, Any], config_path: Path | None = None) -> dict[str, Any]:
    engine = _require(cfg, "engine", config_path)
    if engine not in SFM_ENGINES:
        raise ValueError(f"Invalid SfM engine '{engine}'. Choose one of: {', '.join(SFM_ENGINES)}")

    video = _nested(cfg, "video")

    return {
        "image_path": _require(cfg, "image_path", config_path),
        "output_path": cfg.get("output_path"),
        "engine": engine,
        "matcher": cfg.get("matcher", "exhaustive"),
        "camera_model": cfg.get("camera_model", "SIMPLE_RADIAL"),
        "verbose": cfg.get("verbose", True),
        "video_fps": video.get("fps", 2.0),
        "video_quality": video.get("quality", 2),
    }


def run_sfm_from_config(
    config_path: str | Path,
    image_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> int:
    config_path = Path(config_path)
    cfg = apply_overrides(
        load_yaml_config(config_path),
        {"image_path": image_path, "output_path": output_path},
    )
    params = parse_sfm_config(cfg, config_path=config_path.resolve())
    params["image_path"] = resolve_mapping_input(
        params["image_path"],
        video_fps=params.pop("video_fps"),
        video_quality=params.pop("video_quality"),
        verbose=params["verbose"],
    )

    if params["engine"] == "glomap":
        from .glomap import glomap_pipeline

        return glomap_pipeline(
            params["image_path"],
            params["output_path"],
            None,
            params["matcher"],
            params["camera_model"],
            params["verbose"],
        )

    from .colmap import colmap_pipeline

    return colmap_pipeline(
        params["image_path"],
        params["output_path"],
        None,
        params["matcher"],
        params["camera_model"],
        params["verbose"],
    )
