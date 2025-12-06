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
echo "[1/7] Running Water Float Simulation..."
if [ -f "water_float_sim.blend" ]; then
    echo "  ⚠️  File exists, skipping..."
else
    echo "  - 25 spheres with mass variations"
    echo "  - Wave scale: 0.5 (moderate)"
    $BLENDER -b --python-use-system-env -P examples/water_float.py -- \
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
echo "[2/7] Running Water Rise Simulation..."
if [ -f "water_rise_sim.blend" ]; then
    echo "  ⚠️  File exists, skipping..."
else
    echo "  - 25 objects on seabed"
    echo "  - Water rises from z=0 to z=10"
    echo "  - Very calm waves (0.1)"
    $BLENDER -b --python-use-system-env -P examples/water_rise.py -- \
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
echo "[3/7] Running Water Bucket Simulation..."
if [ -f "water_bucket_sim.blend" ]; then
    echo "  ⚠️  File exists, skipping..."
else
    echo "  - 25 floating objects"
    echo "  - Wave intensity: 1.5"
    echo "  - 4m bucket radius"
    $BLENDER -b --python-use-system-env -P examples/water_bucket.py -- \
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
echo "[4/7] Running Storm Simulation..."
if [ -f "storm_sim.blend" ]; then
    echo "  ⚠️  File exists, skipping..."
else
    echo "  - 25 debris objects"
    echo "  - Storm intensity: 3.0"
    echo "  - Wind chaos: 50.0"
    $BLENDER -b --python-use-system-env -P examples/storm.py -- \
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
echo "[5/7] Running Water Puddles Simulation..."
if [ -f "water_puddles_sim.blend" ]; then
    echo "  ⚠️  File exists, skipping..."
else
    echo "  - Uneven ground with puddles"
    echo "  - 30 debris objects"
    echo "  - Murky water"
    $BLENDER -b --python-use-system-env -P examples/water_puddles.py -- \
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

# 6. Robot Walking - Duck robot walking through water puddles
echo "[6/7] Running Robot Walking Simulation..."
if [ -f "robot_walk.blend" ]; then
    echo "  ⚠️  File exists, skipping..."
else
    echo "  - Duck robot with IK walking"
    echo "  - Uneven terrain with puddles"
    echo "  - Dynamic water ripples"
    $BLENDER -b --python-use-system-env -P examples/robot_walking_water_puddle.py -- \
      --terrain-size 25.0 \
      --puddle-depth 0.6 \
      --walk-speed 1.0 \
      --start-frame $START_FRAME \
      --end-frame $FRAMES \
      --output robot_walk.blend

    if [ $? -eq 0 ]; then
        echo "✅ Robot Walking completed successfully"
    else
        echo "❌ Robot Walking failed"
        exit 1
    fi
fi
echo ""

# 7. Duck Waypoint Walk - Duck following custom waypoints
echo "[7/7] Running Duck Waypoint Walk Simulation..."
if [ -f "duck_waypoint_walk.blend" ]; then
    echo "  ⚠️  File exists, skipping..."
else
    echo "  - Duck walks through custom waypoints"
    echo "  - Smooth curvy path (exploration pattern)"
    echo "  - 400 frames for longer walk"
    $BLENDER -b --python-use-system-env -P examples/duck_waypoint_walk.py -- \
      --waypoint-pattern exploration \
      --waypoint-scale 8.0 \
      --walk-speed 0.8 \
      --follow-duck \
      --show-waypoints \
      --start-frame $START_FRAME \
      --end-frame 400 \
      --output duck_waypoint_walk.blend

    if [ $? -eq 0 ]; then
        echo "✅ Duck Waypoint Walk completed successfully"
    else
        echo "❌ Duck Waypoint Walk failed"
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
echo "  1. water_float_sim.blend      (Classic floating)"
echo "  2. water_rise_sim.blend       (Rising water)"
echo "  3. water_bucket_sim.blend     (Water bucket)"
echo "  4. storm_sim.blend            (Storm)"
echo "  5. water_puddles_sim.blend    (Water Puddles)"
echo "  6. robot_walk.blend           (Robot Walking)"
echo "  7. duck_waypoint_walk.blend   (Duck Waypoint Walk)"
echo ""
echo "To view a simulation:"
echo "  open water_float_sim.blend"
echo ""
echo "To render frames:"
echo "  blender -b water_float_sim.blend -a"
echo ""
