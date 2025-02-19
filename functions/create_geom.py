import sys
import numpy as np
import math
import copy
import os
import shutil

from classes import molecule, parameters
from functions import general, output, tools
from ase.cluster.cubic import FaceCenteredCubic, BodyCenteredCubic
from ase.build import graphene_nanoribbon
from ase.build import graphene as graphene_general_ase
from ase.io import write
# -------------------------------------------------------------------------------------
def select_case(inp):
   #
   """ 
   Select create geometry case

   :inp: input class
   """
   #

   if (inp.gen_graphene):          graphene(inp)
   if (inp.gen_sphere):            sphere(inp)
   if (inp.gen_sphere_core_shell): sphere_core_shell(inp)
   if (inp.gen_rod):               rod(inp)
   if (inp.gen_rod_core_shell):    rod_core_shell(inp)
   if (inp.gen_tip):               tip(inp)
   if (inp.gen_pyramid):           pyramid(inp)
   if (inp.gen_microscope):        microscope(inp)
   if (inp.gen_cone):              cone(inp)

   # Eliminate tmp folder containing bulk structure
   shutil.rmtree(inp.tmp_folder)
# -------------------------------------------------------------------------------------
def graphene(inp):
   #
   """ 
   Generate graphene geometry (ribbon) 

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

   # Pick only atoms within the defined graphene geometry 
   if inp.graphene_structure=='rib':      mol.filter_xyz_graphene_to_ribbon(inp)
   if inp.graphene_structure=='disk':     mol.filter_xyz_graphene_to_disk(inp)
   if inp.graphene_structure=='ring':     mol.filter_xyz_graphene_to_ring(inp)
   if inp.graphene_structure=='triangle': mol.filter_xyz_graphene_to_triangle(inp)

   # Remove dangling bonds
   mol.remove_dangling_bonds_graphene(inp)

   # Translate geometrical center to 000 
   mol.trans_geom_center_to_000()

   # Save filtered geometry
   if inp.graphene_structure=='rib':      file_geom_filtered = f'graphene_ribbon_{inp.X_length}_{inp.Y_length}'
   if inp.graphene_structure=='disk':     file_geom_filtered = f'graphene_disk_{inp.radius}'
   if inp.graphene_structure=='ring':     file_geom_filtered = f'graphene_ring_Out_{inp.radius_out}_In_{inp.radius_in}'
   if inp.graphene_structure=='triangle': file_geom_filtered = f'graphene_triangle_{inp.graphene_edge_type}_{inp.side_length}'

   output.print_geom(mol, file_geom_filtered)
# -------------------------------------------------------------------------------------
def sphere(inp):
   #
   """ 
   Generate sphere geometry 

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

   # Pick only atoms within the defined sphere 
   mol.filter_xyz_in_sphere(inp)

   # Alloy
   if inp.alloy: mol.create_alloy(inp)

   # Save filtered geometry
   file_geom_filtered = f'sphere_r_{inp.radius}_center_{inp.sphere_center[0]}_{inp.sphere_center[1]}_{inp.sphere_center[2]}{inp.alloy_string}'
   output.print_geom(mol, file_geom_filtered)
# -------------------------------------------------------------------------------------
def sphere_core_shell(inp):
   #
   """ 
   Generate sphere core shell geometry 

   :inp: input class
   """
   #

   # Check input
   inp.check_input_case()   
   general.create_results_geom()
   out_log = output.logfile_init()

   # Extract merge cutoff 
   param = parameters.parameters()
   inp.merge_cutoff = param.merge_cutoff.get(inp.atomtype)
 
   # Initialize bulk "molecule" and read geometry
   mol_out = molecule.molecule()
   mol_out = mol_out.read_geom(inp.geom_file,False)

   # Pick only atoms within the defined sphere 
   inp.radius   = inp.radius_out
   inp.atomtype = inp.atomtype_out

   mol_out.filter_xyz_in_sphere(inp)

   # Copy mol_out as initial guess, change atomtype, and create smaller sphere
   mol_in = copy.deepcopy(mol_out)
   mol_in.change_atomtype(inp.atomtype_in)

   inp.radius   = inp.radius_in
   inp.atomtype = inp.atomtype_in

   mol_in.filter_xyz_in_sphere(inp)

   # Create shell by subtracting core geometry
   mol_shell = tools.subtract_geoms(inp,mol_in,mol_out)

   # Alloy core and shell
   if inp.alloy: 
      inp.alloy_string = f"_alloy_{inp.alloy_perc}_perc"

      inp.atomtype = inp.atomtype_out
      inp.atomtype_alloy = inp.atomtype_in
      mol_shell.create_alloy(inp)

      inp.atomtype = inp.atomtype_in
      inp.atomtype_alloy = inp.atomtype_out
      mol_in.create_alloy(inp)

   # Merge to create core-shell
   mol_core_shell = tools.merge_geoms(inp,mol_in,mol_shell)

   # Save filtered geometry
   file_geom_filtered = f'sphere_core_{inp.atomtype_in}_r_{inp.radius_in}_shell_{inp.atomtype_out}_r_{inp.radius_out}{inp.alloy_string}'
   output.print_geom(mol_core_shell, file_geom_filtered)
