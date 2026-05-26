"""Map-Anything model-factory feedforward engine."""

from __future__ import annotations

import contextlib
import copy
import importlib.util
import os
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np

from ..common import (
    MAP_ANYTHING_GIT,
    c2w_to_w2c,
    discover_images,
    feedforward_engine_dir,
    get_vram_gb,
    limit_image_frames,
    to_numpy,
)
from ..deps import ensure_engine_dependencies, pip_install
from ..schema import FeedforwardPrediction

DEFAULT_MODEL_NAME = "vggt"
IMAGES_ONLY_GEOMETRIC_CONFIG = {
    "overall_prob": 0.0,
    "dropout_prob": 1.0,
    "ray_dirs_prob": 0.0,
    "depth_prob": 0.0,
    "cam_prob": 0.0,
    "sparse_depth_prob": 0.0,
    "sparsification_removal_percent": 0.0,
    "depth_scale_norm_all_prob": 0.0,
    "pose_scale_norm_all_prob": 0.0,
}
DEFAULT_FACTORY_KWARGS = {
    "mapanything": {
        "model_id": "facebook/map-anything",
    },
    "mapanything_apache": {
        "model_id": "facebook/map-anything-apache",
    },
    "vggt": {
        "name": "vggt",
        "torch_hub_force_reload": False,
    },
    "dust3r": {
        "name": "dust3r",
        "scene_graph": "complete",
        "inference_batch_size": 32,
        "global_optim_schedule": "cosine",
        "global_optim_lr": 0.01,
        "global_optim_niter": 300,
    },
    "mast3r": {
        "name": "mast3r",
        "scene_graph": "complete",
    },
    "pi3": {
        "name": "pi3",
        "load_pretrained_weights": True,
    },
    "pi3x": {
        "name": "pi3x",
        "torch_hub_force_reload": False,
        "geometric_input_config": IMAGES_ONLY_GEOMETRIC_CONFIG,
    },
    "pow3r": {
        "name": "pow3r",
        "geometric_input_config": IMAGES_ONLY_GEOMETRIC_CONFIG,
    },
    "pow3r_ba": {
        "name": "pow3r_ba",
        "geometric_input_config": IMAGES_ONLY_GEOMETRIC_CONFIG,
        "scene_graph": "complete",
        "inference_batch_size": 32,
        "global_optim_schedule": "cosine",
        "global_optim_lr": 0.01,
        "global_optim_niter": 300,
    },
    "anycalib": {
        "name": "anycalib",
    },
    "must3r": {
        "name": "must3r",
    },
    "da3": {
        "name": "da3",
        "torch_hub_force_reload": False,
        "hf_model_name": "depth-anything/DA3-GIANT-1.1",
        "geometric_input_config": IMAGES_ONLY_GEOMETRIC_CONFIG,
    },
    "moge": {
        "name": "moge-1",
        "model_string": "Ruicheng/moge-vitl",
        "load_custom_ckpt": False,
        "custom_ckpt_path": None,
    },
}

MODEL_PREPROCESS_DEFAULTS = {
    "mapanything": (518, "dinov2", 14),
    "mapanything_apache": (518, "dinov2", 14),
    "mapanything_ablations": (518, "dinov2", 14),
    "modular_dust3r": (512, "dust3r", 16),
    "vggt": (518, "identity", 14),
    "moge": (518, "identity", 14),
    "pi3": (518, "identity", 14),
    "pi3x": (518, "identity", 14),
    "dust3r": (512, "dust3r", 16),
    "mast3r": (512, "dust3r", 16),
    "must3r": (512, "dust3r", 16),
    "pow3r": (512, "dust3r", 16),
    "pow3r_ba": (512, "dust3r", 16),
    "da3": (504, "dinov2", 14),
}

MODEL_EXTRA_BY_NAME = {
    "dust3r": "dust3r",
    "mast3r": "mast3r",
    "pi3x": "pi3",
    "pow3r": "pow3r",
    "pow3r_ba": "pow3r",
    "anycalib": "anycalib",
    "must3r": "must3r",
    "da3": "depth-anything-3",
}

MODEL_IMPORT_BY_NAME = {
    "dust3r": "mapanything.models.external.dust3r",
    "mast3r": "mapanything.models.external.mast3r",
    "pi3x": "mapanything.models.external.pi3x",
    "pow3r": "mapanything.models.external.pow3r",
    "pow3r_ba": "mapanything.models.external.pow3r",
    "anycalib": "mapanything.models.external.anycalib",
    "must3r": "mapanything.models.external.must3r",
    "da3": "mapanything.models.external.da3",
}

