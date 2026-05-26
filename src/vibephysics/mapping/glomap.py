import importlib.util
from pathlib import Path

from .colmap import run_colmap_stage, run_global_mapping_stage
from .utils import prepare_output_directory


def glomap_pipeline(
    image_path: str | Path,
    output_path: str | Path | None = None,
    database_path: str | Path | None = None,
    matcher: str = "exhaustive",
    camera_model: str = "PINHOLE",
    verbose: bool = True,
) -> int:
    """
    Run the complete GLOMAP SfM pipeline: COLMAP extraction/matching + global mapping.

    Global mapping is provided by COLMAP 4.0+ via pycolmap.global_mapping.
    """
    if importlib.util.find_spec("pycolmap") is None:
        print("\n[ERROR] 'pycolmap' is not installed.")
        print("Please install mapping tools with: pip install vibephysics")
        return 1

    image_path = Path(image_path).absolute()
    output_path = prepare_output_directory(image_path, output_path, engine="glomap", verbose=verbose)
    sparse_path = output_path / "sparse"

    db_path = Path(database_path).absolute() if database_path else sparse_path / "database.db"

    status = run_colmap_stage(image_path, db_path, camera_model, matcher, verbose)
    if status != 0:
        return status

    status = run_global_mapping_stage(image_path, db_path, sparse_path, verbose)

    if status == 0 and verbose:
        print(f"\n[SUCCESS] GLOMAP pipeline finished. Results in {output_path}")
    return status
