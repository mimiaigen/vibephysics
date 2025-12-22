import os
from pathlib import Path
from datetime import datetime

def prepare_output_directory(image_path: Path, output_path: Path | None = None, engine: str = "glomap", verbose: bool = True) -> Path:
    """
    Sets up the output directory structure for SfM.
    Creates 'sparse/' directory and symlinks 'images/' for GSplat compatibility.
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = image_path.parent / "mapping_output" / f"{engine}_{timestamp}"
    
    output_path = Path(output_path).absolute()
    if verbose:
        print(f"--- [vibephysics] Preparing {engine} reconstruction in: {output_path} ---")

    # Create sparse directory
    sparse_path = output_path / "sparse"
    sparse_path.mkdir(parents=True, exist_ok=True)
    
    # Symlink images
    img_dst = output_path / "images"
    if not img_dst.exists():
        try:
            os.symlink(image_path.absolute(), img_dst)
            if verbose: print(f"--- [vibephysics] Created images symlink ---")
        except Exception as e:
            if verbose: print(f"Warning: Could not create images symlink: {e}")
            
    return output_path
