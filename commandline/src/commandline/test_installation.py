"""
Test script to verify that MOSbiusV2Tools has been correctly installed.
This script tests all three command-line tools with example files.
"""

import os
import sys
import shutil
import tempfile
import subprocess
import importlib.util

# Try to import pkg_resources, but handle the case when it's not available
try:
    import pkg_resources
    HAS_PKG_RESOURCES = True
except ImportError:
    HAS_PKG_RESOURCES = False

def check_package_installed():
    """Check if the package is properly installed."""
    if HAS_PKG_RESOURCES:
        try:
            pkg_resources.get_distribution("mosbiusv2tools")
            print("✓ MOSbiusV2Tools package is installed")
            return True
        except pkg_resources.DistributionNotFound:
            pass
    
    # Alternative check methods when pkg_resources is not available
    try:
        # Check if we can import the commandline module
        if importlib.util.find_spec("commandline") is not None:
            print("✓ MOSbiusV2Tools package is installed")
            return True
        
        # Check if the command-line tools are in PATH
        for cmd in ["generate_sizes_probe_subckt", "generate_pins_to_RBUS_SBUS_subckt", "generate_switch_matrix_probe_subckt"]:
            if shutil.which(cmd) is not None:
                print("✓ MOSbiusV2Tools command-line tools are available")
                return True
    except ImportError:
        pass
    
    print("✗ MOSbiusV2Tools package is not installed or not in PYTHONPATH")
    return False

def check_command_available(command):
    """Check if a command is available in the PATH."""
    return shutil.which(command) is not None

