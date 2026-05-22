"""LingBot-Map feedforward engine."""

from __future__ import annotations

import contextlib
import importlib.util
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from ..common import (
    DEFAULT_LINGBOT_MAP_MODEL,
    c2w_to_w2c,
    discover_images,
    feedforward_engine_dir,
    images_chw_to_hwc,
    select_skip_frames,
    to_numpy,
)
from ..schema import FeedforwardPrediction

DEFAULT_CACHE = feedforward_engine_dir("lingbot_map")

CHECKPOINT_URLS = {
    "lingbot-map-long": "https://huggingface.co/robbyant/lingbot-map/resolve/main/lingbot-map-long.pt",
    "lingbot-map": "https://huggingface.co/robbyant/lingbot-map/resolve/main/lingbot-map.pt",
}

_LINGBOT_MAP_TQDM_MODULES = (
    "lingbot_map.models.gct_stream",
    "lingbot_map.models.gct_stream_window",
    "lingbot_map.models.gct_stream_window_v2",
)

_BATCHED_NDIMS = {
    "pose_enc": 3,
    "depth": 5,
    "depth_conf": 4,
    "world_points": 5,
    "world_points_conf": 4,
    "extrinsic": 4,
    "intrinsic": 4,
    "chunk_scales": 2,
    "chunk_transforms": 4,
    "images": 5,
}


from ..deps import ensure_engine_dependencies


def is_available() -> bool:
    if importlib.util.find_spec("torch") is None:
        return False
    return importlib.util.find_spec("lingbot_map") is not None


def ensure_dependencies(verbose: bool = True) -> bool:
    return ensure_engine_dependencies("lingbot_map", verbose=verbose)


def download_checkpoint(
    name: str = DEFAULT_LINGBOT_MAP_MODEL,
    cache_dir: Path | None = None,
    verbose: bool = True,
) -> Path:
    cache = cache_dir or DEFAULT_CACHE
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"{name}.pt"
    if path.exists():
        return path
    url = CHECKPOINT_URLS.get(name)
    if not url:
        raise ValueError(f"Unknown LingBot-Map checkpoint '{name}'")
    if verbose:
        print(f"--- [vibephysics] Downloading {name} checkpoint ---")
    try:
        import torch

        torch.hub.download_url_to_file(url, str(path))
    except Exception:
        subprocess.check_call(["curl", "-L", "--fail", "-o", str(path), url])
    return path


def _squeeze_single_batch(key, value):
    batched_ndim = _BATCHED_NDIMS.get(key)
    if batched_ndim is None or not hasattr(value, "ndim"):
        return value
    if value.ndim == batched_ndim and value.shape[0] == 1:
        return value[0]
    return value


def _load_model(args, device):
    """Load GCTStream from checkpoint (mirrors upstream demo.py)."""
    import torch

    if getattr(args, "mode", "streaming") == "windowed":
        from lingbot_map.models.gct_stream_window import GCTStream
    else:
        from lingbot_map.models.gct_stream import GCTStream

    print("Building model...")
    model = GCTStream(
        img_size=args.image_size,
        patch_size=args.patch_size,
        enable_3d_rope=args.enable_3d_rope,
        max_frame_num=args.max_frame_num,
        kv_cache_sliding_window=args.kv_cache_sliding_window,
        kv_cache_scale_frames=args.num_scale_frames,
        kv_cache_cross_frame_special=True,
        kv_cache_include_scale_frames=True,
        use_sdpa=args.use_sdpa,
        camera_num_iterations=args.camera_num_iterations,
    )

    if args.model_path:
        print(f"Loading checkpoint: {args.model_path}")
        ckpt = torch.load(args.model_path, map_location=device, weights_only=False)
        state_dict = ckpt.get("model", ckpt)
        missing, unexpected = model.load_state_dict(state_dict, strict=False)
        if missing:
            print(f"  Missing keys: {len(missing)}")
        if unexpected:
            print(f"  Unexpected keys: {len(unexpected)}")
        print("  Checkpoint loaded.")

    return model.to(device).eval()


