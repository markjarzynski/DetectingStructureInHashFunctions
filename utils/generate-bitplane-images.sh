#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Read hashes from hashes.txt file (one per line)
readarray -t hashes < "$SCRIPT_DIR/../hashes.txt"

width=256
height=128

dir=images/bitplane

mkdir -p $dir

for hash in ${hashes[@]} ;
do
    ./rng2img -b -w $width -h $height $hash
    convert $hash.ppm $hash.bitplane.png
    rm $hash.ppm
    mv $hash.bitplane.png $dir
done

./rng2img -b -w $width -h $height -o devrandom.ppm -f /dev/random
convert devrandom.ppm devrandom.bitplane.png
rm devrandom.ppm
mv devrandom.bitplane.png $dir