def run_test(command, input_file, output_file, dev_mode=False):
    """Run a command and check if it executes without errors."""
    # In development mode, use python -m to run the commands
    if dev_mode:
        cmd_parts = command.split('_')
        module_name = '.'.join(cmd_parts)
        cmd_list = [sys.executable, '-m', f'commandline.{module_name}']
        cmd_display = f"python -m commandline.{module_name}"
    else:
        if not check_command_available(command):
            print(f"✗ Command '{command}' is not available in PATH")
            print(f"  Try installing the package with: pip install -e .")
            print(f"  Or run this script in development mode: python -m commandline.test_installation --dev")
            return False
        cmd_list = [command]
        cmd_display = command
    
    # Add input and output file arguments
    cmd_list.extend([input_file, output_file])
    
    print(f"Running: {cmd_display} {input_file} {output_file}")
    
    try:
        result = subprocess.run(
            cmd_list, 
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
    except FileNotFoundError:
        print(f"✗ Could not find Python module for {command}")
        if dev_mode:
            print("  Make sure you're running from the correct directory")
        return False

def find_examples_directory():
    """Find the examples directory with required test files."""
    # Function to check if directory has all required example files
    def has_required_examples(directory):
        if not os.path.exists(directory):
            return False, set()
        required_files = {
            "all_transistors_4x_sizes.json",
            "INV_string_5_RBUS.json",
            "INV_string_clocked_RBUS_SBUS.json"
        }
        found_files = set(f for f in os.listdir(directory) if f in required_files)
        return found_files == required_files, found_files
    
    # Find examples directory
    examples_dir = None
    example_locations = []
    best_match_count = 0
    best_match_dir = None
    
    # Option 1: Check relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build list of locations to search
    search_paths = [
        (os.path.join(script_dir, 'examples'), "standard examples directory"),
        (os.path.join(script_dir, 'circuit_json_examples'), "circuit examples directory"),
        (os.path.join(script_dir, '..', '..', '..', '..', 'examples'), "root examples directory"),
        (os.path.join(script_dir, '..', '..', '..', '..', 'commandline/circuit_json_examples'), "root circuit examples directory"),
        (os.path.join(os.getcwd(), 'examples'), "examples in current directory"),
        (os.path.join(os.getcwd(), 'commandline/circuit_json_examples'), "circuit examples in current directory"),
    ]
    
    # Add package installation locations if pkg_resources is available
    if HAS_PKG_RESOURCES:
        try:
            package_dir = os.path.dirname(pkg_resources.resource_filename('commandline', '__init__.py'))
            search_paths.extend([
                (os.path.join(package_dir, 'examples'), "installed package examples"),
                (os.path.join(package_dir, 'circuit_json_examples'), "installed package circuit examples"),
                (os.path.join(os.path.dirname(package_dir), 'examples'), "package parent examples"),
            ])
        except (ImportError, FileNotFoundError):
            pass
    
    # Check all possible locations
    for path, description in search_paths:
        if os.path.exists(path):
            has_all, found_files = has_required_examples(path)
            example_locations.append({
                'path': path,
                'description': description,
                'files': found_files
            })
            if has_all:
                examples_dir = path
                break
            elif len(found_files) > best_match_count:
                best_match_count = len(found_files)
                best_match_dir = path
    
    if examples_dir is not None:
        print(f"✓ Found complete examples directory at {examples_dir}")
        return examples_dir
    
    # If we didn't find a complete set, provide detailed feedback
    print("\n✗ Could not find directory with all required example files")
    print("\nSearched locations:")
    for loc in example_locations:
        print(f"\n- {loc['description']}:")
        print(f"  Path: {loc['path']}")
        if loc['files']:
            print("  Found files:")
            for f in sorted(loc['files']):
                print(f"    ✓ {f}")
        else:
            print("  No example files found")
    
    print("\nRequired files:")
    print("- all_transistors_4x_sizes.json")
    print("- INV_string_5_RBUS.json")
    print("- INV_string_clocked_RBUS_SBUS.json")
    
    if best_match_dir:
        print(f"\nBest partial match was in: {best_match_dir}")
        print("Consider copying missing files to this location.")
    
    return None

def main():
    """Run the installation tests."""
    # Check for development mode flag
    dev_mode = '--dev' in sys.argv
    if dev_mode:
        print("Testing MOSbiusV2Tools in development mode...\n")
    else:
        print("Testing MOSbiusV2Tools installation...\n")
    
    if not check_package_installed():
        print("\nPlease install the package using:")
        print("    pip install MOSbiusV2Tools")
        return 1
    
    # Find examples directory
    examples_dir = find_examples_directory()
    if examples_dir is None:
        return 1
    
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
        test1_ok = run_test("generate_sizes_probe_subckt", sizes_file, sizes_output, dev_mode)
        
        # Test 2: generate_pins_to_RBUS_SBUS_subckt
        circuit_file = os.path.join(examples_dir, "INV_string_5_RBUS.json")
        rbus_output = os.path.join(tmp_dir, "test_rbus_output.cir")
        test2_ok = run_test("generate_pins_to_RBUS_SBUS_subckt", circuit_file, rbus_output, dev_mode)
        
        # Test 3: generate_switch_matrix_probe_subckt
        switch_circuit_file = os.path.join(examples_dir, "INV_string_clocked_RBUS_SBUS.json")
        switch_output = os.path.join(tmp_dir, "test_switch_output.cir")
        test3_ok = run_test("generate_switch_matrix_probe_subckt", switch_circuit_file, switch_output, dev_mode)
        
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
            
            # Add helpful installation instructions
            if not dev_mode and not check_command_available("generate_sizes_probe_subckt"):
                print("\nSolution: The package doesn't appear to be installed properly.")
                print("You can either:")
                print("1. Test directly in development mode:")
                print("    python -m commandline.test_installation --dev")
                print("\n2. Install in development mode from source:")
                print("    pip install -e .")
                print("\n3. Install from GitHub:")
                print("    pip install git+https://github.com/peterkinget/MOSbiusV2Tools.git")
            elif dev_mode:
                print("\nMake sure you are running from the correct directory and all dependencies are installed.")
                print("Consider installing in development mode:")
                print("    pip install -e .")
            
            return 1

if __name__ == "__main__":
    sys.exit(main())
