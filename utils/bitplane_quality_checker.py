#!/usr/bin/env python3
"""Report which bitplane indices are good based on /dev/random comparison.

For each hash function, check which bitplane indices (0-31) are within 5% 
of the max /dev/random baseline.

Usage:
    python3 bitplane_quality_checker.py [results_dir]
    
    If results_dir is provided, only checks that specific window/neighborhood.
    Otherwise, checks all configurations in results/.

    This script evaluates the quality of bitplane indices for different hash
    functions by comparing their scores against a /dev/random baseline.

    For each hash function and each bitplane index (0-31), it checks whether
    the score is acceptable relative to /dev/random's worst-case performance.
    A bitplane index is considered "good" if its score is at or below a
    threshold determined by: max_baseline * (1 + margin/100), where max_baseline
    is /dev/random's worst-performing index.

    The --margin flag controls the tolerance level. A margin of 0 means
    bitplane indices must perform as well as or better than /dev/random's
    worst case. A margin of 5 allows up to 5% degradation compared to
    /dev/random's worst case.

    Output shows the ranges of good bitplane indices for each hash function,
    formatted as ranges (e.g., 0-15, 20-31) for readability.
"""

import sys
import argparse
from pathlib import Path
from aggregate_bitplane_runs import compute_bitplane_stats


def parse_result_file(file_path):
    """Parse a result file and return (name, scores_list).
    
    Expected format:
        Line 1: Command line args
        Line 2: name,score1,score2,...,score32[,timing_data...]
    
    Accepts files with 33+ fields (extra fields like timings are ignored).
    """
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            return None
        
        parts = lines[1].strip().split(',')
        if len(parts) < 33:  # name + 32 bitplane scores (may have timings after)
            return None
        
        name = parts[0]
        try:
            # Take only the first 32 scores, ignore any additional timing data
            scores = [int(x) for x in parts[1:33]]
        except ValueError:
            return None
        
        return name, scores
    except Exception as e:
        return None


def get_devrandom_baselines(neighborhood_dir):
    """Get min/max/median /dev/random scores using aggregate_bitplane_runs.py.
    
    Returns:
        Dict mapping stat_name -> list of 32 scores, e.g.:
        {"min": [...], "max": [...], "median": [...]}
    """
    try:
        result = compute_bitplane_stats(neighborhood_dir, "min,max,median")
        # Extract only '/dev/random' hash
        if "/dev/random" in result:
            return result["/dev/random"]
        else:
            print(f"  WARNING: No '/dev/random' hash found in {neighborhood_dir}")
            return None
    except Exception as e:
        print(f"  ERROR computing aggregated devrandom baseline: {e}")
        return None


def get_good_bitplane_indices(bitplane_scores, devrandom_baseline_dict, margin_percent=5):
    """Check which bitplane indices are good.
    
    For each bitplane index (0-31), check if the score is within margin_percent
    of the max value across ALL indices in the /dev/random max baseline.
    
    Args:
        bitplane_scores: List of 32 scores for this bitplane
        devrandom_baseline_dict: Dict with 'max' key containing baseline scores
        margin_percent: Allowed margin as percentage (default 5, meaning 5% tolerance)
    
    Returns list of indices (0-31) that are good.
    """
    if len(bitplane_scores) != 32:
        return []
    
    if not devrandom_baseline_dict or "max" not in devrandom_baseline_dict:
        return []
    
    max_baseline = devrandom_baseline_dict.get("max", [])
    
    if len(max_baseline) != 32:
        return []
    
    # Find the global max across all indices
    global_max = max(max_baseline)
    multiplier = 1.0 + (margin_percent / 100.0)
    threshold = global_max * multiplier
    
    good_indices = []
    for idx, bp_score in enumerate(bitplane_scores):
        if bp_score <= threshold:
            good_indices.append(idx)
    
    return good_indices


def format_indices(indices):
    """Format a list of indices as ranges.
    
    E.g., [0, 1, 2, 5, 6, 10] -> "0-2, 5-6, 10"
    """
    if not indices:
        return "none"
    
    ranges = []
    start = indices[0]
    end = indices[0]
    
    for idx in indices[1:]:
        if idx == end + 1:
            end = idx
        else:
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            start = idx
            end = idx
    
    # Add final range
    if start == end:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{end}")
    
    return ", ".join(ranges)


