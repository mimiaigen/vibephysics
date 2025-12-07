#!/bin/bash
# Run robot/duck simulations

# Clone Open Duck if not present
if [ ! -d "../Open_Duck_Blender" ]; then
    echo "Cloning Open_Duck_Blender..."
    git clone https://github.com/pollen-robotics/Open_Duck_Blender.git ../Open_Duck_Blender
    cd ../Open_Duck_Blender && git lfs pull && cd -
fi

mkdir -p output

echo "Running Duck Waypoint Walk (Figure Eight)..."
python examples/robot/robot_waypoint_walk.py --waypoint-pattern figure_eight --output output/robot_figure_eight.blend

echo "Running Duck Waypoint Walk (Exploration)..."
python examples/robot/robot_waypoint_walk.py --waypoint-pattern exploration --output output/robot_exploration.blend

echo "Running Duck Waypoint Walk (Spiral)..."
python examples/robot/robot_waypoint_walk.py --waypoint-pattern spiral --output output/robot_spiral.blend


echo "Done! Files in output/"
