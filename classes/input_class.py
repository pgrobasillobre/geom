from functions import general, output

class input_class:
   #
   """Input class"""
   #
   def __init__(self):
       
      # -- Translate
      self.translate_controlled_distance = False
      self.translate_1 = False
     
      self.move_geom_to_000   = False
      self.move_geom_1_to_000 = False
      self.move_geom_2_to_000 = False

      self.distances  = []
      self.dir_factor = []

      self.distances_input = ''
      self.geom_file       = ''
      self.geom1_file      = ''
      self.geom2_file      = ''
      self.dir_axis_input  = ''
      self.origin_CM       = ''
      self.origin_CM_1     = ''
      self.origin_CM_2     = '' 

      self.direction = 1.0

      # -- Minimum distance
      self.min_dist = False
      
      # -- Rotate
      self.rotate_angles = False
      self.rotate_1      = False

      self.angles = []

      self.angles_input = ''

      self.angle = 0.0
      
      # -- Geometrical center
      self.geom_center = False

      # -- Specular geometry
      self.geom_specular = False

      # -- Generate structure geometry
      self.create_geom = False
      self.gen_graphene = False
      self.gen_tip = False
      self.gen_cone = False
      self.gen_pyramid = False
      self.gen_microscope = False
      self.elliptic_parabola_a = 1.0 # Modifies stepness along x
      self.elliptic_parabola_b = 1.0 # Modifies stepness along y
      self.elliptic_parabola_c = 0.0 # Fixed for xy parabolloid
      self.z_min = 0.0 
      self.z_max = 0.0 
      self.z_max_paraboloid = 0.0
      self.z_max_pyramid = 0.0 
      self.side_length = 0.0
      self.radius = 0.0
      self.X_length = 0.0
      self.Y_length = 0.0

      self.atomtype = ''
      self.graphene_structures  = ["rib","disk","triangle"]
      self.graphene_structure   = ""
      self.graphene_edge_types  = ["armchair","zigzag"]
      self.graphene_edge_type   = ""

      # -- Merge geometries
      self.merge = False
      self.merge_cutoff = 2.88 # Defaul for Ag/Au
      self.lc = 4.09 # Default reticular distance Ag/Au

      # -- Verbose
      self.verbose = False
      self.verbose_inp = ''

   # -------------------------------- #
   # ------- Check input case ------- #
   
   def check_input_case(self):
      #
      """
      Check requirements for selected cases
      """
      #
      if (self.translate_controlled_distance):
         general.check_file_exists(self.distances_input)
         self.read_input(what='distances')

         general.check_file_exists(self.geom1_file)
         general.check_file_exists(self.geom2_file)

         general.check_file_extension(self.geom1_file,'.xyz')
         general.check_file_extension(self.geom2_file,'.xyz')

         general.check_dir_axis(self)

      elif (self.translate_1):
         general.check_file_exists(self.geom_file)
         general.check_file_extension(self.geom_file,'.xyz')

         general.check_dir_axis(self)

      elif (self.rotate_angles):
         general.check_file_exists(self.angles_input)
         self.read_input(what='angles')

         general.check_file_exists(self.geom_file)
         general.check_file_extension(self.geom_file,'.xyz')

         general.check_dir_axis(self)

      elif (self.rotate_1):
         general.check_file_exists(self.geom_file)
         general.check_file_extension(self.geom_file,'.xyz')

         general.check_dir_axis(self)

      elif (self.min_dist):
         general.check_file_exists(self.geom1_file)
         general.check_file_exists(self.geom2_file)

         general.check_file_extension(self.geom1_file,'.xyz')
         general.check_file_extension(self.geom2_file,'.xyz')

      elif (self.merge):
         general.check_file_exists(self.geom1_file)
         general.check_file_exists(self.geom2_file)

         general.check_file_extension(self.geom1_file,'.xyz')
         general.check_file_extension(self.geom2_file,'.xyz')

      elif (self.geom_center):
         general.check_file_exists(self.geom_file)
         general.check_file_extension(self.geom_file,'.xyz')

      elif (self.geom_specular):
         general.check_file_exists(self.geom_file)
         general.check_file_extension(self.geom_file,'.xyz')

      elif (self.create_geom):
         if (not self.gen_graphene and
             not self.gen_tip      and 
             not self.gen_pyramid  and
             not self.gen_cone     and
             not self.gen_microscope): output.error("Create geom option not recognised.")

         general.check_file_exists(self.geom_file)
         general.check_file_extension(self.geom_file,'.xyz')


   # ------------------------------------------- #
   # ------- Read distances/angles input ------- #

   def read_input(self,what):
      #
      """
      Read input file containing distances/angles in each line
      """
      #
      if (what=='distances'):
         with open(self.distances_input) as infile:
            for line in infile:
               if len(line.split()) == 0: output.error(f'STOP: blank line found in distances input file "{self.distances_input}"')
               if len(line.split())  > 1: output.error(f'STOP: more than one distance found in a single line of input file "{self.distances_input}"')

               self.distances.append(float(line.split()[0])) 

      elif (what=='angles'):
         with open(self.angles_input) as infile:
            for line in infile:
               if len(line.split()) == 0: output.error(f'STOP: blank line found in angles input file "{self.angles_input}"')
               if len(line.split())  > 1: output.error(f'STOP: more than one angle found in a single line of input file "{self.angles_input}"')

               self.angles.append(float(line.split()[0])) 

   # ---------------------------------------- #
   # ------- Change translation sense ------- #
   
   def change_trans_sense(self):
      #
      """
      Change translation sanse
      """
      #
      self.dir_factor = [-x for x in self.dir_factor] 

      return(self)



