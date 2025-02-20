import math
import copy

from classes import molecule
from functions import general, tools, output

# -------------------------------------------------------------------------------------
def rotate_angles(inp):
   #
   """ 
   Rotate molecule at a list of angles given in input.

   :inp: input class
   """
   #
   # Check input, create results folder, initialize logfile
   inp.check_input_case()   
   general.create_results_geom()
   #out_log = output.logfile_init()

   # Initialize molecules and read geometry
   mol = molecule.molecule()
   mol_rot = molecule.molecule()

   mol.read_geom(inp.geom_file,inp.move_geom_to_000)

   # Adjust angles depending on direction
   if inp.dir_axis_input[0] == '-': inp.angles = [360 - angle for angle in inp.angles]
 
   # Rotate over all angles
   for angle in inp.angles:

      mol_rot = tools.rotate(mol,angle,inp.dir_axis_input,mol_rot)

      # Save rotate geometry
      if inp.dir_axis_input[0] == '-': rot_file = f"{inp.geom_file[:-4]}_{inp.dir_axis_input}_degree_{abs(angle - 360)}"
      if inp.dir_axis_input[0] == '+': rot_file = f"{inp.geom_file[:-4]}_{inp.dir_axis_input}_degree_{angle}" 
       
      output.print_geom(mol_rot, rot_file)

      # Close and save logfile
      #output.logfile_close(out_log)
# -------------------------------------------------------------------------------------
def rotate_1(inp):
   #
   """ 
   Rotate molecule to a given angle.

   :inp: input class
   """
   #
   # Check input, create results folder, initialize logfile
   inp.check_input_case()   
   general.create_results_geom()
   #out_log = output.logfile_init()

   # Initialize molecules and read geometry
   mol = molecule.molecule()
   mol_rot = molecule.molecule()

   mol.read_geom(inp.geom_file,inp.move_geom_to_000)

   # Adjust angles depending on direction
   if inp.dir_axis_input[0] == '-': inp.angle = 360.0 - inp.angle
 
   # Rotate 
   mol_rot = tools.rotate(mol,inp.angle,inp.dir_axis_input,mol_rot)

   # Save rotate geometry
   if inp.dir_axis_input[0] == '-': rot_file = f"{inp.geom_file[:-4]}_{inp.dir_axis_input}_degree_{abs(inp.angle - 360)}"
   if inp.dir_axis_input[0] == '+': rot_file = f"{inp.geom_file[:-4]}_{inp.dir_axis_input}_degree_{inp.angle}" 
       
   output.print_geom(mol_rot, rot_file)

   # Close and save logfile
   #output.logfile_close(out_log)
# -------------------------------------------------------------------------------------
