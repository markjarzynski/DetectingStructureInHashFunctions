#!/usr/bin/env python3

import numpy as np
import sys
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find the maximum value for each column across multiple CSV files.",
        epilog="Reads columns 1-32 (after the first column) from CSV files and outputs the maximum values."
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="CSV files to process"
    )
    
    args = parser.parse_args()
    
    # Show help if no files provided
    if not args.files:
        parser.print_help()
        sys.exit(1)
    
    files = args.files

    # Read 32 score columns after the hash label.
    data = [np.loadtxt(file, delimiter=",", dtype=np.uint64, skiprows=1, usecols=range(1,33)) for file in files]

    data = np.vstack(data)
    data = np.nanmax(data, axis=0)

    output = ""
    with open(files[0], 'r') as f:
        output = f.readline()
        output += f.readline().split(',')[0]
        
    for i in data:
        output += "," + str(i)

    print(output)
