#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

mkdir -p "$PARENT_DIR/images/noise"

# Call export_timing_and_best_bitplane.py to generate bitplane data and pipe to rng2noise
python3 "$SCRIPT_DIR/export_timing_and_best_bitplane.py" "$PARENT_DIR/results/timings.csv" "$PARENT_DIR/results/128x128x1x1/5x5x1x1" --best-bitplanes=2 | tail -n +2 | \
awk -F, '{print $1, $4, $6}' | \
while read -r hash best1_index best2_index;
do 
    "$PARENT_DIR/rng2noise" -s 32 -w 1024 -h 1024 -a $best1_index -b $best2_index $hash 
    convert $hash.ppm $hash.png
    mv $hash.png "$PARENT_DIR/images/noise"
done
