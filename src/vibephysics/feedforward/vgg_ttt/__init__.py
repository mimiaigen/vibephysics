"""VGG-T³ feedforward engine."""

from __future__ import annotations

import contextlib
import importlib.util
import os
from collections.abc import Iterator
from pathlib import Path

import numpy as np

# vgg-ttt uses torch.compile during model init; disable on platforms where inductor breaks.
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")

from ..common import (
    c2w_to_w2c,
    discover_images,
    feedforward_engine_dir,
    get_vram_gb,
    images_chw_to_hwc,
    limit_image_frames,
    resolve_torch_device,
)
from ..deps import ensure_engine_dependencies
from ..schema import FeedforwardPrediction

DEFAULT_CACHE = feedforward_engine_dir("vgg_ttt")
DEFAULT_MODEL_ID = "nvidia/vgg-ttt"


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


def _predictions_to_numpy(predictions: dict) -> dict:
    predictions_np = {}
    for key, value in predictions.items():
        if hasattr(value, "detach"):
            value = value.detach().float().cpu().numpy()
        elif not isinstance(value, np.ndarray):
            continue
        predictions_np[key] = value
    return predictions_np


def is_available() -> bool:
    return importlib.util.find_spec("vggttt") is not None


def ensure_dependencies(verbose: bool = True) -> bool:
    return ensure_engine_dependencies("vgg_ttt", verbose=verbose)


@contextlib.contextmanager
def _cuda_fallback_context(device: str) -> Iterator[None]:
    """
    Patch upstream vgg-ttt CUDA-only calls so official ``model.infer()`` can run on CPU.

    The upstream package targets NVIDIA GPUs (``.cuda()``, ``autocast("cuda")``); this
    shim is only active when CUDA is unavailable (e.g. Mac).
    """
    if device == "cuda":
        yield
        return

    import torch

    fallback = torch.device(device)
    orig_tensor_cuda = torch.Tensor.cuda
    orig_module_cuda = torch.nn.Module.cuda
    orig_get_capability = torch.cuda.get_device_capability
    orig_mem_get_info = torch.cuda.mem_get_info
    orig_empty_cache = torch.cuda.empty_cache
    orig_autocast = torch.autocast

    def tensor_cuda(self, device=None, non_blocking=False):
        return self.to(fallback)

    def module_cuda(self, device=None):
        return self.to(fallback)

    def fake_get_device_capability(device=None):
        return (0, 0)

    def fake_mem_get_info(device=None):
        free = 4 * 1024**3
        total = 8 * 1024**3
        return free, total

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

    torch.Tensor.cuda = tensor_cuda  # type: ignore[method-assign]
    torch.nn.Module.cuda = module_cuda  # type: ignore[method-assign]
    torch.cuda.get_device_capability = fake_get_device_capability  # type: ignore[assignment]
    torch.cuda.mem_get_info = fake_mem_get_info  # type: ignore[assignment]
    torch.cuda.empty_cache = lambda: None  # type: ignore[assignment]
    torch.autocast = _AutocastShim  # type: ignore[assignment]

    try:
        yield
    finally:
        torch.Tensor.cuda = orig_tensor_cuda  # type: ignore[method-assign]
        torch.nn.Module.cuda = orig_module_cuda  # type: ignore[method-assign]
        torch.cuda.get_device_capability = orig_get_capability  # type: ignore[assignment]
        torch.cuda.mem_get_info = orig_mem_get_info  # type: ignore[assignment]
        torch.cuda.empty_cache = orig_empty_cache  # type: ignore[assignment]
        torch.autocast = orig_autocast  # type: ignore[assignment]


