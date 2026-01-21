import sys
import os
import ast

from geom.classes import parameters
from geom.functions import output, create_geom

# -------------------------------------------------------------------------------------
def read_command_line(argv, inp):
    """
    Parses command-line arguments and determines the operation mode.

    Args:
        argv (list[str]): List of command-line arguments.
        inp (input_class): An instance containing input parameters.

    Returns:
        None: Calls the appropriate parsing function or displays help.

    Notes:
        - If no arguments are provided, an error is raised.
        - Recognizes different command-line options and triggers the corresponding function.
        - Prints help if `-h` or `-help` is passed.
    """

    if len(argv) < 2:
        output.error("Missing command line arguments.")
    command = argv[1]
    if command in ['-h', '-help']:
        print_help()
    elif command == '-t' or command =='-t1' or command == '-tc':
        parse_translation(argv, inp)
    elif command == '-r' or command =='-r1':
        parse_rotation(argv, inp)
    elif command == '-min':
        parse_min(argv,inp)
    elif command == '-c':
        parse_center(argv,inp)
    elif command == '-mirror':
        parse_mirror(argv, inp)
    elif command == '-create':
        parse_create(argv, inp)
    elif command == '-merge':
        parse_merge(argv,inp)
    elif command == '-rdkit':
        parse_rdkit(argv,inp)
    else:
        output.error(f'Option "{command}" not recognized. Try python3 geom -h')
# -------------------------------------------------------------------------------------
def print_help():
    """
    Prints the help message with usage instructions and exits the program.

    Returns:
        None: Displays the help text and terminates execution.
    """

    help_text = '''

      ==========
      Execution:
      ==========

         * The inputs must contain each angle(degrees)/distance(Å) in different lines, without blank lines

         ------------
         Translation:
         ------------

         Distances in input (controlled dist. between 2 files):

           -t distances_input geom1.xyz origin_CM_1{origin_CM_1_yes/no} geom2.xyz origin_CM_2{origin_CM_2_yes/no} axis{+-}{x/y/z} verbose{verbose_yes/no}

         One translation:

           -t1 shift geom.xyz origin_CM{origin_CM_yes/no} axis{+-}{x/y/z}

         Translation to center of coordinates:

           -tc geom.xyz


         ---------
         Rotation:
         ---------

         Angles in input:

           -r angles_input geom.xyz origin_CM{origin_CM_yes/no} axis{+-}{x/y/z}

         One rotation:

           -r1 angle geom.xyz origin_CM{origin_CM_yes/no} axis{+-}{x/y/z}


         -----------------
         Minimum Distance:
         -----------------

         -min geom1.xyz geom2.xyz


         -------------------
         Geometrical Center:
         -------------------

         -c geom.xyz


         ------------------
         Specular geometry:
         ------------------

         -mirror geom.xyz


         ----------------
         Merge Geometries
         ----------------

         -merge geom1.xyz geom2.xyz cutoff(Å)


         -----------------
         Generate Geometry
         -----------------

         Graphene:

           Ribbon (X: zigzag | Y: armchair): -create -graphene rib X_length Y_length

           Disk: -create -graphene disk radius

           Ring: -create -graphene ring radius_out radius_in

           Triangle: -create -graphene triangle edge_type{armchair/zigzag} side_length

         Nanoparticles:

           Sphere: -create -sphere atom_type radius

           Sphere (3D continuum mesh): -create -sphere -continuum radius mesh_size

           Sphere (core-shell): -create -sphere -core atom_type r_core -shell atom_type r_shell
           
           Rod: -create -rod atom_type main_axis{X/Y/Z} length width

           Rod (3D continuum mesh): -create -rod -continuum main_axis{X/Y/Z} length width mesh_size

           Rod (core-shell): -create -rod main_axis{X/Y/Z} -core atom_type length width -shell atom_type length width
           
           Tip (elliptic paraboloid): -create -tip atom_type z_max a b

           Pyramid (square base): -create -pyramid atom_type z_max base_side_length

           Cone: -create -cone atom_type z_max base_radius

           Microscope: -create -microscope atom_type z_max_paraboloid a b z_max_pyramid base_side_length

           Icosahedron: -create -ico atom_type radius

           Cuboctahedron: -create -cto atom_type radius

           Decahedron: -create -idh atom_type radius

           Bipyramid: -create -bipyramid atom_type width length

           Pencil: -create -pencil -core atom_type -{full/half}shell atom_type core_width core_length shell_length

         -----------------------------
         Additional Options
         -----------------------------

         - The -alloy option allows creating a random alloy by specifying:
             -alloy atom_type -percentual float

         - Core-shell structures are available for spheres and rods:
             -core atom_type r_core -shell atom_type r_shell

         - Dimer creation is available for all nanoparticles by adding:
             -dimer dimer_distance axis{+/-}{x/y/z}

         - Bowtie creation is available for tip, pyramid, cone, and microscope:
             -bowtie bowtie_distance

         - The alloy option is compatible with bowtie and dimer creation.

         Note: Alloying, core-shell, dimer, and bowtie options are only available for Ag and Au-based nanoparticles.


         ------
         RDKit:
         ------

         Visualization:

            -rdkit -i file.[pdb|sdf|mol|smi|xyz] -vis2d | -vis3d

            Options (for -vis2d, can be combined):
                -stereo   Show stereochemistry labels (R/S, E/Z)
                -index    Show atom indices
                -bw       Black and white rendering
                -rm_H     Remove hydrogens
                -abbrevs  Abbreviate ligands
                -aromatic Highlight in pale green aromatic atoms/bonds
                -match    "smiles/smarts"
                          If present, highlight in pale blue a substructure parsed from a SMILES or SMARTS string

         File conversion:

            -rdkit -i file.[pdb|sdf|mol|smi|xyz] -o file.[pdb|sdf|mol|smi|xyz]
        
         Force field geometry optimization:

            -rdkit -i file.[pdb|sdf|mol|smi|xyz]
                    -opt [mmff94|mmff94s|uff] (default=mmff94)
                    [-maxIters N(default=200)]
                    [-o file.[pdb|sdf|mol2|xyz](default=pdb)]

         Conformers generation:

            -rdkit -i file.[pdb|sdf|mol|smi|xyz] 
                    -confs [N] (default=50)
                    [-opt [mmff94|mmff94s|uff] (default=mmff94)]
                    [-maxIters N] (default=200)
                    [-ext [pdb|sdf|xyz] (default=pdb)]
                    [-pruneRms RMS] (default=0.30)

    '''
    print(help_text)
    sys.exit()