def _postprocess(predictions, images):
    """Convert pose encoding to extrinsics (c2w) and move to CPU."""
    import torch
    from lingbot_map.utils.geometry import closed_form_inverse_se3_general
    from lingbot_map.utils.pose_enc import pose_encoding_to_extri_intri

    extrinsic, intrinsic = pose_encoding_to_extri_intri(predictions["pose_enc"], images.shape[-2:])

    extrinsic_4x4 = torch.zeros((*extrinsic.shape[:-2], 4, 4), device=extrinsic.device, dtype=extrinsic.dtype)
    extrinsic_4x4[..., :3, :4] = extrinsic
    extrinsic_4x4[..., 3, 3] = 1.0
    extrinsic_4x4 = closed_form_inverse_se3_general(extrinsic_4x4)
    extrinsic = extrinsic_4x4[..., :3, :4]

    predictions["extrinsic"] = extrinsic
    predictions["intrinsic"] = intrinsic
    predictions.pop("pose_enc_list", None)
    predictions.pop("images", None)

    print("Moving results to CPU...")
    for key in list(predictions.keys()):
        if isinstance(predictions[key], torch.Tensor):
            predictions[key] = _squeeze_single_batch(
                key, predictions[key].to("cpu", non_blocking=True)
            )
    images_cpu = images.to("cpu", non_blocking=True)
    if torch.cuda.is_available():
        torch.cuda.synchronize()

    return predictions, images_cpu


def _prepare_for_visualization(predictions, images=None):
    """Convert predictions to unbatched NumPy arrays (mirrors upstream demo.py)."""
    import torch

    vis_predictions = {}
    for key, value in predictions.items():
        if isinstance(value, torch.Tensor):
            value = _squeeze_single_batch(key, value.detach().cpu())
            vis_predictions[key] = value.numpy()
        elif isinstance(value, np.ndarray):
            vis_predictions[key] = _squeeze_single_batch(key, value)
        else:
            vis_predictions[key] = value

    if images is None:
        images = predictions.get("images")

    if isinstance(images, torch.Tensor):
        images = images.detach().cpu()
    if isinstance(images, np.ndarray):
        images = _squeeze_single_batch("images", images)
    elif isinstance(images, torch.Tensor):
        images = _squeeze_single_batch("images", images).numpy()

    if isinstance(images, torch.Tensor):
        images = images.numpy()

    if images is not None:
        vis_predictions["images"] = images

    return vis_predictions


def _load_and_preprocess_images(
    image_path_list: list[str],
    *,
    image_size: int = 518,
    patch_size: int = 14,
) -> "torch.Tensor":
    if not image_path_list:
        raise ValueError("At least 1 image is required")
    from lingbot_map.utils.load_fn import load_and_preprocess_images as official_load

    return official_load(
        image_path_list,
        mode="crop",
        image_size=image_size,
        patch_size=patch_size,
    )


def _auto_keyframe_interval(num_frames: int, mode: str) -> int:
    if mode == "streaming" and num_frames > 320:
        return (num_frames + 319) // 320
    return 1


def _flashinfer_available() -> bool:
    return importlib.util.find_spec("flashinfer") is not None


def _resolve_use_sdpa(use_sdpa: bool, *, verbose: bool) -> bool:
    if use_sdpa:
        return True
    if not _flashinfer_available():
        if verbose:
            print(
                "--- [vibephysics] FlashInfer not available; using SDPA backend "
                "(set lingbot_map.use_sdpa: true to silence) ---",
                flush=True,
            )
        return True
    return False


def _inference_dtype(device) -> "torch.dtype":
    import torch

    if torch.cuda.is_available():
        cap = torch.cuda.get_device_capability()
        return torch.bfloat16 if cap[0] >= 8 else torch.float16
    return torch.float32


