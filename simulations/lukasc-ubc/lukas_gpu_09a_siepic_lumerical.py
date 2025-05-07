#%%
"""
Simulation of a halfring device using lumerical.
@author: Mustafa Hammood
"""


import os
import sys
# Required packages

from datetime import datetime
start = datetime.now()

def pip_install(package, module=None):
    ''' pip install packages, e.g.,
    pip_install('siepic', 'SiEPIC')
    pip_install('gds_fdtd')
    '''
    import importlib
    try:
        if module:
            importlib.import_module(module)
        else:
            importlib.import_module(package)
    except ImportError:
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", package])
        print(result)
        if module:
            importlib.import_module(module)
        else:
            importlib.import_module(package)
    if module:
        globals()[package] = importlib.import_module(module)
    else:
        globals()[package] = importlib.import_module(package)
    return globals()[package]
    
pip_requirements = [
                    'siepic_ebeam_pdk',
                    'gds_fdtd']
for p in pip_requirements:
    package = pip_install(p)
    if not package:
        print(f' - missing {p}')
    else:
        print(f'Python package: {package.__file__}')

'''
try:
    import gds_fdtd
except:
    # Import gds-fdtd from GitHub repository, installed locally
    file_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),"gds_fdtd")
    if not os.path.exists(file_dir):
        #import sys
        #result = subprocess.run([sys.executable, "-c", "print('ocean')"])
        result = subprocess.run(["git", "clone", "https://github.com/SiEPIC/gds_fdtd.git"])
        print(result)
        result = subprocess.run(["pwd"])
        print(result)
    # Add the directory to sys.path
    # sys.path.append(current_file_dir)
    # Alternatively, insert at the beginning of sys.path
    sys.path.insert(0, file_dir)
    import gds_fdtd
print(gds_fdtd)    
print(gds_fdtd.__file__)    
'''

       
from gds_fdtd.simprocessor import load_component_from_tech
from gds_fdtd.core import parse_yaml_tech
from gds_fdtd.lum_tools import make_sim_lum
import siepic_ebeam_pdk as pdk 
from pya import Layout
from lumapi import FDTD

if __name__ == "__main__":
    
    # Parameters
    pcell_params = {
        'r': 3,     # Radius, in microns
        'w': 0.5,   # Waveguie width, in microns
        'g': 0.1,   # Gap beween the bus waveguide and halfring waveguide
        'Lc':0,     # Directional coupler length
    }
    expected_process_bias = -0.002  # reduction by 2 nm on each side
    pcell_params['w'] += 2*expected_process_bias
    pcell_params['g'] += -2*expected_process_bias
    
    # Technology details for simulations (thicknesses, materials)
    tech_yaml = '''
technology:
  name: "EBeam"

  substrate:
      z_base: 0.0
      z_span: -2
      material:
        lum_db:
          model: SiO2 (Glass) - Palik

  superstrate:
      z_base: 0.0
      z_span: 3
      material:
        lum_db:
          model: SiO2 (Glass) - Palik
  
  pinrec:
    - layer: [1, 10]

  devrec:
    - layer: [68, 0]

  device:
    - layer: [1, 0]
      z_base: 0.0
      z_span: 0.22
      material:
        lum_db:
          model: Si (Silicon) - Palik
      sidewall_angle: 88

    - layer: [4, 0]
      z_base: .3
      z_span: 0.4
      material:
        lum_db:
          model: Si3N4 (Silicon Nitride) - Luke
      sidewall_angle: 83
'''    
    with open('tech.yml', 'w') as outfile:
        outfile.write(tech_yaml)
    technology = parse_yaml_tech('tech.yml')

    '''
    subfolder = os.path.splitext(os.path.basename(__file__))[0]
    tech_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), subfolder, "gds_fdtd/examples/tech_lumerical.yaml")
    technology = parse_yaml_tech(tech_path)
    '''
    
    # load cell from siepic_ebeam_pdk
    ly = Layout()
    ly.technology_name = pdk.tech.name
    cell = ly.create_cell("ebeam_dc_halfring_straight", "EBeam", pcell_params)
    
    # Save the GDS and an image of the cell
    cell.write('layout.gds')
    cell.image('layout.png')

    # simulate with lumerical
    component = load_component_from_tech(cell=cell, tech=technology)
    sparam = make_sim_lum(
        c=component,
        lum=FDTD(),
        wavl_min=1.45,
        wavl_max=1.65,
        wavl_pts=11,
        width_ports=4.0,
        depth_ports=4.0,
        symmetry=(0, 0, 0),
        pol="TE",
        num_modes=1,
        boundary="pml",
        mesh=1,
        run_time_factor=50,
        gpu=True, 
        visualize=False,
        export_plot_file = 'sparam.png',)
    
    print(sparam)
    
    #import yaml
    #with open('sparam.yml', 'w') as outfile:
    #    yaml.dump(sparam, outfile, default_flow_style=False)
    
    print(f'done in {datetime.now()-start}')

# %%