# -------------------------------------------------------------------------------------
def parse_translation(argv, inp):
   """
   Parses translation-related command-line arguments.

   Args:
       argv (list[str]): List of command-line arguments.
       inp (input_class): An instance containing input parameters.

   Returns:
       None: Sets translation-related attributes in `inp`.

   Notes:
       - Handles both controlled distance translation (`-t`), simple shift translation (`-t1`),
         and translation of geometrical center to the center of coordinates (`-tc`).
       - Extracts input filenames, translation parameters, and verbosity settings.
   """

   inp.translate = True

   if argv[1] == '-t':
      inp.translate_controlled_distance = True

      inp.distances_input = str(argv[2])
      inp.geom1_file      = str(argv[3]) 
      inp.origin_CM_1     = str(argv[4])
      inp.geom2_file      = str(argv[5])
      inp.origin_CM_2     = str(argv[6])
      inp.dir_axis_input  = str(argv[7])
      inp.verbose_inp     = str(argv[8])

      if (inp.origin_CM_1 == 'origin_CM_1_yes'): inp.move_geom_1_to_000 = True
      if (inp.origin_CM_2 == 'origin_CM_2_yes'): inp.move_geom_2_to_000 = True
      if (inp.verbose_inp == 'verbose_yes'): inp.verbose = True
   
   elif argv[1] == '-t1':
      inp.translate_1 = True

      inp.shift_t1       = float(argv[2])
      inp.geom_file      = str(argv[3]) 
      inp.origin_CM      = str(argv[4])
      inp.dir_axis_input = str(argv[5])

      if (inp.origin_CM == 'origin_CM_yes'): inp.move_geom_to_000 = True

   elif argv[1] == '-tc':
      inp.translate_center = True
      inp.geom_file      = str(argv[2]) 
# -------------------------------------------------------------------------------------
def parse_rotation(argv, inp):
   """
   Parses rotation-related command-line arguments.

   Args:
       argv (list[str]): List of command-line arguments.
       inp (input_class): An instance containing input parameters.

   Returns:
       None: Sets rotation-related attributes in `inp`.

   Notes:
       - Handles both list-based rotation (`-r`) and single-angle rotation (`-r1`).
       - Extracts input filenames and rotation parameters.
   """

   inp.rotate = True

   if argv[1] == '-r':
      inp.rotate_angles = True

      inp.angles_input   = str(argv[2])
      inp.geom_file      = str(argv[3]) 
      inp.origin_CM      = str(argv[4])
      inp.dir_axis_input = str(argv[5])

      if (inp.origin_CM == 'origin_CM_yes'): inp.move_geom_to_000 = True

   elif argv[1] == '-r1':
      inp.rotate_1 = True

      inp.angle          = float(argv[2])
      inp.geom_file      = str(argv[3]) 
      inp.origin_CM      = str(argv[4])
      inp.dir_axis_input = str(argv[5])

      if (inp.origin_CM == 'origin_CM_yes'): inp.move_geom_to_000 = True
# -------------------------------------------------------------------------------------
def parse_mirror(argv, inp):
   """
   Parses command-line arguments for performing a mirror reflection.

   Args:
       argv (list[str]): List of command-line arguments.
       inp (input_class): An instance containing input parameters.

   Returns:
       None: Sets mirroring attributes in `inp`.
   """

   inp.small_tasks = True

   inp.geom_specular = True
   inp.geom_file = str(argv[2])
# -------------------------------------------------------------------------------------
def parse_merge(argv, inp):
   """
   Parses command-line arguments for merging geometries.

   Args:
       argv (list[str]): List of command-line arguments.
       inp (input_class): An instance containing input parameters.

   Returns:
       None: Sets merging attributes in `inp`.

   Notes:
       - Requires two geometry files and a cutoff distance.
   """

   inp.small_tasks = True

   inp.merge = True
   inp.geom1_file = str(argv[2])
   inp.geom2_file = str(argv[3])
   inp.merge_cutoff = float(argv[4])