AVAILABLE_MODEL_NAMES = tuple(MODEL_PREPROCESS_DEFAULTS)
CORE_PRETRAINED_MODEL_NAMES = {"mapanything", "mapanything_apache"}

CHECKPOINT_URLS = {
    "dust3r": {
        "ckpt_path": (
            "DUSt3R_ViTLarge_BaseDecoder_512_dpt.pth",
            "https://download.europe.naverlabs.com/ComputerVision/DUSt3R/DUSt3R_ViTLarge_BaseDecoder_512_dpt.pth",
        ),
    },
    "mast3r": {
        "ckpt_path": (
            "MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth",
            "https://download.europe.naverlabs.com/ComputerVision/MASt3R/MASt3R_ViTLarge_BaseDecoder_512_catmlpdpt_metric.pth",
        ),
    },
    "must3r": {
        "ckpt_path": (
            "MUSt3R_512.pth",
            "https://download.europe.naverlabs.com/ComputerVision/MUSt3R/MUSt3R_512.pth",
        ),
        "retrieval_ckpt_path": (
            "MUSt3R_512_retrieval_trainingfree.pth",
            "https://download.europe.naverlabs.com/ComputerVision/MUSt3R/MUSt3R_512_retrieval_trainingfree.pth",
        ),
    },
}


def is_available() -> bool:
    if importlib.util.find_spec("torch") is None:
        return False
    return importlib.util.find_spec("mapanything") is not None


def default_model_kwargs(model_name: str) -> dict[str, Any]:
    return copy.deepcopy(DEFAULT_FACTORY_KWARGS.get(model_name, {}))


def _checkpoint_dir() -> Path:
    path = feedforward_engine_dir("map_anything") / "checkpoints"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _download_file(url: str, path: Path, *, verbose: bool = True) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if verbose:
        print(f"--- [vibephysics] Downloading Map-Anything checkpoint: {path.name} ---")
    try:
        import torch

        torch.hub.download_url_to_file(url, str(path))
    except Exception:
        subprocess.check_call(["curl", "-L", "--fail", "-o", str(path), url])


def _resolve_model_kwargs(
    model_name: str,
    model_kwargs: dict[str, Any] | None = None,
    *,
    verbose: bool = True,
) -> dict[str, Any]:
    kwargs = default_model_kwargs(model_name)
    if model_kwargs:
        kwargs.update(model_kwargs)

    for key, (filename, url) in CHECKPOINT_URLS.get(model_name, {}).items():
        if kwargs.get(key):
            continue
        path = _checkpoint_dir() / filename
        _download_file(url, path, verbose=verbose)
        kwargs[key] = str(path)

    if model_name == "mast3r":
        cache_dir = kwargs.get("cache_dir")
        if not cache_dir:
            cache_dir = _checkpoint_dir() / "mast3r_cache"
            kwargs["cache_dir"] = str(cache_dir)
        Path(str(cache_dir)).mkdir(parents=True, exist_ok=True)

    if model_name in {"pow3r", "pow3r_ba"} and not kwargs.get("ckpt_path"):
        path = _checkpoint_dir() / "Pow3R_ViTLarge_BaseDecoder_512_linear.pth"
        raise FileNotFoundError(
            f"Pow3R checkpoint is required but was not found at {path}. "
            "Set map_anything.model_kwargs.ckpt_path to a downloaded "
            "Pow3R_ViTLarge_BaseDecoder_512_linear.pth checkpoint."
        )

    return kwargs


def _build_model(model_name: str, kwargs: dict[str, Any], device: str):
    if model_name in CORE_PRETRAINED_MODEL_NAMES:
        from mapanything.models import MapAnything

        model_id = kwargs.pop("model_id", "facebook/map-anything")
        return MapAnything.from_pretrained(model_id).to(device).eval()

    from mapanything.models import model_factory

    return model_factory(model_name, **kwargs).to(device).eval()


def _vcs_extra_spec(extra: str) -> str:
    return f"mapanything[{extra}] @ {MAP_ANYTHING_GIT}"


def _external_model_importable(model_name: str) -> bool:
    module = MODEL_IMPORT_BY_NAME.get(model_name)
    if module is None:
        return True
    try:
        __import__(module, fromlist=["*"])
    except Exception:
        return False
    return True


