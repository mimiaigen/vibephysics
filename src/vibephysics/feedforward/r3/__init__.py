"""R3 (3D Reconstruction via Relative Regression) feedforward engine."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from ..common import (
    R3_GIT,
    discover_images,
    feedforward_engine_dir,
    get_vram_gb,
    images_chw_to_hwc,
    limit_image_frames,
    to_numpy,
    unproject_depth_map_to_point_map,
)
from ..deps import ensure_engine_dependencies, pip_install
from ..schema import FeedforwardPrediction

DEFAULT_CACHE = feedforward_engine_dir("r3")

DEFAULT_R3_MODEL = "r3"
DEFAULT_R3_CONFIG = "r3-large"

CHECKPOINT_FILES = {
    "r3": ("KevinXu02/R3", "r3.safetensors"),
    "r3_long": ("KevinXu02/R3", "r3_long.safetensors"),
}

# Preset bundles mirror upstream demo.py (--mode).
_MODE_ALIASES = {"short": "local", "sampled": "strided", "sparse": "strided"}

_MODE_PRESETS: dict[str, dict] = {
    "test": dict(
        kv_cache_mode="all",
        enable_fallback=False,
        max_segment_frames=0,
        metric_scale=False,
    ),
    "local": dict(
        kv_cache_mode="dynamic",
        enable_fallback=False,
        max_segment_frames=0,
        metric_scale=False,
    ),
    "long": dict(
        kv_cache_mode="dynamic",
        enable_fallback=True,
        max_segment_frames=300,
        fallback_drought_threshold_pct=45.0,
        metric_scale=True,
        metric_bootstrap_frames=5,
    ),
    "strided": dict(
        kv_cache_mode="all",
        enable_fallback=True,
        max_segment_frames=100,
        fallback_drought_threshold_pct=45.0,
        metric_scale=True,
        metric_bootstrap_frames=5,
    ),
}

# infer.py relative-pose reconstruction defaults (greedy / PGO).
_REL_POSE_KWARGS = {
    "topn_conf": 999,
    "score_mode": "auto",
    "pgo_num_iters": 100,
    "pgo_lr": 0.05,
    "pgo_weight_T": 1.0,
    "pgo_weight_R": 0.5,
    "pgo_weight_fl": 0.1,
    "pgo_init_prior_weight": 1e-4,
    "pgo_keyframe_stride": 0,
    "edge_percentile_cutoff": 0.0,
    "geman_mcclure_c": 0.0,
    "dcs_phi": 0.0,
    "max_translation_per_frame": 0.0,
}

_MACOS_NO_XFORMERS_DEPS = (
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
    ("requests", "requests"),
    ("tqdm", "tqdm"),
    ("pillow_heif", "pillow_heif"),
)


def is_available() -> bool:
    if importlib.util.find_spec("torch") is None:
        return False
    return importlib.util.find_spec("R3") is not None


def macos_experimental_reason() -> str | None:
    """Return the macOS no-xformers caveat, or None on other platforms."""
    if sys.platform == "darwin":
        return (
            "macOS can run parts of the DA3 stack, but upstream R3's normal pip "
            "install pulls 'xformers', which has no macOS wheel and fails to "
            "build here (clang: unsupported option '-fopenmp'). vibephysics will "
            "try an experimental R3 install that skips xformers and runs on MPS/CPU. "
            "Linux + NVIDIA CUDA remains the upstream-supported path."
        )
    return None


def unsupported_platform_reason() -> str | None:
    """Backward-compatible alias for callers that display platform caveats."""
    return macos_experimental_reason()


def _ensure_huggingface_hub(verbose: bool = True) -> None:
    if importlib.util.find_spec("huggingface_hub") is None:
        pip_install("huggingface_hub", verbose=verbose)


def ensure_dependencies(verbose: bool = True) -> bool:
    if is_available():
        return True

    if sys.platform == "darwin":
        return _ensure_macos_experimental_dependencies(verbose=verbose)

    if not ensure_engine_dependencies("r3", verbose=verbose):
        return False
    try:
        _ensure_huggingface_hub(verbose=verbose)
    except Exception:
        if verbose:
            print("\n[vibephysics] huggingface_hub is required for automatic R3 checkpoint download.")
        return False
    return True


def _auto_install_enabled() -> bool:
    return os.environ.get("VIBEPHYSICS_NO_AUTO_INSTALL", "").strip().lower() not in {
        "1",
        "true",
        "yes",
    }


def _ensure_macos_experimental_dependencies(verbose: bool = True) -> bool:
    auto_install = _auto_install_enabled()
    reason = macos_experimental_reason()
    if verbose and reason:
        print(f"\n[vibephysics] R3 macOS experimental mode:\n  {reason}", flush=True)

    for import_name, pip_spec in _MACOS_NO_XFORMERS_DEPS:
        if importlib.util.find_spec(import_name) is not None:
            continue
        if not auto_install:
            if verbose:
                print(f"[vibephysics] Missing {import_name}; auto-install disabled.")
            return False
        try:
            pip_install(pip_spec, verbose=verbose, extra_specs=["numpy<2"])
        except subprocess.CalledProcessError:
            if verbose:
                print(f"[vibephysics] Failed to install {pip_spec}")
            return False

    if importlib.util.find_spec("R3") is not None:
        return True
    if not auto_install:
        if verbose:
            print("[vibephysics] Missing R3; auto-install disabled.")
        return False

    try:
        if verbose:
            print("\n[vibephysics] Installing R3 without upstream dependencies to skip xformers on macOS")
        pip_install("--no-deps", verbose=verbose, extra_specs=[R3_GIT])
    except subprocess.CalledProcessError:
        if verbose:
            print(f"[vibephysics] Failed to install R3. Try manually: pip install --no-deps {R3_GIT}")
        return False
    return importlib.util.find_spec("R3") is not None


def resolve_mode(mode: str | None) -> str:
    normalized = str(mode or "local").strip().lower()
    normalized = _MODE_ALIASES.get(normalized, normalized)
    if normalized not in _MODE_PRESETS:
        raise ValueError(
            f"Unknown R3 mode '{mode}'. Choose one of: {', '.join(_MODE_PRESETS)} "
            "(or aliases short/sampled/sparse)."
        )
    return normalized


def default_model_for_mode(mode: str) -> str:
    return "r3_long"


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
    name: str = DEFAULT_R3_MODEL,
    cache_dir: Path | None = None,
    verbose: bool = True,
) -> Path:
    repo_id, filename = CHECKPOINT_FILES.get(name, (None, None))
    if repo_id is None:
        raise ValueError(f"Unknown R3 checkpoint '{name}'. Choose one of: {', '.join(CHECKPOINT_FILES)}")

    cache = cache_dir or DEFAULT_CACHE
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / filename
    if path.exists():
        if verbose:
            print(f"--- [vibephysics] Using cached checkpoint: {path} ---")
        return path

    _ensure_huggingface_hub(verbose=verbose)
    if verbose:
        print(f"--- [vibephysics] Downloading {filename} from {repo_id} ---")
    try:
        return _hf_hub_download(repo_id, filename, cache)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to download {repo_id}/{filename}. "
            "Checkpoints are public at https://huggingface.co/KevinXu02/R3 — "
            "check your network connection or download manually into "
            f"{cache}."
        ) from exc


def _load_state_dict(model, ckpt_path: str, device) -> None:
    """Load R3 weights with the key remapping used by upstream infer.py."""
    import torch

    if ckpt_path.endswith(".safetensors"):
        from safetensors.torch import load_file

        checkpoint = load_file(ckpt_path, device=str(device) if device.type == "cuda" else "cpu")
    else:
        checkpoint = torch.load(
            ckpt_path,
            map_location=device if device.type == "cuda" else "cpu",
            weights_only=False,
        )
    state_dict = checkpoint.get("state_dict", checkpoint.get("model", checkpoint))

    model_keys = model.state_dict()
    new_state_dict = {}
    for key, value in state_dict.items():
        if key.startswith("net."):
            key = key[len("net.") :]
        if key.startswith("module."):
            key = key[len("module.") :]
        if key.startswith("model."):
            key = "da3." + key[len("model.") :]
        if not key.startswith("da3.") and not key.startswith("projections."):
            if ("da3." + key) in model_keys:
                key = "da3." + key
        new_state_dict[key] = value

    filtered = {k: v for k, v in new_state_dict.items() if k in model_keys}
    print(f"Matched {len(filtered)} keys from checkpoint out of {len(model_keys)} model keys.")
    model.load_state_dict(filtered, strict=False)


def _build_model_kwargs(
    da3_cfg,
    *,
    preset: dict,
    kv_backend: str,
    metric_model_name: str,
) -> dict:
    kwargs = dict(
        da3_cfg=da3_cfg,
        teacher_embed_dim=2048,
        student_embed_dim=2048,
        freeze="none",
        online_mode=True,
        online_kv_cache_mode=preset["kv_cache_mode"],
        online_kv_backend=kv_backend,
        online_recent_frames=0,
        online_verbose=True,
        bank_initial_frames=1,
        keyframe_mode="novelty",
        keyframe_novelty_threshold=0.985,
        keyframe_max_interval=30,
        keyframe_max_keyframes=100,
        online_fallback_enabled=preset["enable_fallback"],
        max_segment_frames=preset.get("max_segment_frames", 0),
    )
    if preset["enable_fallback"]:
        kwargs.update(
            drought_length=3,
            drought_threshold=0,
            drought_threshold_pct=preset.get("fallback_drought_threshold_pct", 50.0),
            num_bridge_frames=10,
            evict_low_conf_threshold=0,
            fallback_ref_mode="bridge",
            min_segment_frames=16,
            fallback_replay_attention="full",
            disable_segment_pgo=True,
        )
    if preset["metric_scale"]:
        kwargs.update(
            metric_scale_enabled=True,
            metric_model_name=metric_model_name,
            metric_bootstrap_frames=preset.get("metric_bootstrap_frames", 3),
        )
    return kwargs


def _resolve_r3_device(verbose: bool = True) -> "torch.device":
    """
    Resolve R3 device with an experimental MPS option.

    Shared feedforward engines only expose CPU/CUDA because most upstream
    methods here are CUDA-first. R3's default DA3 backbone has enough PyTorch
    fallback coverage to be worth trying on Apple Silicon, so this engine
    accepts ``VIBEPHYSICS_DEVICE=mps`` and uses MPS in auto mode when available.
    """
    import torch

    requested = os.environ.get("VIBEPHYSICS_DEVICE", "auto").strip().lower() or "auto"
    if requested not in {"auto", "cuda", "mps", "cpu"}:
        raise ValueError("VIBEPHYSICS_DEVICE must be one of: auto, cuda, mps, cpu")

    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("VIBEPHYSICS_DEVICE=cuda was requested, but CUDA is unavailable.")
        device = torch.device("cuda")
    elif requested == "mps":
        if not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
            raise RuntimeError("VIBEPHYSICS_DEVICE=mps was requested, but MPS is unavailable.")
        device = torch.device("mps")
    elif requested == "cpu":
        device = torch.device("cpu")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    if verbose:
        if device.type == "cuda":
            name = torch.cuda.get_device_name(0)
            print(f"--- [vibephysics] R3 torch device: cuda ({name}; torch {torch.__version__}) ---")
        elif device.type == "mps":
            print(f"--- [vibephysics] R3 torch device: mps (experimental; torch {torch.__version__}) ---")
        else:
            print(f"--- [vibephysics] R3 torch device: cpu (very slow; torch {torch.__version__}) ---")
    return device


def run_r3(
    image_path: Path,
    checkpoint: str | Path | None = None,
    model_name: str | None = None,
    config_name: str = DEFAULT_R3_CONFIG,
    mode: str | None = "local",
    image_size: int = 504,
    kv_backend: str = "dense",
    rel_pose_method: str = "greedy",
    metric_model_name: str = "depth-anything/DA3METRIC-LARGE",
    max_frames: int | None = None,
    max_frames_mode: str = "first",
    verbose: bool = True,
) -> FeedforwardPrediction:
    if not ensure_dependencies(verbose):
        reason = macos_experimental_reason()
        if reason is not None:
            raise RuntimeError(f"R3 experimental macOS dependency setup failed. {reason}")
        raise RuntimeError(
            "R3 not installed. Run: ./run_feedforward.sh --method r3_long "
            "(deps auto-install on first run)"
        )

    import torch
    from omegaconf import OmegaConf

    from R3.models.r3 import R3 as DA3Wrapper
    from R3.utils.config_resolve import resolve_model_config
    from R3.utils.input_io import prepare_image_views
    from R3.utils.pose_enc import pose_encoding_to_extri_intri
    from depth_anything_3.utils.geometry import affine_inverse  # noqa: F401  (parity with infer.py)

    resolved_mode = resolve_mode(mode)
    preset = _MODE_PRESETS[resolved_mode]
    resolved_model = model_name or default_model_for_mode(resolved_mode)

    all_images = discover_images(image_path)
    selected, indices, input_num_frames = limit_image_frames(
        all_images,
        max_frames,
        mode=max_frames_mode,
        verbose=verbose,
        engine_label="R3",
    )
    str_paths = [str(p) for p in selected]

    if verbose:
        print(
            f"--- [vibephysics] R3: loading {len(str_paths)} images "
            f"(mode={resolved_mode}, size={image_size}) ---",
            flush=True,
        )

    device = _resolve_r3_device(verbose=verbose)
    if device.type != "cuda" and verbose:
        print("--- [vibephysics] Warning: R3 on non-CUDA is experimental and may be slow or hit unsupported ops. ---")

    ckpt = Path(checkpoint) if checkpoint else download_checkpoint(resolved_model, verbose=verbose)
    if not ckpt.exists():
        raise FileNotFoundError(f"R3 checkpoint not found: {ckpt}")

    model_config = resolve_model_config(
        config_name=config_name,
        checkpoint_dir=str(ckpt),
        repo_root=None,
    )
    if verbose:
        print(f"--- [vibephysics] R3 config: {model_config['config']} ---", flush=True)

    cfg = OmegaConf.load(model_config["config"])
    if "model" in cfg and "net" in cfg.model and "da3_cfg" in cfg.model.net:
        da3_cfg = cfg.model.net.da3_cfg
    else:
        da3_cfg = cfg

    model_kwargs = _build_model_kwargs(
        da3_cfg,
        preset=preset,
        kv_backend=kv_backend,
        metric_model_name=metric_model_name,
    )
    if verbose:
        print(f"--- [vibephysics] Building R3 model (checkpoint: {ckpt}) ---", flush=True)
    model = DA3Wrapper(**model_kwargs).to(device)
    _load_state_dict(model, str(ckpt), device)
    model.eval()

    views = prepare_image_views(str_paths, image_size, revisit=0, update=True)
    # Save un-normalized RGB before the model applies ImageNet normalization.
    original_imgs = [
        0.5 * (view["img"].squeeze(0).permute(1, 2, 0).cpu().numpy() + 1.0) for view in views
    ]
    for view in views:
        for key in view:
            if isinstance(view[key], torch.Tensor):
                view[key] = view[key].to(device)

    if device.type == "cuda":
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()

    forward_kwargs = dict(
        use_ray_pose=False,
        pose_max_recent=0,
        bootstrap_full_attention_frames=0,
        rel_pose_reconstruction_method=rel_pose_method,
        rel_pose_reconstruction_kwargs=dict(_REL_POSE_KWARGS),
    )

    if verbose:
        print(f"--- [vibephysics] R3 online inference on {len(views)} frames ---", flush=True)

    with torch.no_grad():
        if device.type == "cuda":
            autocast_ctx = torch.autocast("cuda", dtype=torch.bfloat16)
        else:
            from contextlib import nullcontext

            autocast_ctx = nullcontext()
        with autocast_ctx:
            model.clear_online_state()
            predictions = model(views, **forward_kwargs)

    h, w = predictions["images"].shape[-2:]
    extrinsic_t, intrinsic_t = pose_encoding_to_extri_intri(predictions["pose_enc"], (h, w))

    extrinsic_w2c = to_numpy(extrinsic_t[0])  # [S, 4, 4] (or [S, 3, 4])
    if extrinsic_w2c.ndim == 3 and extrinsic_w2c.shape[-2:] == (4, 4):
        extrinsic_w2c = extrinsic_w2c[:, :3, :4]
    intrinsic = to_numpy(intrinsic_t[0])

    depth = to_numpy(predictions["depth"][0])  # [S, H, W, 1]
    if depth.ndim == 4:
        depth = depth[..., 0]
    conf = to_numpy(predictions["depth_conf"][0])  # [S, H, W]

    num_out = depth.shape[0]
    output_frame_ids = [int(fid) for fid in predictions.get("output_frame_ids", range(num_out))]
    if len(output_frame_ids) != num_out:
        output_frame_ids = list(range(num_out))

    rgb = np.stack(
        [np.clip(original_imgs[src], 0.0, 1.0) for src in output_frame_ids],
        axis=0,
    ).astype(np.float32)
    rgb = images_chw_to_hwc(rgb)
    out_paths = [str_paths[src] for src in output_frame_ids]

    world_points = unproject_depth_map_to_point_map(depth, extrinsic_w2c, intrinsic)

    if device.type == "cuda":
        torch.cuda.empty_cache()

    return FeedforwardPrediction(
        images=rgb,
        depth=depth.astype(np.float32),
        conf=conf.astype(np.float32),
        extrinsic=extrinsic_w2c.astype(np.float32),
        intrinsic=intrinsic.astype(np.float32),
        world_points=world_points.astype(np.float32),
        image_paths=out_paths,
        engine="r3",
        metadata={
            "checkpoint": str(ckpt),
            "model_name": resolved_model,
            "config_name": config_name,
            "mode": resolved_mode,
            "image_size": image_size,
            "kv_backend": kv_backend,
            "rel_pose_method": rel_pose_method,
            "metric_scale": preset["metric_scale"],
            "num_frames": num_out,
            "input_num_frames": input_num_frames,
            "selected_indices": indices,
            "output_frame_ids": output_frame_ids,
            "max_frames_mode": max_frames_mode,
            "inference_device": device.type,
            "vram_gb": get_vram_gb(),
            "input_hw": [int(h), int(w)],
            "w2c_as_camera_pose": False,
        },
    )
