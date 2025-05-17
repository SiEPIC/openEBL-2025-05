''''
Automated merge for the edX Silicon Photonics course
by Lukas Chrostowski, 2014-2025

Run using Python, with import klayout and SiEPIC 

Input:
- folder submissions
- containing files {EBeam*, openEBL_*, ELEC463*, ELEC413*, SiEPIC_Passives*, SiEPIC_Actives*}.{GDS,gds,OAS,oas,py}
Output
- in folder "merge"
-   files: EBeam.oas, EBeam.txt, EBeam.coords

'''


# configuration
tech_name = 'EBeam'
top_cell_name = 'EBeam_2025_05'
cell_Width = 605000
cell_Height = 410000
cell_Gap_Width = 8000
cell_Gap_Height = 8000
chip_Width = 8650000
chip_Height1 = 8490000
chip_Height2 = 8780000
br_cutout_x = 7484000
br_cutout_y = 898000
br_cutout2_x = 7855000
br_cutout2_y = 5063000
tr_cutout_x = [6080e3, 6408e3]
tr_cutout_y = [4549e3, 3148e3]

filename_out = 'EBeam'
layers_keep = ['1/0','1/10', '68/0', '81/0', '10/0', '99/0', '26/0', '31/0', '32/0', '33/0', '998/0']
layer_text = '10/0'
layer_SEM = '200/0'
layer_SEM_allow = ['edXphot1x', 'ELEC413','SiEPIC_Passives']  # which submission folder is allowed to include SEM images
layers_move = [[[31,0],[1,0]]] # move shapes from layer 1 to layer 2
dbu = 0.001
log_siepictools = False
framework_file = 'EBL_Framework_1cm_PCM_static.oas'
ubc_file = 'UBC_static.oas'


# record processing time
import time
start_time = time.time()
from datetime import datetime
now = datetime.now()

# KLayout
import pya
from pya import *

# SiEPIC-Tools
import SiEPIC
from SiEPIC._globals import Python_Env, KLAYOUT_VERSION, KLAYOUT_VERSION_3
from SiEPIC.scripts import zoom_out, export_layout
from SiEPIC.utils import find_automated_measurement_labels
import os


# Output layout
layout = pya.Layout()
layout.dbu = dbu
top_cell = layout.create_cell(top_cell_name)
layerText = pya.LayerInfo(int(layer_text.split('/')[0]), int(layer_text.split('/')[1]))
layerTextN = top_cell.layout().layer(layerText)

def disable_libraries():
    print('Disabling KLayout libraries')
    for l in pya.Library().library_ids():
        print(' - %s' % pya.Library().library_by_id(l).name())
        pya.Library().library_by_id(l).delete()

disable_libraries()

# path for this python file
path = os.path.dirname(os.path.realpath(__file__))

# Log file
global log_file
log_file = open(os.path.join(path,filename_out+'.txt'), 'w')
def log(text):
    global log_file
    log_file.write(text)
    log_file.write('\n')

log('SiEPIC-Tools %s, layout merge, running KLayout 0.%s.%s ' % (SiEPIC.__version__, KLAYOUT_VERSION,KLAYOUT_VERSION_3) )
current_time = now.strftime("%Y-%m-%d, %H:%M:%S local time")
log("Date: %s" % current_time)

# Load all the GDS/OAS files from the "framework" folder:
files_in = []
path2 = os.path.abspath(os.path.join(path,"../framework"))
_, _, files = next(os.walk(path2), (None, None, []))
for f in sorted(files):
    files_in.append(os.path.join(path2,f))

# Load all the GDS/OAS files from the "submissions" folder:
path2 = os.path.abspath(os.path.join(path,"../submissions"))
_, _, files = next(os.walk(path2), (None, None, []))
for f in sorted(files):
    files_in.append(os.path.join(path2,f))