def ensure_dependencies(
    verbose: bool = True,
    *,
    model_name: str = DEFAULT_MODEL_NAME,
    install_all: bool = False,
) -> bool:
    if not ensure_engine_dependencies("map_anything", verbose=verbose):
        return False

    auto_install = os.environ.get("VIBEPHYSICS_NO_AUTO_INSTALL", "").strip().lower() not in {
        "1",
        "true",
        "yes",
    }
    install_constraints = ["numpy<2"]

    if install_all:
        spec = _vcs_extra_spec("all")
        if not auto_install:
            if verbose:
                print(f"[vibephysics] Map-Anything [all] extra not installed; auto-install disabled.")
            return False
        try:
            pip_install(spec, verbose=verbose, extra_specs=install_constraints)
        except subprocess.CalledProcessError:
            if verbose:
                print(f"[vibephysics] Failed to install Map-Anything extras with: pip install '{spec}'")
            return False
        return True

    model_name = str(model_name).strip()
    extra = MODEL_EXTRA_BY_NAME.get(model_name)
    if extra is None or _external_model_importable(model_name):
        return True

    spec = _vcs_extra_spec(extra)
    if not auto_install:
        if verbose:
            print(f"[vibephysics] Map-Anything extra '{extra}' for {model_name} not installed; auto-install disabled.")
        return False
    if verbose:
        print(f"--- [vibephysics] Installing Map-Anything extra for {model_name}: {extra} ---")
    try:
        pip_install(spec, verbose=verbose, extra_specs=install_constraints)
    except subprocess.CalledProcessError:
        if verbose:
            print(f"[vibephysics] Install manually with: pip install '{spec}'")
        return False
    return _external_model_importable(model_name)


@contextlib.contextmanager
def _cpu_cuda_shim(device: str) -> Iterator[None]:
    """
    Some factory wrappers assume CUDA for dtype/autocast setup.

    Keep CPU runs importable by turning CUDA autocast into a disabled CPU context
    and returning a conservative fake capability when CUDA is unavailable.
    """
    if device == "cuda":
        yield
        return

    import torch

    orig_autocast = torch.autocast
    orig_get_capability = torch.cuda.get_device_capability

    class _AutocastShim:
        def __init__(self, device_type, *args, **kwargs):
            if device_type == "cuda":
                self._ctx = orig_autocast("cpu", enabled=False)
            else:
                self._ctx = orig_autocast(device_type, *args, **kwargs)

        def __enter__(self):
            return self._ctx.__enter__()

        def __exit__(self, *args):
            return self._ctx.__exit__(*args)

    torch.autocast = _AutocastShim  # type: ignore[assignment]
    torch.cuda.get_device_capability = lambda device=None: (0, 0)  # type: ignore[assignment]
    try:
        yield
    finally:
        torch.autocast = orig_autocast  # type: ignore[assignment]
        torch.cuda.get_device_capability = orig_get_capability  # type: ignore[assignment]


def _model_defaults(model_name: str) -> tuple[int, str, int]:
    return MODEL_PREPROCESS_DEFAULTS.get(model_name, (518, "dinov2", 14))


def _move_views_to_device(views: list[dict[str, Any]], device: str) -> list[dict[str, Any]]:
    moved = []
    for view in views:
        dst = {}
        for key, value in view.items():
            if hasattr(value, "to"):
                dst[key] = value.to(device, non_blocking=True)
            else:
                dst[key] = value
        moved.append(dst)
    return moved


def _normalize_view_metadata(views: list[dict[str, Any]], model_name: str) -> None:
    if model_name != "mast3r":
        return
    for idx, view in enumerate(views):
        view.setdefault("label", ["map_anything"])
        instance = view.get("instance", str(idx))
        if isinstance(instance, str):
            view["instance"] = [instance]


def _views_to_rgb(views: list[dict[str, Any]], norm_type: str) -> np.ndarray:
    from mapanything.utils.image import rgb

    frames = []
    for view in views:
        frame = rgb(view["img"], norm_type)
        if frame.ndim == 4 and frame.shape[0] == 1:
            frame = frame[0]
        frames.append(np.asarray(frame, dtype=np.float32))
    return np.stack(frames, axis=0)


def _squeeze_batch(value: Any) -> np.ndarray:
    arr = to_numpy(value)
    if arr.ndim >= 1 and arr.shape[0] == 1:
        arr = arr[0]
    return arr


def _stack_key(predictions: list[dict[str, Any]], key: str) -> np.ndarray | None:
    values = []
    for pred in predictions:
        if key not in pred:
            return None
        values.append(_squeeze_batch(pred[key]))
    return np.stack(values, axis=0)


