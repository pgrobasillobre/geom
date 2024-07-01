import sys
import os

from functions import output

# -------------------------------------------------------------------------------------
def read_command_line(argv,inp):
   #
   """ 
   Read command line

   :argv : arguments list
   :inp  : input class
   """
   #
   if argv[1] == '-h' or argv[1] == '-help':
      print ('')
      print ('  ==========')
      print ('  Execution:')
      print ('  ==========')
      print ('')
      print ('     * The inputs must contain each angle(degrees)/distance(Å) in different lines, ending with a non-blank line')
      print ('')
      print ('     ------------')
      print ('     Translation:')
      print ('     ------------')
      print ('')
      print ('     Distances in input (controlled dist between 2 files):')
      print ('')
      print ('     ./geom.py -t distances_input geom1.xyz origin_CM_1{origin_CM_1_yes/no} geom2.xyz origin_CM{origin_CM_2_yes/no} axis{+-}{x/y/z} verbose{verbose_yes/no}')
      print ('')
      print ('     One translation:')
      print ('')
      print ('     ./geom.py -t1 shift geom.xyz origin_CM{origin_CM_yes/no} axis{+-}{x/y/z}')
      print ('')
      print ('')
      print ('     ---------')
      print ('     Rotation:')
      print ('     ---------')
      print ('')
      print ('     Angles in input:')
      print ('')
      print ('     ./geom.py -r angles_input geom1.xyz origin_CM{origin_CM_yes/no} axis{+-}{x/y/z}')
      print ('')
      print ('     One rotation:')
      print ('')
      print ('     ./geom.py -r1 angle geom1.xyz origin_CM{origin_CM_yes/no} axis{+-}{x/y/z}')
      print ('')
      print ('')
      print ('     -----------------')
      print ('     Minimum Distance:')
      print ('     -----------------')
      print ('')
      print ('     ./geom.py -min geom1.xyz geom2.xyz')
      print ('')
      print ('')
      print ('     --------------------')
      print ('     Centers grid points:')
      print ('     --------------------')
      print ('')
      print ('     ./geom.py -c geom_inputs')
      print ('')
   
      sys.exit()
    
   elif argv[1] == '-t':
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
      inp.translate_1     = True
      inp.shift_t1        = float(argv[2])
      inp.geom2_file      = str(argv[3]) 
      inp.origin_CM_2     = str(argv[4])
      inp.dir_axis_input  = str(argv[5])
   
   elif argv[1] == '-r':
      inp.rotate = True
      inp.angles_input    = str(argv[2])
      inp.geom1_file      = str(argv[3]) 
      inp.origin_CM       = str(argv[4])
      inp.dir_axis_input  = str(argv[5])
   
   elif argv[1] == '-r1':
      inp.rotate_1 = True
      inp.angle           = float(argv[2])
      inp.geom1_file      = str(argv[3]) 
      inp.origin_CM       = str(argv[4])
      inp.dir_axis_input  = str(argv[5])
   
   elif argv[1] == '-min':
      inp.minimum_distance = True
      inp.geom1_file      = str(argv[2])
      inp.geom2_file      = str(argv[3])
   
   elif argv[1] == '-c':
      inp.centers_grid = True
      inp.input_geom_files = str(argv[2])
   
   else:
      print ('')
      print ('   ERROR: Option not recognised.')
      print ('')
      print ('   --> Try ./geom.py -h')
      print ('')
   
      sys.exit()
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
   if (os.path.exists(f'results_geom')):
      print(' ')
      print(' ------------------------------------------------')
      print(f'  WARNING: "results_geom" folder already exists"')
      print(' ------------------------------------------------')
      print(' ')
      erase_results = input('  Do you want to delete it and continue? (y/n)  ')
      if(erase_results == "y" or erase_results == "yes"):
         os.system(f'rm -rf results_geom')
         print(' ')
      elif(erase_results == 'n' or erase_results == 'no'):
         print(' ')
         continue_ = input('  Type "stop" to kill the job, \n' + 
                           '  otherwise type any key to continue  ')
         print(' ')
         if continue_.lower() == 'stop':
            print('  Program stopped.')
            print(' ')
            sys.exit()
      else:
         print(' ')
         print('  I did not understand what you mean by "' + erase_results + '"')
         print(' ')
         print('  Program stopped.')
         print(' ')
         sys.exit()

   os.system(f'mkdir results_geom')
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------
