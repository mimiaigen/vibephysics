"""Runtime dependency installation for feedforward engines."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys

from .common import DVLT_GIT, LINGBOT_MAP_GIT, MAP_ANYTHING_GIT, R3_GIT, VGGT_OMEGA_GIT, VGG_TTT_GIT

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
    "r3": [
        ("torch", "torch"),
        ("torchvision", "torchvision"),
        ("cv2", "opencv-python"),
        ("PIL", "pillow"),
        ("einops", "einops"),
        ("scipy", "scipy"),
        ("imageio", "imageio"),
        ("safetensors", "safetensors"),
        ("omegaconf", "omegaconf"),
        ("addict", "addict"),
        ("huggingface_hub", "huggingface_hub"),
    ],
    "dvlt": [
        ("torch", "torch"),
        ("torchvision", "torchvision"),
        ("cv2", "opencv-python"),
        ("PIL", "pillow"),
        ("accelerate", "accelerate>=1.8"),
        ("huggingface_hub", "huggingface_hub"),
        ("hydra", "hydra-core"),
        ("omegaconf", "omegaconf"),
        ("safetensors", "safetensors"),
        ("scipy", "scipy"),
        ("pydantic", "pydantic>=2"),
    ],
    "detection_seg": [
        ("torch", "torch"),
        ("torchvision", "torchvision"),
        ("PIL", "pillow"),
        ("huggingface_hub", "huggingface_hub"),
        ("transformers", "transformers>=4.52.0"),
    ],
}

# Engines with PyPI deps only (no upstream Git package to import).
_PYPI_ONLY_ENGINES = frozenset({"detection_seg"})

_ENGINE_MODULES: dict[str, str] = {
    "lingbot_map": "lingbot_map",
    "vggt_omega": "vggt_omega",
    "vgg_ttt": "vggttt",
    "map_anything": "mapanything",
    "r3": "R3",
    "dvlt": "dvlt",
}

_ENGINE_GIT: dict[str, str] = {
    "lingbot_map": LINGBOT_MAP_GIT,
    "vggt_omega": VGGT_OMEGA_GIT,
    "vgg_ttt": VGG_TTT_GIT,
    "map_anything": MAP_ANYTHING_GIT,
    "r3": R3_GIT,
    "dvlt": DVLT_GIT,
}

# Upstream pins numpy>=2 and optional rerun-sdk; feedforward installs dvlt --no-deps + runtime only.
_DVLT_RUNTIME_SPECS = [
    "accelerate>=1.8",
    "huggingface-hub>=0.23",
    "hydra-core>=1.3",
    "omegaconf>=2.3",
    "opencv-python",
    "pillow",
    "safetensors",
    "scipy",
    "tqdm",
    "pydantic>=2",
]

_TORCH_IMPORTS = {"torch", "torchvision"}
_TORCH_INDEX_ENV = "VIBEPHYSICS_TORCH_INDEX_URL"
_NUMPY_BPY_CONSTRAINT = "numpy<2"

# mapanything + uniception declare rerun-sdk (numpy>=2) for optional viz only; never install it here.
_MAP_ANYTHING_RUNTIME_SPECS = [
    "huggingface_hub",
    "hydra-core",
    "natsort",
    "opencv-python-headless==4.10.0.84",
    "orjson",
    "pillow-heif",
    "plyfile",
    "python-box",
    "requests",
    "safetensors",
    "tensorboard",
    "tqdm",
    "trimesh",
]

_UNICEPTION_VERSION = "uniception==0.1.7"
# uniception runtime deps minus rerun-sdk (inference does not import uniception.utils.viz).
_UNICEPTION_RUNTIME_SPECS = [
    "jaxtyping",
    "minio",
    "torchmetrics",
    "timm",
]

# Direct installs for mapanything optional extras (avoid mapanything[extra] pulling rerun-sdk).
MAP_ANYTHING_EXTRA_SPECS: dict[str, list[str]] = {
    "anycalib": ["anycalib @ git+https://github.com/javrtg/AnyCalib.git@main#egg=anycalib"],
    "dust3r": [
        "croco @ git+https://github.com/naver/croco.git@croco_module#egg=croco",
        "dust3r @ git+https://github.com/naver/dust3r.git@dust3r_setup#egg=dust3r",
    ],
    "mast3r": ["mast3r @ git+https://github.com/Nik-V9/mast3r.git@main#egg=mast3r"],
    "must3r": ["must3r @ git+https://github.com/naver/must3r.git@main#egg=must3r"],
    "pi3": ["pi3 @ git+https://github.com/yyfz/Pi3.git@main#egg=pi3"],
    "pow3r": ["pow3r @ git+https://github.com/Nik-V9/pow3r.git@main#egg=pow3r"],
    "depth-anything-3": [
        "depth-anything-3 @ git+https://github.com/Nik-V9/depth-anything-3.git@main#egg=depth-anything-3"
    ],
    "vggt-omega": [
        "vggt-omega @ git+https://github.com/facebookresearch/vggt-omega.git@main#egg=vggt-omega"
    ],
}


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def pip_install(
    spec: str,
    *,
    verbose: bool = True,
    extra_specs: list[str] | None = None,
    index_url: str | None = None,
    no_deps: bool = False,
) -> None:
    specs = [spec, *(extra_specs or [])]
    if verbose:
        source = f" --index-url {index_url}" if index_url else ""
        no_deps_note = " --no-deps" if no_deps else ""
        print(f"--- [vibephysics] Installing{source}{no_deps_note} {' '.join(specs)} ---")
    cmd = [sys.executable, "-m", "pip", "install"]
    if index_url:
        cmd.extend(["--index-url", index_url])
    if no_deps:
        cmd.append("--no-deps")
    cmd.extend(specs)
    subprocess.check_call(cmd)


def _uninstall_rerun_sdk(*, verbose: bool) -> None:
    if importlib.util.find_spec("rerun") is None:
        return
    if verbose:
        print("--- [vibephysics] Removing rerun-sdk (not used by feedforward) ---", flush=True)
    subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "-y", "rerun-sdk"],
        check=False,
        capture_output=not verbose,
    )


def _install_uniception_without_rerun(*, verbose: bool) -> None:
    if _has_module("uniception"):
        return
    if verbose:
        print(
            f"--- [vibephysics] Installing {_UNICEPTION_VERSION} without rerun-sdk ---",
            flush=True,
        )
    pip_install(_UNICEPTION_VERSION, verbose=verbose, no_deps=True)
    if _UNICEPTION_RUNTIME_SPECS:
        pip_install(
            _UNICEPTION_RUNTIME_SPECS[0],
            verbose=verbose,
            extra_specs=[*_UNICEPTION_RUNTIME_SPECS[1:], _NUMPY_BPY_CONSTRAINT],
        )


def _install_map_anything_runtime_deps(*, verbose: bool) -> None:
    pip_install(
        _MAP_ANYTHING_RUNTIME_SPECS[0],
        verbose=verbose,
        extra_specs=[*_MAP_ANYTHING_RUNTIME_SPECS[1:], _NUMPY_BPY_CONSTRAINT],
    )
    _install_uniception_without_rerun(verbose=verbose)
    _uninstall_rerun_sdk(verbose=verbose)


def install_map_anything_from_git(*, verbose: bool) -> None:
    """
    Install Map-Anything without rerun-sdk (requires numpy>=2, conflicts with bpy).
    """
    if verbose:
        print(
            "--- [vibephysics] Installing Map-Anything (skipping optional rerun-sdk; "
            "feedforward inference does not need it) ---",
            flush=True,
        )
    pip_install(MAP_ANYTHING_GIT, verbose=verbose, no_deps=True)
    _install_map_anything_runtime_deps(verbose=verbose)


def install_dvlt_from_git(*, verbose: bool = True) -> None:
    """
    Install DVLT without upstream numpy>=2 / rerun-sdk (conflicts with bpy).

    Weights load from Hugging Face (``nvidia/dvlt``) into .vibephysics/feedforward/huggingface/.
    """
    if verbose:
        print(
            "--- [vibephysics] Installing DVLT from GitHub (--no-deps; numpy<2 compatible runtime) ---",
            flush=True,
        )
    pip_install(DVLT_GIT, verbose=verbose, no_deps=True)
    pip_install(
        _DVLT_RUNTIME_SPECS[0],
        verbose=verbose,
        extra_specs=[*_DVLT_RUNTIME_SPECS[1:], _NUMPY_BPY_CONSTRAINT],
    )


def ensure_dvlt_package(*, verbose: bool = True) -> bool:
    if _has_module("dvlt"):
        return True
    try:
        install_dvlt_from_git(verbose=verbose)
    except subprocess.CalledProcessError:
        if verbose:
            print(
                "[vibephysics] DVLT install failed. Upstream declares numpy>=2; vibephysics uses numpy<2 for bpy. Retry:\n"
                f"  pip install --no-deps {DVLT_GIT}\n"
                f"  pip install {' '.join(_DVLT_RUNTIME_SPECS)} {_NUMPY_BPY_CONSTRAINT}",
                flush=True,
            )
        return False
    return _has_module("dvlt")


def ensure_map_anything_package(*, verbose: bool = True) -> bool:
    if _has_module("mapanything"):
        return True
    try:
        install_map_anything_from_git(verbose=verbose)
    except subprocess.CalledProcessError:
        if verbose:
            print(
                "[vibephysics] Map-Anything install failed. "
                f"Core package needs numpy<2 for Blender (bpy); upstream also pins "
                f"rerun-sdk which requires numpy>=2. vibephysics installs Map-Anything "
                f"without rerun-sdk. Retry:\n"
                f"  pip install --no-deps {MAP_ANYTHING_GIT}\n"
                f"  pip install {' '.join(_MAP_ANYTHING_RUNTIME_SPECS)} {_NUMPY_BPY_CONSTRAINT}\n"
                f"  pip install --no-deps {_UNICEPTION_VERSION}\n"
                f"  pip install {' '.join(_UNICEPTION_RUNTIME_SPECS)} {_NUMPY_BPY_CONSTRAINT}",
                flush=True,
            )
        return False
    return _has_module("mapanything")


def install_map_anything_extra(extra: str, *, verbose: bool = True) -> bool:
    specs = MAP_ANYTHING_EXTRA_SPECS.get(extra)
    if not specs:
        return True
    if not ensure_map_anything_package(verbose=verbose):
        return False
    for spec in specs:
        try:
            pip_install(spec, verbose=verbose, extra_specs=[_NUMPY_BPY_CONSTRAINT])
        except subprocess.CalledProcessError:
            if verbose:
                print(f"[vibephysics] Failed to install Map-Anything extra '{extra}': {spec}")
            return False
    return True


def _nvidia_driver_version() -> str | None:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=driver_version",
                "--format=csv,noheader",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except Exception:
        return None
    return result.stdout.strip().splitlines()[0].strip() or None


def _driver_major(version: str | None) -> int | None:
    if not version:
        return None
    try:
        return int(version.split(".", 1)[0])
    except ValueError:
        return None


def _torch_index_url() -> str | None:
    override = os.environ.get(_TORCH_INDEX_ENV)
    if override:
        return override.strip() or None
    if not sys.platform.startswith("linux"):
        return None

    major = _driver_major(_nvidia_driver_version())
    if major is None:
        return None

    # Pick the newest common PyTorch CUDA wheel family supported by the driver.
    # Users can override with VIBEPHYSICS_TORCH_INDEX_URL for unusual clusters.
    if major >= 570:
        return "https://download.pytorch.org/whl/cu128"
    if major >= 550:
        return "https://download.pytorch.org/whl/cu124"
    if major >= 530:
        return "https://download.pytorch.org/whl/cu121"
    return "https://download.pytorch.org/whl/cpu"


def _ensure_torch_dependencies(engine: str, *, auto_install: bool, verbose: bool) -> bool:
    deps = _PYPI_DEPS[engine]
    needs_torch = any(import_name == "torch" for import_name, _ in deps)
    if not needs_torch:
        return True

    specs: list[str] = []
    if not _has_module("torch"):
        specs.append("torch")
    if any(import_name == "torchvision" for import_name, _ in deps) and not _has_module("torchvision"):
        specs.append("torchvision")

    if not specs:
        return True

    if not auto_install:
        if verbose:
            print(
                "[vibephysics] Missing PyTorch dependency; auto-install disabled. "
                "Install torch/torchvision for your device first."
            )
        return False

    index_url = _torch_index_url()
    if verbose and sys.platform.startswith("linux") and index_url:
        print(
            f"--- [vibephysics] Linux PyTorch install source: {index_url} "
            f"(override with {_TORCH_INDEX_ENV}) ---"
        )
    try:
        pip_install(specs[0], verbose=verbose, extra_specs=specs[1:], index_url=index_url)
    except subprocess.CalledProcessError:
        if verbose:
            print("[vibephysics] Failed to install PyTorch dependencies.")
            if index_url:
                print(
                    "[vibephysics] Try setting "
                    f"{_TORCH_INDEX_ENV}=https://download.pytorch.org/whl/<cpu|cu121|cu124|cu128>"
                )
        return False
    return all(_has_module(import_name) for import_name in ("torch", *specs[1:]))


def ensure_engine_dependencies(engine: str, *, verbose: bool = True) -> bool:
    """Install PyPI + GitHub deps for a feedforward engine on first use."""
    if engine not in _PYPI_DEPS:
        raise ValueError(f"Unknown feedforward engine: {engine}")

    auto_install = os.environ.get("VIBEPHYSICS_NO_AUTO_INSTALL", "").strip().lower() not in {
        "1",
        "true",
        "yes",
    }
    install_constraints = [_NUMPY_BPY_CONSTRAINT] if engine in {"vgg_ttt", "r3"} else None

    if not _ensure_torch_dependencies(engine, auto_install=auto_install, verbose=verbose):
        return False

    for import_name, pip_spec in _PYPI_DEPS[engine]:
        if import_name in _TORCH_IMPORTS:
            continue
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

    if engine in _PYPI_ONLY_ENGINES:
        return all(
            _has_module(import_name)
            for import_name, _ in _PYPI_DEPS[engine]
        )

    module = _ENGINE_MODULES[engine]
    if not _has_module(module):
        if not auto_install:
            if verbose:
                print(f"[vibephysics] Missing {module}; auto-install disabled.")
            return False
        if engine == "map_anything":
            if not ensure_map_anything_package(verbose=verbose):
                return False
        elif engine == "dvlt":
            if not ensure_dvlt_package(verbose=verbose):
                return False
        else:
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
