#!/bin/bash
# Run annotation demos

mkdir -p output

echo "Running BBox Demo..."
python examples/basics/demo_bbox.py

echo "Running Motion Trail Demo..."
python examples/basics/demo_motion_trail.py

echo "Running Point Tracking Demo..."
python examples/basics/demo_point_tracking.py

echo "Running Combined Demo..."
python examples/basics/demo_all_annotations.py

echo "Done! Files in output/"
