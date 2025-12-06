#!/bin/bash
# Run robot/duck simulations with full annotations
# Usage: ./run_robot.sh [--force] [--no-annotations]

BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"
FORCE=false
NO_ANNOTATIONS=""
OUTPUT_DIR="output"

# Parse arguments
for arg in "$@"; do
    case $arg in
        --force)
            FORCE=true
            shift
            ;;
        --no-annotations)
            NO_ANNOTATIONS="--no-annotations"
            shift
            ;;
    esac
done

if [ ! -f "$BLENDER" ]; then
    echo "Blender not found at $BLENDER"
    echo "Please update the BLENDER variable in this script."
    exit 1
fi

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

echo "======================================"
echo "  VibePhysics - Robot Simulations"
echo "  (with Full Annotations)"
echo "======================================"
echo "Output: ./$OUTPUT_DIR/"
if [ "$FORCE" = true ]; then
    echo "Force mode: Overwriting existing files"
fi
if [ -n "$NO_ANNOTATIONS" ]; then
    echo "Annotations: DISABLED"
else
    echo "Annotations: bbox + trails + point tracking"
fi
echo ""

# Helper function
run_sim() {
    local name=$1
    local output=$2
    shift 2
    local args=("$@")
    
    local full_path="$OUTPUT_DIR/$output"
    
    if [ -f "$full_path" ] && [ "$FORCE" = false ]; then
        echo "  ⚠️  $full_path exists, skipping (use --force to overwrite)"
        return 0
    fi
    
    if [ -f "$full_path" ] && [ "$FORCE" = true ]; then
        echo "  🔄 Overwriting $full_path..."
        rm "$full_path"
    fi
    
    $BLENDER -b --python-use-system-env -P "${args[@]}"
    
    if [ $? -eq 0 ]; then
        echo "✅ $name completed"
        return 0
    else
        echo "❌ $name failed"
        return 1
    fi
}

# ======================================================================
# 1. Robot Walking Water Puddle
# ======================================================================
echo "[1/4] Robot Walking Water Puddle..."
echo "  - Open Duck with IK walking"
echo "  - Uneven terrain with puddles"
echo "  - 25 falling debris balls"
echo "  - Full annotations (bbox, trails, points)"
run_sim "Robot Walk" "robot_walk.blend" \
    examples/robot_walking_water_puddle.py -- \
    --terrain-size 25.0 \
    --puddle-depth 0.6 \
    --walk-speed 1.0 \
    --start-frame 1 \
    --end-frame 350 \
    --points-per-object 50 \
    --trail-step 3 \
    $NO_ANNOTATIONS \
    --output $OUTPUT_DIR/robot_walk.blend
echo ""

# ======================================================================
# 2. Duck Waypoint Walk - Exploration Pattern
# ======================================================================
echo "[2/4] Duck Waypoint Walk (Exploration)..."
echo "  - Duck follows exploration waypoints"
echo "  - Camera follows duck"
echo "  - Full annotations"
run_sim "Duck Exploration" "duck_exploration.blend" \
    examples/duck_waypoint_walk.py -- \
    --waypoint-pattern exploration \
    --waypoint-scale 8.0 \
    --walk-speed 0.8 \
    --follow-duck \
    --show-waypoints \
    --start-frame 1 \
    --end-frame 400 \
    --points-per-object 30 \
    --trail-step 2 \
    $NO_ANNOTATIONS \
    --output $OUTPUT_DIR/duck_exploration.blend
echo ""

# ======================================================================
# 3. Duck Waypoint Walk - Figure Eight
# ======================================================================
echo "[3/4] Duck Waypoint Walk (Figure Eight)..."
echo "  - Duck follows figure-8 pattern"
echo "  - 500 frames for full loop"
echo "  - Full annotations"
run_sim "Duck Figure Eight" "duck_figure_eight.blend" \
    examples/duck_waypoint_walk.py -- \
    --waypoint-pattern figure_eight \
    --waypoint-scale 6.0 \
    --walk-speed 0.7 \
    --follow-duck \
    --start-frame 1 \
    --end-frame 500 \
    --points-per-object 30 \
    --trail-step 2 \
    $NO_ANNOTATIONS \
    --output $OUTPUT_DIR/duck_figure_eight.blend
echo ""

# ======================================================================
# 4. Duck Waypoint Walk - Spiral
# ======================================================================
echo "[4/4] Duck Waypoint Walk (Spiral)..."
echo "  - Duck follows outward spiral"
echo "  - 450 frames"
echo "  - Full annotations"
run_sim "Duck Spiral" "duck_spiral.blend" \
    examples/duck_waypoint_walk.py -- \
    --waypoint-pattern spiral \
    --waypoint-scale 10.0 \
    --walk-speed 0.9 \
    --follow-duck \
    --show-waypoints \
    --start-frame 1 \
    --end-frame 450 \
    --points-per-object 30 \
    --trail-step 2 \
    $NO_ANNOTATIONS \
    --output $OUTPUT_DIR/duck_spiral.blend
echo ""

# Summary
echo "======================================"
echo "  Robot Simulations Complete!"
echo "======================================"
echo ""
echo "Generated files in ./$OUTPUT_DIR/:"
echo "  1. robot_walk.blend        - Robot walking in water puddles"
echo "  2. duck_exploration.blend  - Duck exploration pattern"
echo "  3. duck_figure_eight.blend - Duck figure-8 pattern"
echo "  4. duck_spiral.blend       - Duck spiral pattern"
echo ""
echo "Each file includes:"
echo "  📦 Bounding boxes on robot parts & debris"
echo "  🌀 Motion trails for key objects"
echo "  🎯 Point cloud tracking visualization"
echo ""
echo "To view annotations in Blender:"
echo "  1. Open the .blend file"
echo "  2. Look for 'AnnotationViz' collection"
echo "  3. Run 'restore_point_tracking_viewport.py' from Text Editor"
echo "     for dual viewport setup"
echo ""
echo "To render: blender -b $OUTPUT_DIR/<filename>.blend -a"
echo ""
