"""Runtime dependency installation for feedforward engines."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys

from .common import LINGBOT_MAP_GIT, MAP_ANYTHING_GIT, VGGT_OMEGA_GIT, VGG_TTT_GIT

# (import_name, pip_spec)
_PYPI_DEPS: dict[str, list[tuple[str, str]]] = {
    "lingbot_map": [
        ("torch", "torch"),
        ("torchvision", "torchvision"),
        ("cv2", "opencv-python"),
        ("PIL", "pillow"),
        ("einops", "einops"),
        ("scipy", "scipy"),
        ("safetensors", "safetensors"),
        ("huggingface_hub", "huggingface_hub"),
    ],
    "vggt_omega": [
        ("torch", "torch"),
        ("cv2", "opencv-python"),
        ("huggingface_hub", "huggingface_hub"),
    ],
    "vgg_ttt": [
        ("torch", "torch"),
        ("torchvision", "torchvision"),
        ("cv2", "opencv-python"),
        ("huggingface_hub", "huggingface_hub"),
        ("einops", "einops"),
        ("roma", "roma"),
        ("trimesh", "trimesh"),
        ("hydra", "hydra-core"),
    ],
    "map_anything": [
        ("torch", "torch"),
        ("torchvision", "torchvision"),
        ("cv2", "opencv-python"),
        ("PIL", "pillow"),
        ("huggingface_hub", "huggingface_hub"),
        ("hydra", "hydra-core"),
        ("omegaconf", "omegaconf"),
    ],
}

_ENGINE_MODULES: dict[str, str] = {
    "lingbot_map": "lingbot_map",
    "vggt_omega": "vggt_omega",
    "vgg_ttt": "vggttt",
    "map_anything": "mapanything",
}

_ENGINE_GIT: dict[str, str] = {
    "lingbot_map": LINGBOT_MAP_GIT,
    "vggt_omega": VGGT_OMEGA_GIT,
    "vgg_ttt": VGG_TTT_GIT,
    "map_anything": MAP_ANYTHING_GIT,
}


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def pip_install(spec: str, *, verbose: bool = True, extra_specs: list[str] | None = None) -> None:
    specs = [spec, *(extra_specs or [])]
    if verbose:
        print(f"--- [vibephysics] Installing {' '.join(specs)} ---")
    subprocess.check_call([sys.executable, "-m", "pip", "install", *specs])


def ensure_engine_dependencies(engine: str, *, verbose: bool = True) -> bool:
    """Install PyPI + GitHub deps for a feedforward engine on first use."""
    if engine not in _PYPI_DEPS:
        raise ValueError(f"Unknown feedforward engine: {engine}")

    auto_install = os.environ.get("VIBEPHYSICS_NO_AUTO_INSTALL", "").strip().lower() not in {
        "1",
        "true",
        "yes",
    }
    install_constraints = ["numpy<2"] if engine in {"map_anything", "vgg_ttt"} else None

    for import_name, pip_spec in _PYPI_DEPS[engine]:
        if _has_module(import_name):
            continue
        if not auto_install:
            if verbose:
                print(f"[vibephysics] Missing {import_name}; auto-install disabled.")
            return False
        if verbose:
            print(f"\n[vibephysics] Missing {import_name}; installing {pip_spec}")
        try:
            pip_install(pip_spec, verbose=verbose, extra_specs=install_constraints)
        except subprocess.CalledProcessError:
            if verbose:
                print(f"[vibephysics] Failed to install {pip_spec}")
            return False

    module = _ENGINE_MODULES[engine]
    if not _has_module(module):
        if not auto_install:
            if verbose:
                print(f"[vibephysics] Missing {module}; auto-install disabled.")
            return False
        git_spec = _ENGINE_GIT[engine]
        if verbose:
            print(f"\n[vibephysics] Missing {module}; installing from GitHub")
        try:
            pip_install(git_spec, verbose=verbose, extra_specs=install_constraints)
        except subprocess.CalledProcessError:
            if verbose:
                print(f"[vibephysics] Install manually with: pip install {git_spec}")
            return False

    return _has_module(module)
