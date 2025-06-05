#!/usr/bin/env python3
"""
Scan Chain Input Generator

This script processes two SPICE circuit files (switch matrix and sizes) to 
generate a scan chain input file with binary values (0/1) for each PROBE pin.

The output is a text file with one binary digit per line, where:
- The first line corresponds to PROBE<2008>
- The last line corresponds to PROBE<1>
- Each line is either 0 (VSS) or 1 (VDD)

Usage:
    ./combine_probes.py switch_matrix.cir sizes.cir output_file.txt

Author: Peter Kinget
Date: June 5, 2025
"""

import re
import os

def extract_probe_values_from_file(filepath):
    """
    Extract probe values from a SPICE circuit file.
    Maps VDD to 1 and VSS to 0.
    
    Args:
        filepath: Path to the SPICE circuit file
        
    Returns:
        Dictionary mapping probe numbers to binary values (0 or 1)
    """
    probe_values = {}
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                # Skip comment lines and continuation lines
                if line.strip().startswith('*') or line.strip().startswith('+'):
                    continue
                
                # Look for voltage source lines that connect to PROBE
                if line.strip().startswith('V') and 'PROBE<' in line:
                    # Extract the probe number
                    match = re.search(r'PROBE<(\d+)>', line)
                    if match:
                        probe_number = int(match.group(1))
                        
                        # Determine the value (VDD=1, VSS=0)
                        if 'VDD' in line:
                            probe_values[probe_number] = 1
                        elif 'VSS' in line:
                            probe_values[probe_number] = 0
        
        print(f"Extracted {len(probe_values)} probe values from {filepath}")
        return probe_values
    
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return {}

def main():
    import argparse
    
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Extract probe values from SPICE files and output them in a specific order.")
    parser.add_argument("sw_matrix_file", help="Path to the switch matrix SPICE file (.cir)")
    parser.add_argument("sizes_file", help="Path to the sizes SPICE file (.cir)")
    parser.add_argument("output_file", help="Path to the output file to be created")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Use the provided file paths
    sw_matrix_file = args.sw_matrix_file
    sizes_file = args.sizes_file
    output_file = args.output_file
    
    # Extract probe values from both files
    sw_matrix_values = extract_probe_values_from_file(sw_matrix_file)
    sizes_values = extract_probe_values_from_file(sizes_file)
    
    # Combine the dictionaries (sizes take precedence if there's overlap)
    combined_values = {**sw_matrix_values, **sizes_values}
    
    # Create an array with default value 0 for all probes from 1 to 2008
    all_probes = [0] * 2008
    
    # Fill in the known values
    for probe_num, value in combined_values.items():
        if 1 <= probe_num <= 2008:
            all_probes[probe_num-1] = value
    
    # Write values to output file in reverse order (PROBE<2008> down to PROBE<1>)
    with open(output_file, 'w') as f:
        for value in reversed(all_probes):
            f.write(f"{value}\n")
    
    print(f"Combined probe values written to {output_file}")
    print(f"Total probes processed: {len(combined_values)}")
    print(f"First few values (PROBE<2008> to PROBE<2000>): {all_probes[-9:][::-1]}")
    print(f"Last few values (PROBE<8> to PROBE<1>): {all_probes[:8][::-1]}")

if __name__ == "__main__":
    main()