# -------------------------------------------------------------------------------------
def parse_rdkit(argv, inp):
    """
        TO DO
    """

    # Sanitary check
    if "-i" not in argv: output.error('Missing "-i" option for parsing input.')

    inp.rdkit = True

    # Visualization

    if "-vis2d" in argv: inp.rdkit_visualize_2d = True
    if "-vis3d" in argv: inp.rdkit_visualize_3d = True
    if "-stereo" in argv: inp.stereo_annotations = True
    if "-index" in argv: inp.atom_index = True
    if "-bw" in argv: inp.rdkit_bw = True
    if "-rm_H" or "-rm_h" in argv: inp.remove_H = True
    if "-abbrevs" in argv: inp.rdkit_abbreviations = True
    if "-aromatic" in argv: inp.check_aromaticity = True

    if "-match" in argv:
        inp.rdkit_match = True
        inp.match_smiles = extract_value(argv, "-match",value_type=str)
    
    if (inp.rdkit_visualize_2d or inp.rdkit_visualize_3d): inp.rdkit_visualize = True 

    inp.rdkit_mol_file = argv[3]
    inp.rdkit_mol_file_extension = inp.rdkit_mol_file[-4:]

    # File conversion
    if "-o" in argv:
        inp.rdkit_file_conversion = True
        inp.rdkit_output_file = extract_value(argv, "-o",value_type=str)

    # Force field optimization
    if "-opt" in argv:
        inp.rdkit_opt = True
        inp.rdkit_force_field = extract_value_or_default(argv,"-opt",value_type=str,default="mmff94") 

        if "-o" in argv: 
            inp.rdkit_file_conversion = False # Turn off file conversion
        else:
            inp.rdkit_output_file = inp.rdkit_mol_file[:-4] + "_opt.pdb"

        if any(arg.lower() == "-maxiters" for arg in argv):
            inp.rdkit_max_iters = extract_value(argv, "-maxIters",value_type=int)

    # Conformers generation
    if "-confs" in argv:
        inp.rdkit_conformers = True
        inp.rdkit_confs = extract_value_or_default(argv,"-confs",value_type=int,default=50) 
        if "-ext" in argv: 
            inp.rdkit_confs_ext = "." + extract_value(argv,"-ext",value_type=str)
        if any(arg.lower() == "-prunerms" for arg in argv):
            inp.rdkit_confs_prune_rms = extract_value(argv, "-pruneRms", value_type=float)
        inp.rdkit_output_file = inp.rdkit_mol_file[:-4] + inp.rdkit_confs_ext
# -------------------------------------------------------------------------------------
def parse_min(argv, inp):
   """
   Parses command-line arguments for calculating the minimum distance between two geometries.

   Args:
       argv (list[str]): List of command-line arguments.
       inp (input_class): An instance containing input parameters.

   Returns:
       None: Sets minimum distance calculation attributes in `inp`.
   """

   inp.small_tasks = True

   inp.min_dist = True
   inp.geom1_file = str(argv[2])
   inp.geom2_file = str(argv[3])
# -------------------------------------------------------------------------------------
def parse_center(argv, inp):
   """
   Parses command-line arguments for computing the geometric center of a structure.

   Args:
       argv (list[str]): List of command-line arguments.
       inp (input_class): An instance containing input parameters.

   Returns:
       None: Sets geometric centering attributes in `inp`.
   """

   inp.small_tasks = True

   inp.geom_center = True
   inp.geom_file = str(argv[2])
