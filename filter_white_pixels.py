import cv2
import argparse
import os
import numpy as np

def process_image(input_path, threshold):
    print(f"Loading {input_path}...")
    img = cv2.imread(input_path)
    
    if img is None:
        print(f"Error: Could not load image at {input_path}")
        return

    # OpenCV loads images in BGR format
    # Threshold is applied to all three channels
    # Find pixels where B, G, and R are all greater than threshold
    # Note: threshold should be between 0 and 255
    
    # Create mask for white pixels
    # b, g, r = cv2.split(img)
    white_mask = np.all(img > threshold, axis=-1)
    
    # Count white pixels before change
    num_white = np.sum(white_mask)
    total_pixels = img.shape[0] * img.shape[1]
    
    print(f"Threshold: {threshold}/255")
    print(f"Total pixels: {total_pixels}")
    print(f"White pixels found: {num_white} ({100 * num_white / total_pixels:.2f}%)")
    
    # Change white pixels to black (0, 0, 0)
    img_filtered = img.copy()
    img_filtered[white_mask] = [0, 0, 0]
    
    # Determine output path
    base, ext = os.path.splitext(input_path)
    output_path = f"{base}_blacked{ext}"
    
    print(f"Saving to {output_path}...")
    cv2.imwrite(output_path, img_filtered)
    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Turn white pixels in an image into black.")
    parser.add_argument("inputs", nargs="+", help="Path(s) to the input image file(s)")
    parser.add_argument("-t", "--threshold", type=int, default=240, 
                        help="Threshold for whiteness (0 to 255). Pixels with B, G, R > threshold are turned black. Default: 240")
    
    args = parser.parse_args()
    
    for input_path in args.inputs:
        if not os.path.exists(input_path):
            print(f"Error: File {input_path} does not exist.")
        else:
            process_image(input_path, args.threshold)
