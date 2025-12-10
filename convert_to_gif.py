#!/usr/bin/env python3
"""
Convert video to looping GIF

Usage:
    python convert_to_gif.py input.mov output.gif
    python convert_to_gif.py input.mov output.gif --fps 15 --width 480
"""

import subprocess
import sys
import argparse

def convert_to_gif(input_path, output_path, fps=10, width=None):
    """
    Convert video to GIF using ffmpeg.
    
    Args:
        input_path: Path to input video (.mov, .mp4, etc.)
        output_path: Path to output GIF
        fps: Frames per second (lower = smaller file)
        width: Width in pixels (None = keep original size)
    """
    # Build filter string
    if width:
        vf_palette = f'fps={fps},scale={width}:-1:flags=lanczos,palettegen'
        vf_gif = f'fps={fps},scale={width}:-1:flags=lanczos[x];[x][1:v]paletteuse'
    else:
        vf_palette = f'fps={fps},palettegen'
        vf_gif = f'fps={fps}[x];[x][1:v]paletteuse'
    
    # Generate palette for better quality
    palette_cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-vf', vf_palette,
        '-t', '30',  # Limit to 30 seconds
        '/tmp/palette.png'
    ]
    
    # Convert to GIF using palette
    gif_cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-i', '/tmp/palette.png',
        '-lavfi', vf_gif,
        '-loop', '0',  # 0 = infinite loop
        '-t', '30',  # Limit to 30 seconds
        output_path
    ]
    
    print(f"Converting {input_path} to {output_path}...")
    print(f"  FPS: {fps}, Width: {width or 'original'}px, Loop: infinite")
    
    # Generate palette
    print("  Generating palette...")
    subprocess.run(palette_cmd, check=True, capture_output=True)
    
    # Create GIF
    print("  Creating GIF...")
    subprocess.run(gif_cmd, check=True, capture_output=True)
    
    print(f"✅ Done! Saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Convert video to looping GIF')
    parser.add_argument('input', help='Input video file (e.g., video.mov)')
    parser.add_argument('output', nargs='?', default=None, help='Output GIF file')
    parser.add_argument('--fps', type=int, default=10, help='Frames per second (default: 15)')
    parser.add_argument('--width', type=int, default=None, help='Width in pixels (default: original size)')
    
    args = parser.parse_args()
    
    # Default output name
    if args.output is None:
        args.output = args.input.rsplit('.', 1)[0] + '.gif'
    
    convert_to_gif(args.input, args.output, args.fps, args.width)


if __name__ == '__main__':
    main()