# -------------------------------------------------------------------------------------
def parse_create(argv, inp):
   """
   Parses command-line arguments for generating different types of geometries.

   Args:
       argv (list[str]): List of command-line arguments.
       inp (input_class): An instance containing input parameters.

   Returns:
       None: Sets attributes in `inp` for geometry generation.

   Notes:
       - Handles the creation of graphene structures, nanoparticles, and bulk metal structures.
       - Validates input parameters and extracts atomic and structural properties.
   """

   inp.create_geom = True 

   # Extract parameters
   param = parameters.parameters()

   # Determine the script's location
   script_path = os.path.abspath(__file__)
   # Get the directory containing the script
   script_dir = os.path.dirname(script_path)
   # Get upper directory
   base_dir = os.path.dirname(script_dir)
   
   if (argv[2] == '-graphene'):
      inp.gen_graphene = True
      inp.create_ase_bulk = True

      inp.atomtype = "c"
      inp.graphene_structure = argv[3] 

      if inp.graphene_structure not in inp.graphene_structures: 
         output.error(f'Requested graphene structure "{inp.graphene_structure}" not recognised') 

      elif inp.graphene_structure == "rib":
         inp.X_length = float(argv[4])
         inp.Y_length = float(argv[5])

      elif inp.graphene_structure == 'disk':
         inp.radius = float(argv[4])

      elif inp.graphene_structure == 'ring':
         inp.radius_out = float(argv[4])
         inp.radius_in  = float(argv[5])
         if (inp.radius_in >= inp.radius_out): output.error(f'Inner radius must be smaller than outer radius.')

      elif inp.graphene_structure == 'triangle':
         inp.graphene_edge_type = argv[4]
         inp.side_length = float(argv[5])
         if inp.graphene_edge_type not in inp.graphene_edge_types:
            output.error(f'Requested edge type "{inp.graphene_edge_type}" not recognised')

      else:
         output.error(f'Create graphene option "{inp.graphene_structure}" not recognized. Try python3 geom -h')

      # Create bulk graphene dynamically
      create_geom.create_ase_bulk_graphene(inp, base_dir)

   else:
      if ('-core' and '-shell') in argv: 
         inp.gen_core_shell = True

      elif ('-continuum') in argv:
         inp.gen_3d_mesh = True

      elif ("-pencil") in argv:
          inp.gen_pencil = True

      else:
         inp.atomtype = argv[3].lower()
         if inp.atomtype not in param.metal_atomtypes: output.error(f'Atom Type "{argv[3]}" not recognised')

         check_FCC_or_BCC(inp.atomtype)

      if (argv[2] == '-sphere'): 
         if (inp.gen_core_shell): 
            inp.gen_sphere_core_shell = True
            inp.create_ase_bulk = True

            inp.atomtype_in  = argv[4].lower()
            inp.radius_in    = float(argv[5])

            inp.atomtype_out = argv[7].lower()
            inp.radius_out   = float(argv[8])

            if (inp.atomtype_in not in inp.atomtypes_core_shell):
               output.error(f'Core atom type "{inp.atomtype_in}" not supported.')
            elif (inp.atomtype_out not in inp.atomtypes_core_shell):
               output.error(f'Shell atom type "{inp.atomtype_out}" not supported.')
            elif (inp.atomtype_in == inp.atomtype_out):
               output.error(f"Core and shell atom types coincide.")

            if inp.radius_in >= inp.radius_out: output.error(f'Shell radius must be greater than core radius.')

            # Set to create bulk ase geometry                                                                                      
            inp.atomtype = inp.atomtype_out
            inp.radius = inp.radius_out

         elif (inp.gen_3d_mesh):
            inp.gen_3d_mesh_sphere = True
            inp.create_ase_bulk = False

            inp.radius = float(argv[4])
            inp.mesh_size = float(argv[5])
            inp.mesh_output = f"results_geom/sphere_r_{inp.radius}_mesh_size_{inp.mesh_size}.msh"

         else:
            inp.gen_sphere = True
            inp.create_ase_bulk = True

            inp.radius = float(argv[4])

      elif (argv[2] == '-rod'): 
         if (inp.gen_core_shell):
            inp.gen_rod_core_shell = True
            inp.create_ase_bulk = True

            inp.main_axis = argv[3].lower()
            inp.atomtype_in = argv[5].lower()
            inp.rod_length_in = float(argv[6])
            inp.rod_width_in = float(argv[7])

            inp.atomtype_out = argv[9].lower()
            inp.rod_length_out = float(argv[10])
            inp.rod_width_out = float(argv[11])

            if (inp.atomtype_in not in inp.atomtypes_core_shell):
               output.error(f'Core atom type "{inp.atomtype_in}" not supported.')
            elif (inp.atomtype_out not in inp.atomtypes_core_shell):
               output.error(f'Shell atom type "{inp.atomtype_out}" not supported.')
            elif (inp.atomtype_in == inp.atomtype_out):
               output.error(f"Core and shell atom types coincide.")

            if inp.rod_width_in  >= inp.rod_length_in:  output.error(f"Core rod width must be greater than core length.")
            if inp.rod_width_out >= inp.rod_length_out: output.error(f"Shell rod width must be greater than shell length.")

            if inp.rod_width_in  >= inp.rod_width_out:  output.error(f"Shell rod width must be greater than core rod width.")
            if inp.rod_length_in >= inp.rod_length_out: output.error(f"Shell rod length must be greater than core rod length.")

            # Set to create bulk ase geometry                                                                                      
            inp.atomtype = inp.atomtype_out
            inp.rod_length = inp.rod_length_out
            inp.rod_width = inp.rod_width_out

         elif (inp.gen_3d_mesh):
            inp.gen_3d_mesh_rod = True
            inp.create_ase_bulk = False

            inp.main_axis = argv[4].lower()
            inp.rod_length = float(argv[5])
            inp.rod_width = float(argv[6])
            inp.mesh_size = float(argv[7])

            if inp.rod_width >= inp.rod_length: output.error(f"Rod width must be smaller than length.")

            inp.mesh_output = f"results_geom/rod_{inp.main_axis.upper()}_l_{inp.rod_length}_w_{inp.rod_width}_mesh_size_{inp.mesh_size}.msh"
         else:
            inp.gen_rod = True
            inp.create_ase_bulk = True

            inp.main_axis = argv[4].lower()
            inp.rod_length = float(argv[5])
            inp.rod_width = float(argv[6])

            if inp.rod_width >= inp.rod_length: output.error(f"Rod width must be smaller than length.")

         if inp.main_axis not in inp.axes: output.error(f"Axis {inp.main_axis} not recognized.") 

      elif (argv[2] == '-tip'): 
         inp.gen_tip = True
         inp.create_ase_bulk = True

         inp.z_max = float(argv[4])
         inp.elliptic_parabola_a = float(argv[5])
         inp.elliptic_parabola_b = float(argv[6])

      elif (argv[2] == '-pyramid'): 
         inp.gen_pyramid = True
         inp.create_ase_bulk = True
         inp.z_max = float(argv[4])
         inp.side_length =  float(argv[5])

      elif (argv[2] == '-microscope'): 
         inp.gen_microscope = True
         inp.create_ase_bulk = True
         inp.z_max_paraboloid = float(argv[4])
         inp.elliptic_parabola_a = float(argv[5])
         inp.elliptic_parabola_b = float(argv[6])
         inp.z_max_pyramid = float(argv[7])                                              
         inp.side_length =  float(argv[8])

      elif (argv[2] == '-cone'): 
         inp.gen_cone = True
         inp.create_ase_bulk = True
         inp.z_max = float(argv[4])
         inp.radius = float(argv[5])

      elif (argv[2] == '-ico'): 
         inp.gen_icosahedra = True
         inp.radius = float(argv[4])

      elif (argv[2] == '-cto'): 
         inp.gen_cto = True
         inp.radius = float(argv[4])

      elif (argv[2] == '-idh'): 
         inp.gen_idh = True
         inp.radius = float(argv[4])

      elif (argv[2] == '-bipyramid'):
         inp.gen_bipyramid = True
         inp.create_ase_bulk = True
         inp.bipyramid_width = float(argv[4]) / 2.0 
         inp.bipyramid_length = float(argv[5]) / 2.0

         if inp.bipyramid_width >= inp.bipyramid_length: output.error(f"Bipyramid width must be smaller than length.")

         # Set to create bulk ase geometry
         inp.rod_width  = inp.bipyramid_width
         inp.rod_length = inp.bipyramid_length
         inp.main_axis  = "z"

      elif (inp.gen_pencil): 
         inp.create_ase_bulk = True
         inp.atomtype_in = argv[4].lower()
         inp.atomtype_out = argv[6].lower()
         inp.bipyramid_width = float(argv[7]) / 2.0
         inp.bipyramid_length = float(argv[8]) / 2.0
         inp.rod_length = float(argv[9]) / 2.0

         if inp.bipyramid_length <= inp.bipyramid_width: output.error(f"Pencil shell outer radius must be greater than core inner radius.")
         if inp.bipyramid_length > inp.rod_length: output.error(f"Pencil shell outer length must be greater than or equal to core inner length.")

         if any("-fullshell" in arg.lower() for arg in argv):
             inp.pencil_type = "fullshell"
         elif any("-halfshell" in arg.lower() for arg in argv):
             inp.pencil_type = "halfshell"
         else:
             output.error("Pencil shell type not recognised. \n\n" 
                          "   Options: \n\n"
                          "     -fullshell\n\n" \
                          "     -halfshell")
        
         if (inp.atomtype_in not in inp.atomtypes_core_shell):
             output.error(f'Core atom type "{inp.atomtype_in}" not supported.')
         elif (inp.atomtype_out not in inp.atomtypes_core_shell):
             output.error(f'Shell atom type "{inp.atomtype_out}" not supported.')
         elif (inp.atomtype_in == inp.atomtype_out):
             output.error(f"Core and shell atom types coincide.")
        
         # Set to create bulk ase geometry
         inp.atomtype = inp.atomtype_out
         inp.rod_width  = inp.bipyramid_width*2.0
         inp.rod_length = inp.rod_length*2.0
         inp.main_axis  = "z"

      else:
         output.error(f'Create nanoparticle option "{argv[2]}" not recognized. Try python3 geom -h')

      # Create bulk metal dynamically
      if inp.create_ase_bulk: create_geom.create_ase_bulk_metal(inp, base_dir)

      # Alloy case
      parse_alloy_arguments(argv, inp, output)

      # Create dimer case
      parse_dimer_argument(argv, inp, output)

      # Create bowtie case
      parse_bowtie_argument(argv, inp, output)