def _quat_xyzw_to_rotmat(quat: np.ndarray) -> np.ndarray:
    quat = np.asarray(quat, dtype=np.float64)
    norm = np.linalg.norm(quat, axis=-1, keepdims=True)
    quat = quat / np.maximum(norm, 1e-8)
    x, y, z, w = [quat[..., i] for i in range(4)]
    rot = np.empty((*quat.shape[:-1], 3, 3), dtype=np.float64)
    rot[..., 0, 0] = 1.0 - 2.0 * (y * y + z * z)
    rot[..., 0, 1] = 2.0 * (x * y - z * w)
    rot[..., 0, 2] = 2.0 * (x * z + y * w)
    rot[..., 1, 0] = 2.0 * (x * y + z * w)
    rot[..., 1, 1] = 1.0 - 2.0 * (x * x + z * z)
    rot[..., 1, 2] = 2.0 * (y * z - x * w)
    rot[..., 2, 0] = 2.0 * (x * z - y * w)
    rot[..., 2, 1] = 2.0 * (y * z + x * w)
    rot[..., 2, 2] = 1.0 - 2.0 * (x * x + y * y)
    return rot


def _camera_poses_from_factory_outputs(predictions: list[dict[str, Any]]) -> np.ndarray:
    camera_poses = _stack_key(predictions, "camera_poses")
    if camera_poses is not None:
        return camera_poses

    cam_trans = _stack_key(predictions, "cam_trans")
    cam_quats = _stack_key(predictions, "cam_quats")
    if cam_trans is None or cam_quats is None:
        raise ValueError("Map-Anything output is missing camera_poses or cam_trans/cam_quats.")

    rot = _quat_xyzw_to_rotmat(cam_quats)
    c2w = np.tile(np.eye(4, dtype=np.float64), (rot.shape[0], 1, 1))
    c2w[:, :3, :3] = rot
    c2w[:, :3, 3] = cam_trans
    return c2w.astype(np.float32)


def _c2w_to_w2c(c2w: np.ndarray) -> np.ndarray:
    c2w = np.asarray(c2w, dtype=np.float32)
    if c2w.ndim == 2:
        c2w = c2w[None]
    if c2w.shape[-2:] == (4, 4):
        return np.linalg.inv(c2w)[:, :3, :4].astype(np.float32)
    if c2w.shape[-2:] == (3, 4):
        return c2w_to_w2c(c2w).astype(np.float32)
    raise ValueError(f"Expected camera poses shaped (N,4,4) or (N,3,4), got {c2w.shape}")


def _intrinsics_from_outputs(predictions: list[dict[str, Any]]) -> np.ndarray:
    intrinsic = _stack_key(predictions, "intrinsics")
    if intrinsic is not None:
        return intrinsic.astype(np.float32)

    ray_directions = _stack_key(predictions, "ray_directions")
    if ray_directions is None:
        raise ValueError("Map-Anything output is missing intrinsics and ray_directions.")

    import torch
    from mapanything.utils.geometry import recover_pinhole_intrinsics_from_ray_directions

    rays = torch.from_numpy(ray_directions.astype(np.float32))
    return recover_pinhole_intrinsics_from_ray_directions(rays).detach().cpu().float().numpy()


def _depth_from_outputs(predictions: list[dict[str, Any]]) -> np.ndarray:
    depth_z = _stack_key(predictions, "depth_z")
    if depth_z is not None:
        if depth_z.ndim == 4 and depth_z.shape[-1] == 1:
            depth_z = depth_z[..., 0]
        return depth_z.astype(np.float32)

    pts3d_cam = _stack_key(predictions, "pts3d_cam")
    if pts3d_cam is not None:
        return pts3d_cam[..., 2].astype(np.float32)

    depth_along_ray = _stack_key(predictions, "depth_along_ray")
    ray_directions = _stack_key(predictions, "ray_directions")
    if depth_along_ray is None or ray_directions is None:
        raise ValueError("Map-Anything output is missing depth_z or depth_along_ray/ray_directions.")
    if depth_along_ray.ndim == 4 and depth_along_ray.shape[-1] == 1:
        depth_along_ray = depth_along_ray[..., 0]
    return (depth_along_ray * ray_directions[..., 2]).astype(np.float32)


