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
    get_vram_gb,
    images_chw_to_hwc,
    limit_image_frames,
    resolve_torch_device,
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
        del state_dict, ckpt

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


# Official demo.py thresholds (streaming KV cache vs windowed cross-window alignment).
STREAMING_FULL_KEYFRAME_MAX = 320
WINDOWED_AUTO_THRESHOLD = 321
DEFAULT_STREAMING_KEYFRAME_BUDGET = 320


def _is_auto_mode(mode: str | None) -> bool:
    if mode is None:
        return True
    return str(mode).strip().lower() in {"", "auto", "null", "none"}


def resolve_inference_settings(
    num_frames: int,
    *,
    mode: str | None = None,
    keyframe_interval: int | None = None,
    max_streaming_keyframes: int | None = None,
    vram_gb: float | None = None,
) -> tuple[str, int, bool]:
    """
    Pick LingBot-Map inference mode and keyframe interval from frame count.

    Auto (mode unset or ``auto``):
      - streaming while the retained keyframe cache fits the detected GPU
      - >320 frames: windowed with cross-window alignment (keyframe_interval=1)

    Explicit ``streaming`` on long clips keeps official demo behavior
    (auto keyframe_interval = ceil(num_frames / keyframe budget)).
    """
    auto_mode = _is_auto_mode(mode)
    resolved_mode = "streaming" if auto_mode else str(mode).strip().lower()
    if resolved_mode not in {"streaming", "windowed"}:
        raise ValueError(f"Unknown LingBot-Map mode '{mode}'. Use streaming, windowed, or auto.")

    budget = _resolve_streaming_keyframe_budget(
        max_streaming_keyframes=max_streaming_keyframes,
        vram_gb=vram_gb,
    )
    low_vram_streaming_over_budget = (
        vram_gb is not None and vram_gb <= 16.5 and num_frames > budget
    )
    if auto_mode and (num_frames >= WINDOWED_AUTO_THRESHOLD or low_vram_streaming_over_budget):
        resolved_mode = "windowed"

    if keyframe_interval is not None:
        resolved_keyframe = max(int(keyframe_interval), 1)
    elif resolved_mode == "streaming":
        resolved_keyframe = max((num_frames + budget - 1) // budget, 1)
    else:
        resolved_keyframe = 1

    return resolved_mode, resolved_keyframe, auto_mode


def _resolve_streaming_keyframe_budget(
    *,
    max_streaming_keyframes: int | None = None,
    vram_gb: float | None = None,
) -> int:
    """
    Limit LingBot streaming keyframes to keep the retained CUDA KV cache bounded.

    The official demo uses 320, which is too high for ~16 GB GPUs at 518px.
    Explicit config/env values win; otherwise scale conservatively by total VRAM.
    """
    if max_streaming_keyframes is not None:
        return max(int(max_streaming_keyframes), 1)

    import os

    env_value = os.environ.get("VIBEPHYSICS_LINGBOT_MAX_STREAMING_KEYFRAMES")
    if env_value not in (None, ""):
        return max(int(env_value), 1)

    if vram_gb is None:
        return DEFAULT_STREAMING_KEYFRAME_BUDGET
    if vram_gb <= 16.5:
        return 32
    if vram_gb <= 24:
        return 48
    if vram_gb <= 32:
        return 64
    if vram_gb <= 48:
        return 128
    return DEFAULT_STREAMING_KEYFRAME_BUDGET


def _resolve_window_params(
    *,
    window_size: int,
    overlap_size: int,
    auto_mode: bool,
    vram_gb: float | None = None,
) -> tuple[int, int]:
    import os

    env_window = os.environ.get("VIBEPHYSICS_LINGBOT_WINDOW_SIZE")
    env_overlap = os.environ.get("VIBEPHYSICS_LINGBOT_OVERLAP_SIZE")
    if env_window not in (None, ""):
        window_size = int(env_window)
    elif auto_mode and vram_gb is not None:
        if vram_gb <= 16.5:
            window_size = min(window_size, 24)
        elif vram_gb <= 24:
            window_size = min(window_size, 32)
        elif vram_gb <= 32:
            window_size = min(window_size, 48)

    if env_overlap not in (None, ""):
        overlap_size = int(env_overlap)
    elif auto_mode and vram_gb is not None and vram_gb <= 24:
        overlap_size = min(overlap_size, max(window_size // 4, 1))

    window_size = max(int(window_size), 2)
    overlap_size = max(min(int(overlap_size), window_size - 1), 0)
    return window_size, overlap_size


def format_inference_plan(
    num_frames: int,
    *,
    mode: str | None = None,
    keyframe_interval: int | None = None,
    max_streaming_keyframes: int | None = None,
    vram_gb: float | None = None,
    window_size: int = 64,
    overlap_size: int = 16,
) -> str:
    resolved_mode, resolved_keyframe, auto_mode = resolve_inference_settings(
        num_frames,
        mode=mode,
        keyframe_interval=keyframe_interval,
        max_streaming_keyframes=max_streaming_keyframes,
        vram_gb=vram_gb,
    )
    auto_note = " (auto)" if auto_mode else ""
    window_size, overlap_size = _resolve_window_params(
        window_size=window_size,
        overlap_size=overlap_size,
        auto_mode=auto_mode,
        vram_gb=vram_gb,
    )
    if resolved_mode == "windowed":
        return (
            f"LingBot-Map plan{auto_note}: {num_frames} frames -> "
            f"windowed (window_size={window_size}, overlap={overlap_size}, "
            f"keyframe_interval={resolved_keyframe})"
        )
    if resolved_keyframe > 1:
        budget = (num_frames + resolved_keyframe - 1) // resolved_keyframe
        return (
            f"LingBot-Map plan{auto_note}: {num_frames} frames -> "
            f"streaming (keyframe_interval={resolved_keyframe}; "
            f"retains ~{budget} keyframes; non-keyframes skip KV cache)"
        )
    return f"LingBot-Map plan{auto_note}: {num_frames} frames -> streaming (every frame a keyframe)"


def preview_input_plan(
    input_path: str | Path,
    *,
    mode: str | None = None,
    keyframe_interval: int | None = None,
    max_streaming_keyframes: int | None = None,
    vram_gb: float | None = None,
    max_frames: int | None = None,
    max_frames_mode: str = "first",
    video_fps: float = 2.0,
    window_size: int = 64,
    overlap_size: int = 16,
) -> str:
    """Estimate inference plan from a path before full reconstruction (for CLI preview)."""
    from ..reconstruct import (
        default_video_frames_dir,
        discover_images,
        existing_frames_in_dir,
        looks_like_video_path,
    )

    path = Path(input_path)
    num_frames: int | None = None

    if path.is_dir():
        try:
            num_frames = len(discover_images(path))
        except (ValueError, FileNotFoundError):
            pass
    elif path.is_file() and looks_like_video_path(path):
        existing = existing_frames_in_dir(default_video_frames_dir(path))
        if existing:
            num_frames = len(existing)
        else:
            num_frames = _estimate_video_frame_count(path, video_fps)
    elif path.is_file():
        num_frames = 1

    if num_frames is None:
        return "Inference plan: frame count unknown until video frames are extracted"
    if max_frames is not None and num_frames > max_frames:
        num_frames = max_frames
    suffix = ""
    if max_frames is not None and max_frames_mode == "first":
        suffix = " [first consecutive frames]"
    elif max_frames is not None:
        suffix = " [spread across full input]"
    return format_inference_plan(
        num_frames,
        mode=mode,
        keyframe_interval=keyframe_interval,
        max_streaming_keyframes=max_streaming_keyframes,
        vram_gb=vram_gb,
        window_size=window_size,
        overlap_size=overlap_size,
    ) + suffix


def _estimate_video_frame_count(video_path: Path, extract_fps: float) -> int | None:
    import subprocess

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        duration = float(result.stdout.strip())
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        return None
    return max(int(duration * max(float(extract_fps), 1e-6)), 1)


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

    if device.type == "cuda":
        cap = torch.cuda.get_device_capability(device)
        return torch.bfloat16 if cap[0] >= 8 else torch.float16
    return torch.float32


def _forced_tqdm(*args, **kwargs):
    from tqdm import tqdm as std_tqdm

    desc = str(kwargs.get("desc", args[0] if args else ""))
    unit = "windows" if "window" in desc.lower() else "frames"
    kwargs.setdefault("file", sys.stderr)
    kwargs["disable"] = False
    kwargs.setdefault("mininterval", 1.0)
    kwargs.setdefault("dynamic_ncols", True)
    kwargs.setdefault("unit", unit)
    kwargs.setdefault("bar_format", "{desc}: {n_fmt}/{total_fmt} {unit} [{elapsed}<{remaining}]")
    return std_tqdm(*args, **kwargs)


def _estimate_window_count(num_frames: int, window_size: int, overlap_size: int) -> int:
    if num_frames <= 0:
        return 0
    if num_frames <= window_size:
        return 1
    stride = max(window_size - overlap_size, 1)
    return ((num_frames - window_size + stride - 1) // stride) + 1


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
    max_streaming_keyframes: int | None = None,
    window_size: int = 64,
    overlap_size: int = 16,
    overlap_keyframes: int | None = None,
    num_scale_frames: int = 8,
    camera_num_iterations: int = 4,
    use_sdpa: bool = False,
    image_size: int = 518,
    patch_size: int = 14,
    max_frames: int | None = None,
    max_frames_mode: str = "first",
    verbose: bool = True,
) -> FeedforwardPrediction:
    if not ensure_dependencies(verbose):
        raise RuntimeError(
            "LingBot-Map not ready. Run: ./run_feedforward.sh --method lingbot_map "
            "(deps auto-install on first run)"
        )

    import torch
    from lingbot_map.utils.geometry import unproject_depth_map_to_point_map

    image_path = Path(image_path)
    all_images = discover_images(image_path)
    input_num_frames = len(all_images)
    selected, indices, _ = limit_image_frames(
        all_images,
        max_frames,
        mode=max_frames_mode,
        verbose=verbose,
        engine_label="LingBot-Map",
    )
    paths = [str(p) for p in selected]
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

    device_info = resolve_torch_device(verbose=verbose)
    device = torch.device(device_info.device)
    mode, keyframe_interval, mode_auto = resolve_inference_settings(
        num_frames,
        mode=mode,
        keyframe_interval=keyframe_interval,
        max_streaming_keyframes=max_streaming_keyframes,
        vram_gb=device_info.cuda_total_memory_gb,
    )
    if mode == "windowed":
        window_size, overlap_size = _resolve_window_params(
            window_size=window_size,
            overlap_size=overlap_size,
            auto_mode=mode_auto,
            vram_gb=device_info.cuda_total_memory_gb,
        )
    if verbose:
        print(
            f"--- [vibephysics] {format_inference_plan(num_frames, mode='auto' if mode_auto else mode, keyframe_interval=keyframe_interval, max_streaming_keyframes=max_streaming_keyframes, vram_gb=device_info.cuda_total_memory_gb, window_size=window_size, overlap_size=overlap_size)} ---",
            flush=True,
        )

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
        torch.cuda.empty_cache()

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
        else:
            num_windows = _estimate_window_count(num_frames, window_size, overlap_size)
            print(
                f"--- [vibephysics] Windowed: {num_frames} source frames -> "
                f"{num_windows} overlapping windows "
                f"(window_size={window_size}, overlap_size={overlap_size}, "
                f"keyframe_interval={keyframe_interval}) ---",
                flush=True,
            )

    with _lingbot_map_progress(verbose):
        with torch.no_grad():
            if device.type == "cuda" and dtype != torch.float32:
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
            "mode_auto_selected": mode_auto,
            "keyframe_interval": keyframe_interval,
            "max_streaming_keyframes": max_streaming_keyframes,
            "window_size": window_size,
            "overlap_size": overlap_size,
            "overlap_keyframes": overlap_keyframes,
            "num_frames": num_frames,
            "input_num_frames": input_num_frames,
            "selected_indices": indices,
            "max_frames_mode": max_frames_mode,
            "use_sdpa": use_sdpa,
            "inference_device": device_info.device,
            "vram_gb": get_vram_gb(),
            "preprocess_mode": "crop",
            "image_size": image_size,
            "input_hw": [int(h), int(w)],
            "w2c_as_camera_pose": True,
        },
    )
