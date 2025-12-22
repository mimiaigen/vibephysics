import argparse
import subprocess
import sys
from pathlib import Path

def vid2frames(video_path, output_dir=None, quality=2, fps=None):
    """
    Extract frames from a video using ffmpeg.
    
    Args:
        video_path: Path to the input video file.
        output_dir: Directory to save frames. Defaults to ./output/<video_name>
        quality: JPEG quality (1-31, lower is better). Default 2.
        fps: Target frames per second. If None, extracts all frames.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        print(f"Error: Video file {video_path} does not exist.")
        return

    # Determine output directory
    if output_dir is None:
        # Create output/video_name/ in the same directory as the video
        output_dir = video_path.parent / "output" / video_path.stem
    else:
        output_dir = Path(output_dir)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")

    # Build ffmpeg command
    # -i: input file
    # -q:v: video quality (2 is high quality)
    # -vf: video filter for fps
    # output pattern: frame_%04d.jpg
    output_pattern = output_dir / "frame_%04d.jpg"
    
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-q:v", str(quality),
    ]

    if fps:
        cmd.extend(["-vf", f"fps={fps}"])

    cmd.extend([
        str(output_pattern),
        "-y" # Overwrite output files if they exist
    ])

    print(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run ffmpeg and show output
        subprocess.run(cmd, check=True)
        print(f"\nFinished! Frames saved in: {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error during video processing: {e}", file=sys.stderr)
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please install ffmpeg.", file=sys.stderr)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert video frames to JPG images using ffmpeg.")
    parser.add_argument("video_path", type=str, help="Path to the input video file (mp4, mov, etc.)")
    parser.add_argument("--output", "-o", type=str, help="Output directory (default: ./output/<video_name>)")
    parser.add_argument("--quality", "-q", type=int, default=2, help="JPEG quality (1-31, default: 2)")
    parser.add_argument("--fps", "-f", type=float, default=5, help="Target frames per second (e.g., 1, 10, 24)")
    
    args = parser.parse_args()
    
    vid2frames(args.video_path, args.output, args.quality, args.fps)
