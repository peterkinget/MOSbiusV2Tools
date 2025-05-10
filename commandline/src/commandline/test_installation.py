"""
Test script to verify that MOSbiusV2Tools has been correctly installed.
This script tests all three command-line tools with example files.
"""

import os
import sys
import shutil
import tempfile
import subprocess
import pkg_resources

def check_package_installed():
    """Check if the package is properly installed."""
    try:
        pkg_resources.get_distribution("mosbiusv2tools")
        print("✓ MOSbiusV2Tools package is installed")
        return True
    except pkg_resources.DistributionNotFound:
        print("✗ MOSbiusV2Tools package is not installed")
        return False

def check_command_available(command):
    """Check if a command is available in the PATH."""
    return shutil.which(command) is not None

def run_test(command, input_file, output_file):
    """Run a command and check if it executes without errors."""
    if not check_command_available(command):
        print(f"✗ Command '{command}' is not available in PATH")
        return False
    
    print(f"Running: {command} {input_file} {output_file}")
    
    try:
        result = subprocess.run(
            [command, input_file, output_file], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print(f"✓ {command} executed successfully")
        
        # Check if output file exists and has content
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f"✓ Output file '{output_file}' was created with content")
            return True
        else:
            print(f"✗ Output file '{output_file}' is empty or wasn't created")
            return False
    except subprocess.CalledProcessError as e:
        print(f"✗ {command} failed with error:")
        print(e.stderr)
        return False

def main():
    """Run the installation tests."""
    print("Testing MOSbiusV2Tools installation...\n")
    
    if not check_package_installed():
        print("\nPlease install the package using:")
        print("    pip install MOSbiusV2Tools")
        return 1
    
    # Find examples directory
    examples_dir = None
    
    # Option 1: Check relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(script_dir, 'examples')):
        examples_dir = os.path.join(script_dir, 'examples')
    
    # Option 2: Check for examples in standard locations
    search_paths = [
        script_dir,                     # Current directory
        os.path.join(script_dir, '..'), # Parent directory
        os.path.dirname(script_dir),    # Another form of parent
        os.getcwd(),                    # Working directory
    ]
    
    for path in search_paths:
        if examples_dir is None and os.path.exists(os.path.join(path, 'examples')):
            examples_dir = os.path.join(path, 'examples')
            break
    
    # Option 3: Check in package directory
    if examples_dir is None:
        try:
            # Try to find examples relative to the installed package
            package_dir = os.path.dirname(pkg_resources.resource_filename('commandline', '__init__.py'))
            for check_dir in [package_dir, os.path.dirname(package_dir), os.path.dirname(os.path.dirname(package_dir))]:
                if os.path.exists(os.path.join(check_dir, 'examples')):
                    examples_dir = os.path.join(check_dir, 'examples')
                    break
        except (pkg_resources.DistributionNotFound, FileNotFoundError):
            pass
    
    if examples_dir is None:
        print("✗ Examples directory not found")
        print("Please run this script from the MOSbiusV2Tools root directory")
        return 1
    
    print(f"✓ Found examples directory at {examples_dir}")
    
    # Create a temporary directory for test outputs
    with tempfile.TemporaryDirectory() as tmp_dir:
        print(f"\nUsing temporary directory: {tmp_dir}\n")
        
        # Before starting tests, let's verify we have the example files
        print("\nChecking example files:")
        example_files = {
            "all_transistors_4x_sizes.json": False,
            "INV_string_5_RBUS.json": False,
            "INV_string_clocked_RBUS_SBUS.json": False
        }
        
        for file in os.listdir(examples_dir):
            if file in example_files:
                example_files[file] = True
                print(f"✓ Found {file}")
        
        missing_files = [f for f, found in example_files.items() if not found]
        if missing_files:
            print(f"✗ Missing example files: {', '.join(missing_files)}")
            print("Please make sure you have all the required example files in the examples directory.")
            return 1
        
        # Test 1: generate_sizes_probe_subckt
        sizes_file = os.path.join(examples_dir, "all_transistors_4x_sizes.json")
        sizes_output = os.path.join(tmp_dir, "test_sizes_output.cir")
        test1_ok = run_test("generate_sizes_probe_subckt", sizes_file, sizes_output)
        
        # Test 2: generate_pins_to_RBUS_SBUS_subckt
        circuit_file = os.path.join(examples_dir, "INV_string_5_RBUS.json")
        rbus_output = os.path.join(tmp_dir, "test_rbus_output.cir")
        test2_ok = run_test("generate_pins_to_RBUS_SBUS_subckt", circuit_file, rbus_output)
        
        # Test 3: generate_switch_matrix_probe_subckt
        switch_circuit_file = os.path.join(examples_dir, "INV_string_clocked_RBUS_SBUS.json")
        switch_output = os.path.join(tmp_dir, "test_switch_output.cir")
        test3_ok = run_test("generate_switch_matrix_probe_subckt", switch_circuit_file, switch_output)
        
        # Print summary
        print("\nTest Summary:")
        print(f"- Generate Sizes Probe Subcircuit: {'PASS' if test1_ok else 'FAIL'}")
        print(f"- Generate Pins to RBUS/SBUS Subcircuit: {'PASS' if test2_ok else 'FAIL'}")
        print(f"- Generate Switch Matrix Probe Subcircuit: {'PASS' if test3_ok else 'FAIL'}")
        
        if test1_ok and test2_ok and test3_ok:
            print("\n✓ All tests passed! MOSbiusV2Tools is correctly installed.")
            return 0
        else:
            print("\n✗ Some tests failed. Please check the error messages above.")
            return 1

if __name__ == "__main__":
    sys.exit(main())
