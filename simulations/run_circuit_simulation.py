import sys
import os

import klayout.db as pya
from SiEPIC.utils import get_layout_variables
#from SiEPIC.utils.layout import find_opt_in_labels
from SiEPIC.opics_netlist_sim import circuit_simulation_opics

import siepic_ebeam_pdk

def main(file_gds):

    # Load GDS file
    #file_gds = "/Users/lukasc/Documents/GitHub/openEBL-2025-05/submissions/EBeam_LukasChrostowski_MZI.oas"
    layout = pya.Layout()
    layout.read(file_gds)
    top_cell = layout.top_cell()
    tech_name = "EBeam"
    # Set the layout's technology to match the PDK
    layout.technology_name = tech_name

    # Access layer 10/0
    layer_index = layout.layer(pya.LayerInfo(10, 0))

    # Extract opt-in labels
    opt_in_labels = []
    for shape in top_cell.shapes(layer_index).each():
        if shape.is_text():
            label_text = shape.text.string
            if "opt_in" in label_text:
                opt_in_labels.append(label_text)

    print(f"Found {len(opt_in_labels)} opt-in labels: {opt_in_labels}")

    # Extract base path and filename (without extension)
    base_dir = os.path.dirname(file_gds)
    base_name = os.path.splitext(os.path.basename(file_gds))[0]



    # Run simulation for each label
    for label_text in opt_in_labels:
        # Compose output PNG path
        output_png = os.path.join(base_dir, f"{base_name}_{label_text}.png")
        print(f"\nRunning simulation for {label_text}")
        try:
            circuit_simulation_opics(
                topcell=top_cell,
                opt_in_selection_text=[label_text],
                verbose=False,
                save_file = output_png
            )
        except Exception as e:
            print(f"Error for {label_text}: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_circuit_simulation.py <file_gds.oas/gds>")
        sys.exit(1)

    file_gds = sys.argv[1]
    if not os.path.exists(file_gds):
        print(f"File not found: {file_gds}")
        sys.exit(1)

    main(file_gds)
