#!/usr/bin/env python3
"""
Split a GIF into two parts

Usage:
    python split_gif.py input.gif
    python split_gif.py input.gif --output-prefix my_split
"""

import argparse
from PIL import Image
import os


def split_gif(input_path, output_prefix=None):
    """
    Split a GIF file into two parts (first half and second half of frames).
    
    Args:
        input_path: Path to input GIF
        output_prefix: Prefix for output files (default: input filename without extension)
    """
    # Default output prefix
    if output_prefix is None:
        output_prefix = os.path.splitext(input_path)[0]
    
    print(f"Loading {input_path}...")
    
    # Open the GIF
    gif = Image.open(input_path)
    
    # Get total number of frames
    n_frames = 0
    try:
        while True:
            gif.seek(n_frames)
            n_frames += 1
    except EOFError:
        pass
    
    print(f"Total frames: {n_frames}")
    
    if n_frames < 2:
        print("❌ Error: GIF must have at least 2 frames to split")
        return
    
    # Calculate split point
    split_point = n_frames // 2
    print(f"Splitting at frame {split_point}")
    print(f"  Part 1: frames 0-{split_point-1} ({split_point} frames)")
    print(f"  Part 2: frames {split_point}-{n_frames-1} ({n_frames - split_point} frames)")
    
    # Get GIF properties
    gif.seek(0)
    duration = gif.info.get('duration', 100)  # Default 100ms if not specified
    loop = gif.info.get('loop', 0)  # 0 = infinite loop
    
    # Extract first half
    output_path_1 = f"{output_prefix}_part1.gif"
    print(f"\nCreating {output_path_1}...")
    frames_1 = []
    for i in range(split_point):
        gif.seek(i)
        frame = gif.copy()
        frames_1.append(frame)
    
    frames_1[0].save(
        output_path_1,
        save_all=True,
        append_images=frames_1[1:],
        duration=duration,
        loop=loop,
        optimize=False
    )
    print(f"✅ Saved {output_path_1}")
    
    # Extract second half
    output_path_2 = f"{output_prefix}_part2.gif"
    print(f"\nCreating {output_path_2}...")
    frames_2 = []
    for i in range(split_point, n_frames):
        gif.seek(i)
        frame = gif.copy()
        frames_2.append(frame)
    
    frames_2[0].save(
        output_path_2,
        save_all=True,
        append_images=frames_2[1:],
        duration=duration,
        loop=loop,
        optimize=False
    )
    print(f"✅ Saved {output_path_2}")
    
    print(f"\n✨ Done! Split {input_path} into:")
    print(f"  - {output_path_1}")
    print(f"  - {output_path_2}")


def main():
    parser = argparse.ArgumentParser(description='Split a GIF into two parts')
    parser.add_argument('input', help='Input GIF file')
    parser.add_argument('--output-prefix', default=None, 
                        help='Prefix for output files (default: input filename)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"❌ Error: File not found: {args.input}")
        return
    
    split_gif(args.input, args.output_prefix)


if __name__ == '__main__':
    main()
