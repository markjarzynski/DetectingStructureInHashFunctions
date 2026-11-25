#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Read hashes from hashes.txt file (one per line)
readarray -t hashes < "$SCRIPT_DIR/../hashes.txt"

width=512
height=512

dir=images/hashes

mkdir -p $dir

for hash in ${hashes[@]} ;
do
    ./rng2img -w $width -h $height $hash
    convert $hash.ppm $hash.png
    rm $hash.ppm
    mv $hash.png $dir
done

./rng2img -w $width -h $height -o devrandom.ppm -f /dev/random
convert devrandom.ppm devrandom.png
rm devrandom.ppm
mv devrandom.png $dir
