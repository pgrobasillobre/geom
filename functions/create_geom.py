import sys
import numpy as np
import copy

from classes import molecule
from functions import general, output

def select_case(inp):
   #
   """ 
   Select create geometry case

   :inp: input class
   """
   #

   if (inp.gen_tip):     tip(inp)
   if (inp.gen_pyramid): pyramid(inp)
 

def tip(inp):
   #
   """ 
   Generate round tip geometry 

   :inp: input class
   """
   #

   # Check input
   inp.check_input_case()   
   general.create_results_geom()
   out_log = output.logfile_init()
 
   # Initialize bulk "molecule" and read geometry
   mol = molecule.molecule()
   mol.read_geom(inp.geom_file,False)

   # Pick only atoms within the defined paraboloid
   mol.filter_xyz_in_elliptic_paraboloid(inp)

   # Save filtered geometry
   file_geom_filtered = f'ellyptic_paraboloid_a-{inp.elliptic_parabola_a}_b-{inp.elliptic_parabola_b}_zmin-{inp.z_min}_zmax-{inp.z_max}'
   output.print_geom(mol, file_geom_filtered)


def pyramid(inp):
   #
   """
   Generate pyramid geometry (with square base)

   :inp: input class
   """
   #

   # Check input
   inp.check_input_case()
   general.create_results_geom()
   out_log = output.logfile_init()

   # Initialize bulk "molecule" and read geometry
   mol = molecule.molecule()
   mol.read_geom(inp.geom_file, False)

   # Define vertices with respect to the center (C[0,0,0]) of the XY-plane base
   #
   # XY base (center 5 in the +z direction)
   #
   #   4 ______ 1     ^ y            
   #    |      |      |             
   #    |   C  |      o ---> x      
   #    |______|     z              
   #   3        2 

   centers = {
       "center_1": [inp.side_length / 2.0, inp.side_length / 2.0, 0.0],
       "center_2": [inp.side_length / 2.0, -inp.side_length / 2.0, 0.0],
       "center_3": [-inp.side_length / 2.0, -inp.side_length / 2.0, 0.0],
       "center_4": [-inp.side_length / 2.0, inp.side_length / 2.0, 0.0],
       "center_5": [0.0, 0.0, inp.z_max]
   }

   # Function to calculate normal and RHS for planes
   def calculate_normal_and_rhs(center_a, center_b, apex):
       a = [center_a[i] - apex[i] for i in range(3)]
       b = [center_b[i] - apex[i] for i in range(3)]
       normal = np.cross(a, b)
       rhs = -sum(normal[i] * apex[i] for i in range(3))
       return normal, rhs

   # Define planes to cut the pyramid
   # Eqs. --> n_x * x + n_y * y + n_z * z + rhs = 0
   planes = {
       "n_125": calculate_normal_and_rhs(centers["center_1"], centers["center_2"], centers["center_5"]),
       "n_235": calculate_normal_and_rhs(centers["center_2"], centers["center_3"], centers["center_5"]),
       "n_345": calculate_normal_and_rhs(centers["center_3"], centers["center_4"], centers["center_5"]),
       "n_415": calculate_normal_and_rhs(centers["center_4"], centers["center_1"], centers["center_5"])
   } 

   # Pick only atoms within the defined pyramid
   mol.filter_xyz_in_pyramid(inp,centers, planes)

   # Save filtered geometry
   file_geom_filtered = f'pyramid_length-{inp.side_length}_zmin-{inp.z_min}_zmax-{inp.z_max}'
   output.print_geom(mol, file_geom_filtered)