def check_neighborhood(neighborhood_dir, margin_percent=5):
    """Check all bitplanes in a single neighborhood directory.
    
    Args:
        neighborhood_dir: Path to a neighborhood directory (e.g., results/128x128x1x1/5x5x1x1)
        margin_percent: Allowed margin as percentage (default 5)
    
    Returns:
        (good_index_ranges, devrandom_baselines)
    """
    # Get aggregated devrandom baselines (min, max, median across all runs)
    devrandom_baselines = get_devrandom_baselines(neighborhood_dir)
    if devrandom_baselines is None:
        return {}, None
    
    # Read bitplane files from first run (sample representative values)
    run_dirs = sorted([d for d in neighborhood_dir.iterdir() if d.is_dir() and d.name.startswith('run')])
    if not run_dirs:
        print(f"  WARNING: No run directories found in {neighborhood_dir}")
        return {}, devrandom_baselines
    
    first_run = run_dirs[0]
    bitplane_files = sorted([f for f in first_run.glob("*.txt") if f.name != "devrandom.txt"])
    
    if not bitplane_files:
        print(f"  No bitplane files found")
        return {}, devrandom_baselines
    
    good_index_ranges = {}
    for bp_file in bitplane_files:
        bp_data = parse_result_file(bp_file)
        if bp_data is None:
            continue
        
        bp_name, bp_scores = bp_data
        good_indices = get_good_bitplane_indices(bp_scores, devrandom_baselines, margin_percent)
        if good_indices:
            good_index_ranges[bp_name] = good_indices
    
    return good_index_ranges, devrandom_baselines


def main():
    parser = argparse.ArgumentParser(
        description="""Check bitplane quality against /dev/random baseline (per-index).""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "results_dir",
        nargs="?",
        help="Specific results directory to check (e.g., results/128x128x1x1/5x5x1x1). "
             "If omitted, checks all configurations in results/.",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=0,
        help="Allowed margin of error as a percentage (default: 0). "
             "A margin of 0 means scores must be <= the max baseline. "
             "A margin of 5 means scores up to 5%% above the max baseline are considered good.",
    )
    parser.add_argument(
        "--show-baselines",
        action="store_true",
        help="Show /dev/random baseline statistics (min, median, max).",
    )
    parser.add_argument(
        "--show-dimensions",
        action="store_true",
        help="Show window and neighborhood dimensions.",
    )
    args = parser.parse_args()
    
    if args.results_dir:
        # Check a specific directory
        check_dir = Path(args.results_dir)
        if not check_dir.exists():
            print(f"ERROR: Directory not found: {check_dir}")
            sys.exit(1)
        
        if not check_dir.is_dir():
            print(f"ERROR: Not a directory: {check_dir}")
            sys.exit(1)
        
        # Infer window and neighborhood from path
        parts = check_dir.parts
        if len(parts) >= 2:
            neighborhood_size = parts[-1]
            window_size = parts[-2]
        else:
            window_size = "?"
            neighborhood_size = "?"
        
        good_index_ranges, baselines = check_neighborhood(check_dir, args.margin)
        
        if args.show_dimensions:
            print(f"{window_size} / {neighborhood_size}:")
        if args.show_baselines and baselines:
            print(f"/dev/random min: {baselines.get('min', 'N/A')}")
            print(f"/dev/random median: {baselines.get('median', 'N/A')}")
            print(f"/dev/random max: {baselines.get('max', 'N/A')}")
        
        if good_index_ranges:
            for bp_name in sorted(good_index_ranges.keys()):
                indices = good_index_ranges[bp_name]
                formatted = format_indices(indices)
                print(f"{bp_name}: {formatted}")
        else:
            print(f"  No good bitplane indices found")
    
    else:
        # Check all directories (original behavior)
        results_dir = Path(__file__).parent.parent / "results"
        
        if not results_dir.exists():
            print(f"ERROR: Results directory not found: {results_dir}")
            sys.exit(1)
        
        # Traverse window sizes (e.g., 128x128x1x1)
        window_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir() and 'x' in d.name])
        
        if not window_dirs:
            print(f"ERROR: No window size directories found in {results_dir}")
            sys.exit(1)
        
        # For each window size
        for window_dir in window_dirs:
            window_size = window_dir.name
            
            # For each neighborhood size
            neighborhood_dirs = sorted([d for d in window_dir.iterdir() if d.is_dir() and 'x' in d.name])
            
            for neighborhood_dir in neighborhood_dirs:
                neighborhood_size = neighborhood_dir.name
                
                good_index_ranges, baselines = check_neighborhood(neighborhood_dir, args.margin)
                
                if not baselines:
                    print(f"  WARNING: Could not get devrandom baseline for {window_size} / {neighborhood_size}")
                    continue
                
                if args.show_dimensions:
                    print(f"\n{window_size} / {neighborhood_size}:")
                else:
                    print()
                if args.show_baselines and baselines:
                    print(f"/dev/random min: {baselines.get('min', 'N/A')}")
                    print(f"/dev/random median: {baselines.get('median', 'N/A')}")
                    print(f"/dev/random max: {baselines.get('max', 'N/A')}")
                
                if good_index_ranges:
                    for bp_name in sorted(good_index_ranges.keys()):
                        indices = good_index_ranges[bp_name]
                        formatted = format_indices(indices)
                        print(f"{bp_name}: {formatted}")
                else:
                    print(f"  No good bitplane indices found")


if __name__ == "__main__":
    main()
