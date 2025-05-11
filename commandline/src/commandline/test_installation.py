"""
Test script for MOSbiusV2Tools command-line tools.

This script verifies the installation and functionality of MOSbiusV2Tools command-line utilities:
1. generate_sizes_probe_subckt
2. generate_pins_to_RBUS_SBUS_subckt
3. generate_switch_matrix_probe_subckt
4. generate_nodes_subckt
"""

import os
import sys
import shutil
import tempfile
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional
import importlib.util

@dataclass
class TestCase:
    """Configuration for a single test case"""
    command: str
    input_file: str
    description: str

class MOSbiusTestConfig:
    """Test configuration and file mappings"""
    # Test cases mapping input files to commands
    TESTS = [
        TestCase("generate_sizes_probe_subckt", 
                "all_transistors_4x_sizes.json",
                "Generate sizes probe subcircuit"),
        TestCase("generate_pins_to_RBUS_SBUS_subckt",
                "INV_string_5_RBUS.json", 
                "Generate pins to RBUS/SBUS subcircuit"),
        TestCase("generate_switch_matrix_probe_subckt",
                "INV_string_clocked_RBUS_SBUS.json",
                "Generate switch matrix probe subcircuit"),
        TestCase("generate_nodes_subckt",
                "INV_string_12_NODE.json",
                "Generate nodes subcircuit")
    ]
    
    # Required example files
    REQUIRED_FILES = {test.input_file for test in TESTS}

    def __init__(self):
        self.examples_dir = self._find_examples()
        self.dev_mode = '--dev' in sys.argv

    def _find_examples(self) -> Optional[str]:
        """Find the directory containing example files"""
        search_paths = self._get_search_paths()
        
        for path in search_paths:
            if self._has_required_files(path):
                return path
        return None

    def _get_search_paths(self) -> List[str]:
        """Get list of paths to search for example files"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        if self.dev_mode:
            # In dev mode, look in repository examples directory
            paths = [os.path.join(script_dir, '..', '..', '..', '..', 'examples')]
        else:
            # In installed mode, look in mosbiusv2tools_examples
            paths = [os.path.join(sys.prefix, 'mosbiusv2tools_examples')]
        
        valid_paths = [os.path.normpath(p) for p in paths if os.path.exists(p)]
        if not valid_paths:
            print("\n✗ Could not find examples directory")
            print(f"Expected location: {paths[0]}")
            if self.dev_mode:
                print("Make sure you're running from the repository root")
            else:
                print("Make sure the package is installed correctly")
            return []
        
        for path in valid_paths:
            print(f"\nFound examples in: {path}")
            if os.path.exists(path):
                files = [f for f in os.listdir(path) if f.endswith('.json')]
                if files:
                    print(f"Available examples: {', '.join(sorted(files))}")
        
        return valid_paths

    def _has_required_files(self, directory: str) -> bool:
        """Check if directory contains all required example files"""
        try:
            files = os.listdir(directory)
            return all(f in files for f in self.REQUIRED_FILES)
        except OSError:
            return False

class MOSbiusTestRunner:
    """Handles test execution and reporting"""
    def __init__(self, config: MOSbiusTestConfig):
        self.config = config
        self.results: Dict[str, bool] = {}

    def run_command(self, test_case: TestCase, output_file: str) -> bool:
        """Run a single command and verify its output"""
        cmd_parts = test_case.command.split('_')
        
        if self.config.dev_mode:
            cmd = [sys.executable, '-m', f'commandline.{".".join(cmd_parts)}']
        else:
            if not shutil.which(test_case.command):
                print(f"✗ Command '{test_case.command}' not found in PATH")
                return False
            cmd = [test_case.command]

        input_path = os.path.join(self.config.examples_dir, test_case.input_file)
        cmd.extend([input_path, output_file])

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"✓ {test_case.description}: PASS")
                return True
            else:
                print(f"✗ {test_case.description}: Output file empty or missing")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"✗ {test_case.description}: Command failed")
            print(f"  Error: {e.stderr}")
            return False
        except Exception as e:
            print(f"✗ {test_case.description}: Unexpected error")
            print(f"  {str(e)}")
            return False

    def run_all_tests(self) -> bool:
        """Run all test cases"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            for test_case in self.config.TESTS:
                output_file = os.path.join(tmp_dir, f"test_{test_case.command}_output.cir")
                self.results[test_case.description] = self.run_command(test_case, output_file)

        return all(self.results.values())

    def print_summary(self) -> None:
        """Print test results summary"""
        print("\nTest Summary:")
        for description, passed in self.results.items():
            print(f"- {description}: {'PASS' if passed else 'FAIL'}")

def check_installation() -> bool:
    """Verify that MOSbiusV2Tools is properly installed"""
    try:
        if importlib.util.find_spec("commandline") is not None:
            print("✓ MOSbiusV2Tools package is found")
            return True
    except ImportError:
        pass

    print("✗ MOSbiusV2Tools package is not installed")
    return False

def main() -> int:
    """Main test orchestration"""
    print(f"Testing MOSbiusV2Tools in {'development' if '--dev' in sys.argv else 'installation'} mode...\n")

    if not check_installation():
        print("\nPlease install the package:")
        print("    pip install MOSbiusV2Tools")
        return 1

    config = MOSbiusTestConfig()
    if config.examples_dir is None:
        print("\n✗ Could not find example files")
        print("Please ensure example files are in one of:")
        for path in config._get_search_paths():
            print(f"- {path}")
        return 1

    runner = MOSbiusTestRunner(config)
    success = runner.run_all_tests()
    runner.print_summary()

    if success:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        print("\nTroubleshooting:")
        print("1. Make sure all dependencies are installed")
        print("2. Try running in development mode: python -m commandline.test_installation --dev")
        print("3. Try reinstalling: pip install -e .")
        return 1

if __name__ == "__main__":
    sys.exit(main())
