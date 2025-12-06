#!/bin/bash
# Run annotation demos

BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"

if [ ! -f "$BLENDER" ]; then
    echo "Blender not found at $BLENDER"
    echo "Please update the BLENDER variable in this script."
    exit 1
fi

echo "======================================"
echo "  VibePhysics - Annotation Demos"
echo "======================================"
echo ""

# Ensure output directory exists
mkdir -p output

# 1. BBox Demo
echo "[1/4] Running BBox Demo..."
$BLENDER -b --python-use-system-env -P examples/demo_bbox.py

if [ $? -eq 0 ]; then
    echo "✅ BBox Demo Success"
else
    echo "❌ BBox Demo Failed"
fi
echo ""

# 2. Motion Trail Demo
echo "[2/4] Running Motion Trail Demo..."
$BLENDER -b --python-use-system-env -P examples/demo_motion_trail.py

if [ $? -eq 0 ]; then
    echo "✅ Motion Trail Demo Success"
else
    echo "❌ Motion Trail Demo Failed"
fi
echo ""

# 3. Point Tracking Demo
echo "[3/4] Running Point Tracking Demo..."
$BLENDER -b --python-use-system-env -P examples/demo_point_tracking.py

if [ $? -eq 0 ]; then
    echo "✅ Point Tracking Demo Success"
else
    echo "❌ Point Tracking Demo Failed"
fi
echo ""

# 4. Combined Demo
echo "[4/4] Running Combined Demo (All Annotations)..."
$BLENDER -b --python-use-system-env -P examples/demo_all_annotations.py

if [ $? -eq 0 ]; then
    echo "✅ Combined Demo Success"
else
    echo "❌ Combined Demo Failed"
fi
echo ""

echo "======================================"
echo "  Done! Output files in 'output/' folder:"
echo "  - demo_bbox.blend"
echo "  - demo_motion_trail.blend"
echo "  - demo_point_tracking.blend"
echo "  - demo_all_annotations.blend"
echo "======================================"
