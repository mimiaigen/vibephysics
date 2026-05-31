"""Déjà View (DVLT) feedforward engine — https://github.com/nv-tlabs/dvlt"""

from __future__ import annotations

import contextlib
import importlib.util
import os
from collections.abc import Iterator
from pathlib import Path

import numpy as np
from PIL import Image

from ..common import (
    c2w_to_w2c,
    discover_images,
    feedforward_engine_dir,
    feedforward_hf_hub_cache,
    get_vram_gb,
    images_chw_to_hwc,
    limit_image_frames,
    resolve_torch_device,
    to_numpy,
)
from ..deps import ensure_engine_dependencies
from ..schema import FeedforwardPrediction

DEFAULT_CACHE = feedforward_engine_dir("dvlt")
DEFAULT_CHECKPOINT = "nvidia/dvlt"
DEFAULT_IMG_SIZE = 504
DEFAULT_PATCH_SIZE = 14


def _depth_edge(depth: np.ndarray, rtol: float = 0.03, kernel_size: int = 3) -> np.ndarray:
    depth = np.asarray(depth)
    original_shape = depth.shape
    depth = depth.reshape(-1, *original_shape[-2:])

    pad = kernel_size // 2
    padded = np.pad(depth, ((0, 0), (pad, pad), (pad, pad)), mode="edge")
    depth_max = np.full_like(depth, -np.inf)
    depth_min = np.full_like(depth, np.inf)

    for y in range(kernel_size):
        for x in range(kernel_size):
            window = padded[:, y : y + depth.shape[-2], x : x + depth.shape[-1]]
            depth_max = np.maximum(depth_max, window)
            depth_min = np.minimum(depth_min, window)

    relative_jump = (depth_max - depth_min) / np.maximum(np.abs(depth), 1e-6)
    return (relative_jump > rtol).reshape(original_shape)


def _filter_depth_conf_edges(depth: np.ndarray, conf: np.ndarray, *, rtol: float = 0.03) -> np.ndarray:
    conf = conf.copy()
    depth_for_edges = depth[..., 0] if depth.ndim == 4 else depth
    conf[_depth_edge(depth_for_edges, rtol=rtol)] = 0.0
    return conf


def is_available() -> bool:
    return importlib.util.find_spec("dvlt") is not None


def ensure_dependencies(verbose: bool = True) -> bool:
    from ..deps import ensure_dvlt_package

    return ensure_dvlt_package(verbose=verbose)


