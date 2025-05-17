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
Script to load .gds file passed in through commmand line and run verification using layout_check().
Ouput lyrdb file is saved to path specified by 'file_lyrdb' variable in the script.

Jasmina Brar 12/08/23, and Lukas Chrostowski

"""

# gds file to run verification on
gds_file = sys.argv[1]

print('')
print('')
print('')
print('')
print('Running SiEPIC-Tools automated verification for file %s' % gds_file)

try:
   # load into layout
   layout = pya.Layout()
   layout.read(gds_file)
except:
   print('Error loading layout')
   num_errors = 1


import klayout.db as pya

def top_cell_with_most_subcells_or_shapes(layout):
   """
   Returns the top cell that contains the most subcells or the most shapes in a KLayout layout.

   :param layout: pya.Layout object
   :return: The top cell with the most subcells or shapes
   
   by ChatGPT
   """
   top_cells = layout.top_cells()

   if not top_cells:
      return None

   if len(top_cells) == 1:
      return layout.top_cell()

   max_subcells = -1
   best_cell = None

   for top_cell in top_cells:
      subcell_count = sum(1 for _ in top_cell.each_child_cell())  # Count subcells

      # Prioritize by subcells first, then shapes if there's a tie
      if subcell_count > max_subcells:
         max_subcells = subcell_count
         best_cell = top_cell

   print (f' - found multiple top cells: {[c.name for c in top_cells]}, chose {best_cell.name}')
   return best_cell

# Example usage
# layout = pya.Layout()  # Load your layout
# top_cell = top_cell_with_most_subcells_or_shapes(layout)
# if top_cell:
#     print(f"Top cell with most subcells/shapes: {top_cell.name}")


try:
   # get top cell from layout
   top_cell = top_cell_with_most_subcells_or_shapes(layout)
   
   if not top_cell:
      print('No top cell in the layout')
   else:
      print('Top cell: %s' % top_cell.name)

   # set layout technology because the technology seems to be empty, and we cannot load the technology using TECHNOLOGY = get_technology() because this isn't GUI mode
   # refer to line 103 in layout_check()
   # tech = layout.technology()
   # print("Tech:", tech.name)
   layout.TECHNOLOGY = get_technology_by_name('EBeam')

   # get file path, filename, path for output lyrdb file
   path = os.path.dirname(os.path.realpath(__file__))
   filename = gds_file.split(".")[0]
   file_lyrdb = os.path.join(path,filename+'.lyrdb')

   # run verification
   num_errors = layout_check(cell = top_cell, verbose=False, GUI=True, file_rdb=file_lyrdb)

except:
   print('Unknown error occurred')
   num_errors = 1

# Print the result value to standard output
print(num_errors)