def _forced_tqdm(*args, **kwargs):
    from tqdm import tqdm as std_tqdm

    kwargs.setdefault("file", sys.stderr)
    kwargs["disable"] = False
    kwargs.setdefault("mininterval", 1.0)
    kwargs.setdefault("dynamic_ncols", True)
    kwargs.setdefault("bar_format", "{desc}: {n_fmt}/{total_fmt} frames [{elapsed}<{remaining}]")
    return std_tqdm(*args, **kwargs)


@contextlib.contextmanager
def _lingbot_map_progress(enabled: bool = True) -> Iterator[None]:
    if not enabled:
        yield
        return

    saved: list[tuple[object, object]] = []
    for name in _LINGBOT_MAP_TQDM_MODULES:
        mod = sys.modules.get(name)
        if mod is None:
            try:
                mod = __import__(name, fromlist=["tqdm"])
            except ImportError:
                continue
        if hasattr(mod, "tqdm"):
            saved.append((mod, mod.tqdm))
            mod.tqdm = _forced_tqdm

    try:
        yield
    finally:
        for mod, orig in saved:
            mod.tqdm = orig


def run_lingbot_map(
    image_path: Path,
    model_path: Path | None = None,
    model_name: str = DEFAULT_LINGBOT_MAP_MODEL,
    mode: str | None = None,
    keyframe_interval: int | None = None,
    window_size: int = 64,
    overlap_size: int = 16,
    overlap_keyframes: int | None = None,
    num_scale_frames: int = 8,
    camera_num_iterations: int = 4,
    use_sdpa: bool = False,
    image_size: int = 518,
    patch_size: int = 14,
    max_frames: int | None = None,
    verbose: bool = True,
) -> FeedforwardPrediction:
    if not ensure_dependencies(verbose):
        raise RuntimeError("LingBot-Map not ready. Run: ./run_lingbot_map.sh (deps auto-install on first run)")

    import torch
    from lingbot_map.utils.geometry import unproject_depth_map_to_point_map

    image_path = Path(image_path)
    all_images = discover_images(image_path)
    if max_frames is not None and len(all_images) > max_frames:
        selected, indices = select_skip_frames(all_images, max_frames)
    else:
        selected, indices = all_images, list(range(len(all_images)))
    paths = [str(p) for p in selected]
    if verbose and len(selected) < len(all_images):
        print(
            f"--- [vibephysics] LingBot-Map: using {len(selected)}/{len(all_images)} "
            f"input frames (evenly subsampled) ---",
            flush=True,
        )
    if verbose:
        print(
            f"--- [vibephysics] LingBot-Map: loading {len(paths)} images "
            f"(preprocess=crop, size={image_size}) ---",
            flush=True,
        )

    images = _load_and_preprocess_images(paths, image_size=image_size, patch_size=patch_size)
    h, w = images.shape[-2], images.shape[-1]
    num_frames = images.shape[0]
    if verbose:
        print(f"--- [vibephysics] Preprocessed to {w}x{h} ({num_frames} frames) ---", flush=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if mode is None:
        mode = "streaming"
    if keyframe_interval is None:
        keyframe_interval = _auto_keyframe_interval(num_frames, mode)

    use_sdpa = _resolve_use_sdpa(use_sdpa, verbose=verbose)

    ckpt = model_path or download_checkpoint(model_name, verbose=verbose)
    if verbose:
        print(f"--- [vibephysics] Building LingBot-Map model (checkpoint: {ckpt}) ---", flush=True)
        print(
            "--- [vibephysics] Note: official code may warn about empty DINOv2 "
            "pretrained_path — weights load from the LingBot-Map checkpoint next. ---",
            flush=True,
        )
    args = SimpleNamespace(
        mode=mode,
        image_size=image_size,
        patch_size=patch_size,
        enable_3d_rope=True,
        max_frame_num=1024,
        kv_cache_sliding_window=64,
        num_scale_frames=num_scale_frames,
        use_sdpa=use_sdpa,
        camera_num_iterations=camera_num_iterations,
        model_path=str(ckpt),
        window_size=window_size,
        overlap_size=overlap_size,
        overlap_keyframes=overlap_keyframes,
        keyframe_interval=keyframe_interval,
    )

    model = _load_model(args, device)
    dtype = _inference_dtype(device)
    if dtype != torch.float32 and getattr(model, "aggregator", None) is not None:
        if verbose:
            print(f"--- [vibephysics] Casting aggregator to {dtype} ---", flush=True)
        model.aggregator = model.aggregator.to(dtype=dtype)

    if device.type == "cuda":
        images = images.to(device)

    output_device = torch.device("cpu")
    if verbose:
        backend = "SDPA" if use_sdpa else "FlashInfer"
        print(f"--- [vibephysics] {mode} inference (dtype={dtype}, {backend}) ---", flush=True)
        if mode == "streaming":
            print(
                f"--- [vibephysics] Phase 1: {num_scale_frames} scale frames; "
                f"Phase 2: frames {num_scale_frames}-{num_frames - 1} one-by-one "
                f"(keyframe_interval={keyframe_interval}; 1 = every frame) ---",
                flush=True,
            )

    with _lingbot_map_progress(verbose):
        with torch.no_grad():
            if torch.cuda.is_available() and dtype != torch.float32:
                autocast_ctx = torch.amp.autocast("cuda", dtype=dtype)
            else:
                from contextlib import nullcontext

                autocast_ctx = nullcontext()
            with autocast_ctx:
                if mode == "streaming":
                    predictions = model.inference_streaming(
                        images,
                        num_scale_frames=num_scale_frames,
                        keyframe_interval=keyframe_interval,
                        output_device=output_device,
                    )
                else:
                    predictions = model.inference_windowed(
                        images,
                        window_size=window_size,
                        overlap_size=overlap_size,
                        overlap_keyframes=overlap_keyframes,
                        num_scale_frames=num_scale_frames,
                        keyframe_interval=keyframe_interval,
                        output_device=output_device,
                    )

    images_for_post = predictions.get("images", images.cpu() if device.type == "cuda" else images)
    predictions, images_cpu = _postprocess(predictions, images_for_post)
    vis = _prepare_for_visualization(predictions, images_cpu)

    extrinsic_c2w = to_numpy(vis["extrinsic"])
    intrinsic = to_numpy(vis["intrinsic"])
    depth = to_numpy(vis["depth"])
    conf = to_numpy(vis.get("depth_conf", np.ones_like(depth[..., 0])))
    if depth.ndim == 4:
        depth_squeeze = depth
    else:
        depth_squeeze = depth[..., None] if depth.ndim == 3 else depth

    if "world_points" in vis:
        world_points = to_numpy(vis["world_points"])
        if world_points.ndim == 5:
            world_points = world_points[..., :3]
    else:
        world_points = unproject_depth_map_to_point_map(depth_squeeze, extrinsic_c2w, intrinsic)

    extrinsic_w2c = c2w_to_w2c(extrinsic_c2w)

    if depth.ndim == 4:
        depth = depth[..., 0]

    rgb = images_chw_to_hwc(to_numpy(vis["images"]))

    return FeedforwardPrediction(
        images=rgb,
        depth=depth.astype(np.float32),
        conf=conf.astype(np.float32),
        extrinsic=extrinsic_w2c.astype(np.float32),
        intrinsic=intrinsic.astype(np.float32),
        world_points=world_points.astype(np.float32),
        image_paths=paths,
        engine="lingbot_map",
        metadata={
            "model_name": model_name,
            "mode": mode,
            "keyframe_interval": keyframe_interval,
            "window_size": window_size,
            "overlap_size": overlap_size,
            "num_frames": num_frames,
            "input_num_frames": len(all_images),
            "selected_indices": indices,
            "use_sdpa": use_sdpa,
            "preprocess_mode": "crop",
            "image_size": image_size,
            "input_hw": [int(h), int(w)],
            "w2c_as_camera_pose": True,
        },
    )
