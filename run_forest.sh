#!/bin/bash

# Duck Forest Walk - Robot walking through dense forest on uneven terrain
# Output: ./output/duck_forest_walk.blend
# 
# Usage: ./run_forest.sh [options]
# 
# Examples:
#   ./run_forest.sh                                         # Default: frustum_only mode
#   ./run_forest.sh --frustum-mode all                      # Show all points (no culling)
#   ./run_forest.sh --frustum-mode highlight                # All visible, in-frustum red
#   ./run_forest.sh --frustum-mode frustum_only             # Only in-frustum visible (default)
#   ./run_forest.sh --num-trees 100                         # More trees
#   ./run_forest.sh --no-physics                            # Fastest playback
#
# Point Tracking Options:
#   --points-per-tree 1000      → Points per tree (default: 1000)
#   --frustum-mode all          → Show ALL points (basic, no culling)
#   --frustum-mode highlight    → Show all, in-frustum points turn RED
#   --frustum-mode frustum_only → Only show points INSIDE frustum (default)
#   --frustum-distance 20.0     → Frustum far distance in meters (default: 20m)
#
# Size Reference (all in meters):
#   --terrain-size 150.0   → 150m x 150m terrain (default)
#   --robot-height 0.5     → 0.5m tall robot (default)
#   --tree-height-min 5.0  → minimum tree height 5m (default)
#   --tree-height-max 8.0  → maximum tree height 8m (default)
#   --min-tree-distance 0.5 → 0.5m minimum gap between trees (default)
#   --path-width 1.5       → 1.5m wide path (default)
#   --tree-collision       → Enable rigid body on trees (slower, off by default)
#   --no-physics           → Disable ALL physics (fastest playback)
#
# Camera Options:
#   --active-camera mounted   → POV camera (default)
#   --active-camera following → Third-person tracking
#   --active-camera center    → Overview shots

python examples/robot/robot_forest_walk.py "$@"