# -------------------------------------------------------------------------------------
def rod(inp):
   #
   """ 
   Generate rod geometry 

   :inp: input class
   """
   #

   # Check input
   inp.check_input_case()   
   general.create_results_geom()
   out_log = output.logfile_init()

   # Extract merge cutoff 
   param = parameters.parameters()
   inp.merge_cutoff = param.merge_cutoff.get(inp.atomtype)
 
   # Initialize bulk "molecule" and read geometry
   mol_sphere_1 = molecule.molecule()
   mol_sphere_2 = molecule.molecule()
   mol_cylinder = molecule.molecule()

   mol_sphere_1.read_geom(inp.geom_file,False)
   mol_sphere_2.read_geom(inp.geom_file,False)
   mol_cylinder.read_geom(inp.geom_file,False)

   # Create individual sphere at the extremes of the rods 
   tools.determine_sphere_center(inp,'+')
   mol_sphere_1.filter_xyz_in_sphere(inp)

   tools.determine_sphere_center(inp,'-')
   mol_sphere_2.filter_xyz_in_sphere(inp)

   # Create cylinder
   mol_cylinder.filter_xyz_in_cylinder(inp)

   # -------------------------------------
   # Merge cylinder and spheres geometries
   # -------------------------------------

   mol_tmp = tools.merge_geoms(inp,mol_sphere_1,mol_sphere_2)
   mol_rod = tools.merge_geoms(inp,mol_cylinder,mol_tmp)

   # Alloy
   if inp.alloy: mol_rod.create_alloy(inp)

   # Save filtered geometry
   file_geom_filtered = f'rod_{inp.main_axis.upper()}_l_{inp.rod_length}_w_{inp.rod_width}{inp.alloy_string}'
   output.print_geom(mol_rod, file_geom_filtered)
