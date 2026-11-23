#!/usr/bin/env python3
"""Aggregate per-bitplane scores across run directories.

Given a directory like:
    results/128x128x128x1/3x3x3x1/

This script reads all `runN/*.txt` files, parses the second line in each file,
and computes min/max/median for each of the 32 bitplane scores per hash.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
from pathlib import Path
from typing import Callable


ScoreList = list[int]
Aggregated = dict[str, ScoreList]


def _parse_result_file(file_path: Path) -> tuple[str, list[int]]:
    """Parse a result file and return (hash_name, 32 scores)."""
    with file_path.open("r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    if len(lines) < 2:
        raise ValueError(f"File has fewer than 2 lines: {file_path}")

    fields = [field.strip() for field in lines[1].split(",") if field.strip() != ""]
    if len(fields) != 33:
        raise ValueError(
            f"Expected 33 comma-separated fields on line 2 (hash + 32 scores), "
            f"got {len(fields)} in {file_path}"
        )

    hash_name = fields[0]
    try:
        scores = [int(value) for value in fields[1:]]
    except ValueError as exc:
        raise ValueError(f"Non-numeric score in {file_path}: {exc}") from exc

    return hash_name, scores


def _stat_funcs(names: str) -> list[tuple[str, Callable[[list[int]], int]]]:
    """Return list of (name, function) tuples for comma-separated stat names."""
    funcs = []
    for name in names.split(","):
        stat_name = name.strip().lower()
        if stat_name == "min":
            funcs.append(("min", min))
        elif stat_name == "max":
            funcs.append(("max", max))
        elif stat_name == "median":
            # There are exactly 9 runs, so the median of integer values is an integer.
            funcs.append(("median", lambda values: int(statistics.median(values))))
        else:
            raise ValueError(f"Unknown stat '{name}'. Use one of: min, max, median")
    return funcs


def compute_bitplane_stats(base_dir: str | Path, stats: str = "median") -> dict[str, dict[str, dict[str, int]]]:
    """Compute per-hash, per-bitplane stats across all runs.

    Args:
        base_dir: Directory containing `run1`, `run2`, ... subdirectories.
        stats: Comma-separated list of stats (e.g., "min,max,median").

    Returns:
        Dict mapping hash name -> stat name -> list of 32 aggregated scores.
    """
    root = Path(base_dir)
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")

    run_dirs = sorted(path for path in root.iterdir() if path.is_dir() and path.name.startswith("run"))
    expected_runs = 9
    if len(run_dirs) != expected_runs:
        raise ValueError(
            f"Expected exactly {expected_runs} run directories under {root}, found {len(run_dirs)}: "
            f"{', '.join(path.name for path in run_dirs)}"
        )

    per_hash_per_bitplane: dict[str, list[list[int]]] = {}

    for run_dir in run_dirs:
        txt_files = sorted(run_dir.glob("*.txt"))
        if not txt_files:
            raise ValueError(f"No .txt files found in {run_dir}")

        for txt_file in txt_files:
            hash_name, scores = _parse_result_file(txt_file)
            buckets = per_hash_per_bitplane.setdefault(hash_name, [[] for _ in range(32)])
            for bitplane_idx, score in enumerate(scores):
                buckets[bitplane_idx].append(score)

    stat_funcs = _stat_funcs(stats)
    result: dict[str, dict[str, list[int]]] = {}
    for hash_name, bitplane_buckets in per_hash_per_bitplane.items():
        result[hash_name] = {}
        for stat_name, reducer in stat_funcs:
            aggregated_scores: ScoreList = []
            for idx, values in enumerate(bitplane_buckets):
                if len(values) != expected_runs:
                    raise ValueError(
                        f"Expected {expected_runs} values for hash '{hash_name}', "
                        f"bitplane {idx}, found {len(values)}"
                    )
                aggregated_scores.append(reducer(values))
            result[hash_name][stat_name] = aggregated_scores

    return result


def compute_bitplane_stat(base_dir: str | Path, stat: str = "median") -> Aggregated:
    """Backward compatibility wrapper for single stat.
    
    Returns:
        Dict mapping hash name -> list of 32 aggregated scores (for single stat only).
    """
    result = compute_bitplane_stats(base_dir, stat)
    # Extract single stat from multi-stat result
    return {hash_name: scores[stat] for hash_name, scores in result.items()}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate min/max/median per bitplane across run directories"
    )
    parser.add_argument(
        "base_dir",
        help="Directory containing run1..run9, e.g. results/128x128x128x1/3x3x3x1",
    )
    parser.add_argument(
        "--stat",
        default="median",
        help="Comma-separated aggregation functions: min,max,median (default: median)",
    )
    parser.add_argument(
        "--output",
        help="Optional output CSV path. If omitted, prints CSV to stdout.",
    )
    args = parser.parse_args()

    result = compute_bitplane_stats(args.base_dir, args.stat)

    if args.output:
        output_prefix = Path(args.output)
        # For backward compatibility, if only one stat, write to the specified file
        # Otherwise, write each stat to output_<stat>.csv
        stat_list = [s.strip() for s in args.stat.split(",")]
        if len(stat_list) == 1:
            stat_name = stat_list[0]
            output_file = output_prefix
            header = ["hash"] + [f"bit{i}" for i in range(32)]
            with output_file.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                for hash_name in sorted(result):
                    writer.writerow([hash_name] + result[hash_name][stat_name])
            print(f"Wrote {args.stat} aggregates for {len(result)} hashes to {output_file}")
        else:
            for stat_name in stat_list:
                output_file = output_prefix.parent / f"{output_prefix.stem}_{stat_name}.csv"
                header = ["hash"] + [f"bit{i}" for i in range(32)]
                with output_file.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    for hash_name in sorted(result):
                        writer.writerow([hash_name] + result[hash_name][stat_name])
                print(f"Wrote {stat_name} aggregates for {len(result)} hashes to {output_file}")
        return

    # Print to stdout
    stat_list = [s.strip() for s in args.stat.split(",")]
    for stat_idx, stat_name in enumerate(stat_list):
        if stat_idx > 0:
            print()
        writer = csv.writer(sys.stdout)
        writer.writerow([f"hash_{stat_name}"] + [f"bit{i}" for i in range(32)])
        for hash_name in sorted(result):
            writer.writerow([hash_name] + result[hash_name][stat_name])


if __name__ == "__main__":
    main()
