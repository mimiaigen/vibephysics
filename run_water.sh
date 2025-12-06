#!/bin/bash
# Run water-related simulations
# Usage: ./run_water.sh [--force]

BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"
FRAMES=250
START_FRAME=1
FORCE=false
OUTPUT_DIR="output"

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
echo "  VibePhysics - Water Simulations"
echo "======================================"
echo "Frames: $START_FRAME to $FRAMES"
echo "Output: ./$OUTPUT_DIR/"
if [ "$FORCE" = true ]; then
    echo "Force mode: Overwriting existing files"
fi
echo ""

# Helper function to run simulation
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
echo "[1/5] Water Float Simulation..."
echo "  - 25 spheres with mass variations"
echo "  - Moderate waves (0.5)"
run_sim "Water Float" "water_float_sim.blend" \
    examples/water_float.py -- \
    --num-spheres 25 \
    --wave-scale 0.5 \
    --collision-spawn \
    --start-frame $START_FRAME \
    --end-frame $FRAMES \
    --points-per-object 30 \
    --output $OUTPUT_DIR/water_float_sim.blend
echo ""

# 2. Water Rise - Calm water rising
echo "[2/5] Water Rise Simulation..."
echo "  - 25 objects on seabed"
echo "  - Water rises from z=0 to z=10"
run_sim "Water Rise" "water_rise_sim.blend" \
    examples/water_rise.py -- \
    --num-objects 25 \
    --rise-height 10.0 \
    --rise-duration 200 \
    --calm-wave-scale 0.1 \
    --start-frame $START_FRAME \
    --end-frame $FRAMES \
    --points-per-object 30 \
    --output $OUTPUT_DIR/water_rise_sim.blend
echo ""

# 3. Water Bucket - Periodic waves
echo "[3/5] Water Bucket Simulation..."
echo "  - 25 floating objects"
echo "  - Wave intensity: 1.5"
run_sim "Water Bucket" "water_bucket_sim.blend" \
    examples/water_bucket.py -- \
    --num-floats 25 \
    --wave-intensity 1.5 \
    --bucket-radius 4.0 \
    --start-frame $START_FRAME \
    --end-frame $FRAMES \
    --points-per-object 30 \
    --output $OUTPUT_DIR/water_bucket_sim.blend
echo ""

# 4. Storm - Violent weather with debris
echo "[4/5] Storm Simulation..."
echo "  - 25 debris objects"
echo "  - Storm intensity: 3.0"
run_sim "Storm" "storm_sim.blend" \
    examples/storm.py -- \
    --num-debris 25 \
    --storm-intensity 3.0 \
    --wind-chaos 50.0 \
    --start-frame $START_FRAME \
    --end-frame $FRAMES \
    --points-per-object 30 \
    --output $OUTPUT_DIR/storm_sim.blend
echo ""

# 5. Water Puddles - Uneven terrain
echo "[5/5] Water Puddles Simulation..."
echo "  - Uneven ground with puddles"
echo "  - 30 debris objects"
run_sim "Water Puddles" "water_puddles_sim.blend" \
    examples/water_puddles.py -- \
    --num-debris 30 \
    --terrain-size 20.0 \
    --puddle-depth 0.5 \
    --start-frame $START_FRAME \
    --end-frame $FRAMES \
    --points-per-object 30 \
    --output $OUTPUT_DIR/water_puddles_sim.blend
echo ""

# Summary
echo "======================================"
echo "  Water Simulations Complete!"
echo "======================================"
echo ""
echo "Generated files in ./$OUTPUT_DIR/:"
echo "  1. water_float_sim.blend    (Classic floating)"
echo "  2. water_rise_sim.blend     (Rising water)"
echo "  3. water_bucket_sim.blend   (Water bucket)"
echo "  4. storm_sim.blend          (Storm)"
echo "  5. water_puddles_sim.blend  (Puddles)"
echo ""
echo "To view: open $OUTPUT_DIR/<filename>.blend"
echo "To render: blender -b $OUTPUT_DIR/<filename>.blend -a"
echo ""
