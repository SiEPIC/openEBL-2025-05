import pya
from pya import *
import SiEPIC
from SiEPIC.verification import layout_check
from SiEPIC.scripts import zoom_out
from SiEPIC.utils import get_technology_by_name
import siepic_ebeam_pdk
import os
import sys
"""
Script to load .gds file passed in through commmand line and run submission checks:
- layout floorplan dimensions
- number of top cells
- check for Black box cells

Jasmina Brar 12/08/23, and Lukas Chrostowski, 2025/02

"""

# Allowed BB cells:
bb_cells = [
        'ebeam_gc_te1550',
        'ebeam_gc_tm1550',
        'GC_TE_1550_8degOxide_BB', 
        'GC_TM_1550_8degOxide_BB', 
        'ebeam_gc_te1310', 
        'ebeam_gc_te1310_8deg', 
        'GC_TE_1310_8degOxide_BB', 
        'ebeam_GC_TM_1310_8degOxide',
        'GC_TM_1310_8degOxide_BB',
        'GC_TM_1310_8degOxide_BB$1', 
        'ebeam_splitter_swg_assist_te1310', 
        'ebeam_splitter_swg_assist_te1550',
        'ebeam_dream_splitter_1x2_te1550_BB',
]


# gds file to run verification on
if len(sys.argv) > 1:
   gds_file = sys.argv[1]
else:
   print('run this script by passing the file name as parameter')
   print('running as a demo using submissions/EBeam_LukasChrostowski_MZI.oas')
   gds_file = "submissions/EBeam_LukasChrostowski_MZI.oas"

print('')
print('')
print('')
print('')
print('Running submission checks for file %s' % gds_file)


from SiEPIC.scripts import replace_cell, cells_containing_bb_layers    

import xml.etree.ElementTree as ET

def extract_sources_from_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    sources = []
    for source in root.iter('source'):
        text = source.text
        if text:
            parts = text.split('@')[0].split('/')
            if len(parts) >= 2:
                try:
                    values = [int(parts[0]), int(parts[1])]
                    sources.append(values)
                except ValueError:
                    continue  # Skip non-integer entries
    return sources



def check():
   
   
   try:
      # load into layout
      layout = pya.Layout()
      layout.read(gds_file)
      num_errors = 0
      
   except:
      print('Error loading layout')
      print(f' file: {gds_file}')
      print(f' files in the folder: {os.listdir(os.path.dirname(gds_file))}')
      num_errors = 1
      return num_errors


   try:
      # get top cell from layout
      if len(layout.top_cells()) != 1:
         print('Error: layout does not have 1 top cell. It has %s.' % len(layout.top_cells()))
         print(f' - cells: {[c.name for c in layout.each_cell()]}')
         print(f' - file size: {os.path.getsize(gds_file)}')
         num_errors += 1
         return num_errors

      top_cell = layout.top_cell()

      # set layout technology because the technology seems to be empty, and we cannot load the technology using TECHNOLOGY = get_technology() because this isn't GUI mode
      # refer to line 103 in layout_check()
      # tech = layout.technology()
      # print("Tech:", tech.name)
      layout.TECHNOLOGY = get_technology_by_name('EBeam')

      # Make sure layout extent fits within the allocated area.
      cell_Width = 605000
      cell_Height = 410000

      # Define the layers of interest
      layers_of_interest = [(1, 0), (4, 0)]

      # Initialize an empty bounding box
      combined_bbox = pya.Region()
      
      # Loop through layers and merge bounding boxes
      for layer_num, layer_dt in layers_of_interest:
         layer_index = layout.find_layer(pya.LayerInfo(layer_num, layer_dt))
         # print(f'layer: {layer_num} / {layer_dt} - {layer_index}')
         if layer_index == None:
            continue  # layer not found, skip
         bbox = top_cell.bbox_per_layer(layer_index)
         # print(bbox)
         combined_bbox += pya.Region(bbox)

      combined_bbox.merge()
         
      if combined_bbox:
         w = combined_bbox.bbox().width()
         h = combined_bbox.bbox().height()
         if w > cell_Width or h > cell_Height:
            print("Error: Bounding box of selected layers (%.3f µm x %.3f µm) exceeds allowed size %.3f µm x %.3f µm" %
                  (w / 1000, h / 1000,
                     cell_Width / 1000, cell_Height / 1000))
            num_errors += 1
         else:
            print("Bounding box of selected layers is %.3f µm x %.3f µm" %
                  (w / 1000, h / 1000))
      else:
         print("No shapes found in the specified layers.")
         num_errors += 1


      # Check black box cells, by replacing them with an empty cell, 
      # then checking if there are any BB geometries left over
      dummy_layout = pya.Layout()
      dummy_cell = dummy_layout.create_cell("dummy_cell")
      dummy_file = "dummy_cell.gds"
      dummy_cell.write(dummy_file)
      bb_count = 0
      print ('Performing Black Box cell replacement check')
      for i in range(len(bb_cells)):
         text_out, count, error = replace_cell(layout, 
               cell_x_name = bb_cells[i], 
               cell_y_name = dummy_cell.name, 
               cell_y_file = dummy_file, 
               Exact = False, RequiredCharacter='$',
               run_layout_diff = False,
               debug = False,)
         if count and count > 0:
            bb_count += count
            print(' - black box cell: %s' % bb_cells[i])
      print (' - Number of black box cells to be replaced: %s' % bb_count)

      cells_bb = cells_containing_bb_layers(top_cell, BB_layerinfo=pya.LayerInfo(998,0), verbose=False)
      print(' - Number of unreplaced BB cells: %s' % len(cells_bb))
      if len(cells_bb) > 0:
         print(' - Names of unreplaced BB cells: %s' % set(cells_bb))
         print('ERROR: unidentified black box cells. Please ensure that the design only uses cells contained in the PDK: https://github.com/SiEPIC/SiEPIC_EBeam_PDK. Also ensure that the cells have not been modified in any way (rotations, origin changes, resizing, renaming).')
      num_errors += len(cells_bb)
      

   except:
      print('Runtime exception.')
      if num_errors == 0:
         num_errors = 1

   layout.technology_name = 'EBeam'
   pdk_layers = extract_sources_from_xml(layout.technology().eff_layer_properties_file())
   for l in layout.layer_infos():
      if [l.layer,l.datatype] not in pdk_layers:
         print (f'Error: the layer {l} in the design is not defined in the PDK.')
         num_errors += 1


   return num_errors

if __name__ == "__main__":
   # run checks
   num_errors = check()
   # Print the result value to standard output
   print(num_errors)