# Create course cells using the folder name under the top cell
cell_edXphot1x = layout.create_cell("edX")
t = Trans(Trans.R0, 0,0)
top_cell.insert(CellInstArray(cell_edXphot1x.cell_index(), t))
cell_ELEC413 = layout.create_cell("ELEC413")
top_cell.insert(CellInstArray(cell_ELEC413.cell_index(), t))
cell_SiEPIC_Passives = layout.create_cell("SiEPIC_Passives")
top_cell.insert(CellInstArray(cell_SiEPIC_Passives.cell_index(), t))
cell_openEBL = layout.create_cell("openEBL")
top_cell.insert(CellInstArray(cell_openEBL.cell_index(), t))

# Create a date	stamp cell, and add a text label
merge_stamp = '.merged:'+now.strftime("%Y-%m-%d-%H:%M:%S")
cell_date = layout.create_cell(merge_stamp)
text = Text (merge_stamp, Trans(Trans.R0, 0, 0) )
shape = cell_date.shapes(layout.layer(10,0)).insert(text)
top_cell.insert(CellInstArray(cell_date.cell_index(), t))   

# Origins for the layouts
x,y = 0,cell_Height+cell_Gap_Height

# Keep track of the width of the cells, for each column
max_cell_Width = 0

import subprocess
import pandas as pd
for f in [f for f in files_in if '.oas' in f[-4:].lower() or '.gds' in f[-4:].lower()]:
    basefilename = os.path.basename(f)

    # GitHub Action gets the actual time committed.  This can be done locally
    # via git restore-mtime.  Then we can load the time from the file stamp

    filedate = datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y%m%d_%H%M")
    log("\nLoading: %s, dated %s" % (os.path.basename(f), filedate))

    # Tried to get it from GitHub but that didn't work:
    # get the time the file was last updated from the Git repository 
    # a = subprocess.run(['git', '-C', os.path.dirname(f), 'log', '-1', '--pretty=%ci',  basefilename], stdout = subprocess.PIPE) 
    # filedate = pd.to_datetime(str(a.stdout.decode("utf-8"))).strftime("%Y%m%d_%H%M")
    #filedate = os.path.getctime(os.path.dirname(f)) # .strftime("%Y%m%d_%H%M")
    
  
    # Load layout  
    layout2 = pya.Layout()
    layout2.read(f)

    if 'elec413' in basefilename.lower():
        course = 'ELEC413'
    elif 'openebl' in basefilename.lower():
        course = 'openEBL'
    elif 'siepic_passives' in basefilename.lower():
        course = 'SiEPIC_Passives'
    elif 'ebeam' in basefilename.lower():
        course = 'edXphot1x'
    else:
        course = 'openEBL'

    cell_course = eval('cell_' + course)
    log("  - course name: %s" % (course) )

    # Check the DBU Database Unit, in case someone changed it, e.g., 5 nm, or 0.1 nm.
    if round(layout2.dbu,10) != dbu:
        log('  - WARNING: The database unit (%s dbu) in the layout does not match the required dbu of %s.' % (layout2.dbu, dbu))
        print('  - WARNING: The database unit (%s dbu) in the layout does not match the required dbu of %s.' % (layout2.dbu, dbu))
        # Step 1: change the DBU to match, but that magnifies the layout
        wrong_dbu = layout2.dbu
        layout2.dbu = dbu
        # Step 2: scale the layout
        try:
            # determine the scaling required
            scaling = round(wrong_dbu / dbu, 10)
            layout2.transform (pya.ICplxTrans(scaling, 0, False, 0, 0))
            log('  - WARNING: Database resolution has been corrected and the layout scaled by %s' % scaling) 
        except:
            print('ERROR IN EBeam_merge.py: Incorrect DBU and scaling unsuccessful')
    
    # check that there is one top cell in the layout
    num_top_cells = len(layout2.top_cells())
    if num_top_cells > 1:
        log('  - layout should only contain one top cell; contains (%s): %s' % (num_top_cells, [c.name for c in layout2.top_cells()]) )
    if num_top_cells == 0:
        log('  - layout does not contain a top cell')

    # Find the top cell
    for cell in layout2.top_cells():
        if os.path.basename(f) == framework_file:
            # Create sub-cell using the filename under top cell
            subcell2 = layout.create_cell(os.path.basename(f)+"_"+filedate)
            t = Trans(Trans.R0, 0,0)
            top_cell.insert(CellInstArray(subcell2.cell_index(), t))
            # copy
            subcell2.copy_tree(layout2.cell(cell.name)) 
            break

        if os.path.basename(f) == ubc_file:
            # Create sub-cell using the filename under top cell
            subcell2 = layout.create_cell(os.path.basename(f)+"_"+filedate)
            t = Trans(Trans.R0, 8780000,8780000)      
            top_cell.insert(CellInstArray(subcell2.cell_index(), t))
            # copy
            subcell2.copy_tree(layout2.cell(cell.name)) 
            break


        if num_top_cells == 1 or cell.name.lower() == 'top' or cell.name.lower() == 'EBeam_':
            log("  - top cell: %s" % cell.name)

            # check layout height
            if cell.bbox().top < cell.bbox().bottom:
                log(' - WARNING: empty layout. Skipping.')
                break
                
            # Create sub-cell using the filename under course cell
            subcell2 = layout.create_cell(os.path.basename(f)+"_"+filedate)
            
            # Clear extra layers
            layers_keep2 = [layer_SEM] if course in layer_SEM_allow else []
            for li in layout2.layer_infos():
                if li.to_s() in layers_keep + layers_keep2:
                    log('  - loading layer: %s' % li.to_s())
                else:
                    log('  - deleting layer: %s' % li.to_s())
                    layer_index = layout2.find_layer(li)
                    layout2.delete_layer(layer_index)
                    
            # Delete non-text geometries in the Text layer
            layer_index = layout2.find_layer(int(layer_text.split('/')[0]), int(layer_text.split('/')[1]))
            if type(layer_index) != type(None):
                s = cell.begin_shapes_rec(layer_index)
                shapes_to_delete = []
                while not s.at_end():
                    if s.shape().is_text():
                        text = s.shape().text.string
                        if text.startswith('SiEPIC-Tools'):
                            if log_siepictools:
                                log('  - %s' % s.shape() )
                            s.shape().delete()
                            subcell2.shapes(layerTextN).insert(pya.Text(text, 0, 0))
                        elif text.startswith('opt_in'):
                            log('  - measurement label: %s' % text )
                    else:
                        shapes_to_delete.append( s.shape() )
                    s.next()
                for s in shapes_to_delete:
                    s.delete()

            # bounding box of the cell
            bbox = cell.bbox()
            log('  - bounding box: %s' % bbox.to_s() )
                            
            # Create sub-cell under subcell cell, using user's cell name
            subcell = layout.create_cell(cell.name)
            t = Trans(Trans.R0, -bbox.left,-bbox.bottom)
            subcell2.insert(CellInstArray(subcell.cell_index(), t))
        
            # clip / crop cells
            cell2 = layout2.clip(cell.cell_index(), pya.Box(bbox.left,bbox.bottom,bbox.left+cell_Width,bbox.bottom+cell_Height))
            bbox2 = layout2.cell(cell2).bbox()
            if bbox != bbox2:
                log('  - WARNING: Cell was clipped to maximum size of %s X %s' % (cell_Width, cell_Height) )
                log('  - clipped bounding box: %s' % bbox2.to_s() )

            # Copy the cropped version
            subcell.copy_tree(layout2.cell(cell2))  

            # Check if this cell would overlap with other Floorplans, then move if necessary

            # Get Floorplan regions for the entire chip so far
            Layer_FP = layout.find_layer(99,0)  # or use "layer"
            iter1 = pya.RecursiveShapeIterator(layout, top_cell, Layer_FP )
            r1 = pya.Region()
            while not iter1.at_end():
                # print("   - %s" % iter1.trans())
                if not iter1.shape().is_text(): 
                    r1.insert(iter1.shape().polygon.transformed(iter1.trans())) 
                iter1.next()        
            r1.merge()

            # Track the maximum width of the cells, for each column
            x_offset = 0
            max_cell_Width = max(max_cell_Width, subcell2.bbox().right + x_offset)
            
            def next_position(x, y, cell_Gap_Height, cell_Gap_Width, chip_Height, cell_Height, cell_Width):
                # Measure the height of the cell that was added, and move up
                y += cell_Gap_Height
                if y + subcell2.bbox().top > chip_Height2:
                    y = 0
                    x += cell_Width + cell_Gap_Width
                    cell_Width = 0
                return x, y, cell_Width

            x,y, max_cell_Width = next_position(x, y, cell_Gap_Height, cell_Gap_Width, chip_Height2, cell_Height, max_cell_Width)
            
            interacting = True
            while interacting:
                r2 = pya.Region(pya.Box(x+x_offset,y, x+x_offset+bbox2.width(),y+bbox2.height()))
                interacting = r2.interacting(r1)
                if interacting:
                    # print("   - Overlapping Floorplan: %s" % r2.interacting(r1))
                    x,y, max_cell_Width = next_position(x, y, cell_Gap_Height, cell_Gap_Width, chip_Height2, cell_Height, max_cell_Width)


            # Insert cell instance in the chip
            t = Trans(Trans.R0, x+x_offset,y)
            cell_course.insert(CellInstArray(subcell2.cell_index(), t))            
            log('  - Placed at position: %s, %s' % (x,y) )
                
            # Measure the height of the cell that was added, and move up
            y += subcell.bbox().height()
            
            '''
            if y + cell_Height > chip_Height1 and x == 0:
                y = cell_Height + cell_Gap_Height
                x += cell_Width + cell_Gap_Width
            if y + cell_Height > chip_Height2:
                y = cell_Height + cell_Gap_Height
                x += cell_Width + cell_Gap_Width
            # check top right cutout for PCM
            for i in range(len(tr_cutout_x)):
                if x + cell_Width > tr_cutout_x[i] and y + cell_Height > tr_cutout_y[i]:
                    # go to the next column
                    y = cell_Height + cell_Gap_Height    
                    x += cell_Width + cell_Gap_Width
            # Check bottom right cutout for PCM
            if x + cell_Width > br_cutout_x and y < br_cutout_y:
                y = br_cutout_y
            # Check bottom right cutout #2 for PCM
            if x + cell_Width > br_cutout2_x and y < br_cutout2_y:
                y = br_cutout2_y
            '''


# move layers
for i in range(0,len(layers_move)):
    layer1=layout.find_layer(*layers_move[i][0])
    layer2=layout.find_layer(*layers_move[i][1])
    layout.move_layer(layer1, layer2)

# Export as-is layout, for UW fabrication
log('')

#export_layout (top_cell, path, filename='EBeam', relative_path='', format='gds')
file_out = export_layout (top_cell, path, filename='EBeam', relative_path='', format='oas')
# log("Layout exported successfully %s: %s" % (save_options.format, file_out) )


log("\nExecution time: %s seconds" % int((time.time() - start_time)))

log_file.close()

# Display the layout in KLayout, using KLayout Package "klive", which needs to be installed in the KLayout Application
try:
    if Python_Env == 'Script':
        from SiEPIC.utils import klive
        klive.show(file_out, technology=tech_name)
except:
    pass
 

# Create an image of the layout
import siepic_ebeam_pdk
layout.technology_name = 'EBeam'
top_cell.image(os.path.join(path,'EBeam.png'))

print("KLayout EBeam_merge.py, completed in: %s seconds" % int((time.time() - start_time)))


