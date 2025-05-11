import json
import os
from datetime import datetime

def generate_nodes_subckt(circuit_file, output_spice_file):
    """
    Generates a SPICE subcircuit file connecting chip pins to NODE nodes.

    Args:
        circuit_file (str): Path to the circuit JSON file.
        output_spice_file (str): Path to the output SPICE netlist file.
    """
    # Define the paths to the necessary support files
    chip_config_dir = os.path.join(os.path.dirname(__file__), "chip_config_data")
    pin_mapping_file = os.path.join(chip_config_dir, "pin_name_to_number.json")
    subckt_template_file = os.path.join(os.path.dirname(__file__), "..", "subckt_templates", "PK_NODE_external_connections_template.cir")

    print(f"Looking for pin mapping file at: {pin_mapping_file}")
    print(f"Looking for template file at: {subckt_template_file}")

    # Load the circuit JSON file
    with open(circuit_file, "r") as f:
        circuit_data = json.load(f)

    # Load the pin mapping JSON file
    with open(pin_mapping_file, "r") as f:
        pin_name_to_number = json.load(f)

    # Start building the SPICE subcircuit
    spice_subcircuit = f"* File created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    spice_subcircuit += f"* From {circuit_file}\n\n"

    # Read the SPICE template
    with open(subckt_template_file, "r") as f:
        spice_template = f.read()
    spice_subcircuit += spice_template + "\n"

    # Handle VDD connections (pin 13)
    for pin_name in circuit_data.get('VDD', []):
        pin_number = pin_name_to_number.get(pin_name)
        if pin_number is not None:
            spice_subcircuit += f"* {pin_name} connected to VDD\n"
            spice_subcircuit += f"Vshort_VDD_{pin_name} pin<{int(pin_number)}> pin<13> 0\n"
        else:
            print(f"Warning: Pin name '{pin_name}' not found in pin mapping")

    # Handle VSS connections (pin 1)
    for pin_name in circuit_data.get('VSS', []):
        pin_number = pin_name_to_number.get(pin_name)
        if pin_number is not None:
            spice_subcircuit += f"* {pin_name} connected to VSS\n"
            spice_subcircuit += f"Vshort_VSS_{pin_name} pin<{int(pin_number)}> pin<1> 0\n"
        else:
            print(f"Warning: Pin name '{pin_name}' not found in pin mapping")

    # Handle other nodes
    for node, pin_names in circuit_data.items():
        if node in ['VDD', 'VSS']:
            continue

        # Extract the node number (e.g., NODE<1> -> 1)
        try:
            node_number = int(node.replace("NODE", "").strip("<>"))
        except ValueError:
            print(f"Warning: Invalid node format '{node}', expected NODE<n>")
            continue

        # Iterate through the pin names connected to this node
        for pin_name in pin_names:
            pin_number = pin_name_to_number.get(pin_name)
            if pin_number is not None:
                spice_subcircuit += f"* {pin_name} connected to NODE<{node_number}>\n"
                spice_subcircuit += f"Vshort_NODE_{node_number}_{pin_name} NODE<{node_number}> pin<{int(pin_number)}> 0\n"
            else:
                print(f"Warning: Pin name '{pin_name}' not found in pin mapping")

    # Close the subcircuit
    spice_subcircuit += ".ENDS\n"

    # Write the generated SPICE subcircuit to the output file
    with open(output_spice_file, "w") as f:
        f.write(spice_subcircuit)

    print(f"SPICE subcircuit saved to {output_spice_file}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate a SPICE subcircuit connecting pins to NODEs.")
    parser.add_argument("circuit_file", help="Path to the circuit JSON file.")
    parser.add_argument("output_spice_file", help="Path to the output SPICE netlist file.")

    args = parser.parse_args()

    generate_nodes_subckt(
        circuit_file=args.circuit_file,
        output_spice_file=args.output_spice_file
    )

if __name__ == "__main__":
    main()
