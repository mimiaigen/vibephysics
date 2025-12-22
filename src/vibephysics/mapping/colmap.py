import os
import sys
import subprocess
from pathlib import Path
from .utils import prepare_output_directory

def run_colmap_stage(
    image_path: Path, 
    database_path: Path, 
    camera_model: str = "PINHOLE", 
    matcher: str = "exhaustive", 
    verbose: bool = True
) -> int:
    """
    Runs COLMAP feature extraction and matching in a isolated subprocess.
    """
    if verbose: print(f"--- [vibephysics] Starting COLMAP feature extraction & matching ---")
    
    env = os.environ.copy()
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    colmap_code = f"""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import pycolmap
from pathlib import Path
import sys

db_path = Path(r'{str(database_path)}')
img_path = Path(r'{str(image_path)}')

print('--- [Process] Extracting features ---')
pycolmap.extract_features(db_path, img_path, camera_model='{camera_model}')

print('--- [Process] Matching features ({matcher}) ---')
if '{matcher}' == 'exhaustive':
    pycolmap.match_exhaustive(db_path)
elif '{matcher}' == 'sequential':
    pycolmap.match_sequential(db_path)
else:
    print('Error: Unsupported matcher {matcher}')
    sys.exit(1)
"""
    p = subprocess.run([sys.executable, "-c", colmap_code], env=env)
    return p.returncode

def run_incremental_mapping_stage(
    image_path: Path, 
    database_path: Path, 
    sparse_path: Path, 
    verbose: bool = True
) -> int:
    """
    Runs COLMAP incremental mapper in a isolated subprocess.
    """
    if verbose: print(f"--- [vibephysics] Starting COLMAP Incremental Mapping ---")
    
    env = os.environ.copy()
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    mapping_code = f"""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import pycolmap
import sys

print('--- [Process] Running COLMAP Incremental Mapper ---')
reconstructions = pycolmap.incremental_mapping(
    database_path=r'{str(database_path)}',
    image_path=r'{str(image_path)}',
    output_path=r'{str(sparse_path)}'
)

if reconstructions:
    print(f'--- [Process] Found {{len(reconstructions)}} models ---')
    sys.exit(0)
else:
    print('--- [Process] Mapping failed ---')
    sys.exit(1)
"""
    p = subprocess.run([sys.executable, "-c", mapping_code], env=env)
    return p.returncode

def colmap_pipeline(
    image_path: str | Path,
    output_path: str | Path | None = None,
    database_path: str | Path | None = None,
    matcher: str = "exhaustive",
    camera_model: str = "PINHOLE",
    verbose: bool = True
) -> int:
    """
    Run the complete COLMAP SfM pipeline: Extraction/Matching + Incremental Mapping.
    """
    import importlib.util
    if importlib.util.find_spec("pycolmap") is None:
        print("\n[ERROR] 'pycolmap' is not installed.")
        print("Please install mapping tools with: pip install vibephysics[mapping]")
        return 1

    image_path = Path(image_path).absolute()
    output_path = prepare_output_directory(image_path, output_path, engine="colmap", verbose=verbose)
    sparse_path = output_path / "sparse"
    
    db_path = Path(database_path).absolute() if database_path else sparse_path / "database.db"

    # 1. Extraction & Matching
    status = run_colmap_stage(image_path, db_path, camera_model, matcher, verbose)
    if status != 0: return status

    # 2. Incremental Mapping
    status = run_incremental_mapping_stage(image_path, db_path, sparse_path, verbose)
    
    if status == 0 and verbose: print(f"\n[SUCCESS] COLMAP pipeline finished. Results in {output_path}")
    return status