def run_map_anything(
    image_path: Path,
    model_name: str = DEFAULT_MODEL_NAME,
    model_kwargs: dict[str, Any] | None = None,
    install_all_extras: bool = False,
    resolution: int | None = None,
    norm_type: str | None = None,
    patch_size: int | None = None,
    resize_mode: str = "fixed_mapping",
    size: int | tuple[int, int] | None = None,
    max_frames: int | None = None,
    max_frames_mode: str = "first",
    verbose: bool = True,
) -> FeedforwardPrediction:
    if not ensure_dependencies(verbose, model_name=model_name, install_all=install_all_extras):
        raise RuntimeError(
            "Map-Anything not ready. Install with: "
            "pip install 'mapanything[all] @ git+https://github.com/facebookresearch/map-anything.git'"
        )

    import torch
    from mapanything.utils.image import load_images

    default_resolution, default_norm_type, default_patch = _model_defaults(model_name)
    resolution = int(resolution or default_resolution)
    norm_type = norm_type or default_norm_type
    patch_size = int(patch_size or default_patch)

    all_images = discover_images(image_path)
    selected, indices, input_num_frames = limit_image_frames(
        all_images,
        max_frames,
        mode=max_frames_mode,
        verbose=verbose,
        engine_label=f"Map-Anything/{model_name}",
    )
    paths = [str(path) for path in selected]

    if verbose:
        print(
            f"--- [vibephysics] Map-Anything: loading {len(paths)} images "
            f"(model={model_name}, resolution_set={resolution}, norm={norm_type}) ---",
            flush=True,
        )

    views = load_images(
        paths,
        resize_mode=resize_mode,
        size=size,
        norm_type=norm_type,
        patch_size=patch_size,
        resolution_set=resolution,
        verbose=verbose,
    )
    rgb = _views_to_rgb(views, norm_type)
    h, w = rgb.shape[1:3]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu" and verbose:
        print("--- [vibephysics] Warning: Map-Anything factory models may be slow on CPU ---", flush=True)

    _normalize_view_metadata(views, model_name)
    kwargs = _resolve_model_kwargs(model_name, model_kwargs, verbose=verbose)

    with _cpu_cuda_shim(device):
        if verbose:
            print(f"--- [vibephysics] Building Map-Anything factory model '{model_name}' ---", flush=True)
        model = _build_model(model_name, kwargs, device)
        views_device = _move_views_to_device(views, device)
        with torch.no_grad():
            if model_name in CORE_PRETRAINED_MODEL_NAMES:
                if verbose:
                    print("--- [vibephysics] Running Map-Anything model.infer() ---", flush=True)
                predictions = model.infer(
                    views_device,
                    use_amp=(device == "cuda"),
                    amp_dtype="bf16",
                )
            else:
                if verbose:
                    print("--- [vibephysics] Running Map-Anything model.forward() ---", flush=True)
                predictions = model(views_device)

    world_points = _stack_key(predictions, "pts3d")
    if world_points is None:
        raise ValueError("Map-Anything output is missing pts3d.")

    depth = _depth_from_outputs(predictions)
    conf = _stack_key(predictions, "conf")
    if conf is None:
        conf = np.ones_like(depth, dtype=np.float32)
    if conf.ndim == 4 and conf.shape[-1] == 1:
        conf = conf[..., 0]

    intrinsic = _intrinsics_from_outputs(predictions)
    extrinsic_w2c = _c2w_to_w2c(_camera_poses_from_factory_outputs(predictions))

    finite_points = np.isfinite(world_points).all(axis=-1)
    finite_depth = np.isfinite(depth)
    if not np.any(finite_points) or not np.any(finite_depth) or not np.isfinite(extrinsic_w2c).all():
        raise RuntimeError(
            "Map-Anything produced non-finite geometry. "
            "On CPU this is commonly caused by mixed precision; AMP is disabled for CPU runs, "
            "so rerun this command with the updated adapter."
        )

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return FeedforwardPrediction(
        images=rgb.astype(np.float32),
        depth=depth.astype(np.float32),
        conf=conf.astype(np.float32),
        extrinsic=extrinsic_w2c.astype(np.float32),
        intrinsic=intrinsic.astype(np.float32),
        world_points=world_points.astype(np.float32),
        image_paths=paths,
        engine="map_anything",
        metadata={
            "model_name": model_name,
            "model_kwargs": kwargs,
            "resize_mode": resize_mode,
            "resolution": resolution,
            "norm_type": norm_type,
            "patch_size": patch_size,
            "selected_indices": indices,
            "input_num_frames": input_num_frames,
            "max_frames_mode": max_frames_mode,
            "vram_gb": get_vram_gb(),
            "input_hw": [int(h), int(w)],
            "w2c_as_camera_pose": False,
        },
    )
