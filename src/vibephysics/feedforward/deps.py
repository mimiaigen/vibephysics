"""Runtime dependency installation for feedforward engines."""

from __future__ import annotations

import importlib.util
import subprocess
import sys

from .common import LINGBOT_MAP_GIT, VGGT_OMEGA_GIT, VGG_TTT_GIT

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
}

_ENGINE_MODULES: dict[str, str] = {
    "lingbot_map": "lingbot_map",
    "vggt_omega": "vggt_omega",
    "vgg_ttt": "vggttt",
}

_ENGINE_GIT: dict[str, str] = {
    "lingbot_map": LINGBOT_MAP_GIT,
    "vggt_omega": VGGT_OMEGA_GIT,
    "vgg_ttt": VGG_TTT_GIT,
}


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def pip_install(spec: str, *, verbose: bool = True) -> None:
    if verbose:
        print(f"--- [vibephysics] Installing {spec} ---")
    subprocess.check_call([sys.executable, "-m", "pip", "install", spec])


def ensure_engine_dependencies(engine: str, *, verbose: bool = True) -> bool:
    """Install PyPI + GitHub deps for a feedforward engine on first use."""
    if engine not in _PYPI_DEPS:
        raise ValueError(f"Unknown feedforward engine: {engine}")

    for import_name, pip_spec in _PYPI_DEPS[engine]:
        if _has_module(import_name):
            continue
        if verbose:
            print(f"\n[vibephysics] Missing {import_name}; installing {pip_spec}")
        try:
            pip_install(pip_spec, verbose=verbose)
        except subprocess.CalledProcessError:
            if verbose:
                print(f"[vibephysics] Failed to install {pip_spec}")
            return False

    module = _ENGINE_MODULES[engine]
    if not _has_module(module):
        git_spec = _ENGINE_GIT[engine]
        if verbose:
            print(f"\n[vibephysics] Missing {module}; installing from GitHub")
        try:
            pip_install(git_spec, verbose=verbose)
        except subprocess.CalledProcessError:
            if verbose:
                print(f"[vibephysics] Install manually with: pip install {git_spec}")
            return False

    return _has_module(module)
