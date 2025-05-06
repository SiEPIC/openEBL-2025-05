'''
--- Simple MZI ---
  
by Lukas Chrostowski, 2020-2025 
 
 
 
Example simple script to
 - choose the fabrication technology provided by Applied Nanotools, using silicon (Si) waveguides
 - use the SiEPIC-EBeam-PDK technology
 - using KLayout and SiEPIC-Tools, with function including connect_pins_with_waveguide and connect_cell
 - create a new layout with a top cell, limited a design area of 605 microns wide by 410 microns high.
 - create three Mach-Zehnder Interferometer (MZI) circuits
   Two Mach-Zehnders have a small path length difference, while the other uses a very long spiral to provide a large path length difference and therefore a small free-spectral range (FSR).
 - export to OASIS for submission to fabrication

using SiEPIC-Tools function including connect_pins_with_waveguide and connect_cell

Use instructions:

Run in Python, e.g., VSCode

pip install required packages:
 - klayout, SiEPIC, siepic_ebeam_pdk, numpy

'''

designer_name = 'LukasChrostowski'
top_cell_name = 'EBeam_%s_MZI' % designer_name
export_type = 'static'  # static: for fabrication, PCell: include PCells in file

import pya
from pya import Trans, CellInstArray, Text

import SiEPIC
from SiEPIC._globals import Python_Env
from SiEPIC.scripts import connect_cell, connect_pins_with_waveguide, zoom_out, export_layout
from SiEPIC.utils import create_cell2
from SiEPIC.utils.layout import new_layout, floorplan, coupler_array
from SiEPIC.extend import to_itype
from SiEPIC.verification import layout_check

import os

if Python_Env == 'Script':
    try:
        # For external Python mode, when installed using pip install siepic_ebeam_pdk
        import siepic_ebeam_pdk
    except:
        # Load the PDK from a folder, e.g, GitHub, when running externally from the KLayout Application
        import os, sys
        path_GitHub = os.path.expanduser('~/Documents/GitHub/')
        sys.path.insert(0,os.path.join(path_GitHub, 'SiEPIC_EBeam_PDK/klayout'))
        import siepic_ebeam_pdk

tech_name = 'EBeam'

from packaging import version
if version.parse(SiEPIC.__version__) < version.parse("0.5.4"):
    raise Exception("Errors", "This example requires SiEPIC-Tools version 0.5.4 or greater.")


'''
Create a new layout using the EBeam technology,
with a top cell
and Draw the floor plan
'''    
cell, ly = new_layout(tech_name, top_cell_name, GUI=True, overwrite = True)
floorplan(cell, 605e3, 410e3)

dbu = ly.dbu

from SiEPIC.scripts import connect_pins_with_waveguide, connect_cell
waveguide_type='Strip TE 1550 nm, w=500 nm'
waveguide_type_delay='Si routing TE 1550 nm (compound waveguide)'

# Load cells from library
# SiEPIC create_cell2 is an enhanced version (with error checking) of pya.Layout.create_cell
cell_ebeam_gc = create_cell2(ly, 'GC_TE_1550_8degOxide_BB', tech_name)
cell_ebeam_y = create_cell2(ly, 'ebeam_y_1550', tech_name)

# grating couplers, place at absolute positions
# automated test label
x,y = 60000, 15000
instGC = coupler_array(cell, 
         cell_name = 'GC_TE_1550_8degOxide_BB',
         cell_library = tech_name,
         x_offset = x, y_offset = y,
         label = "opt_in_TE_1550_device_%s_MZI1" % designer_name,
         #cell_params = None,
         count = 2,
         )    

# Y branches:
# Approach #1: place it at an absolute position:
t = Trans.from_s('r0 %s, %s' % (x+20000,y))
instY1 = cell.insert(CellInstArray(cell_ebeam_y.cell_index(), t))

# Approach #2: attach it to an existing component, then move relative
instY2 = connect_cell(instGC[0], 'opt1', cell_ebeam_y, 'opt1')
instY2.transform(Trans(20000,-10000))

# Waveguides:
connect_pins_with_waveguide(instGC[1], 'opt1', instY1, 'opt1', waveguide_type=waveguide_type)
connect_pins_with_waveguide(instGC[0], 'opt1', instY2, 'opt1', waveguide_type=waveguide_type)
connect_pins_with_waveguide(instY1, 'opt2', instY2, 'opt3', waveguide_type=waveguide_type)
connect_pins_with_waveguide(instY1, 'opt3', instY2, 'opt2', waveguide_type=waveguide_type,turtle_B=[25,-90])

