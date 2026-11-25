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

- `structure-in-noise` - Main pattern analysis tool for examining hash functions and PRNGs
- `structure-in-noise-reference` - Reference implementation for validation
- `rng2img` - Converts RNG output to PPM image format
- `rng2noise` - Processes RNG data
- `fft-test` - FFT-based frequency analysis (requires libfftw3-dev)

To clean up compiled binaries:

```bash
make clobber
```


Usage
-----

**structure-in-noise**: Analyzes patterns in hash functions by extracting neighborhoods and counting matches.

Basic usage:

```bash
./structure-in-noise <hashname> [OPTIONS]
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
./structure-in-noise lcg

# Analyze the z component of 'pcg3d' with verbose output
./structure-in-noise -v pcg3d.z

# Analyze with larger neighborhoods (7x7) and 256x256 buffer
./structure-in-noise -w 256 -h 256 -i 7 -j 7 xxhash32_2

# Analyze only bit 15 with random starting positions
./structure-in-noise -r -b 15 murmur3_2

# 3D analysis with 256x256x256 buffer and random starting position
./structure-in-noise -r -w 256 -h 256 -d 256 -i 5 -j 5 -k 5 pcg3d
```

**Quick test**: Run pattern analysis on a selection of hash functions:

```bash
make quicktest
```


Utilities
---------

The repository includes two helper scripts for combining run outputs with timing data:

- `utils/aggregate_bitplane_runs.py`
- `utils/export_timing_and_best_bitplane.py`

### `aggregate_bitplane_runs.py`

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


### `export_timing_and_best_bitplane.py`

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

Example 1: timings.csv + run directory (compute median bitplane scores from runs):

```bash
python utils/export_timing_and_best_bitplane.py \
	results/timings.csv \
	results/128x128x128x1/5x5x5x1 \
	--score-stat median \
	--output results/5x5-timing-bestbit.csv
```

Example 2: median-timings.csv + run directory:

```bash
python utils/median.py results/timings.csv > /tmp/median-timings.csv

python utils/export_timing_and_best_bitplane.py \
	/tmp/median-timings.csv \
	results/128x128x128x1/5x5x5x1 \
	--score-stat median
```

Example 2b: median-timings.csv + run directory + top 3 best bitplanes:

```bash
python utils/export_timing_and_best_bitplane.py \
	/tmp/median-timings.csv \
	results/128x128x128x1/5x5x5x1 \
	--score-stat median \
	--best-bitplanes 3
```

Example 3: timings.csv + previously exported aggregate CSV:

```bash
python utils/aggregate_bitplane_runs.py \
	results/128x128x128x1/5x5x5x1 \
	--stat median \
	--output /tmp/agg_5x5.csv

python utils/export_timing_and_best_bitplane.py \
	results/timings.csv \
	/tmp/agg_5x5.csv \
	--output results/5x5-from-agg.csv
```


