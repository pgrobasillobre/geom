from functions import general

class input_class:
    #
    """Input class"""
    #
    def __init__(self):
        
       # -- Translate
       self.translate_controlled_distance   = False
       self.translate_1 = False
       self.move_geom_1_to_000 = False
       self.move_geom_2_to_000 = False

       self.distances  = []
       self.dir_factor = []
 
       self.distances_input = ''
       self.geom1_file      = ''
       self.geom2_file      = ''
       self.dir_axis_input  = ''
       self.origin_CM_1     = ''
       self.origin_CM_2     = '' 

       self.direction = 1.0

       # -- Minimum distance
       self.minimum_distance = False
       
       # -- Rotate
       self.rotate   = False
       self.rotate_1 = False
       self.move_geom_to_000 = False
       self.angles = []
       
       # -- Center grid points
       self.centers_grid = False

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
          self.read_input_distances()

          general.check_file_exists(self.geom1_file)
          general.check_file_exists(self.geom2_file)

          general.check_file_extension(self.geom1_file,'.xyz')
          general.check_file_extension(self.geom2_file,'.xyz')

          general.check_dir_axis(self)

    # ------------------------------------ #
    # ------- Read input distances ------- #

    def read_input_distances(self):
       #
       """
       Read input file containing distances in each line
       """
       #
       with open(self.distances_input) as infile:
          for line in infile:
             if len(line.split()) == 0: output.error(f'STOP: blank line found in distances input file "{self.distances_input}"')
             if len(line.split())  > 1: output.error(f'STOP: more than one distance found in a single line of input file "{self.distances_input}"')

             self.distances.append(float(line.split()[0])) 

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
 
 

