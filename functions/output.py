import sys

# -------------------------------------------------------------------------------------
def error(error_message):
   #
   """ 
   Raise error and stop

   :error_message : Error message to raise
   """
   #
   print("")
   print("")
   print("   " + error_message)
   print("")
   print("")
   sys.exit()
# -------------------------------------------------------------------------------------
def error_dir_axis(dir_axis_input):
   #
   """ 
   Raise error related to axis input

   :dir_axis_input: Direction axis not supported
   """
   #
   print(' ')
   print(' ERROR: Sense or direction axis "' + dir_axis_input + '" not supported')
   print(' ')
   print('    Options:')
   print('    --------')
   print('      +x, +y, +z')
   print('      -x, -y, -z')
   print(' ')
   sys.exit()
# -------------------------------------------------------------------------------------
def logfile_init():
   #
   """
   Initialize logfile memory unit
   """
   #
   out_log = open('results_geom/logfile.txt','w')

   return(out_log)
# -------------------------------------------------------------------------------------
def logfile_close(out_log):
   #
   """
   Close logfile memory unit
   """
   #
   out_log.close()

   return(out_log)
# -------------------------------------------------------------------------------------
def print_geom(molecule,output_file):
   #
   """
   Print geometry to xyz file

   :molecule   : molecule class 
   :output_file: output file name
   """
   #
   with open(f'results_geom/{output_file}.xyz', 'w') as out_f:
       out_f.write(f"{molecule.nAtoms}\n")
       out_f.write('Generated with GEOM code\n')

       for i in range(molecule.nAtoms):
           atom, x, y, z = molecule.atoms[i], *molecule.xyz[:, i]
           out_f.write(f'{atom.capitalize():2} {x:20.8f} {y:20.8f} {z:20.8f}\n')
# -------------------------------------------------------------------------------------
def print_optimization_starts():
   #
   """
   Print optimization starts banner
   """
   #
   print(' ')
   print(' ')
   print(' ===================================== ')
   print(' DISTANCE OPTIMIZATION PROCESS STARTED')
   print(' ===================================== ')
   print(' ')
# -------------------------------------------------------------------------------------
def print_optimizing_distance(distance):
   #
   """
   Print optimization distance message
   """
   # 
   print(f'  ------ Optimizing d = {distance} Å ------ ')  
   print('\n')
# -------------------------------------------------------------------------------------
def print_computed_distance(dist):
   #
   """
   Print computed distance
   """
   # 
   print('  Computed distance = ' + str(round(dist,4)) + ' Å')
   print('\n') 
# -------------------------------------------------------------------------------------
def print_convergence_achieved(dist):
   #
   """
   Print converged achieved 
   """
   # 
   print('  Convergence achieved to distance ' +  str(round(dist,4)) + ' Å') 
   print('')
# -------------------------------------------------------------------------------------
def save_distance_opt(out_log,distance,dist_new,dir_axis_input):
   #
   """
   Save converged distance in logfile
   """
   #
   out_log.write(f"\n"
                 f" {' ------ Optimizing d =':>22} {distance:20.8f} {'Å ------ ':>12}\n\n")
   
   out_log.write(f" {'  Convergence achieved to distance':>34} {dist_new:20.8f} {'Å':>5}\n\n\n")
# -------------------------------------------------------------------------------------
def print_normal_termination(inp):
   #
   """
   Print normal termination banner
   """
   #
   if (not inp.min_dist and not inp.geom_center):
      print(' ')
      print(' ===================================== ')
      print('           NORMAL TERMINATION          ')
      print(' ===================================== ')
      print(' ')
# -------------------------------------------------------------------------------------
def print_min_dist(inp,distance):
   #
   """
   Print minimum distance
   """
   #
   distance = round(distance,4)

   print('')
   print('  -----------------------------------------------')
   print(f'    Geometry 1: {inp.geom1_file}')
   print(f'    Geometry 2: {inp.geom2_file}')
   print('')
   print(f'    Minimum\n    distance  : {distance} Å')
   print('  -----------------------------------------------')
   print('')
# -------------------------------------------------------------------------------------
def print_geom_center(inp,xyz_c):
   #
   """
   Print geometrical center of given molecule distance

   :inp  : input class
   :xyz_c: geometrical center
   """
   #
   x = round(xyz_c[0],4)
   y = round(xyz_c[1],4)
   z = round(xyz_c[2],4)

   print('')
   print('  ------------------------------------------')
   print(f'    Geometry : {inp.geom_file}')
   print('')
   print(f'    Geometrical \n    Center (xyz,Å)  : {x} {y} {z} ')
   print('  ------------------------------------------')
   print('')
# -------------------------------------------------------------------------------------
