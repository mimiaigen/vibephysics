#!/bin/bash
# Run all basic demos

mkdir -p output

python examples/basics/demo_bbox.py
python examples/basics/demo_motion_trail.py
python examples/basics/demo_point_tracking.py
python examples/basics/demo_all_annotations.py
python examples/basics/demo_frustum_culling.py

echo "Done! Files in output/"
