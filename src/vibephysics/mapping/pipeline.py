import sys
from .colmap import colmap_pipeline
from .glomap import glomap_pipeline

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run SfM pipeline (COLMAP or GLOMAP).")
    parser.add_argument("--image_path", required=True, help="Path to images.")
    parser.add_argument("--output_path", default=None, help="Output directory.")
    parser.add_argument("--engine", choices=["glomap", "colmap"], default="glomap", help="SfM engine to use.")
    parser.add_argument("--matcher", choices=["exhaustive", "sequential"], default="exhaustive")
    parser.add_argument("--camera_model", default="SIMPLE_RADIAL")
    parser.add_argument("--quiet", action="store_false", dest="verbose")
    
    args = parser.parse_args()
    
    if args.engine == "glomap":
        sys.exit(glomap_pipeline(args.image_path, args.output_path, None, args.matcher, args.camera_model, args.verbose))
    else:
        sys.exit(colmap_pipeline(args.image_path, args.output_path, None, args.matcher, args.camera_model, args.verbose))

if __name__ == "__main__":
    main()
