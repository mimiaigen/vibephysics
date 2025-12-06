#!/bin/bash
# Run robot/duck simulations

# Clone Open Duck if not present
if [ ! -d "../Open_Duck_Blender" ]; then
    echo "Cloning Open_Duck_Blender..."
    git clone https://github.com/pollen-robotics/Open_Duck_Blender.git ../Open_Duck_Blender
    cd ../Open_Duck_Blender && git lfs pull && cd -
fi

mkdir -p output

echo "Running Robot Walking Water Puddle..."
python examples/robot/duck_walking_water_puddle.py --output output/robot_walk.blend

echo "Running Duck Waypoint Walk (Exploration)..."
python examples/robot/duck_waypoint_walk.py --waypoint-pattern exploration --output output/duck_exploration.blend

echo "Running Duck Waypoint Walk (Figure Eight)..."
python examples/robot/duck_waypoint_walk.py --waypoint-pattern figure_eight --output output/duck_figure_eight.blend

echo "Running Duck Waypoint Walk (Spiral)..."
python examples/robot/duck_waypoint_walk.py --waypoint-pattern spiral --output output/duck_spiral.blend

echo "Done! Files in output/"