def run_vgg_ttt(
    image_path: Path,
    model_id: str = DEFAULT_MODEL_ID,
    preprocess_mode: str = "crop",
    image_size: int = 518,
    max_frames: int | None = None,
    max_frames_mode: str = "first",
    filter_depth_edges: bool = True,
    depth_edge_rtol: float = 0.03,
    conf_percentile: float = 50.0,
    num_ttt_steps: int | None = 1,
    memory_efficient_inference: bool = False,
    verbose: bool = True,
) -> FeedforwardPrediction:
    if not ensure_dependencies(verbose):
        raise RuntimeError("VGG-T³ not installed. Run: ./run_vgg_ttt.sh (deps auto-install on first run)")

    import torch
    from vggttt.nets.vggt.img import load_and_preprocess_images
    from vggttt.nets.vggt.models.vggt import VGGT

    all_images = discover_images(image_path)
    selected, indices, input_num_frames = limit_image_frames(
        all_images,
        max_frames,
        mode=max_frames_mode,
        verbose=verbose,
        engine_label="VGG-T³",
    )
    str_paths = [str(p) for p in selected]

    if preprocess_mode not in ("crop", "pad"):
        raise ValueError("preprocess_mode must be 'crop' or 'pad'")

    if verbose:
        print(
            f"--- [vibephysics] VGG-T³: loading {len(str_paths)} images "
            f"(size={image_size}, mode={preprocess_mode}) ---"
        )

    device = resolve_torch_device(verbose=verbose).device
    if device == "cpu" and verbose:
        print(
            "--- [vibephysics] Warning: no CUDA GPU; running official model.infer() on CPU "
            "(CUDA calls patched — slow on Mac) ---",
            flush=True,
        )

    with _cuda_fallback_context(device):
        if verbose:
            print(f"--- [vibephysics] Loading model {model_id} ---", flush=True)
        model = VGGT.from_pretrained(model_id).eval().to(device)

        # Official API: load_and_preprocess_images(...) -> infer(images)
        images = load_and_preprocess_images(
            str_paths,
            mode=preprocess_mode,
            target_size=image_size,
        ).to(device)

        if verbose:
            print(f"--- [vibephysics] Preprocessed to {tuple(images.shape)} ---", flush=True)
            print(
                f"--- [vibephysics] VGG-T³: model.infer() on {len(str_paths)} frames "
                f"(single batch, num_ttt_steps={num_ttt_steps}) ---",
                flush=True,
            )

        with torch.inference_mode():
            predictions = model.infer(
                images,
                num_ttt_steps=num_ttt_steps,
                memory_efficient_inference=memory_efficient_inference,
                offload_to_cpu=(device == "cpu"),
            )

    predictions_np = _predictions_to_numpy(predictions)
    depth = predictions_np["depth"]
    if depth.ndim == 3:
        depth = depth[..., None]

    conf = predictions_np["conf"]
    if conf.ndim == 3:
        conf = conf[..., None]

    if filter_depth_edges:
        conf = _filter_depth_conf_edges(depth, conf, rtol=depth_edge_rtol)

    pose_c2w = predictions_np["pose"]
    if pose_c2w.shape[-2:] == (4, 4):
        w2c4 = np.linalg.inv(pose_c2w)
        extrinsic_w2c = w2c4[..., :3, :4].astype(np.float32)
    else:
        if pose_c2w.ndim == 2:
            pose_c2w = pose_c2w[None]
        extrinsic_w2c = c2w_to_w2c(pose_c2w)

    intrinsic_np = predictions_np["intrinsics"].astype(np.float32)
    world_points = predictions_np["pts3d"].astype(np.float32)
    rgb = images_chw_to_hwc(images.detach().cpu().numpy())

    if depth.ndim == 4:
        depth = depth[..., 0]
    if conf.ndim == 4:
        conf = conf[..., 0]

    h, w = rgb.shape[1:3]
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return FeedforwardPrediction(
        images=rgb,
        depth=depth.astype(np.float32),
        conf=conf.astype(np.float32),
        extrinsic=extrinsic_w2c.astype(np.float32),
        intrinsic=intrinsic_np,
        world_points=world_points,
        image_paths=str_paths,
        engine="vgg_ttt",
        metadata={
            "model_id": model_id,
            "preprocess_mode": preprocess_mode,
            "image_size": image_size,
            "selected_indices": indices,
            "input_num_frames": input_num_frames,
            "max_frames_mode": max_frames_mode,
            "inference_device": device,
            "inference_api": "vggttt.VGGT.infer",
            "vram_gb": get_vram_gb(),
            "input_hw": [int(h), int(w)],
            "conf_filter_mode": "percentile",
            "conf_percentile": float(conf_percentile),
            "filter_depth_edges": filter_depth_edges,
            "depth_edge_rtol": depth_edge_rtol,
            "num_ttt_steps": num_ttt_steps,
            "memory_efficient_inference": memory_efficient_inference,
            "w2c_as_camera_pose": False,
        },
    )