# -------------------------------------------------------------------------------------
def parse_dimer_argument(argv, inp, output):
    """
    Parses dimer-related command-line arguments and updates the `inp` object.

    Args:
        argv (list[str]): Command-line arguments list.
        inp (input_class): The input class instance where dimer attributes are stored.
        output (module): The output module for error handling.

    Returns:
        None: Updates inp.create_dimer, inp.distances, and inp.dir_axis_input.

    Notes:
        - Searches for "-dimer" in argv.
        - Reads the next argument as a float and stores it in inp.distances as a list.
        - Reads the following argument as an axis specification (+x, -y, +z, etc.).
        - Ensures the extracted values are valid.
    """

    if "-dimer" in argv:
        inp.create_dimer = True
        idx = argv.index("-dimer")  

        # Ensure there are at least two more arguments after "-dimer" (distance & axis)
        if idx + 2 >= len(argv):
            output.error("Missing dimer distance value or axis after '-dimer'.")

        # Parse the next argument as a float and store it in a list
        try:
            inp.distances = [float(argv[idx + 1])]
        except ValueError:
            output.error(f'Invalid dimer distance "{argv[idx + 1]}". It must be a number.')

        # Ensure the dimer distance is greater than 0
        if inp.distances[0] <= 0:
            output.error(f'Dimer distance "{inp.distances[0]}" must be greater than zero.')

        # Extract and validate the axis argument
        inp.dir_axis_input = argv[idx + 2].lower()

        # Call axis validation function
        check_dir_axis(inp)
