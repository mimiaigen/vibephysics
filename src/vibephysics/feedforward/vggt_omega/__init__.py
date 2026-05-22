"""VGGT-Omega feedforward engine."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from ..common import discover_images, feedforward_engine_dir, get_vram_gb, images_chw_to_hwc, select_skip_frames
from ..schema import FeedforwardPrediction

DEFAULT_CACHE = feedforward_engine_dir("vggt_omega")

CHECKPOINT_FILES = {
    "vggt-omega-1b-512": ("facebook/VGGT-Omega", "vggt_omega_1b_512.pt"),
    "vggt-omega-1b-256-text": ("facebook/VGGT-Omega", "vggt_omega_1b_256_text.pt"),
}

_HF_TOKEN_ENV_KEYS = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_HUB_TOKEN")

_VRAM_BENCHMARK = {
    1: 6.02,
    10: 6.67,
    25: 7.80,
    50: 9.66,
    100: 13.37,
    200: 20.82,
    300: 28.26,
    400: 35.71,
    500: 43.15,
}


def _unproject_depth_map_to_point_map(
    depth_map: np.ndarray,
    extrinsic: np.ndarray,
    intrinsic: np.ndarray,
) -> np.ndarray:
    """VGGT-Omega demo_gradio.py unprojection (w2c extrinsics)."""
    depth = depth_map[..., 0] if depth_map.ndim == 4 else depth_map
    num_frames, height, width = depth.shape

    y, x = np.meshgrid(np.arange(height), np.arange(width), indexing="ij")
    x = np.broadcast_to(x[None], (num_frames, height, width))
    y = np.broadcast_to(y[None], (num_frames, height, width))

    fx = intrinsic[:, 0, 0][:, None, None]
    fy = intrinsic[:, 1, 1][:, None, None]
    cx = intrinsic[:, 0, 2][:, None, None]
    cy = intrinsic[:, 1, 2][:, None, None]

    camera_points = np.stack(
        [(x - cx) / fx * depth, (y - cy) / fy * depth, depth],
        axis=-1,
    )

    rotation = extrinsic[:, :3, :3]
    translation = extrinsic[:, :3, 3]
    return np.einsum(
        "sij,shwj->shwi",
        np.transpose(rotation, (0, 2, 1)),
        camera_points - translation[:, None, None, :],
    ).astype(np.float32)


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
    return importlib.util.find_spec("vggt_omega") is not None


def _pip_install(spec: str, verbose: bool = True) -> None:
    if verbose:
        print(f"--- [vibephysics] Installing {spec} ---")
    subprocess.check_call([sys.executable, "-m", "pip", "install", spec])


def _ensure_huggingface_hub(verbose: bool = True) -> None:
    if importlib.util.find_spec("huggingface_hub") is None:
        _pip_install("huggingface_hub", verbose=verbose)


def _token_from_env() -> str | None:
    for key in _HF_TOKEN_ENV_KEYS:
        token = os.environ.get(key)
        if token:
            return token.strip()
    return None


def _is_auth_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    if any(token in message for token in ("401", "403", "gated", "authorized", "authentication", "credentials")):
        return True
    try:
        from huggingface_hub.errors import GatedRepoError, HfHubHTTPError

        if isinstance(exc, GatedRepoError):
            return True
        if isinstance(exc, HfHubHTTPError) and exc.response.status_code in (401, 403):
            return True
    except Exception:
        pass
    return False


def ensure_hf_auth(verbose: bool = True, *, interactive: bool = True) -> bool:
    _ensure_huggingface_hub(verbose=verbose)
    from huggingface_hub import get_token, login

    env_token = _token_from_env()
    if env_token:
        login(token=env_token, add_to_git_credential=False)
        return True

    if get_token():
        return True

    if interactive and sys.stdin.isatty():
        if verbose:
            print("--- [vibephysics] Hugging Face login required (gated VGGT-Omega checkpoint) ---")
            print("Request access first: https://huggingface.co/facebook/VGGT-Omega")
        login(add_to_git_credential=False)
        return bool(get_token())

    return False


def ensure_dependencies(verbose: bool = True) -> bool:
    missing = []
    for package in ("torch", "cv2", "vggt_omega"):
        if importlib.util.find_spec("cv2" if package == "cv2" else package) is None:
            missing.append("opencv-python" if package == "cv2" else package)
    if missing:
        if verbose:
            print(f"\n[vibephysics] VGGT-Omega dependencies missing: {', '.join(missing)}")
            print('Install with: pip install "vibephysics[vggt_omega]"')
        return False
    try:
        _ensure_huggingface_hub(verbose=False)
    except Exception:
        if verbose:
            print("\n[vibephysics] huggingface_hub is required for automatic checkpoint download.")
        return False
    return True


def _hf_hub_download(repo_id: str, filename: str, cache: Path) -> Path:
    from huggingface_hub import hf_hub_download

    hub_cache = feedforward_engine_dir("huggingface")
    downloaded = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=str(cache),
        cache_dir=str(hub_cache),
    )
    return Path(downloaded)


def download_checkpoint(
    name: str = "vggt-omega-1b-512",
    cache_dir: Path | None = None,
    verbose: bool = True,
    *,
    interactive_auth: bool = True,
) -> Path:
    repo_id, filename = CHECKPOINT_FILES.get(name, (None, None))
    if repo_id is None:
        raise ValueError(f"Unknown VGGT-Omega checkpoint '{name}'")

    cache = cache_dir or DEFAULT_CACHE
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / filename
    if path.exists():
        if verbose:
            print(f"--- [vibephysics] Using cached checkpoint: {path} ---")
        return path

    _ensure_huggingface_hub(verbose=verbose)
    ensure_hf_auth(verbose=verbose, interactive=interactive_auth)

    if verbose:
        print(f"--- [vibephysics] Downloading {filename} from {repo_id} ---")

    try:
        return _hf_hub_download(repo_id, filename, cache)
    except Exception as exc:
        if _is_auth_error(exc) and interactive_auth and sys.stdin.isatty():
            if verbose:
                print("--- [vibephysics] Download unauthorized; retrying Hugging Face login ---")
            from huggingface_hub import login

            login(add_to_git_credential=False)
            try:
                return _hf_hub_download(repo_id, filename, cache)
            except Exception as retry_exc:
                exc = retry_exc
        raise RuntimeError(
            f"Failed to download {repo_id}/{filename}. "
            "Request access at https://huggingface.co/facebook/VGGT-Omega, then either:\n"
            "  - rerun in an interactive terminal (login prompt will appear), or\n"
            "  - export HF_TOKEN=<your_hf_token> before running."
        ) from exc


def estimate_vram_gb(num_frames: int) -> float:
    if num_frames <= 0:
        return _VRAM_BENCHMARK[1]
    keys = sorted(_VRAM_BENCHMARK)
    if num_frames <= keys[0]:
        return _VRAM_BENCHMARK[keys[0]]
    if num_frames >= keys[-1]:
        return _VRAM_BENCHMARK[keys[-1]] * (num_frames / keys[-1])

    for lo, hi in zip(keys, keys[1:]):
        if lo <= num_frames <= hi:
            t = (num_frames - lo) / (hi - lo)
            return _VRAM_BENCHMARK[lo] + t * (_VRAM_BENCHMARK[hi] - _VRAM_BENCHMARK[lo])
    return _VRAM_BENCHMARK[keys[-1]]


def _predictions_to_numpy(predictions: dict) -> dict:
    predictions_np = {}
    for key, value in predictions.items():
        if hasattr(value, "detach"):
            value = value.detach().float().cpu().numpy()
        elif not isinstance(value, np.ndarray):
            continue
        if value.ndim >= 1 and value.shape[0] == 1:
            value = value[0]
        predictions_np[key] = value
    return predictions_np


def run_vggt_omega(
    image_path: Path,
    checkpoint: str | Path | None = None,
    checkpoint_name: str = "vggt-omega-1b-512",
    image_resolution: int = 512,
    preprocess_mode: str = "balanced",
    enable_alignment: bool = False,
    batch_size: int | None = None,
    filter_depth_edges: bool = True,
    depth_edge_rtol: float = 0.03,
    conf_percentile: float = 50.0,
    verbose: bool = True,
) -> FeedforwardPrediction:
    if not ensure_dependencies(verbose):
        raise RuntimeError('VGGT-Omega not installed. Run: pip install "vibephysics[vggt_omega]"')

    import torch
    from vggt_omega.models import VGGTOmega
    from vggt_omega.utils.load_fn import load_and_preprocess_images
    from vggt_omega.utils.pose_enc import encoding_to_camera

    ckpt = Path(checkpoint) if checkpoint else download_checkpoint(checkpoint_name, verbose=verbose)
    if not ckpt.exists():
        raise FileNotFoundError(
            f"VGGT-Omega checkpoint not found: {ckpt}. "
            "Download from https://huggingface.co/facebook/VGGT-Omega (gated access)."
        )

    all_images = discover_images(image_path)
    if batch_size is None:
        batch_size = len(all_images)
    else:
        batch_size = min(batch_size, len(all_images))

    selected, indices = select_skip_frames(all_images, batch_size)
    str_paths = [str(p) for p in selected]

    if preprocess_mode not in ("balanced", "max_size"):
        raise ValueError("preprocess_mode must be 'balanced' or 'max_size'")

    if verbose:
        print(
            f"--- [vibephysics] VGGT-Omega: loading {len(str_paths)} images "
            f"(resolution={image_resolution}, mode={preprocess_mode}) ---"
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu" and verbose:
        print("--- [vibephysics] Warning: VGGT-Omega expects CUDA; running on CPU ---")

    model = VGGTOmega(enable_alignment=enable_alignment).to(device).eval()
    model.load_state_dict(torch.load(str(ckpt), map_location="cpu"))

    images = load_and_preprocess_images(
        str_paths,
        mode=preprocess_mode,
        image_resolution=image_resolution,
    ).to(device)
    if verbose:
        print(f"--- [vibephysics] Preprocessed to {tuple(images.shape)} ---")

    with torch.inference_mode():
        predictions = model(images)

    extrinsic, intrinsic = encoding_to_camera(
        predictions["pose_enc"],
        predictions["images"].shape[-2:],
    )
    predictions["extrinsic"] = extrinsic
    predictions["intrinsic"] = intrinsic

    predictions_np = _predictions_to_numpy(predictions)
    depth = predictions_np["depth"]
    if depth.ndim == 3:
        depth = depth[..., None]

    conf = predictions_np["depth_conf"]
    if conf.ndim == 3:
        conf = conf[..., None]

    extrinsic_np = predictions_np["extrinsic"]
    if extrinsic_np.ndim == 4 and extrinsic_np.shape[-2:] == (4, 4):
        extrinsic_np = extrinsic_np[:, :3, :4]

    intrinsic_np = predictions_np["intrinsic"]
    if filter_depth_edges:
        conf = _filter_depth_conf_edges(depth, conf, rtol=depth_edge_rtol)

    world_points = _unproject_depth_map_to_point_map(depth, extrinsic_np, intrinsic_np)
    rgb = images_chw_to_hwc(predictions_np["images"])

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
        extrinsic=extrinsic_np.astype(np.float32),
        intrinsic=intrinsic_np.astype(np.float32),
        world_points=world_points.astype(np.float32),
        image_paths=str_paths,
        engine="vggt_omega",
        metadata={
            "checkpoint": str(ckpt),
            "checkpoint_name": checkpoint_name,
            "image_resolution": image_resolution,
            "preprocess_mode": preprocess_mode,
            "enable_alignment": enable_alignment,
            "selected_indices": indices,
            "vram_gb": get_vram_gb(),
            "input_hw": [int(h), int(w)],
            "conf_filter_mode": "percentile",
            "conf_percentile": float(conf_percentile),
            "filter_depth_edges": filter_depth_edges,
            "depth_edge_rtol": depth_edge_rtol,
            "w2c_as_camera_pose": False,
        },
    )
