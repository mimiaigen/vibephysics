import os
import subprocess
from pathlib import Path
from datetime import datetime

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".JPG", ".PNG"}
VIDEO_EXTENSIONS = {".mov", ".mp4", ".avi", ".mkv", ".webm", ".m4v", ".MOV", ".MP4", ".MKV", ".WEBM", ".M4V"}


def is_video_file(path: Path) -> bool:
    return path.is_file() and path.suffix in VIDEO_EXTENSIONS


def extract_video_frames(
    video_path: Path,
    output_dir: Path | None = None,
    fps: float | None = 2.0,
    quality: int = 2,
    verbose: bool = True,
) -> Path:
    video_path = Path(video_path).absolute()
    if not video_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {video_path}")

    if output_dir is None:
        output_dir = video_path.parent / "output" / video_path.stem
    output_dir = Path(output_dir).absolute()
    output_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(output_dir.glob("frame_*.jpg"))
    if existing:
        if verbose:
            print(f"--- [vibephysics] Using {len(existing)} existing frames in {output_dir} ---")
        return output_dir

    output_pattern = output_dir / "frame_%04d.jpg"
    cmd = ["ffmpeg", "-i", str(video_path), "-q:v", str(quality)]
    if fps is not None:
        cmd.extend(["-vf", f"fps={fps}"])
    cmd.extend([str(output_pattern), "-y"])

    if verbose:
        print(f"--- [vibephysics] Extracting frames from {video_path.name} ---")
        print(f"Running: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True, capture_output=not verbose)
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg not found. Install ffmpeg to use video input.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ffmpeg failed to extract frames from {video_path}") from exc

    extracted = sorted(output_dir.glob("frame_*.jpg"))
    if not extracted:
        raise RuntimeError(f"No frames extracted from {video_path}")
    if verbose:
        print(f"--- [vibephysics] Extracted {len(extracted)} frames to {output_dir} ---")
    return output_dir


def resolve_mapping_input(
    input_path: str | Path,
    video_fps: float | None = 2.0,
    video_quality: int = 2,
    frames_dir: Path | None = None,
    verbose: bool = True,
) -> Path:
    """
    Resolve mapping input to an image folder.

    Accepts a directory of images, a single image file, or a video file (.mov, .mp4, ...).
    Videos are converted to a frame folder via ffmpeg.
    """
    input_path = Path(input_path).absolute()
    if not input_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    if input_path.is_dir():
        return input_path

    if is_video_file(input_path):
        return extract_video_frames(
            input_path,
            output_dir=frames_dir,
            fps=video_fps,
            quality=video_quality,
            verbose=verbose,
        )

    if input_path.suffix.lower() in {ext.lower() for ext in IMAGE_EXTENSIONS}:
        return input_path

    raise ValueError(
        f"Unsupported input: {input_path}. "
        "Provide a video (.mov, .mp4, ...), an image folder, or a single image file."
    )


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