# -------------------------------------------------------------------------------------
def parse_bowtie_argument(argv, inp, output):
    """
    Parses bowtie-related command-line arguments and updates the `inp` object.

    Args:
        argv (list[str]): 
            List of command-line arguments.
        inp (input_class): 
            An instance of the input class where bowtie attributes are stored.
        output (module): 
            The output module used for error handling.

    Returns:
        None: 
            This function does not return a value but updates `inp.create_bowtie`, 
            `inp.distances`, and `inp.dir_axis_input`.

    Raises:
        ValueError: 
            If bowtie arguments are missing or contain invalid values.

    Notes:
        - This function checks if "-bowtie" is present in `argv`.
        - If found, it ensures that the bowtie structure is only available 
          for tip, pyramid, cone, and microscope structures.
        - The function then extracts the bowtie distance (must be a positive float).
        - If any validation fails, it calls `output.error()` to handle errors.
    """

    if "-bowtie" in argv:

        # Option only available for tip, pyramid, cone, microscope structures
        if (not inp.gen_tip      and
            not inp.gen_pyramid  and 
            not inp.gen_cone     and 
            not inp.gen_microscope): output.error(f'bowtie structure only available for tip, pyramid, cone, and microscope structures.')

        inp.create_bowtie = True
        idx = argv.index("-bowtie")  

        # Ensure there are at least two more arguments after "-bowtie" (distance & axis)
        if idx + 1 >= len(argv):
            output.error("Missing bowtie distance value.")

        # Parse the next argument as a float and store it in a list
        try:
            inp.distances = [float(argv[idx + 1])]
        except ValueError:
            output.error(f'Invalid dimer distance "{argv[idx + 1]}". It must be a number.')

        # Ensure the bowtie distance is greater than 0
        if inp.distances[0] <= 0:
            output.error(f'Bowtie distance "{inp.distances[0]}" must be greater than zero.')
# -------------------------------------------------------------------------------------
def parse_alloy_arguments(argv, inp, output):
    """
    Parses alloy-related command-line arguments and updates the `inp` object.

    Args:
        argv (list[str]): Command-line arguments list.
        inp (input_class): The input class instance where alloy attributes are stored.
        output (module): The output module for error handling.

    Returns:
        None: Updates `inp` attributes based on the parsed alloy arguments.

    Notes:
        - Handles both cases:
            1. `-alloy atom_type -percentual float`
            2. `-alloy -percentual float`
        - Ensures `inp.alloy_perc` is a **valid float** and **between 0 and 100**.
        - If atom type is omitted, it defaults to `inp.atomtype`.
    """

    # Check if "-alloy" exists in argv
    if "-alloy" in argv:
        inp.alloy = True
        idx = argv.index("-alloy")  # Get index of "-alloy"

        # Ensure there is at least one more argument after "-alloy"
        if idx + 1 >= len(argv):
            output.error("Missing alloy parameters after '-alloy'.")

        # Case 1: Next argument is an atom type
        if argv[idx + 1] != "-percentual":
            inp.atomtype_alloy = argv[idx + 1].lower()
            if idx + 2 >= len(argv) or argv[idx + 2] != "-percentual":
                output.error("Expected '-percentual' after alloy atom type.")

            percentual_idx = idx + 3  # Alloy percentage should be after "-percentual"

        # Case 2: No atom type, only "-percentual float"
        else:
            percentual_idx = idx + 2  # Alloy percentage should be after "-percentual"

        # Ensure there's a percentage value
        if percentual_idx >= len(argv):
            output.error("Missing alloy percentage value after '-percentual'.")

        # Extract and validate alloy percentage
        try:
            inp.alloy_perc = float(argv[percentual_idx])
        except ValueError:
            output.error(f'Invalid alloy percentage "{argv[percentual_idx]}". It must be a number.')

        # Validate range
        if inp.alloy_perc == 0.0 or inp.alloy_perc == 100.0 or inp.alloy_perc < 0.0 or inp.alloy_perc > 100.0:
            output.error(f'Alloy percentual requested {inp.alloy_perc} %. It must be greater than 0 and lower than 100.')

        # Validate atom types if not in core-shell mode
        if not inp.gen_core_shell:
            if inp.atomtype not in inp.atomtypes_alloys:
                output.error(f'Alloy atom type "{inp.atomtype}" not supported.')
            if inp.atomtype_alloy not in inp.atomtypes_alloys:
                output.error(f'Alloy atom type "{inp.atomtype_alloy}" not supported.')
            if inp.atomtype_alloy == inp.atomtype:
                output.error(f'Alloy atom type coincides with original geometry atom type.')

            # Generate alloy string
            inp.alloy_string = f'_alloy_{inp.atomtype_alloy}_{inp.alloy_perc:5.2f}_perc'
# -------------------------------------------------------------------------------------
def check_file_exists(infile):
   """
   Checks if a given file exists.

   Args:
       infile (str): Path to the input file.

   Returns:
       None: Raises an error if the file is not found.
   """

   if (not os.path.exists(infile)): output.error('file "' + infile + '" not found')
# -------------------------------------------------------------------------------------
def check_FCC(atomtype,string):
   """ 
   Checks if the given metallic atom type follows an FCC arrangement.

   Args:
       atomtype (str): Type of metal atom.
       string (str): Structure name being validated.

   Returns:
       None: Raises an error if the atom type is not FCC.
   """

   param = parameters.parameters()

   arrangement = param.atomic_arrangement.get(atomtype)

   if arrangement != 'FCC': output.error(f'"{atomtype.capitalize()}" presents {arrangement} arrangement. FCC is required to create {string}.')