# 2nd MZI
# grating couplers, place at absolute positions
x,y = 180000, 15000
instGC = coupler_array(cell, 
         cell_name = 'GC_TE_1550_8degOxide_BB',
         cell_library = tech_name,
         x_offset = x, y_offset = y,
         label = "opt_in_TE_1550_device_%s_MZI2" % designer_name,
         #cell_params = None,
         count = 2,
         )    

# Y branches:
instY1 = connect_cell(instGC[1], 'opt1', cell_ebeam_y, 'opt1')
instY1.transform(Trans(20000,0))
instY2 = connect_cell(instGC[0], 'opt1', cell_ebeam_y, 'opt1')
instY2.transform(Trans(20000,0))

# Waveguides:

connect_pins_with_waveguide(instGC[1], 'opt1', instY1, 'opt1', waveguide_type=waveguide_type)
connect_pins_with_waveguide(instGC[0], 'opt1', instY2, 'opt1', waveguide_type=waveguide_type)
connect_pins_with_waveguide(instY1, 'opt2', instY2, 'opt3', waveguide_type=waveguide_type)
connect_pins_with_waveguide(instY1, 'opt3', instY2, 'opt2', waveguide_type=waveguide_type,turtle_B=[125,-90])

# 3rd MZI, with a very long delay line
cell_ebeam_delay = ly.create_cell('spiral_paperclip', 'EBeam_Beta',
                                  {'waveguide_type':waveguide_type_delay,
                                   'length':130,
                                   'loops':12,
                                   'flatten':True})
x,y = 60000, 265000
instGC = coupler_array(cell, 
         cell_name = 'GC_TE_1550_8degOxide_BB',
         cell_library = tech_name,
         x_offset = x, y_offset = y,
         label = "opt_in_TE_1550_device_%s_MZI3" % designer_name,
         count = 2,
         )    

# Y branches:
instY1 = connect_cell(instGC[1], 'opt1', cell_ebeam_y, 'opt1')
instY1.transform(Trans(20000,0))
instY2 = connect_cell(instGC[0], 'opt1', cell_ebeam_y, 'opt1')
instY2.transform(Trans(20000,0))

# Spiral:
instSpiral = connect_cell(instY2, 'opt2', cell_ebeam_delay, 'optA')
instSpiral.transform(Trans(20000,0))

# Waveguides:
connect_pins_with_waveguide(instGC[1], 'opt1', instY1, 'opt1', waveguide_type=waveguide_type)
connect_pins_with_waveguide(instGC[0], 'opt1', instY2, 'opt1', waveguide_type=waveguide_type)
connect_pins_with_waveguide(instY1, 'opt2', instY2, 'opt3', waveguide_type=waveguide_type)
connect_pins_with_waveguide(instY2, 'opt2', instSpiral, 'optA', waveguide_type=waveguide_type)
connect_pins_with_waveguide(instY1, 'opt3', instSpiral, 'optB', waveguide_type=waveguide_type,turtle_B=[5,-90])

# Zoom out
zoom_out(cell)

# Export for fabrication, removing PCells
path = os.path.dirname(os.path.realpath(__file__))
filename = os.path.splitext(os.path.basename(__file__))[0]
if export_type == 'static':
    file_out = export_layout(cell, path, filename, relative_path = '..', format='oas', screenshot=True)
else:
    file_out = os.path.join(path,'..',filename+'.oas')
    ly.write(file_out)

# Verify
file_lyrdb = os.path.join(path,filename+'.lyrdb')
num_errors = layout_check(cell = cell, verbose=False, GUI=True, file_rdb=file_lyrdb)
print('Number of errors: %s' % num_errors)

# Create an image of the layout
# cell.image(os.path.join(path,filename+'.png'))   

# Display the layout in KLayout, using KLayout Package "klive", which needs to be installed in the KLayout Application
if Python_Env == 'Script':
    if version.parse(SiEPIC.__version__) > version.parse("0.5.16"):
        cell.show(lyrdb_filename=file_lyrdb)
    else:
        from SiEPIC.utils import klive
        klive.show(file_out, lyrdb_filename=file_lyrdb, technology=tech_name)
