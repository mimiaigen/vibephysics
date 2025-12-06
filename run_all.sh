#!/bin/bash
# Run all physics simulations with 250 frames
# Usage: ./run_all.sh [--force]

BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"
FRAMES=250
START_FRAME=1
OUTPUT_DIR="output"
FORCE=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --force)
            FORCE=true
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
echo "  VibePhysics - Run All Simulations"
echo "======================================"
echo "Frames: $START_FRAME to $FRAMES"
echo "Output: ./$OUTPUT_DIR/"
if [ "$FORCE" = true ]; then
    echo "Force mode: Overwriting existing files"
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

# 1. Water Float - Classic floating spheres
echo "[1/7] Running Water Float Simulation..."
    echo "  - 25 spheres with mass variations"
    echo "  - Wave scale: 0.5 (moderate)"
run_sim "Water Float" "water_float_sim.blend" \
    examples/water_float.py -- \
      --num-spheres 25 \
      --wave-scale 0.5 \
      --collision-spawn \
      --start-frame $START_FRAME \
      --end-frame $FRAMES \
    --output $OUTPUT_DIR/water_float_sim.blend
echo ""

# 2. Water Rise - Calm water rising from z=0 to z=10
echo "[2/7] Running Water Rise Simulation..."
    echo "  - 25 objects on seabed"
    echo "  - Water rises from z=0 to z=10"
    echo "  - Very calm waves (0.1)"
run_sim "Water Rise" "water_rise_sim.blend" \
    examples/water_rise.py -- \
      --num-objects 25 \
      --rise-height 10.0 \
      --rise-duration 200 \
      --calm-wave-scale 0.1 \
      --start-frame $START_FRAME \
      --end-frame $FRAMES \
    --output $OUTPUT_DIR/water_rise_sim.blend
echo ""

# 3. Water Bucket - Periodic waves
echo "[3/7] Running Water Bucket Simulation..."
    echo "  - 25 floating objects"
    echo "  - Wave intensity: 1.5"
    echo "  - 4m bucket radius"
run_sim "Water Bucket" "water_bucket_sim.blend" \
    examples/water_bucket.py -- \
      --num-floats 25 \
      --wave-intensity 1.5 \
      --bucket-radius 4.0 \
      --start-frame $START_FRAME \
      --end-frame $FRAMES \
    --output $OUTPUT_DIR/water_bucket_sim.blend
echo ""

# 4. Storm - Violent weather with debris
echo "[4/7] Running Storm Simulation..."
    echo "  - 25 debris objects"
    echo "  - Storm intensity: 3.0"
    echo "  - Wind chaos: 50.0"
run_sim "Storm" "storm_sim.blend" \
    examples/storm.py -- \
      --num-debris 25 \
      --storm-intensity 3.0 \
      --wind-chaos 50.0 \
      --start-frame $START_FRAME \
      --end-frame $FRAMES \
    --output $OUTPUT_DIR/storm_sim.blend
echo ""

# 5. Water Puddles - Uneven terrain with shallow water
echo "[5/7] Running Water Puddles Simulation..."
    echo "  - Uneven ground with puddles"
    echo "  - 30 debris objects"
    echo "  - Murky water"
run_sim "Water Puddles" "water_puddles_sim.blend" \
    examples/water_puddles.py -- \
      --num-debris 30 \
      --terrain-size 20.0 \
      --puddle-depth 0.5 \
      --start-frame $START_FRAME \
      --end-frame $FRAMES \
    --output $OUTPUT_DIR/water_puddles_sim.blend
echo ""

# 6. Robot Walking - Duck robot walking through water puddles
echo "[6/7] Running Robot Walking Simulation..."
    echo "  - Duck robot with IK walking"
    echo "  - Uneven terrain with puddles"
    echo "  - Dynamic water ripples"
echo "  - Full annotations"
run_sim "Robot Walking" "robot_walk.blend" \
    examples/robot_walking_water_puddle.py -- \
      --terrain-size 25.0 \
      --puddle-depth 0.6 \
      --walk-speed 1.0 \
      --start-frame $START_FRAME \
      --end-frame $FRAMES \
    --output $OUTPUT_DIR/robot_walk.blend
echo ""

# 7. Duck Waypoint Walk - Duck following custom waypoints
echo "[7/7] Running Duck Waypoint Walk Simulation..."
    echo "  - Duck walks through custom waypoints"
    echo "  - Smooth curvy path (exploration pattern)"
    echo "  - 400 frames for longer walk"
echo "  - Full annotations"
run_sim "Duck Waypoint Walk" "duck_waypoint_walk.blend" \
    examples/duck_waypoint_walk.py -- \
      --waypoint-pattern exploration \
      --waypoint-scale 8.0 \
      --walk-speed 0.8 \
      --follow-duck \
      --show-waypoints \
      --start-frame $START_FRAME \
      --end-frame 400 \
    --output $OUTPUT_DIR/duck_waypoint_walk.blend
echo ""

# Summary
echo "======================================"
echo "  All Simulations Completed!"
echo "======================================"
echo ""
echo "Generated files in ./$OUTPUT_DIR/:"
echo "  1. water_float_sim.blend      (Classic floating)"
echo "  2. water_rise_sim.blend       (Rising water)"
echo "  3. water_bucket_sim.blend     (Water bucket)"
echo "  4. storm_sim.blend            (Storm)"
echo "  5. water_puddles_sim.blend    (Water Puddles)"
echo "  6. robot_walk.blend           (Robot Walking)"
echo "  7. duck_waypoint_walk.blend   (Duck Waypoint Walk)"
echo ""
echo "To view a simulation:"
echo "  open $OUTPUT_DIR/water_float_sim.blend"
echo ""
echo "To render frames:"
echo "  blender -b $OUTPUT_DIR/water_float_sim.blend -a"
echo ""
