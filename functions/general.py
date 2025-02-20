import sys
import os

from functions import output, create_geom

# -------------------------------------------------------------------------------------
def read_command_line(argv, inp):
    if len(argv) < 2:
        output.error("Missing command line arguments.")
    command = argv[1]
    if command in ['-h', '-help']:
        print_help()
    elif command == '-t' or command =='-t1':
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
    else:
        output.error("ERROR: Option not recognized. Try python3 geom -h")
# -------------------------------------------------------------------------------------
def print_help():
    """ 
    Prints help message and exits 
    """
    #

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

         Nanoparticles (Ag/Au/Na):

           Sphere: -create -sphere atom_type radius center_x center_y center_z [optional: -alloy atom_type -percentual float]
 
           Spherical core-shell (Au/Ag): -create -sphere -core r_core atom_type -shell r_shell atom_type [optional: -alloy -percentual float]

           Rod: -create -rod atom_type length width main_axis{X/Y/Z} [optional: -alloy atom_type -percentual float]

           Rod core-shell (Au/Ag): -create -rod main_axis{X/Y/Z} -core atom_type length width -shell atom_type length width [optional: -alloy atom_type -percentual float]

           Tip (elliptic paraboloid): -create -tip atom_type z_max a b [optional: -alloy atom_type -percentual float]

           Pyramid (square base): -create -pyramid atom_type z_max base_side_length [optional: -alloy atom_type -percentual float]

           Cone: -create -cone atom_type z_max base_radius [optional: -alloy atom_type -percentual float]

           Microscope: -create -microscope atom_type z_max_paraboloid a b z_max_pyramid base_side_length [optional: -alloy atom_type -percentual float]

           Icosahedral: -create -ico atom_type radius

    '''
    print(help_text)
    sys.exit()
# -------------------------------------------------------------------------------------
def parse_translation(argv, inp):
   """
   Parse translation command line

   :argv : arguments list
   :inp  : input class
   """
   #
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
# -------------------------------------------------------------------------------------
def parse_rotation(argv, inp):
   """
   Parse rotation command line

   :argv : arguments list
   :inp  : input class
   """
   #
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
   Parse mirror command line

   :argv : arguments list
   :inp  : input class
   """
   #
   inp.geom_specular = True
   inp.geom_file = str(argv[2])
# -------------------------------------------------------------------------------------
def parse_merge(argv, inp):
   """
   Parse merge command line

   :argv : arguments list
   :inp  : input class
   """
   #
   inp.merge = True
   inp.geom1_file = str(argv[2])
   inp.geom2_file = str(argv[3])
   inp.merge_cutoff = float(argv[4])
# -------------------------------------------------------------------------------------
def parse_min(argv, inp):
   """
   Parse min command line

   :argv : arguments list
   :inp  : input class
   """
   #
   inp.min_dist = True
   inp.geom1_file = str(argv[2])
   inp.geom2_file = str(argv[3])
# -------------------------------------------------------------------------------------
def parse_center(argv, inp):
   """
   Parse center command line

   :argv : arguments list
   :inp  : input class
   """
   #
   inp.geom_center = True
   inp.geom_file = str(argv[2])
# -------------------------------------------------------------------------------------
def parse_create(argv, inp):
   """
   Parse create command line

   :argv : arguments list
   :inp  : input class
   """
   #
   inp.create_geom = True 

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
         if (inp.radius_in >= inp.radius_out): output.error(f'Inner radius must be smaller than Outter radius.')

      elif inp.graphene_structure == 'triangle':
         inp.graphene_edge_type = argv[4]
         inp.side_length = float(argv[5])
         if inp.graphene_edge_type not in inp.graphene_edge_types:
            output.error(f'Requested edge type "{inp.graphene_edge_type}" not recognised')

      # Create bulk graphene dynamically
      create_geom.create_ase_bulk_graphene(inp, base_dir)

   else:
      if ('-core' and '-shell') in argv: 
         inp.gen_core_shell = True

      else:
         inp.atomtype = argv[3].lower()
         if inp.atomtype not in inp.metal_atomtypes: output.error(f'Atom Type "{argv[3]}" not recognised')

      if (argv[2] == '-sphere'): 
         if (inp.gen_core_shell): 
            inp.gen_sphere_core_shell = True
            inp.create_ase_bulk = True

            inp.radius_in    = float(argv[4])
            inp.atomtype_in  = argv[5]
            inp.radius_out   = float(argv[7])
            inp.atomtype_out = argv[8]

            inp.sphere_center = [0.0, 0.0, 0.0]

            if (inp.atomtype_in not in inp.atomtypes_core_shell):
               output.error(f'Core atom type "{inp.atomtype_in}" not supported.')
            elif (inp.atomtype_out not in inp.atomtypes_core_shell):
               output.error(f'Shell atom type "{inp.atomtype_out}" not supported.')
            elif (inp.atomtype_in == inp.atomtype_out):
               output.error(f"Core and shell atom types coincide.")

            # Set to create bulk ase geometry                                                                                      
            inp.atomtype = inp.atomtype_out
            inp.radius = inp.radius_out

         else:
            inp.gen_sphere = True
            inp.create_ase_bulk = True

            inp.radius = float(argv[4])
            for i in range(3): inp.sphere_center[i] = float(argv[5+i])

      elif (argv[2] == '-rod'): 
         if (inp.gen_core_shell):
            inp.gen_rod_core_shell = True
            inp.create_ase_bulk = True

            inp.main_axis = argv[3].lower()
            inp.atomtype_in = argv[5]
            inp.rod_length_in = float(argv[6])
            inp.rod_width_in = float(argv[7])

            inp.atomtype_out = argv[9]
            inp.rod_length_out = float(argv[10])
            inp.rod_width_out = float(argv[11])

            if (inp.atomtype_in not in inp.atomtypes_core_shell):
               output.error(f'Core atom type "{inp.atomtype_in}" not supported.')
            elif (inp.atomtype_out not in inp.atomtypes_core_shell):
               output.error(f'Shell atom type "{inp.atomtype_out}" not supported.')
            elif (inp.atomtype_in == inp.atomtype_out):
               output.error(f"Core and shell atom types coincide.")

            # Set to create bulk ase geometry                                                                                      
            inp.atomtype = inp.atomtype_out
            inp.rod_length = inp.rod_length_out
            inp.rod_width = inp.rod_width_out
  
         else:
            inp.gen_rod = True
            inp.create_ase_bulk = True

            inp.rod_length = float(argv[4])
            inp.rod_width = float(argv[5])
            inp.main_axis = argv[6].lower()

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


      # Create bulk metal dynamically
      if inp.create_ase_bulk: create_geom.create_ase_bulk_metal(inp, base_dir)

      # Alloy case
      if ('-alloy' in argv): inp.alloy = True
    
      if (inp.alloy):
         inp.alloy_perc = float(argv[-1])
         if (inp.alloy_perc == 0.0   or 
             inp.alloy_perc == 100.0 or 
             inp.alloy_perc  < 0.0   or
             inp.alloy_perc  > 100.0): output.error(f'Alloy percentual requested {inp.alloy_perc} %. It must be greater than 0 and lower than 100')

         if not inp.gen_core_shell:
            inp.atomtype_alloy = argv[-3].lower()
            if inp.atomtype_alloy not in inp.metal_atomtypes: output.error(f"Alloy atom type {inp.atomtype_alloy} not supported.")
            if inp.atomtype_alloy == inp.atomtype: output.error(f"Alloy atom type coincides with original geometry atom type.")

            inp.gen_core_shell: inp.alloy_string = f'_alloy_{inp.atomtype_alloy}_{inp.alloy_perc:5.2f}_perc'
# -------------------------------------------------------------------------------------
def check_file_exists(infile):
   #
   """ 
   Check if file exist

   :infile : Input file to check
   """
   #
   if (not os.path.exists(infile)): output.error('STOP: file "' + infile + '" not found')
# -------------------------------------------------------------------------------------
def check_file_extension(infile,extension):
   #
   """ 
   Check file extension

   :infile   : Input file to check
   :extension: 
   """
   #
   i = len(extension)
   if (infile[-i:] != extension): output.error('STOP: extension "' + extension + '" not found in file "' + infile + '"' )
# -------------------------------------------------------------------------------------
def check_dir_axis(inp):
   #
   """ 
   Check direction axis to translate/rotate

   :inp: input class
   """
   #
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
   #
   """ 
   Create results folder
   """
   #
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
