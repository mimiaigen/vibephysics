#!/bin/bash
# Run water simulations

mkdir -p output

echo "Running Water Float..."
python examples/water/water_float.py --output output/water_float.blend

echo "Running Water Rise..."
python examples/water/water_rise.py --output output/water_rise.blend

echo "Running Water Bucket..."
python examples/water/water_bucket.py --output output/water_bucket.blend

echo "Running Storm..."
python examples/water/storm.py --output output/storm.blend

echo "Running Water Puddles..."
python examples/water/water_puddles.py --output output/water_puddles.blend

echo "Done! Files in output/"
