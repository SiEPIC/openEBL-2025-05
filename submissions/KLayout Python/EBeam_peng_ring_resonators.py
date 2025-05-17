# $description: Double-bus ring resonator sweep (EBeam)
# $show-in-menu
# $group-name: Examples_EBeam
# $menu-path: siepic_menu.exlayout.begin
  
"""
Scripted layout for ring resonators using KLayout and SiEPIC-Tools
in the SiEPIC-EBeam-PDK "EBeam" technology

by Lukas Chrostowski, 2020-2025
"""

import SiEPIC
from packaging import version
if version.parse(SiEPIC.__version__) < version.parse("0.5.1"):
    raise Exception('This example requires SiEPIC-Tools version 0.5.1 or greater.')
import os
import pya
from pya import Trans, CellInstArray, Text
from SiEPIC._globals import Python_Env
from SiEPIC.scripts import export_layout
from SiEPIC.verification import layout_check


class ring_layout():

    def __init__(self):
        
        # Designer name
        username = 'peng'
        
        # Configure parameter sweep
        self.sweep_radius = [3, 5, 10, 10] # microns
        self.sweep_gap = [0.07, 0.07, 0.07, 0.10] # microns
        
        # Waveguide parameters
        self.pol = "TE" # polarization
        self.wg_bend_radius = 5 # microns
        self.wg_width = 0.5 # microns

        # Layout parameters
        self.filename = f'EBeam_{username}_ring_resonators'
        self.x_offset = 11  # horizontal spacing between the designs

    def layout(self):
        '''Create a layout for testing a double-bus ring resonator.
        uses:
         - the SiEPIC EBeam Library
        creates the layout in the presently selected cell
        deletes everything first
        '''

        print("SiEPIC_EBeam_PDK: Example - EBeam_ring_resonators.py")

        if Python_Env == "Script":
            # For external Python mode, when installed using pip install siepic_ebeam_pdk
            import siepic_ebeam_pdk
        self.tech_name = "EBeam"

        # Import functions from SiEPIC-Tools
        from SiEPIC.extend import to_itype
        from SiEPIC.scripts import connect_cell, connect_pins_with_waveguide
        from SiEPIC.utils.layout import new_layout, floorplan

        """
        Create a new layout using the EBeam technology,
        with a top cell
        and Draw the floor plan
        """
        self.top_cell, self.ly = new_layout(self.tech_name, self.filename, GUI=True, overwrite=True)
        top_cell, ly = self.top_cell, self.ly
        floorplan(top_cell, 605e3, 410e3)

        # Layer mapping:
        LayerSiN = ly.layer(ly.TECHNOLOGY["Si"])
        fpLayerN = ly.layer(ly.TECHNOLOGY["FloorPlan"])
        TextLayerN = ly.layer(ly.TECHNOLOGY["Text"])

        # Create a sub-cell for our Ring resonator layout
        dbu = ly.dbu
        cell = top_cell.layout().create_cell("RingResonator")
        t = Trans(Trans.R0, 40 / dbu, 12 / dbu)

        # place the cell in the top cell
        top_cell.insert(CellInstArray(cell.cell_index(), t))

        # Import cell from the SiEPIC EBeam Library
        cell_ebeam_gc = ly.create_cell("GC_%s_1550_8degOxide_BB" % self.pol, "EBeam")
        # get the length of the grating coupler from the cell
        gc_length = cell_ebeam_gc.bbox().width() * dbu
        # spacing of the fibre array to be used for testing
        GC_pitch = 127

        # Loop through the parameter sweep
        for i in range(len(self.sweep_gap)):
            # place layout at location:
            if i == 0:
                x = 0
            else:
                # next device is placed at the right-most element + length of the grating coupler
                x = inst_dc2.bbox().right * dbu + gc_length + self.x_offset

            # get the parameters
            r = self.sweep_radius[i]
            g = self.sweep_gap[i]

            # Grating couplers, Ports 0, 1, 2, 3 (from the bottom up)
            instGCs = []
            for i in range(0, 4):
                t = Trans(Trans.R0, to_itype(x, dbu), i * 127 / dbu)
                instGCs.append(cell.insert(CellInstArray(cell_ebeam_gc.cell_index(), t)))

            # Label for automated measurements, laser on Port 2, detectors on Ports 1, 3, 4
            t = Trans(Trans.R90, to_itype(x, dbu), to_itype(GC_pitch * 2, dbu))
            text = Text(
                "opt_in_%s_1550_device_RingDouble%sr%sg%s"
                % (self.pol.upper(), self.pol.upper(), int(round(r*1000)), int(round(g * 1000))),
                t,
            )
            text.halign = 1
            cell.shapes(TextLayerN).insert(text).text_size = 5 / dbu

            # Ring resonator from directional coupler PCells
            cell_dc = ly.create_cell(
                "ebeam_dc_halfring_straight",
                "EBeam",
                {"r": r, "w": self.wg_width, "g": g, "bustype": 0},
            )
            y_ring = GC_pitch * 3 / 2
            # first directional coupler
            t1 = Trans(Trans.R270, to_itype(x + self.wg_bend_radius, dbu), to_itype(y_ring, dbu))
            inst_dc1 = cell.insert(CellInstArray(cell_dc.cell_index(), t1))
            # add 2nd directional coupler, snapped to the first one
            inst_dc2 = connect_cell(inst_dc1, "pin2", cell_dc, "pin4")

            # Create paths for waveguides, with the type defined in WAVEGUIDES.xml in the PDK
            waveguide_type = "Strip TE 1550 nm, w=500 nm"

            # GC1 to bottom-left of ring pin3
            connect_pins_with_waveguide(
                instGCs[1], "opt1", inst_dc1, "pin3", waveguide_type=waveguide_type
            )

            # GC2 to top-left of ring pin1
            connect_pins_with_waveguide(
                instGCs[2], "opt1", inst_dc1, "pin1", waveguide_type=waveguide_type
            )

            # GC0 to top-right of ring
            connect_pins_with_waveguide(
                instGCs[0], "opt1", inst_dc2, "pin1", waveguide_type=waveguide_type
            )

            # GC3 to bottom-right of ring
            connect_pins_with_waveguide(
                instGCs[3], "opt1", inst_dc2, "pin3", waveguide_type=waveguide_type
            )

        # Introduce an error, to demonstrate the Functional Verification
        # inst_dc2.transform(Trans(1000, -1000))

        return ly, top_cell

    def export(self):
        
        # Save
        path = os.path.dirname(os.path.realpath(__file__))
        file_out = export_layout(
            self.top_cell, path, self.filename, relative_path="..", format="oas", screenshot=True
        )

        print(" - verification")
        file_lyrdb = os.path.join(path, self.filename + ".lyrdb")
        num_errors = layout_check(cell=self.top_cell, verbose=False, GUI=True, file_rdb=file_lyrdb)

        if Python_Env == "Script":
            from SiEPIC.utils import klive
            klive.show(file_out, lyrdb_filename=file_lyrdb, technology=self.tech_name)

        print(" - done")

if __name__ == "__main__":
    
    # initialize
    r = ring_layout()
    
    # create the layout
    r.layout()
    
    # export the layout
    r.export()
    