# -------------------------------------------------------------------------------------
def check_FCC_or_BCC(atomtype):
   """ 
   Checks if the given metallic atom type follows either an FCC or BCC arrangement.

   Args:
       atomtype (str): Type of metal atom.

   Returns:
       None: Raises an error if the atom type is not FCC or BCC.
   """

   param = parameters.parameters()

   arrangement = param.atomic_arrangement.get(atomtype)

   if arrangement !='FCC' and arrangement != 'BCC': output.error(f'"{atomtype.capitalize()}" presents {arrangement} arrangement. Only FCC and BCC are supported for metal creation.')
# -------------------------------------------------------------------------------------
def check_file_extension(infile,extension):
   """ 
   Checks if the input file has the correct extension.

   Args:
       infile (str): Path to the input file.
       extension (str): Expected file extension.

   Returns:
       None: Raises an error if the file does not have the expected extension.
   """

   i = len(extension)
   if (infile[-i:] != extension): output.error('extension "' + extension + '" not found in file "' + infile + '"' )
# -------------------------------------------------------------------------------------
def check_file_extension_rdkit(infile,accepted_extensions):
    """ 
    Checks if the input file has a RDKit-supported extension.

    Args:
        infile (str): Path to the input file.
        accepted_extensions (list): List of accepted file extensions for RDKit.

    Returns:
        None: Raises an error if the file extension is not supported.
    """
   
    file_extension = infile[-4:].lower()
    if file_extension not in accepted_extensions:
        msg = (
            f"File extension '{file_extension}' for RDKit not supported.\n\n"
            "   Accepted file extensions:"
            + "".join(f"\n     - {ext}" for ext in accepted_extensions)
        )
        output.error(msg)
# -------------------------------------------------------------------------------------
def check_accepted_parameters(param,accepted_params,label="Parameter"):
    """ 
    Checks if a parameter is in the list of accepted parameters.

    Args:
        param (str): Parameter value to check.
        accepted_params (list): List of accepted parameter values.
        label (str, optional): Label for the parameter in error messages.

    Returns:
        None: Raises an error if the parameter is not in accepted parameters.
    """
   
    if param not in accepted_params:
        msg = (
            f"{label.capitalize()} '{param}' not supported.\n\n"
            "   Accepted entries:"
            + "".join(f"\n     - {parameter}" for parameter in accepted_params)
        )
        output.error(msg)
# -------------------------------------------------------------------------------------
def check_dir_axis(inp):
   """ 
   Validates the direction axis input for translation or rotation.

   Args:
       inp (input_class): An instance containing input parameters.

   Returns:
       input_class: Updated `inp` with validated direction axis settings.

   Notes:
       - Ensures that the axis is properly formatted (e.g., `+x`, `-y`).
       - Assigns the corresponding numerical translation factor.
   """

   if ((len(inp.dir_axis_input) < 2) or 
       (len(inp.dir_axis_input) > 2) or
       (inp.dir_axis_input[1] != 'x' and inp.dir_axis_input[1] != 'y' and inp.dir_axis_input[1] != 'z') or
       (inp.dir_axis_input[0] != '+' and inp.dir_axis_input[0] != '-')): output.error_dir_axis(inp.dir_axis_input)
   
   if (inp.dir_axis_input[0] == '+'): inp.direction =  1.0
   if (inp.dir_axis_input[0] == '-'): inp.direction = -1.0
   if (inp.dir_axis_input[1] =='x') : inp.dir_factor = [inp.direction,0.0,0.0]
   if (inp.dir_axis_input[1] =='y') : inp.dir_factor = [0.0,inp.direction,0.0]
   if (inp.dir_axis_input[1] =='z') : inp.dir_factor = [0.0,0.0,inp.direction]

   return(inp)
# -------------------------------------------------------------------------------------
def create_results_geom():
   """ 
   Creates the `results_geom` directory if it does not already exist.

   Returns:
       None: Ensures that output files can be stored in the correct location.
   """

   #if (os.path.exists('results_geom')):
   #   print(' ')
   #   print(' ------------------------------------------------')
   #   print(f'  WARNING: "results_geom" folder already exists"')
   #   print(' ------------------------------------------------')
   #   print(' ')
   #   erase_results = input('  Do you want to delete it and continue? (y/n)  ')
   #   if(erase_results == "y" or erase_results == "yes"):
   #      os.system(f'rm -rf results_geom')
   #      print(' ')
   #   elif(erase_results == 'n' or erase_results == 'no'):
   #      print(' ')
   #      continue_ = input('  Type "stop" to kill the job, \n' + 
   #                        '  otherwise type any key to continue  ')
   #      print(' ')
   #      if continue_.lower() == 'stop':
   #         print('  Program stopped.')
   #         print(' ')
   #         sys.exit()
   #   else:
   #      print(' ')
   #      print('  I did not understand what you mean by "' + erase_results + '"')
   #      print(' ')
   #      print('  Program stopped.')
   #      print(' ')
   #      sys.exit()

   if (not(os.path.exists('results_geom'))): os.system('mkdir results_geom')
