'''
Waveguide simulations, using Python and Lumerical MODE

by Lukas Chrostowski, 2025, SiEPIC Program

- strip waveguide, height, width, core material (Si or SiN), cladding (oxide)
- effective index (neff) vs. wavelength
- compact model for neff vs. wavelength (neff, ng, D)
- mode profile

'''


import lumapi
import numpy as np
import matplotlib.pyplot as plt

class Waveguide():
    '''
    Units: meters 
    '''
    def __init__(self):
        # Waveguide parameters
        self.wg_material_core = 'Si3N4 (Silicon Nitride) - Luke'
        self.wg_material_clad = 'SiO2 (Glass) - Palik'
        self.wg_width = 350e-9
        self.wg_height = 220e-9
        
        # simulation parameters
        self.wavelength_start = 1200e-9  # 1200 nm
        self.wavelength_stop = 1700e-9  # 1700 nm
        self.wavelength_points = 10
        self.wavelengths = np.linspace(self.wavelength_start, self.wavelength_stop, self.wavelength_points)
        
        # simulation details
        self.sim_width = 2e-6
        self.sim_height = 2e-6
        self.sim_mesh_cells_x = 100
        self.sim_mesh_cells_y = 100
        self.sim_mesh_override_size = 10e-9
        

    def simulate(self):
        
        # Initialize Lumerical MODE session
        mode = lumapi.MODE()

        # Start new project
        mode.switchtolayout()
        mode.new()

        # Draw the silicon waveguide
        mode.addrect(name='waveguide core')
        mode.setnamed('waveguide core', 'x span', self.wg_width)
        mode.setnamed('waveguide core', 'y min', 0)
        mode.setnamed('waveguide core', 'y max', self.wg_height)
        mode.setnamed('waveguide core', 'material', self.wg_material_core)

        # Add cladding layer (oxide)
        mode.addrect(name='waveguide cladding')
        mode.setnamed('waveguide cladding', 'x span', self.sim_width)
        mode.setnamed('waveguide cladding', 'y span', self.sim_height)
        mode.setnamed('waveguide cladding', 'material', self.wg_material_clad)

        # Add FDE eigenmode solver
        mode.addfde()
        mode.setnamed('FDE', 'x span', self.sim_width)
        mode.setnamed('FDE', 'y span', self.sim_height)
        mode.setnamed('FDE', 'mesh cells x', self.sim_mesh_cells_x)
        mode.setnamed('FDE', 'mesh cells y', self.sim_mesh_cells_y)

        # Mesh override in waveguide region
        mode.addmesh()
        mode.setnamed('mesh', 'x span', self.wg_width)
        mode.setnamed('mesh', 'y min', 0)
        mode.setnamed('mesh', 'y max', self.wg_height)
        mode.setnamed('mesh', 'dx', self.sim_mesh_override_size)
        mode.setnamed('mesh', 'dy', self.sim_mesh_override_size)

        # Store results:
        self.neff1=[]
        self.neff2=[]

        # Run simulations, once for each wavelength 
        for wl in self.wavelengths:
            mode.switchtolayout()
            mode.select('MODE')
            mode.setnamed('MODE', 'wavelength', wl)
            mode.run()
            mode.mesh()
            f1 = mode.getdata('MODE::data::material', 'f')
            eps1 = np.square(mode.getdata('MODE::data::material', 'index_x'))

            mode.setanalysis('wavelength', wl)
            mode.setanalysis('search', 1)
            mode.setanalysis('use max index', 1)
            mode.setanalysis('number of trial modes', 2)
            mode.findmodes()

            pol1 = mode.getdata('mode1', 'TE polarization fraction')
            pol2 = mode.getdata('mode2', 'TE polarization fraction')
            TEmode, TMmode = ('mode1', 'mode2') if pol1 > 0.5 else ('mode2', 'mode1')

            self.neff1.append(float(np.real(mode.getresult("FDE::data::mode1", 'neff'))))
            self.neff2.append(float(np.real(mode.getresult("FDE::data::mode2", 'neff'))))


        
    def save(self):
        
        # Output file
        output_file = 'waveguide_neff.csv'
        with open(output_file, 'w') as file:
            file.write('waveguide width, waveguide height, core material, clad material, wavelength, effective index\n')

        with open(output_file, 'a') as file:
            print("Saving results to file...")
            for wl, neff in zip(self.wavelengths, self.neff1):
                print(f'{self.wg_width}, {self.wg_height}, {self.wg_material_core}, {self.wg_material_clad}, {wl}, {neff}')
                file.write(f'{self.wg_width}, {self.wg_height}, {self.wg_material_core}, {self.wg_material_clad}, {wl}, {neff}\n')




if __name__ == "__main__":
    print("SiEPIC - Python Lumerical - waveguide simulation")
    
    wg = Waveguide()

    wg.simulate()

    wg.save()    
