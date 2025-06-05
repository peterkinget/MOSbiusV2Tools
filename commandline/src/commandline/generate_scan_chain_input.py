import json
import os
import argparse
from datetime import datetime

def get_device_sizing_probe_values(sizes_file):
    """
    Process the sizes JSON file to determine device sizing register values.
    
    Args:
        sizes_file (str): Path to the JSON file containing device sizes.
    
    Returns:
        dict: A dictionary mapping probe register numbers to binary values (0 or 1).
    """
    # Define the path to the chip_config_data directory
    chip_config_dir = os.path.join(os.path.dirname(__file__), "chip_config_data")
    registers_file = os.path.join(chip_config_dir, "device_name_to_sizing_registers.json")
    
    print(f"Looking for registers file at: {registers_file}")
    
    # Load sizes and registers
    with open(sizes_file, "r") as f:
        sizes = json.load(f)
    
    with open(registers_file, "r") as f:
        registers = json.load(f)
    
    # Initialize the output dictionary for register settings
    register_settings = {}
    
    # Generate register settings
    for device, bit_to_register in registers.items():
        size = sizes.get(device, [0])[0]  # Default size to 0 if device is not in sizes.json
        if not (0 <= size <= 31):  # Validate size is a 5-bit number
            print(f"Warning: Size {size} for device {device} is not a 5-bit number.")
            size = 0
        
        # Iterate through the registers and set their values based on the size
        for bit, register in sorted(bit_to_register.items(), key=lambda x: int(x[0])):
            register_settings[int(register)] = 1 if int(bit) & size else 0
    
    return register_settings

def get_switch_matrix_probe_values(circuit_json_path):
    """
    Process the circuit JSON file to determine switch matrix probe values.
    
    Args:
        circuit_json_path (str): Path to the circuit JSON file.
    
    Returns:
        dict: A dictionary mapping probe register numbers to binary values (0 or 1).
    """
    # Define the path to the chip_config_data directory
    chip_config_dir = os.path.join(os.path.dirname(__file__), "chip_config_data")
    
    # Load the pin-to-switch matrix mapping JSON
    pin_map_path = os.path.join(chip_config_dir, "pin_name_to_sw_matrix_pin_number.json")
    print(f"Looking for pin map file at: {pin_map_path}")
    with open(pin_map_path, 'r') as pin_map_file:
        pin_to_sw_matrix = json.load(pin_map_file)
    
    # Load the switch matrix-to-register mapping JSON
    register_map_path = os.path.join(chip_config_dir, "switch_matrix_register_map.json")
    print(f"Looking for register map file at: {register_map_path}")
    with open(register_map_path, 'r') as register_map_file:
        sw_matrix_to_register = json.load(register_map_file)
    
    # Load the circuit JSON
    with open(circuit_json_path, 'r') as circuit_file:
        circuit_data = json.load(circuit_file)
    
    # Initialize register settings dictionary (probe number to value mapping)
    register_settings = {}
    
    # Iterate through each connection in the circuit JSON
    for bus, entries in circuit_data.items():
        if bus.startswith("RBUS"):
            # Handle RBUS connections
            for pin in entries:
                sw_matrix_pin = pin_to_sw_matrix.get(pin, None)
                if sw_matrix_pin is None:
                    print(f"Warning: Pin '{pin}' not found in pin-to-switch matrix mapping")
                    continue
                
                # Support both numeric and string sw_matrix_pin
                if isinstance(sw_matrix_pin, str):
                    register = sw_matrix_to_register.get(sw_matrix_pin, {}).get(bus, None)
                else:
                    register = sw_matrix_to_register.get(str(int(sw_matrix_pin)), {}).get(bus, None)

                if register is None:
                    print(f"Warning: Register not found for sw_matrix_pin '{sw_matrix_pin}' and bus '{bus}'")
                    continue
                
                # Set this register to 1 (connect to VDD)
                register_settings[int(register)] = 1
                
        elif bus.startswith("SBUS"):
            # Handle SBUS connections
            for entry in entries:
                terminal = entry["terminal"]
                connection = entry["connection"]
                
                # Determine SBUSa and SBUSb keys
                sbus_a = f"{bus}a"
                sbus_b = f"{bus}b"
                
                sw_matrix_pin = pin_to_sw_matrix.get(terminal, None)
                if sw_matrix_pin is None:
                    print(f"Warning: Pin '{terminal}' not found in pin-to-switch matrix mapping")
                    continue
                
                # Support both numeric and string sw_matrix_pin
                if not isinstance(sw_matrix_pin, str):
                    sw_matrix_pin = str(int(sw_matrix_pin))
                
                register_a = sw_matrix_to_register.get(sw_matrix_pin, {}).get(sbus_a, None)
                register_b = sw_matrix_to_register.get(sw_matrix_pin, {}).get(sbus_b, None)
                
                if (register_a is None) or (register_b is None):
                    print(f"Warning: Register not found for sw_matrix_pin '{sw_matrix_pin}' and buses '{sbus_a} and {sbus_b}'")
                    continue
                
                # Decode the type of connection
                if connection == "ON":
                    # Both switches are ON (connected to VDD)
                    register_settings[int(register_a)] = 1
                    register_settings[int(register_b)] = 1
                elif connection == "PHI1":
                    # SBUSa connected to VDD, SBUSb connected to VSS
                    register_settings[int(register_a)] = 1
                    register_settings[int(register_b)] = 0
                elif connection == "PHI2":
                    # SBUSa connected to VSS, SBUSb connected to VDD
                    register_settings[int(register_a)] = 0
                    register_settings[int(register_b)] = 1
                else:  # Default to "OFF"
                    # Both switches are OFF (connected to VSS)
                    register_settings[int(register_a)] = 0
                    register_settings[int(register_b)] = 0
    
    return register_settings

