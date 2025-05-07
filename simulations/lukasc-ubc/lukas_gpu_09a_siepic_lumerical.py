#%%
"""
Simulation of a halfring device using lumerical.
@author: Mustafa Hammood
"""

# Parameters
expected_process_bias = -2  # reduction by 2 nm on each side

import os
import sys
import subprocess

# Required packages

try:
    import SiEPIC
except:
    result = subprocess.run([sys.executable, "-m", "pip","install","siepic"])
    print(result)
    import SiEPIC
    
from SiEPIC.install import install
pip_requirements = ['matplotlib','shapely','tidy3d','siepic_ebeam_pdk']
for p in pip_requirements:
    if not install(p):
        print(f' - missing {p}')


# Import gds-fdtd from GitHub repository, installed locally
file_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),"gds_fdtd")
if not os.path.exists(file_dir):
    #import sys
    #result = subprocess.run([sys.executable, "-c", "print('ocean')"])
    result = subprocess.run(["git", "clone", "https://github.com/mustafacc/gds_fdtd.git"])
    print(result)
    result = subprocess.run(["pwd"])
    print(result)
# Add the directory to sys.path
# sys.path.append(current_file_dir)
# Alternatively, insert at the beginning of sys.path
sys.path.insert(0, file_dir)
import gds_fdtd
print(gds_fdtd)    


       
from gds_fdtd.simprocessor import load_component_from_tech
from gds_fdtd.core import parse_yaml_tech
from gds_fdtd.lum_tools import make_sim_lum
import siepic_ebeam_pdk as pdk  # noqa: F401
from pya import Layout
from lumapi import FDTD

if __name__ == "__main__":
    tech_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tech_lumerical.yaml")
    technology = parse_yaml_tech(tech_path)

    # load cell from siepic_ebeam_pdk
    ly = Layout()
    ly.technology_name = pdk.tech.name
    cell = ly.create_cell("ebeam_dc_halfring_straight", "EBeam", {})

    component = load_component_from_tech(cell=cell, tech=technology)

    # simulate with lumerical
    make_sim_lum(
        c=component,
        lum=FDTD(),
        wavl_min=1.45,
        wavl_max=1.65,
        wavl_pts=101,
        width_ports=4.0,
        depth_ports=4.0,
        symmetry=(0, 0, 0),
        pol="TE",
        num_modes=1,
        boundary="pml",
        mesh=3,
        run_time_factor=50,)

# %%