# -------------------------------------------------------------------------------------
def rod_core_shell(inp):
   #
   """ 
   Generate rod core shell geometry 

   :inp: input class
   """
   #

   # Check input
   inp.check_input_case()   
   general.create_results_geom()
   out_log = output.logfile_init()

   # Extract merge cutoff 
   param = parameters.parameters()
   inp.merge_cutoff = param.merge_cutoff.get(inp.atomtype)
 
   # Initialize bulk "molecule" and read geometry
   mol_sphere_1 = molecule.molecule()
   mol_sphere_2 = molecule.molecule()
   mol_cylinder = molecule.molecule()

   mol_sphere_1.read_geom(inp.geom_file,False)
   mol_sphere_2.read_geom(inp.geom_file,False)
   mol_cylinder.read_geom(inp.geom_file,False)

   # ----------------------- #
   # --------- Out --------- #

   # Populate input class
   inp.rod_length = inp.rod_length_out
   inp.rod_width = inp.rod_width_out

   inp.atomtype = inp.atomtype_out

   # Create individual sphere at the extremes of the rods 
   tools.determine_sphere_center(inp,'+')
   mol_sphere_1.filter_xyz_in_sphere(inp)

   tools.determine_sphere_center(inp,'-')
   mol_sphere_2.filter_xyz_in_sphere(inp)

   # Create cylinder
   mol_cylinder.filter_xyz_in_cylinder(inp)

   # Merge cylinder and spheres geometries
   mol_tmp = tools.merge_geoms(inp,mol_sphere_1,mol_sphere_2)
   mol_out = tools.merge_geoms(inp,mol_cylinder,mol_tmp)

   # ---------------------- #
   # --------- In --------- #

   # Copy mol_out as initial guess, change atomtype, and populate input class
   mol_sphere_1 = copy.deepcopy(mol_out)
   mol_sphere_1.change_atomtype(inp.atomtype_in)

   mol_sphere_2 = copy.deepcopy(mol_out)
   mol_sphere_2.change_atomtype(inp.atomtype_in)

   inp.rod_length = inp.rod_length_in
   inp.rod_width = inp.rod_width_in

   inp.atomtype = inp.atomtype_in

   # Create individual sphere at the extremes of the rods 
   tools.determine_sphere_center(inp,'+')
   mol_sphere_1.filter_xyz_in_sphere(inp)

   tools.determine_sphere_center(inp,'-')
   mol_sphere_2.filter_xyz_in_sphere(inp)

   # Create cylinder
   mol_cylinder.filter_xyz_in_cylinder(inp)

   # Merge cylinder and spheres geometries
   mol_tmp = tools.merge_geoms(inp,mol_sphere_1,mol_sphere_2)
   mol_in = tools.merge_geoms(inp,mol_cylinder,mol_tmp)

   # Create shell by subtracting core geometry
   mol_shell = tools.subtract_geoms(inp,mol_in,mol_out)

   # debug
   output.print_geom(mol_shell, 'shell')

   # debug
   output.print_geom(mol_in, 'core')

   # Alloy core and shell
   if inp.alloy: 
      inp.alloy_string = f"_alloy_{inp.alloy_perc}_perc"

      inp.atomtype = inp.atomtype_out
      inp.atomtype_alloy = inp.atomtype_in
      mol_shell.create_alloy(inp)

      inp.atomtype = inp.atomtype_in
      inp.atomtype_alloy = inp.atomtype_out
      mol_in.create_alloy(inp)

   # Merge to create core-shell
   mol_core_shell = tools.merge_geoms(inp,mol_in,mol_shell)

   # Save filtered geometry
   file_geom_filtered = f'rod_core_{inp.atomtype_in}_L_{inp.rod_length_in}_R_{inp.rod_width_in}_shell_{inp.atomtype_out}_L_{inp.rod_length_out}_R_{inp.rod_width_out}_shell_{inp.atomtype_out}{inp.alloy_string}'
   output.print_geom(mol_core_shell, file_geom_filtered)
# -------------------------------------------------------------------------------------
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

   # Alloy
   if inp.alloy: mol.create_alloy(inp)

   # Save filtered geometry
   file_geom_filtered = f'elliptic_paraboloid_a-{inp.elliptic_parabola_a}_b-{inp.elliptic_parabola_b}_zmin-{inp.z_min}_zmax-{inp.z_max}{inp.alloy_string}'
   output.print_geom(mol, file_geom_filtered)
# -------------------------------------------------------------------------------------
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

   # Alloy
   if inp.alloy: mol.create_alloy(inp)

   # Save filtered geometry
   file_geom_filtered = f'pyramid_length-{inp.side_length}_zmin-{inp.z_min}_zmax-{inp.z_max}{inp.alloy_string}'
   output.print_geom(mol, file_geom_filtered)
