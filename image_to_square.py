import argparse
import os
import sys
from PIL import Image, ImageOps

# Attempt to import pillow-heif for HEIC support
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_SUPPORT = True
except ImportError:
    HEIF_SUPPORT = False

def process_image(input_path, border_thickness, output_path=None):
    """
    Makes an image 1:1 by padding the shortest side to match the longest side 
    with a white background, then adds an additional white border.
    """
    if not os.path.exists(input_path):
        print(f"Error: File {input_path} not found.")
        return

    try:
        # Open image and ensure it's in a color mode that handles transparency/alpha correctly
        # We convert to RGBA first to handle PNG/HEIC transparency, then flatten to RGB on white.
        with Image.open(input_path) as img:
            img = img.convert("RGBA")
            w, h = img.size
            
            # 1. Determine the size of the square (longest edge)
            max_dim = max(w, h)
            
            # 2. Create the white square canvas
            # We use RGBA to paste the original (which might have transparency) 
            # onto a solid white background.
            square_canvas = Image.new("RGBA", (max_dim, max_dim), (255, 255, 255, 255))
            
            # Calculate position to center the image
            upper_left_x = (max_dim - w) // 2
            upper_left_y = (max_dim - h) // 2
            
            # Paste the original image onto the white square
            square_canvas.paste(img, (upper_left_x, upper_left_y), img)
            
            # 3. Convert back to RGB to drop alpha channel (pure white background now solid)
            final_square = square_canvas.convert("RGB")
            
            # 4. Add the additional thick white border
            # border_thickness is applied to all sides
            final_img = ImageOps.expand(final_square, border=border_thickness, fill="white")
            
            # Determine output path if not provided
            if not output_path:
                file_dir = os.path.dirname(input_path)
                file_name = os.path.basename(input_path)
                name, ext = os.path.splitext(file_name)
                # Save as JPG or PNG for compatibility; here we respect original extension if possible
                # But HEIC should be saved as JPG/PNG for general use.
                out_ext = ext if ext.lower() in ['.jpg', '.jpeg', '.png'] else '.jpg'
                output_path = os.path.join(file_dir, f"{name}_1x1{out_ext}")

            final_img.save(output_path, quality=95)
            print(f"Successfully processed:\n  Input:  {input_path}\n  Output: {output_path}\n  Size:   {final_img.size}")

    except Exception as e:
        print(f"Failed to process {input_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Make an image 1:1 with white padding and an extra white border.")
    parser.add_argument("input", help="Path to the input image (JPG, PNG, HEIC, etc.)")
    parser.add_argument("--border", type=int, default=100, help="Thickness of the additional white border (default: 100px)")
    parser.add_argument("--output", help="Optional output path")

    args = parser.parse_args()

    if not HEIF_SUPPORT:
        ext = os.path.splitext(args.input)[1].lower()
        if ext in ['.heic', '.heif']:
            print("Error: HEIC file detected but 'pillow-heif' is not installed.")
            print("Please run: pip install pillow-heif")
            sys.exit(1)

    process_image(args.input, args.border, args.output)

if __name__ == "__main__":
    main()
