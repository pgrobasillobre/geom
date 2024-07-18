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
 



 
