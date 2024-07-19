import math
import copy

from classes import molecule
from functions import tools, general, output

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

   # Check input
   inp.check_input_case()   
 
   # Initialize molecules and read geometries
   mol_1 = molecule.molecule()
   mol_2 = molecule.molecule()

   mol_1.read_geom(inp.geom1_file,False)
   mol_2.read_geom(inp.geom2_file,False)
 
   # Calc min distance
   distance = tools.calc_min_distance(mol_1,mol_2)

   # Print calculated minimum distance
   output.print_min_dist(inp,distance)


#       ______                        
#      / ____/__  ____  ____ ___      
#     / / __/ _ \/ __ \/ __ `__ \     
#    / /_/ /  __/ /_/ / / / / / /     
#    \____/\___/\____/_/ /_/ /_/      
#                                     
#       ______           __           
#      / ____/__  ____  / /____  _____
#     / /   / _ \/ __ \/ __/ _ \/ ___/
#    / /___/  __/ / / / /_/  __/ /    
#    \____/\___/_/ /_/\__/\___/_/     
#                                     

def geom_center(inp):
   #
   """ 
   Calculate geometrical center

   :inp: input class
   """
   #

   # Check input
   inp.check_input_case()   
 
   # Initialize molecule and read geometry
   mol = molecule.molecule()
   mol.read_geom(inp.geom_file,False)
 
   output.print_geom_center(inp,mol.xyz_center)


#       ______                                  
#      / ____/__  ____  ____ ___                
#     / / __/ _ \/ __ \/ __ `__ \               
#    / /_/ /  __/ /_/ / / / / / /               
#    \____/\___/\____/_/ /_/ /_/                
#                                               
#       _____                       __          
#      / ___/____  ___  _______  __/ /___ ______
#      \__ \/ __ \/ _ \/ ___/ / / / / __ `/ ___/
#     ___/ / /_/ /  __/ /__/ /_/ / / /_/ / /    
#    /____/ .___/\___/\___/\__,_/_/\__,_/_/     
#        /_/                                    
#

def geom_specular(inp):
   #
   """ 
   Create specular geometry

   :inp: input class
   """
   #

   # Check input
   inp.check_input_case()   
   general.create_results_geom()
   out_log = output.logfile_init()
 
   # Initialize molecule and read geometry
   mol = molecule.molecule()
   mol.read_geom(inp.geom_file,True)
 
   # Create specular geometry along x and move at 5 Å 
   shift = (mol.xyz_max[0] - mol.xyz_min[0]) + 5.0
   dir_factor = [1.0,0.0,0.0]

   mol.xyz[0,:] = -mol.xyz[0,:]

   mol.translate_geom(shift,dir_factor)
 
   # Save specular geometry
   output.print_geom(mol, inp.geom_file[:-4]+'_000_mirror')

   # Close and save logfile
   output.logfile_close(out_log)
 

#        __  ___                                            
#       /  |/  /__  _________ ____                          
#      / /|_/ / _ \/ ___/ __ `/ _ \                         
#     / /  / /  __/ /  / /_/ /  __/                         
#    /_/  /_/\___/_/   \__, /\___/                          
#                     /____/                                
#       ______                          __       _          
#      / ____/__  ____  ____ ___  ___  / /______(_)__  _____
#     / / __/ _ \/ __ \/ __ `__ \/ _ \/ __/ ___/ / _ \/ ___/
#    / /_/ /  __/ /_/ / / / / / /  __/ /_/ /  / /  __(__  ) 
#    \____/\___/\____/_/ /_/ /_/\___/\__/_/  /_/\___/____/  
#                                                           

def merge_geoms(inp):
   #
   """ 
   Merge two geometries

   :inp: input class
   """
   #

   # Check input
   inp.check_input_case()   
   general.create_results_geom()
   out_log = output.logfile_init()
 
   # Initialize molecules and read geometries
   mol_1 = molecule.molecule()
   mol_2 = molecule.molecule()

   mol_1.read_geom(inp.geom1_file,False)
   mol_2.read_geom(inp.geom2_file,False)
 
   # Merge two geometries
   mol_3 = tools.merge_geoms(inp,mol_1,mol_2)

   # Save merged geometry
   file_geom_merged = f"{inp.geom1_file[:-4]}_MERGED_{inp.geom2_file[:-4]}"
   output.print_geom(mol_3, file_geom_merged)

   # Close and save logfile
   output.logfile_close(out_log)
 
