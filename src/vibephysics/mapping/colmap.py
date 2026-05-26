import importlib.util
import os
import subprocess
import sys
from pathlib import Path

from .utils import find_sparse_model, prepare_output_directory, resolve_mapping_input

MAPPERS = {
    "glomap": ("global_mapping", "GLOMAP"),
    "colmap": ("incremental_mapping", "COLMAP incremental"),
}


def _run_pycolmap(code: str) -> int:
    env = os.environ.copy()
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    wrapped = f'import os\nos.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"\n{code}'
    return subprocess.run([sys.executable, "-c", wrapped], env=env).returncode


def _extract_and_match(
    image_path: Path,
    database_path: Path,
    camera_model: str,
    matcher: str,
    verbose: bool,
) -> int:
    if verbose:
        print("--- [vibephysics] Feature extraction & matching ---")
    db, img = str(database_path), str(image_path)
    code = f"""
import pycolmap
from pathlib import Path

db_path = Path(r'{db}')
img_path = Path(r'{img}')
reader_options = pycolmap.ImageReaderOptions()
reader_options.camera_model = '{camera_model}'
pycolmap.extract_features(db_path, img_path, reader_options=reader_options)
matchers = {{'exhaustive': pycolmap.match_exhaustive, 'sequential': pycolmap.match_sequential}}
matchers['{matcher}'](db_path)
"""
    return _run_pycolmap(code)


def _run_mapper(
    mapper: str,
    image_path: Path,
    database_path: Path,
    sparse_path: Path,
    verbose: bool,
) -> int:
    fn_name, label = MAPPERS[mapper]
    if verbose:
        print(f"--- [vibephysics] {label} mapping ---")
    db, img, out = str(database_path), str(image_path), str(sparse_path)
    guard = ""
    if fn_name == "global_mapping":
        guard = """
if not hasattr(pycolmap, "global_mapping"):
    raise SystemExit("pycolmap >= 4.0 required for GLOMAP. Run: pip install 'pycolmap>=4.0'")
"""
    code = f"""
import pycolmap
import sys
{guard}
reconstructions = pycolmap.{fn_name}(
    database_path=r'{db}',
    image_path=r'{img}',
    output_path=r'{out}',
)
sys.exit(0 if reconstructions else 1)
"""
    return _run_pycolmap(code)


def sfm_pipeline(
    image_path: str | Path,
    output_path: str | Path | None = None,
    database_path: str | Path | None = None,
    matcher: str = "sequential",
    camera_model: str = "SIMPLE_RADIAL",
    verbose: bool = True,
    video_fps: float | None = 2.0,
    video_quality: int = 2,
    mapper: str = "glomap",
    save_blend: bool = True,
    blend_path: str | Path | None = None,
    point_size: float = 0.03,
    rotation: tuple[float, float, float] = (-90, 0, 0),
    animate: bool = True,
    animation_fps: int = 24,
) -> int:
    """Run sparse SfM: feature extraction, matching, then global or incremental mapping."""
    if mapper not in MAPPERS:
        raise ValueError(f"Unknown mapper '{mapper}'. Choose: {', '.join(MAPPERS)}")
    if importlib.util.find_spec("pycolmap") is None:
        print("\n[ERROR] pycolmap is not installed. Run: pip install vibephysics")
        return 1
    if matcher not in {"exhaustive", "sequential"}:
        print(f"\n[ERROR] Unknown matcher '{matcher}'. Choose: exhaustive, sequential")
        return 1

    image_path = resolve_mapping_input(
        image_path,
        video_fps=video_fps,
        video_quality=video_quality,
        verbose=verbose,
    )
    output_path = prepare_output_directory(image_path, output_path, engine=mapper, verbose=verbose)
    sparse_path = output_path / "sparse"
    db_path = Path(database_path).absolute() if database_path else sparse_path / "database.db"

    status = _extract_and_match(image_path, db_path, camera_model, matcher, verbose)
    if status != 0:
        return status

    status = _run_mapper(mapper, image_path, db_path, sparse_path, verbose)
    if status != 0:
        return status

    if verbose:
        print(f"\n[SUCCESS] {MAPPERS[mapper][1]} finished. Results in {output_path}")

    if not save_blend:
        return 0

    sparse_model = find_sparse_model(sparse_path)
    if sparse_model is None:
        print(f"[ERROR] No sparse model found under {sparse_path}")
        return 1

    from .map_visual import save_reconstruction_blend

    blend_out = Path(blend_path) if blend_path else Path(output_path) / "visualize.blend"
    return save_reconstruction_blend(
        sparse_model,
        blend_out,
        point_size=point_size,
        rotation=rotation,
        animate=animate,
        animation_fps=animation_fps,
        video_fps=video_fps,
        frames_dir=image_path,
        verbose=verbose,
    )


def glomap_pipeline(*args, **kwargs) -> int:
    """Global SfM via COLMAP 4.0+ (pycolmap.global_mapping)."""
    return sfm_pipeline(*args, mapper="glomap", **kwargs)


def colmap_pipeline(*args, **kwargs) -> int:
    """Incremental SfM via pycolmap.incremental_mapping."""
    return sfm_pipeline(*args, mapper="colmap", **kwargs)