# -------------------------------------------------------------------------------------
def extract_string_or_list(argv, flag):
    """
    Extract the argument(s) that follow a CLI flag.

    Accepts:
      - <flag> CO             -> ["CO"]
      - <flag> "CO"           -> ["CO"]
      - <flag> CO,OH          -> ["CO","OH"]
      - <flag> ["CO","OH"]    -> ["CO","OH"]   (quoted or unquoted list)
      - <flag> [CO, OH]       -> ["CO","OH"]   (bare items)

    Returns a list of strings.
    """
    if flag not in argv:
        return []

    i = argv.index(flag)
    if i + 1 >= len(argv):
        raise ValueError(f'Missing argument after "{flag}"')

    # Grab everything after the flag
    tokens = argv[i+1:]

    # Reassemble if it's a list starting with '['
    if tokens[0].startswith('['):
        depth = 0
        parts = []
        for tok in tokens:
            depth += tok.count('[')
            depth -= tok.count(']')
            parts.append(tok)
            if depth <= 0:
                break
        raw = ' '.join(parts).strip()
    else:
        raw = tokens[0].strip()

    # Try Python literal eval
    try:
        if raw.startswith('['):
            val = ast.literal_eval(raw)
            if isinstance(val, (list, tuple)):
                return [str(x).strip().strip('"').strip("'") for x in val]
            return [str(val)]
        else:
            if ',' in raw:
                return [p.strip().strip('"').strip("'") for p in raw.split(',') if p.strip()]
            return [raw.strip().strip('"').strip("'")]
    except Exception:
        # Fallback for [CO, OH] without quotes
        if raw.startswith('[') and raw.endswith(']'):
            inner = raw[1:-1]
            items = [p.strip().strip('"').strip("'") for p in inner.split(',') if p.strip()]
            return items
        return [raw.strip().strip('"').strip("'")]
# -------------------------------------------------------------------------------------
def extract_value(argv, flag, value_type):
    """
    Extract the argument that follows a CLI flag and cast it to a given type.

    Args:
        argv (list): Command-line arguments.
        flag (str): Flag to search for (case-insensitive).
        value_type (type): Expected Python type (e.g., str, int, float).

    Returns:
        The value converted to the expected type.

    Raises:
        ValueError: If the flag is present but has no value, 
                    or if the value cannot be converted to the expected type.
        SystemExit: If the flag is not found (via output.error()).
    """
    # Normalize for case-insensitive search
    argv_lower = [arg.lower() for arg in argv]
    flag_lower = flag.lower()

    if flag_lower not in argv_lower:
        output.error(f'Requested flag "{flag}" not found')

    i = argv_lower.index(flag_lower)

    # Case 1: flag is last in argv → no value provided
    if i + 1 >= len(argv):
        raise ValueError(f'Missing argument after "{flag}"')

    token = argv[i + 1]

    # Case 2: next token looks like another flag → treat as missing
    if token.startswith("-"):
        raise ValueError(f'Missing argument after "{flag}" (found another flag \"{token}\")')

    # Type validation
    try:
        if value_type is str:
            value = token
        elif value_type is int:
            value = int(token)
        elif value_type is float:
            value = float(token)
        else:
            raise TypeError(f'Unsupported value_type "{value_type.__name__}". '
                            'Allowed: str, int, float.')
    except ValueError:
        raise ValueError(f'Expected a {value_type.__name__} after "{flag}", got "{token}"')

    return value
# -------------------------------------------------------------------------------------
def extract_value_or_default(argv, flag, value_type=str, default=None):
    """
    Extract the argument that follows a CLI flag and cast it to a given type.
    If the flag is absent or has no following value, return the provided default.
    If the flag is present but the value is not convertible to the requested type, raise ValueError.

    Args:
        argv (list[str]): Command-line arguments.
        flag (str): Flag to search for (case-insensitive).
        value_type (type): One of {str, int, float}.
        default (Any): Default value if the flag is missing or has no argument.
                       If not None, its type must match `value_type`.

    Returns:
        Any: The value converted to `value_type`, or `default` when appropriate.

    Raises:
        TypeError: If `value_type` is unsupported, or `default`'s type doesn't match `value_type`.
        ValueError: If the flag is present but the following token can't be converted to `value_type`.
    """
    # Validate requested type
    if value_type not in (str, int, float):
        raise TypeError(f'Unsupported value_type "{getattr(value_type, "__name__", value_type)}". Allowed: str, int, float.')

    # Validate default type (allow None)
    if default is not None and not isinstance(default, value_type):
        raise TypeError(
            f'Default value type mismatch for flag "{flag}": '
            f'expected {value_type.__name__}, got {type(default).__name__}.'
        )

    # Case-insensitive search for the flag
    argv_lower = [a.lower() for a in argv]
    flag_lower = flag.lower()

    # If flag not present → return default
    if flag_lower not in argv_lower:
        return default

    i = argv_lower.index(flag_lower)

    # Flag is last token → no value provided → return default
    if i + 1 >= len(argv):
        return default

    token = argv[i + 1]

    # Next token looks like another flag → treat as missing → return default
    if token.startswith("-"):
        return default

    # Cast to the requested type
    try:
        if value_type is str:
            return token
        elif value_type is int:
            return int(token)
        elif value_type is float:
            return float(token)
    except ValueError as e:
        raise ValueError(
            f'Invalid {value_type.__name__} value "{token}" provided for flag "{flag}".'
        ) from e
# -------------------------------------------------------------------------------------
def check_equal_extensions(infile1,infile2):
   """ 
   Checks if two input files have the same extension. If yes, raises an error.

   Args:
       infile1 (str): Path to the first input file.
       infile2 (str): Path to the second input file.
    """
   
   ext1 = infile1[-4:].lower()
   ext2 = infile2[-4:].lower()

   if (ext1 == ext2): output.error('input files must have different extensions ("' + ext1 + '" found in both files)')
# -------------------------------------------------------------------------------------