@contextlib.contextmanager
def _dvlt_hf_cache() -> Iterator[None]:
    """Keep DVLT / nvidia/dvlt weights under .vibephysics/feedforward/huggingface/."""
    hub_dir = feedforward_hf_hub_cache()
    hf_home = hub_dir.parent
    saved = {
        "HF_HOME": os.environ.get("HF_HOME"),
        "HUGGINGFACE_HUB_CACHE": os.environ.get("HUGGINGFACE_HUB_CACHE"),
    }
    os.environ["HF_HOME"] = str(hf_home)
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(hub_dir)
    try:
        yield
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def run_dvlt(
    image_path: Path,
    *,
    checkpoint: str | Path = DEFAULT_CHECKPOINT,
    img_size: int = DEFAULT_IMG_SIZE,
    patch_size: int = DEFAULT_PATCH_SIZE,
    max_frames: int | None = None,
    max_frames_mode: str = "first",
    filter_depth_edges: bool = True,
    depth_edge_rtol: float = 0.03,
    conf_percentile: float = 50.0,
    verbose: bool = True,
) -> FeedforwardPrediction:
    if not ensure_dependencies(verbose):
        raise RuntimeError(
            "DVLT not installed. Run: ./run_feedforward.sh --method dvlt "
            "(deps auto-install on first run)"
        )

    import torch
    from accelerate import Accelerator
    from dvlt.common.constants import DataField, PredictionField
    from dvlt.model.dvlt.model import DVLT
    from dvlt.util.preprocess import preprocess_images

    all_images = discover_images(image_path)
    selected, indices, input_num_frames = limit_image_frames(
        all_images,
        max_frames,
        mode=max_frames_mode,
        verbose=verbose,
        engine_label="DVLT",
    )
    str_paths = [str(p) for p in selected]
    pil_frames = [Image.open(p).convert("RGB") for p in selected]

    if verbose:
        print(
            f"--- [vibephysics] DVLT: loading {len(str_paths)} images "
            f"(img_size={img_size}, patch_size={patch_size}) ---",
            flush=True,
        )

    device = resolve_torch_device(verbose=verbose).device
    if device == "cpu" and verbose:
        print(
            "--- [vibephysics] Warning: DVLT expects CUDA; running on CPU will be very slow ---",
            flush=True,
        )

    mixed_precision = "bf16" if device != "cpu" else "no"
    accelerator = Accelerator(mixed_precision=mixed_precision)
    torch_device = accelerator.device

    with _dvlt_hf_cache():
        if verbose:
            print(f"--- [vibephysics] Loading DVLT checkpoint: {checkpoint} ---", flush=True)
        model = DVLT(img_size=int(img_size))
        model.load_pretrained(str(checkpoint), strict=True)
        model.setup_test(accelerator)

        batch = preprocess_images(
            pil_frames,
            img_size=int(img_size),
            patch_size=int(patch_size),
            device=torch_device,
        )

        if verbose:
            shape = tuple(batch[DataField.IMAGES].shape)
            print(f"--- [vibephysics] Preprocessed batch images {shape} ---", flush=True)

        with torch.inference_mode():
            with accelerator.autocast():
                predictions = model.predict(batch, accelerator)

    cameras = predictions[PredictionField.CAMERAS]
    if isinstance(cameras, (list, tuple)):
        cameras = cameras[0]

    extrinsic_c2w = to_numpy(cameras.camera_to_worlds).astype(np.float32)
    if extrinsic_c2w.ndim == 2:
        extrinsic_c2w = extrinsic_c2w[None]
    intrinsic = to_numpy(cameras.get_intrinsics_matrices()).astype(np.float32)
    if intrinsic.ndim == 2:
        intrinsic = intrinsic[None]

    depths = to_numpy(predictions[PredictionField.DEPTHS])
    if depths.ndim == 4:
        depths = depths[0]
    conf = to_numpy(predictions[PredictionField.DEPTHS_CONF])
    if conf.ndim == 4:
        conf = conf[0]
    world_points = to_numpy(predictions[PredictionField.WORLD_POINTS])
    if world_points.ndim == 5:
        world_points = world_points[0]

    if filter_depth_edges:
        conf = _filter_depth_conf_edges(depths, conf, rtol=depth_edge_rtol)

    extrinsic_w2c = c2w_to_w2c(extrinsic_c2w)
    images_tensor = batch[DataField.IMAGES]
    if hasattr(images_tensor, "detach"):
        images_tensor = images_tensor.detach().float().cpu().numpy()
    rgb = images_chw_to_hwc(images_tensor[0])

    depth_out = depths.astype(np.float32)
    conf_out = conf.astype(np.float32)
    h, w = int(rgb.shape[1]), int(rgb.shape[2])

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return FeedforwardPrediction(
        images=rgb,
        depth=depth_out,
        conf=conf_out,
        extrinsic=extrinsic_w2c.astype(np.float32),
        intrinsic=intrinsic,
        world_points=world_points.astype(np.float32),
        image_paths=str_paths,
        engine="dvlt",
        metadata={
            "checkpoint": str(checkpoint),
            "img_size": int(img_size),
            "patch_size": int(patch_size),
            "selected_indices": indices,
            "input_num_frames": input_num_frames,
            "max_frames_mode": max_frames_mode,
            "inference_device": str(device),
            "vram_gb": get_vram_gb(),
            "input_hw": [h, w],
            "conf_filter_mode": "percentile",
            "conf_percentile": float(conf_percentile),
            "filter_depth_edges": filter_depth_edges,
            "depth_edge_rtol": depth_edge_rtol,
            "w2c_as_camera_pose": False,
            "upstream_repo": "https://github.com/nv-tlabs/dvlt",
        },
    )