# -------------------------------------------------------------------------------------
def cone(inp):
   #
   """
   Generate cone geometry 

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

   # Pick only atoms within the defined cone
   mol.filter_xyz_in_cone(inp)

   # Alloy
   if inp.alloy: mol.create_alloy(inp)

   # Save filtered geometry
   file_geom_filtered = f'cone_radius-{inp.radius}_zmin-{inp.z_min}_zmax-{inp.z_max}{inp.alloy_string}'
   output.print_geom(mol, file_geom_filtered)
# -------------------------------------------------------------------------------------
def microscope(inp):
   #
   """ 
   Generate microscope with pyramidal tip 

   :inp: input class
   """
   #

   # Check input
   inp.check_input_case()   
   general.create_results_geom()
   out_log = output.logfile_init()

   # Extract lattice constant and merge cutoff
   param = parameters.parameters()
   lattice_constant = param.lattice_constant.get(inp.atomtype)
   inp.merge_cutoff = param.merge_cutoff.get(inp.atomtype)
 
   # ---------------------------------------------
   # Create paraboloid from bulk metallic geometry
   # ---------------------------------------------

   inp.z_max = inp.z_max_paraboloid
   mol_paraboloid = molecule.molecule()
   mol_paraboloid.read_geom(inp.geom_file,False)
   mol_paraboloid.filter_xyz_in_elliptic_paraboloid(inp)

   #file_geom_paraboloid = f'elliptic_paraboloid_{inp.elliptic_parabola_a}_b-{inp.elliptic_parabola_b}_zmin-{inp.z_min}_zmax-{inp.z_max}'
   #output.print_geom(mol_paraboloid, file_geom_paraboloid)


   # ------------------------------------------
   # Create pyramid from bulk metallic geometry
   # ------------------------------------------

   inp.z_max = inp.z_max_pyramid
   mol_pyramid = molecule.molecule()
   mol_pyramid.read_geom(inp.geom_file, False)

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
   mol_pyramid.filter_xyz_in_pyramid(inp,centers, planes)

   # Rotate pyramid 180 degrees along z
   mol_pyramid_rot = molecule.molecule()
   mol_pyramid_rot = tools.rotate(mol_pyramid,180.0,'+x',mol_pyramid_rot)

   # Move 1/2*reticular_distance (lc) up in the z axis
   shift = math.ceil((inp.z_max_pyramid/2.0)/lattice_constant) * lattice_constant

   mol_pyramid_rot.translate_geom(shift,[0.0,0.0, 1.0])

   #file_geom_pyramid = f'pyramid_length-{inp.side_length}_zmin-{inp.z_min}_zmax-{inp.z_max}'
   #output.print_geom(mol_pyramid_rot, file_geom_pyramid)

   # -----------------------------------------
   # Merge paraboloid and pyramidal geometries
   # -----------------------------------------

   mol_microscope = tools.merge_geoms(inp,mol_paraboloid,mol_pyramid_rot)

   # Alloy
   if inp.alloy: mol_microscope.create_alloy(inp)

   file_geom_microscope = f'microscope_parabola_{inp.z_max}_{inp.elliptic_parabola_a}_{inp.elliptic_parabola_b}_pyramid_{inp.z_max}_{inp.side_length}{inp.alloy_string}'
   output.print_geom(mol_microscope, file_geom_microscope)
# -------------------------------------------------------------------------------------
def create_ase_bulk_metal(inp, base_dir):
   """
   Create temporary bulk metal XYZ file with ASE

   :inp: input class
   :base_dir: absolute path to folder
   """
   #

   # Extract lattice constant and atomic arrangement from parameters dictionary
   param = parameters.parameters()
   lattice_constant = param.lattice_constant.get(inp.atomtype)
   atomic_arrangement = param.atomic_arrangement.get(inp.atomtype)

   # Create tmp folder
   inp.tmp_folder = os.path.join(base_dir,'tmp')
   if os.path.exists(inp.tmp_folder): shutil.rmtree(inp.tmp_folder)
   os.mkdir(inp.tmp_folder)

   # Determine minimum layers required by ASE
   layers = get_layers(inp,lattice_constant)

   # Create atomic structure and write on tmp/tmp_bulk.xyz
   surfaces = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
   if atomic_arrangement=='FCC': 
      atoms = FaceCenteredCubic(inp.atomtype.capitalize(), surfaces, layers, latticeconstant=lattice_constant)
   elif atomic_arrangement=='BCC':
      layers = [int(x * 1.5) for x in layers] # Extra layers required for BCC
      atoms = BodyCenteredCubic(inp.atomtype.capitalize(), surfaces, layers, latticeconstant=lattice_constant)

   inp.geom_file = os.path.join(inp.tmp_folder,'tmp_bulk.xyz')
   write(inp.geom_file, atoms)
# -------------------------------------------------------------------------------------
def get_layers(inp, lattice_constant):
   """
   Dynamically calculate the required number of ASE layers for creating bulk structures
   as a function of the structural shapes.

   :inp: input class
   :lattice constant: lattice_constant parameter
   """
   #

   # Scaling factor to ensure enough layers are considered, independently of FCC of BCC structure
   structure_scaling = 2.0

   if inp.gen_sphere or inp.gen_sphere_core_shell:

       # Find the maximum distance from the origin + sphere radius
       max_shift = max(abs(inp.sphere_center[0]), abs(inp.sphere_center[1]), abs(inp.sphere_center[2]))
       R = inp.radius + max_shift

       return [int(structure_scaling * R / lattice_constant) + 2] * 3  # Same layers for x, y, z

   elif inp.gen_rod or inp.gen_rod_core_shell:

       axis = inp.main_axis.lower()

       R = inp.rod_width / 2.0
       L = 2.0 * structure_scaling * inp.rod_length

       layers = [max(3, int(structure_scaling * 2 * R / lattice_constant) + 2)] * 3  

       axis_index = {"x": 0, "y": 1, "z": 2}[axis]
       layers[axis_index] = max(3, int(L / lattice_constant) + 2)  # Adjust for rod length

       return layers

   elif inp.gen_tip:
      H = structure_scaling * inp.z_max  # Tip height
      return [int(H / lattice_constant) + 2] * 3  # Tip grows mostly in z-axis

   elif inp.gen_cone:
       H = inp.z_max
       R = structure_scaling * inp.radius
       return [int(2 * R / lattice_constant) + 2, int(2 * R / lattice_constant) + 2, int(H / lattice_constant) + 2]

   elif inp.gen_pyramid:
      if inp.z_max > inp.side_length:
          H = 1.5 * structure_scaling * inp.z_max  
          L = inp.side_length  
      elif inp.side_length > inp.z_max:
          H = inp.z_max  
          L = 1.5 * structure_scaling * inp.side_length  
      else:
          # If both are equal, apply scaling to L
          H = inp.z_max
          L = 1.5 * structure_scaling * inp.side_length

      return [int(L / lattice_constant) + 2, int(L / lattice_constant) + 2, int(H / lattice_constant) + 2]

   elif inp.gen_microscope:
       H_paraboloid = 1.5 * structure_scaling * inp.z_max_paraboloid
       H_pyramid    = 1.5 * structure_scaling * inp.z_max_pyramid
       L            = 1.5 * structure_scaling * inp.side_length
       return [int(L / lattice_constant) + 2, int(L / lattice_constant) + 2, int((H_paraboloid + H_pyramid) / lattice_constant) + 2]
# -------------------------------------------------------------------------------------
def create_ase_bulk_graphene(inp, base_dir):
   """
   Create temporary bulk graphene XYZ file with ASE

   :inp: input class
   :base_dir: absolute path to folder
   """
   #

   # Extract lattice constant from parameters dictionary
   param = parameters.parameters()
   lattice_constant = param.lattice_constant.get(inp.atomtype)

   # Create tmp folder
   inp.tmp_folder = os.path.join(base_dir,'tmp')
   if os.path.exists(inp.tmp_folder): shutil.rmtree(inp.tmp_folder)
   os.mkdir(inp.tmp_folder)

   # Create initial graphene structure with ASE
   if inp.graphene_structure == "rib" or inp.graphene_structure == "triangle":
      # Increase size of bulk structure by a factor to ensure correct geometry creation
      geom_scale = 1.5

      # If triangle, create side_length X side_length ribbon to cut
      if inp.graphene_structure == "triangle":
         inp.X_length = inp.side_length 
         inp.Y_length = inp.side_length
         geom_scale = 2.0

      # Oversize by 1.5x
      scaled_width  = geom_scale * inp.X_length
      scaled_length = geom_scale * inp.Y_length

      # Convert dimensions to graphene_nanoribbon parameters
      n = int(scaled_width / 2.13)   # Number of dimer rows for width
      m = int(scaled_length / 4.26)  # Number of unit cells for length

      # Create flat armchair nanoribbon in XY plane
      # Armchair structure will then be managed
      graphene_xyz = graphene_nanoribbon(n=n, m=m, type='armchair')
      graphene_xyz.rotate(90, 'x', rotate_cell=True)

   elif inp.graphene_structure == "disk" or inp.graphene_structure == "ring":
      # Select radius to define structure. Both inp.radius and inp.radius_out are initialized to zero  
      radius_selected = max(inp.radius, inp.radius_out)

      # Create a large graphene sheet in XY plane
      radius_int = math.ceil(radius_selected) # Round to upper integer for function compatibility
      graphene_xyz = graphene_general_ase(a=lattice_constant, size=(2*radius_int, 2*radius_int, 1))  # Large enough to extract disk

   # Center the graphene at (0,0,0) and write on tmp/tmp_bulk.xyz
   graphene_xyz.translate(-graphene_xyz.get_center_of_mass())
   inp.geom_file = os.path.join(inp.tmp_folder,'tmp_bulk.xyz')
   write(inp.geom_file, graphene_xyz)
# -------------------------------------------------------------------------------------
