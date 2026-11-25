Detecting Structure in Hash Functions
=====================================

Finding repeating patterns, artifacts, and structure in Pseudo Random Hash Functions (PRHFs).

Building
--------

If compiling `fft-test`, first install the required dependency:

```bash
sudo apt-get install libfftw3-dev
```

Compile all binaries using:

```bash
make
```

This will compile the following tools:

- `structure-in-hash-functions` - Main pattern analysis tool for examining hash functions and PRNGs
- `structure-in-hash-functions-reference` - Reference implementation for validation
- `rng2img` - Converts RNG output to PPM image format
- `rng2noise` - Processes RNG data
- `fft-test` - FFT-based frequency analysis (requires libfftw3-dev)

To clean up compiled binaries:

```bash
make clobber
```


Running
-------

**structure-in-hash-functions**: Analyzes patterns in hash functions by extracting neighborhoods and counting matches.

Basic usage:

```bash
./structure-in-hash-functions <hashname> [OPTIONS]
```

Common options:

- `-w <value>` : Width of the search window (default: 128)
- `-h <value>` : Height of the search window (default: 128)
- `-i <value>` : Neighborhood width (default: 5)
- `-j <value>` : Neighborhood height (default: 5)
- `-b <bit>` : Analyze only a specific bit (0-31)
- `-r` : Use random starting positions
- `-v` : Verbose output

Examples:

```bash
# Analyze the 'lcg' hash function with default settings
./structure-in-hash-functions lcg

# Analyze the z component of 'pcg3d' with verbose output
./structure-in-hash-functions -v pcg3d.z

# Analyze with larger neighborhoods (7x7) and 256x256 buffer
./structure-in-hash-functions -w 256 -h 256 -i 7 -j 7 xxhash32_2

# Analyze only bit 15 with random starting positions
./structure-in-hash-functions -r -b 15 murmur3_2

# 3D analysis with 256x256x256 buffer and random starting position
./structure-in-hash-functions -r -w 256 -h 256 -d 256 -i 5 -j 5 -k 5 pcg3d
```

**Quick test**: Run pattern analysis on a selection of hash functions:

```bash
make quicktest
```

A reference (unoptimized) implementation is provided as `structure-in-noise-reference`.

**rng2img**

`rng2img` can be used to generate an image of a hash function as a `ppm` file. You can use ImageMagick to convert it to a png.

```bash
./rng2img pcg_lcgcombine2
convert pcg_lcgcombine2.ppm pcg_lcgcombine.png
```

Common options:
- `-b` : Bit mode - extract individual bits from hash
- `-c` : Color mode - use 3-channel color output
- `-q` : Quad mode - divide image into quadrants
- `-f <filename>` : Read from binary file instead of hash
- `-w <width>` : Image width (default: 256)
- `-h <height>` : Image height (default: 256)
- `-o <filename>` : Output filename (default: <hash>.ppm)

**Finding the best bitplane**:

To visualize individual bitplanes and find which ones have the least structure, use the `-b` flag:

```bash
# Generate bitplane visualizations for bits 0-31
for bit in {0..31}; do
  ./rng2img -b ${bit} -w 512 -h 512 -o "pcg3d_bit_${bit}.ppm" pcg3d
done
```

**rng2noise**

`rng2noise` generates perlin-like noise from hash functions. It allows tuning of the noise parameters via the `-a` and `-b` flags, which control the hash table indices used for the noise computation.

Basic usage:

```bash
./rng2noise pcg3d
convert pcg3d.ppm pcg3d_noise.png
```

Common options:
- `-f <filename>` : Read from binary file instead of hash
- `-w <width>` : Image width (default: 256)
- `-h <height>` : Image height (default: 256)
- `-o <filename>` : Output filename (default: <hash>.ppm)
- `-s <scale>` : Noise scale factor (default: 16.0)
- `-a <value>` : First hash parameter (default: 13)
- `-b <value>` : Second hash parameter (default: 19)

Examples:

