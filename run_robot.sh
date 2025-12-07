#!/bin/bash
# Run robot/duck simulations

# Camera selection: center, following, or mounted (default: mounted)
CAMERA=${1:-mounted}

# Clone Open Duck if not present
if [ ! -d "../Open_Duck_Blender" ]; then
    echo "Cloning Open_Duck_Blender..."
    git clone https://github.com/pollen-robotics/Open_Duck_Blender.git ../Open_Duck_Blender
    cd ../Open_Duck_Blender && git lfs pull && cd -
fi

mkdir -p output

echo "Using camera: $CAMERA"

echo "Running Duck Waypoint Walk (Figure Eight)..."
python examples/robot/robot_waypoint_walk.py --waypoint-pattern figure_eight --active-camera $CAMERA --output output/robot_figure_eight_${CAMERA}.blend

echo "Running Duck Waypoint Walk (Exploration)..."
python examples/robot/robot_waypoint_walk.py --waypoint-pattern exploration --active-camera $CAMERA --output output/robot_exploration_${CAMERA}.blend

echo "Running Duck Waypoint Walk (Spiral)..."
python examples/robot/robot_waypoint_walk.py --waypoint-pattern spiral --active-camera $CAMERA --output output/robot_spiral_${CAMERA}.blend


echo "Done! Files in output/"
echo "  - robot_figure_eight_${CAMERA}.blend"
echo "  - robot_exploration_${CAMERA}.blend"
echo "  - robot_spiral_${CAMERA}.blend"
echo ""
echo "Usage: sh run_robot.sh [camera]"
echo "  camera: center, following, or mounted (default: mounted)"
