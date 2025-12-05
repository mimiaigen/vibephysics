#!/bin/bash
# Usage: ./run.sh [script arguments]
# Example: ./run.sh --num-spheres 10 --wave-scale 1.5 --output my_sim.blend
# Run with --help to see all available options: ./run.sh --help

if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    /Applications/Blender.app/Contents/MacOS/Blender -b --python-use-system-env -P ./scripts/water_float.py -- --help
else
    /Applications/Blender.app/Contents/MacOS/Blender -b --python-use-system-env -P ./scripts/water_float.py -- "$@"
fi