def generate_scan_chain_input(circuit_json_path, sizes_json_path, output_path):
    """
    Generate a text file with binary values for PROBE pins from PROBE<2008> to PROBE<1>.
    
    Args:
        circuit_json_path (str): Path to the circuit JSON file.
        sizes_json_path (str): Path to the JSON file containing device sizes.
        output_path (str): Path to the output text file with binary values.
    """
    # Get probe values from device sizing
    sizing_probe_values = get_device_sizing_probe_values(sizes_json_path)
    
    # Get probe values from switch matrix
    switch_matrix_probe_values = get_switch_matrix_probe_values(circuit_json_path)
    
    # Merge the two dictionaries, with switch matrix values taking precedence
    all_probe_values = {**sizing_probe_values, **switch_matrix_probe_values}
    
    # Create an array with 2008 zeros as default values
    MAX_PROBE_COUNT = 2008
    probe_array = [0] * MAX_PROBE_COUNT
    
    # Fill in the known probe values
    for probe_num, value in all_probe_values.items():
        if 1 <= probe_num <= MAX_PROBE_COUNT:
            probe_array[MAX_PROBE_COUNT - probe_num] = value
    
    # Write the probe values to the output file
    with open(output_path, 'w') as output_file:
        for value in probe_array:
            output_file.write(f"{value}\n")
    
    print(f"Scan chain input file generated at: {output_path}")
    print(f"Total registers set: {len(all_probe_values)}")

def main():
    parser = argparse.ArgumentParser(description="Generate a scan chain input file with binary values for PROBE pins.")
    parser.add_argument("circuit_json", help="Path to the circuit JSON file.")
    parser.add_argument("sizes_json", help="Path to the JSON file containing device sizes.")
    parser.add_argument("output_file", help="Path to the output text file with binary values.")
    
    args = parser.parse_args()
    
    generate_scan_chain_input(
        circuit_json_path=args.circuit_json,
        sizes_json_path=args.sizes_json,
        output_path=args.output_file
    )

if __name__ == "__main__":
    main()