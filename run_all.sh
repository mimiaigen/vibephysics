#!/bin/bash
# Run all physics simulations with 250 frames
# Usage: ./run_all.sh

BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"
FRAMES=250
START_FRAME=1

echo "======================================"
echo "  VibePhysics - Run All Simulations"
echo "======================================"
echo "Frames: $START_FRAME to $FRAMES"
echo ""

# 1. Water Float - Classic floating spheres
echo "[1/4] Running Water Float Simulation..."
if [ -f "water_float_sim.blend" ]; then
    echo "  ⚠️  File exists, skipping..."
else
    echo "  - 25 spheres with mass variations"
    echo "  - Wave scale: 0.5 (moderate)"
    $BLENDER -b --python-use-system-env -P scripts/water_float.py -- \
      --num-spheres 25 \
      --wave-scale 0.5 \
      --collision-spawn \
      --start-frame $START_FRAME \
      --end-frame $FRAMES \
      --output water_float_sim.blend

    if [ $? -eq 0 ]; then
        echo "✅ Water Float completed successfully"
    else
        echo "❌ Water Float failed"
        exit 1
    fi
fi
echo ""

# 2. Water Rise - Calm water rising from z=0 to z=10
echo "[2/4] Running Water Rise Simulation..."
if [ -f "water_rise_sim.blend" ]; then
    echo "  ⚠️  File exists, skipping..."
else
    echo "  - 25 objects on seabed"
    echo "  - Water rises from z=0 to z=10"
    echo "  - Very calm waves (0.1)"
    $BLENDER -b --python-use-system-env -P scripts/water_rise.py -- \
      --num-objects 25 \
      --rise-height 10.0 \
      --rise-duration 200 \
      --calm-wave-scale 0.1 \
      --start-frame $START_FRAME \
      --end-frame $FRAMES \
      --output water_rise_sim.blend

    if [ $? -eq 0 ]; then
        echo "✅ Water Rise completed successfully"
    else
        echo "❌ Water Rise failed"
        exit 1
    fi
fi
echo ""

# 3. Water Bucket - Periodic waves
echo "[3/4] Running Water Bucket Simulation..."
if [ -f "water_bucket_sim.blend" ]; then
    echo "  ⚠️  File exists, skipping..."
else
    echo "  - 25 floating objects"
    echo "  - Wave intensity: 1.5"
    echo "  - 4m bucket radius"
    $BLENDER -b --python-use-system-env -P scripts/water_bucket.py -- \
      --num-floats 25 \
      --wave-intensity 1.5 \
      --bucket-radius 4.0 \
      --start-frame $START_FRAME \
      --end-frame $FRAMES \
      --output water_bucket_sim.blend

    if [ $? -eq 0 ]; then
        echo "✅ Water Bucket completed successfully"
    else
        echo "❌ Water Bucket failed"
        exit 1
    fi
fi
echo ""

# 4. Storm - Violent weather with debris
echo "[4/4] Running Storm Simulation..."
if [ -f "storm_sim.blend" ]; then
    echo "  ⚠️  File exists, skipping..."
else
    echo "  - 25 debris objects"
    echo "  - Storm intensity: 3.0"
    echo "  - Wind chaos: 50.0"
    $BLENDER -b --python-use-system-env -P scripts/storm.py -- \
      --num-debris 25 \
      --storm-intensity 3.0 \
      --wind-chaos 50.0 \
      --start-frame $START_FRAME \
      --end-frame $FRAMES \
      --output storm_sim.blend

    if [ $? -eq 0 ]; then
        echo "✅ Storm completed successfully"
    else
        echo "❌ Storm failed"
        exit 1
    fi
fi
echo ""

# 5. Water Puddles - Uneven terrain with shallow water
echo "[5/5] Running Water Puddles Simulation..."
if [ -f "water_puddles_sim.blend" ]; then
    echo "  ⚠️  File exists, skipping..."
else
    echo "  - Uneven ground with puddles"
    echo "  - 30 debris objects"
    echo "  - Murky water"
    $BLENDER -b --python-use-system-env -P scripts/water_puddles.py -- \
      --num-debris 30 \
      --terrain-size 20.0 \
      --puddle-depth 0.5 \
      --start-frame $START_FRAME \
      --end-frame $FRAMES \
      --output water_puddles_sim.blend

    if [ $? -eq 0 ]; then
        echo "✅ Water Puddles completed successfully"
    else
        echo "❌ Water Puddles failed"
        exit 1
    fi
fi
echo ""

# Summary
echo "======================================"
echo "  All Simulations Completed!"
echo "======================================"
echo ""
echo "Generated files:"
echo "  1. water_float_sim.blend  (Classic floating)"
echo "  2. water_rise_sim.blend   (Rising water)"
echo "  3. water_bucket_sim.blend (Water bucket)"
echo "  4. storm_sim.blend        (Storm)"
echo "  5. water_puddles_sim.blend (Water Puddles)"
echo ""
echo "To view a simulation:"
echo "  open water_float_sim.blend"
echo ""
echo "To render frames:"
echo "  blender -b water_float_sim.blend -a"
echo ""
