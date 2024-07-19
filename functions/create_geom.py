import math
import copy

from classes import molecule
from functions import tools, general, output


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

 



 
