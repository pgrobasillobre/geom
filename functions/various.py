import math
import copy

from classes import molecule
from functions import tools

#        __  ____       _                         
#       /  |/  (_)___  (_)___ ___  __  ______ ___ 
#      / /|_/ / / __ \/ / __ `__ \/ / / / __ `__ \
#     / /  / / / / / / / / / / / / /_/ / / / / / /
#    /_/  /_/_/_/ /_/_/_/ /_/ /_/\__,_/_/ /_/ /_/ 
#                                                 
#        ____  _      __                          
#       / __ \(_)____/ /_____ _____  ________     
#      / / / / / ___/ __/ __ `/ __ \/ ___/ _ \    
#     / /_/ / (__  ) /_/ /_/ / / / / /__/  __/    
#    /_____/_/____/\__/\__,_/_/ /_/\___/\___/     
#                                               

def min_dist(inp):
   #
   """ 
   Calculate minimum distance between two molecules

   :inp: input class
   """
   #
   #
   # Check input, create results folder, initialize logfile
   inp.check_input_case()   
 
   # Initialize molecules class and read geometries
   mol_1 = molecule.molecule()
   mol_2 = molecule.molecule()

   mol_1.read_geom(inp.geom1_file,False)
   mol_2.read_geom(inp.geom2_file,False)
 
   # Calc min distance
   distance = tools.calc_min_distance(mol_1,mol_2)

   print('')
   print('  -------------------------------')
   print('    Geometry 1: ' + inp.geom1_file)
   print('    Geometry 2: ' + inp.geom2_file)
   print('')
   print('    Minimum\n' + 
         '    distance  : ' + str(round(distance,4)) + ' Å')
   print('  -------------------------------')
   