```bash
# Generate noise with custom scale
./rng2noise -s 8.0 -w 512 -h 512 pcg3d

# Experiment with different parameter combinations
./rng2noise -a 7 -b 11 pcg3d
convert pcg3d.ppm pcg3d_a7_b11.png

./rng2noise -a 13 -b 19 pcg3d
convert pcg3d.ppm pcg3d_a13_b19.png

# Use different scale factors to control feature frequency
./rng2noise -s 4.0 -a 13 -b 19 pcg3d
convert pcg3d.ppm pcg3d_scale4.png

./rng2noise -s 32.0 -a 13 -b 19 pcg3d
convert pcg3d.ppm pcg3d_scale32.png
```

The `-a` and `-b` parameters control which bitplane of the hash to use for the noise. See using `export_timing_and_best_bitplane.py` on how to export the best bitplanes per hash.

Utilities
---------

The repository includes a few helper scripts for combining run outputs with timing data, the major two being:

- `utils/aggregate_bitplane_runs.py`
- `utils/export_timing_and_best_bitplane.py`
- `utils/bitplane_quality_checker.py`

### aggregate_bitplane_runs.py

Aggregates per-hash, per-bitplane scores across `run1`..`run9` and computes one of:

- `min`
- `max`
- `median`

Example (print median aggregation to stdout):

```bash
python utils/aggregate_bitplane_runs.py \
	results/128x128x128x1/3x3x3x1 \
	--stat median
```

Example (write min aggregation to CSV):

```bash
python utils/aggregate_bitplane_runs.py \
	results/128x128x128x1/3x3x3x1 \
	--stat min \
	--output /tmp/agg_3x3_min.csv
```

### export_timing_and_best_bitplane.py

Produces a CSV with:

- `hash`
- `median_timing`
- for `--best-bitplanes 1` (default):
	- `lowest_bitplane_score`
	- `lowest_bitplane_index`
- for `--best-bitplanes N`:
	- `best1_score`, `best1_index`, ..., `bestN_score`, `bestN_index`

Inputs:

- timings source: `results/timings.csv` or a precomputed `median-timings.csv`
- one or more score sources:
	- run directory (for example `results/128x128x128x1/5x5x5x1/`), or
	- CSV previously exported by `aggregate_bitplane_runs.py`
- optional: `--best-bitplanes N` to export the N best (lowest-score) bitplanes per hash

Example 1: compute median bitplane scores from runs

```bash
python utils/export_timing_and_best_bitplane.py \
	results/timings.csv \
	results/128x128x128x1/5x5x5x1 \
	--score-stat median
```

Example 2: use an aggregate csv file and a precomputed median-timings.csv

```bash
python utils/median.py results/timings.csv > /tmp/median-timings.csv

python utils/export_timing_and_best_bitplane.py \
	/tmp/median-timings.csv \
	/tmp/agg_3x3_min.csv \
	--score-stat median
```

Example 3: show top 2 best bitplanes

```bash
python utils/export_timing_and_best_bitplane.py \
	results/timings.csv \
	results/128x128x128x1/5x5x5x1 \
	--score-stat median \
	--best-bitplanes 2
```

### bitplane_quality_checker.py

Outputs which bitplanes of which hash functions have results that are comparable to `/dev/random`.

**Options:**

- `--margin`: Allowed margin of error as a percentage (default: 0, meaning scores must be ≤ baseline)
  - `--margin 0`: strict mode - indices must perform as well as or better than `/dev/random`'s worst case
  - `--margin 5`: allows up to 5% degradation compared to baseline
- `--show-baselines`: Display `/dev/random` min/median/max baseline statistics
- `--show-dimensions`: Show window and neighborhood dimensions in output

**Examples:**

Check all configurations in results with default 0% margin:

```bash
python utils/bitplane_quality_checker.py
```

Check a specific window/neighborhood configuration:

```bash
python utils/bitplane_quality_checker.py results/128x128x128x1/5x5x5x1
```

Relax to a 5% margin with baseline statistics:

```bash
python utils/bitplane_quality_checker.py \
	--margin 5 \
	--show-baselines \
	results/128x128x128x1/5x5x5x1
```