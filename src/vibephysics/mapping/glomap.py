import os
import sys
import subprocess
from pathlib import Path
from .utils import prepare_output_directory
from .colmap import run_colmap_stage

def run_glomap_stage(
    image_path: Path, 
    database_path: Path, 
    sparse_path: Path, 
    verbose: bool = True
) -> int:
    """
    Runs GLOMAP global mapper in a isolated subprocess.
    """
    if verbose: print(f"--- [vibephysics] Starting GLOMAP stage ---")
    
    env = os.environ.copy()
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    glomap_code = f"""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import pyglomap
import sys

print('--- [Process] Running GLOMAP Global Mapper ---')
status = pyglomap.run_mapper(
    database_path=r'{str(database_path)}',
    image_path=r'{str(image_path)}',
    output_path=r'{str(sparse_path)}'
)
sys.exit(status)
"""
    p = subprocess.run([sys.executable, "-c", glomap_code], env=env)
    return p.returncode

def glomap_pipeline(
    image_path: str | Path,
    output_path: str | Path | None = None,
    database_path: str | Path | None = None,
    matcher: str = "exhaustive",
    camera_model: str = "SIMPLE_RADIAL",
    verbose: bool = True
) -> int:
    """
    Run the complete GLOMAP SfM pipeline: COLMAP Extraction/Matching + GLOMAP Global Mapping.
    """
    try:
        import pyglomap
    except ImportError:
        print("\n[ERROR] 'pyglomap' is not installed.")
        return 1

    image_path = Path(image_path).absolute()
    output_path = prepare_output_directory(image_path, output_path, engine="glomap", verbose=verbose)
    sparse_path = output_path / "sparse"
    
    db_path = Path(database_path).absolute() if database_path else sparse_path / "database.db"

    # 1. Extraction & Matching
    status = run_colmap_stage(image_path, db_path, camera_model, matcher, verbose)
    if status != 0: return status

    # 2. GLOMAP
    status = run_glomap_stage(image_path, db_path, sparse_path, verbose)
    
    if status == 0 and verbose: print(f"\n[SUCCESS] GLOMAP pipeline finished. Results in {output_path}")
    return status
