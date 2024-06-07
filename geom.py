from __future__ import division
import sys
import re
import math
import numpy as np
import os.path
import os

#                    ██████╗ ███████╗ ██████╗ ███╗   ███╗     ██████╗ ██████╗ ██████╗ ███████╗                
#                   ██╔════╝ ██╔════╝██╔═══██╗████╗ ████║    ██╔════╝██╔═══██╗██╔══██╗██╔════╝                
#   █████╗█████╗    ██║  ███╗█████╗  ██║   ██║██╔████╔██║    ██║     ██║   ██║██║  ██║█████╗      █████╗█████╗
#   ╚════╝╚════╝    ██║   ██║██╔══╝  ██║   ██║██║╚██╔╝██║    ██║     ██║   ██║██║  ██║██╔══╝      ╚════╝╚════╝
#                   ╚██████╔╝███████╗╚██████╔╝██║ ╚═╝ ██║    ╚██████╗╚██████╔╝██████╔╝███████╗                
#                    ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝     ╚═╝     ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝                
   
#
# PURPOSE: Managing xyz files to translate and rotate 
#
# EXECUTION details: python3 geom.py -h 
#

# ========================================================================
# ============================== GENERAL =================================

# -- Convergence options
convergence      = 0.010
convergence_step = 0.010

# -- General parameters
zero = 0.0
one  = 1.0
two  = 2.0

min_dist = 1.0

# -- Input stuff
# translate
translate   = False
translate_1 = False
move_geom_1_to_000 = False
move_geom_2_to_000 = False
distances     = []

# rotate
rotate   =  False
rotate_1 = False
move_geom_to_000 = False
angles        = []

# minimum distance
minimum_distance = False

# Center grid points
centers_grid = False

# ========================================================================
# ========================= READ COMMAND LINE ============================


# -- Read command line
if sys.argv[1] == '-h' or sys.argv[1] == '-help':
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
   print ('     ./geom.py -t distances_input geom1.xyz origin_CM_1{origin_CM_1_yes/no} geom2.xyz origin_CM{origin_CM_2_yes/no} axys{+-}{x/y/z} verbose{verbose_yes/no}')
   print ('')
   print ('     One translation:')
   print ('')
   print ('     ./geom.py -t1 shift geom.xyz origin_CM{origin_CM_yes/no} axys{+-}{x/y/z}')
   print ('')
   print ('')
   print ('     ---------')
   print ('     Rotation:')
   print ('     ---------')
   print ('')
   print ('     Angles in input:')
   print ('')
   print ('     ./geom.py -r angles_input geom1.xyz origin_CM{origin_CM_yes/no} axys{+-}{x/y/z}')
   print ('')
   print ('     One rotation:')
   print ('')
   print ('     ./geom.py -r1 angle geom1.xyz origin_CM{origin_CM_yes/no} axys{+-}{x/y/z}')
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
 
elif sys.argv[1] == '-t':
   translate = True
   distances_input = str(sys.argv[2])
   geom1_file      = str(sys.argv[3]) 
   origin_CM_1     = str(sys.argv[4])
   geom2_file      = str(sys.argv[5])
   origin_CM_2     = str(sys.argv[6])
   dir_axis_input  = str(sys.argv[7])
   verbose_inp     = str(sys.argv[8])

elif sys.argv[1] == '-t1':
   translate_1     = True
   shift_t1        = float(sys.argv[2])
   geom2_file      = str(sys.argv[3]) 
   origin_CM_2     = str(sys.argv[4])
   dir_axis_input  = str(sys.argv[5])

elif sys.argv[1] == '-r':
   rotate = True
   angles_input    = str(sys.argv[2])
   geom1_file      = str(sys.argv[3]) 
   origin_CM       = str(sys.argv[4])
   dir_axis_input  = str(sys.argv[5])

elif sys.argv[1] == '-r1':
   rotate_1 = True
   angle           = float(sys.argv[2])
   geom1_file      = str(sys.argv[3]) 
   origin_CM       = str(sys.argv[4])
   dir_axis_input  = str(sys.argv[5])

elif sys.argv[1] == '-min':
   minimum_distance = True
   geom1_file      = str(sys.argv[2])
   geom2_file      = str(sys.argv[3])

elif sys.argv[1] == '-c':
   centers_grid = True
   input_geom_files = str(sys.argv[2])

else:
   print ('')
   print ('   ERROR: Option not recognised.')
   print ('')
   print ('   --> Try ./geom.py -h')
   print ('')

   sys.exit()



# ========================================================================
# ==============================  FUNCTIONS ==============================
#
# ------------------------------- #
# ------- Read geometries ------- #

def read_geom(input_file):
#
   """
   Function to read geometries from xyz file

   :input_file: file with geometry in xyz format
   """
#
   with open(input_file, 'r') as infile:
      n_atoms = int(infile.readline())
      infile.readline()
#   
      atoms = []
      x = [] 
      y = [] 
      z = []
#   
      for line in infile:
         line = line.split()
         atoms.append(line[0])
         x.append([float(line[1])])
         y.append([float(line[2])])
         z.append([float(line[3])])
#   
   return(n_atoms,atoms,x,y,z)

# -------------------------------------------- #
# ------- Change translation direction ------- #

def change_trans_dir():
#
   """
   Function to change the direction for translation of geom2

   """
#
   factor_x_ = -one * factor_x 
   factor_y_ = -one * factor_y 
   factor_z_ = -one * factor_z 
#   
   return(factor_x_,factor_y_,factor_z_)

# ------------------------------------------ #
# ------- Calculate minimum distance ------- #

def calc_min_distance():
#
   """
   Function to calculate the minimum distance between geom1 and geom2

   :x1, y1, z1: coordinates of geom1
   :x2, y2, z2: coordinates of geom2

   :return: dist; minimum distance between the two geometries
   """ 
#
   distIJ_min = 999999999999.9 # Initialize
#
   for i in range(n_geom2):
      for j in range(n_geom1):
         x_IJ =  np.array(x2[i]) - np.array(x1[j])
         y_IJ =  np.array(y2[i]) - np.array(y1[j])
         z_IJ =  np.array(z2[i]) - np.array(z1[j])
#
         distIJ = math.sqrt(x_IJ**two + y_IJ**two + z_IJ**two)
#
         if(distIJ < distIJ_min): distIJ_min = distIJ
#
   dist = distIJ_min
#
   return dist



# ------------------------------------------------- #
# ------- Translate geometry along dir_axis ------- #
#

def translate_geom(shift):
#
   """
   Function to translate geom2 along dir_axis

   :return: dist; minimum distance between the two geometries
   """ 
#
   x = []
   y = []
   z = []
#
   for i in range(n_geom2):
      x.append(float(np.array(x2[i]) + factor_x * shift))  
      y.append(float(np.array(y2[i]) + factor_y * shift)) 
      z.append(float(np.array(z2[i]) + factor_z * shift)) 

   return(x,y,z)


# ----------------------------------------------------------- #
# ------- Translate geometry to origin of coordinates ------- #
#

def translate_geom_to_000(geom_center,x0,y0,z0):
#
   """
   Function to translate a given geometry to the origin of coordinates

   :return: dist; minimum distance between the two geometries
   """
#
   x = []
   y = []
   z = []
#
   for i in range(len(x0)):
      x.append(float(np.array(x0[i]) - geom_center[0]))
      y.append(float(np.array(y0[i]) - geom_center[1]))
      z.append(float(np.array(z0[i]) - geom_center[2]))

   return(x,y,z)


# -------------------------------------------- #
# ------- Rotate geometry along x axis ------- #
#

def rotate_x(x, y, z, angle_):

    theta = math.radians(angle_)

    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)

    x_rot = x
    y_rot = [np.array(y[i]) * cos_theta - np.array(z[i]) * sin_theta for i in range(len(y))]
    z_rot = [np.array(y[i]) * sin_theta + np.array(z[i]) * cos_theta for i in range(len(z))]

    return x_rot, y_rot, z_rot


# -------------------------------------------- #
# ------- Rotate geometry along y axis ------- #
#

def rotate_y(x, y, z, angle_):

    theta = math.radians(angle_)

    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)

    x_rot = [np.array(x[i])  * cos_theta + np.array(z[i]) * sin_theta for i in range(len(x))]
    y_rot = y
    z_rot = [-np.array(x[i]) * sin_theta + np.array(z[i]) * cos_theta for i in range(len(z))]

    return x_rot, y_rot, z_rot


# -------------------------------------------- #
# ------- Rotate geometry along z axis ------- #
#

def rotate_z(x, y, z, angle_):

    theta = math.radians(angle_)

    cos_theta = math.cos(theta)
    sin_theta = math.sin(theta)

    x_rot = [np.array(x[i]) * cos_theta - np.array(y[i]) * sin_theta  for i in range(len(x))]
    y_rot = [np.array(x[i]) * sin_theta + np.array(y[i]) * cos_theta  for i in range(len(y))]
    z_rot = z

    return x_rot, y_rot, z_rot


# ------------------------------ #
# ------- Print geometry ------- #
#

def print_geom(output_file,n,atoms,x,y,z):
#
   """
   Function to print a given geometry

   :n: number of atoms
   :atoms: identifier string
   :x, y, z: coordinates
   """
#
   out_f = open(output_file, 'w')
   out_f.write("{}\n".format(n))
   out_f.write('Generated with PGI code\n')
#
   for i in range(n):
      out_f.write(' %2s' % atoms[i])
      out_f.write(' %20.8f' % np.array(x[i]))
      out_f.write(' %20.8f' % np.array(y[i]))
      out_f.write(' %20.8f' % np.array(z[i]))
      out_f.write('\n')

   out_f.close()
 


#
#     _________  ___   _  ________   ___ ______________  _  __
#    /_  __/ _ \/ _ | / |/ / __/ /  / _ /_  __/  _/ __ \/ |/ /
#     / / / , _/ __ |/    /\ \/ /__/ __ |/ / _/ // /_/ /    / 
#    /_/ /_/|_/_/ |_/_/|_/___/____/_/ |_/_/ /___/\____/_/|_/
# 
#

if (translate):

   # ========================================================================
   # =========================== INPUT CHECKS ===============================
   
   # ------- distances file ------- #
   if (os.path.exists(distances_input)):
      with open(distances_input, 'r') as infile:
   
         for line in infile:
            distances.append(float(line))
   
         distances.sort()
   elif (not os.path.exists(distances_input)):
      print(' ')
      print('  STOP: distances input file "' + distances_input + '" is not in the current folder')
      print(' ')
      sys.exit()
   
   
   # ------- geom files ------- #
   
   if (geom1_file[-4:] != '.xyz'):
      print(' ')
      print('  STOP: .xyz extension not found in "' + geom1_file + ' file')
      print(' ')
      sys.exit()
   
   if (not os.path.exists(geom1_file)):
      print(' ')
      print('  STOP: "' + geom1_file + '" is not in the current folder' )
      print(' ')
      sys.exit()
   
   if (origin_CM_1 == 'origin_CM_1_yes'):
      move_geom_1_to_000 = True
   
   if (geom2_file[-4:] != '.xyz'):
      print(' ')
      print('  STOP: .xyz extension not found in "' + geom2_file + ' file')
      print(' ')
      sys.exit()
   
   if (origin_CM_2 == 'origin_CM_2_yes'):
      move_geom_2_to_000 = True
   
   if (not os.path.exists(geom2_file)):
      print(' ')
      print('  STOP: ' + geom2_file + ' is not in the current folder' )
      print(' ')
      sys.exit()
   
   # ------- dir axis ------- #
   
   if (len(dir_axis_input) < 2):
      print(' ')
      print(' ERROR: Sense or direction axis ' + dir_axis_input + ' not supported')
      print(' ')
      print('    Options:')
      print('    --------')
      print('      +x, +y, +z')
      print('      -x, -y, -z')
      print(' ')
      sys.exit()
   
   if (dir_axis_input[1] != 'x' and dir_axis_input[1] != 'y' and dir_axis_input[1] != 'z' or
       dir_axis_input[0] != '+' and dir_axis_input[0] != '-'):
      print(' ')
      print(' ERROR: Sense or direction axis ' + dir_axis_input + ' not supported')
      print(' ')
      print('    Options:')
      print('    --------')
      print('      +x, +y, +z')
      print('      -x, -y, -z')
      print(' ')
      sys.exit()
   
   # -- Results folder and Logfile
   if (os.path.exists('results_translate')):
      print(' ')
      print(' -----------------------------------------------------')
      print('  WARNING: "results_translate" folder already exists"')
      print(' -----------------------------------------------------')
      print(' ')
      erase_results = input('  Do you want to delete it and continue? (y/n)  ')
      if(erase_results == "y" or erase_results == "yes"):
         os.system('rm -rf results_translate/')
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
   
   if not (os.path.exists('results_translate')): os.system('mkdir results_translate')
   
   out_log = open('logfile.txt', 'w')
   
   
   
   
   # ========================================================================
   # ========================  INITIALIZE VARIABLES =========================
   
   # Direction
   if dir_axis_input[0] == '-':
      direction = -one
   elif dir_axis_input[0] == '+':
      direction = one
   
   # Axis
   if dir_axis_input[1]=='x':
   	factor_x = direction
   	factor_y = zero
   	factor_z = zero
   elif dir_axis_input[1]=='y':
           factor_x = zero
           factor_y = direction
           factor_z = zero
   elif dir_axis_input[1]=='z':
           factor_x = zero
           factor_y = zero
           factor_z = direction
   
   dist     = zero
   pre_dist = zero
   verbose  = False
   
   # Fixed coordinates
   x1 = []
   y1 = []
   z1 = []
   
   # Translational coordinates
   x2 = []
   y2 = []
   z2 = []
   
   # Output options
   if (verbose_inp=='verbose_yes'): verbose = True 
   
   
  
   
   
   # ========================================================================
   # ========================================================================
   
   
   
   
   
   # ========================================================================
   # ========================================================================
   # ===========================  MAIN PROGRAM ==============================
   # ========================================================================
   # ========================================================================
   
   
   # ========================================================================
   # ===========================  READ GEOMETRIES ===========================
   
   n_geom1, atoms_1, x1, y1, z1 = read_geom(geom1_file)
   n_geom2, atoms_2, x2, y2, z2 = read_geom(geom2_file)
   
   
   
   # ========================================================================
   # ==========  MOVE GEOM1 AND GEOM2 TO THE ORIGIN OF COORDINATES ==========
   
   geom1_center = []
   geom2_center = []
   
   # -- Calculate geometrical centers
   geom1_center.append(np.mean(x1,0))
   geom1_center.append(np.mean(y1,0))
   geom1_center.append(np.mean(z1,0))
   
   geom2_center.append(np.mean(x2,0))
   geom2_center.append(np.mean(y2,0))
   geom2_center.append(np.mean(z2,0))
   
   
   # -- Translate to the origin of coordinates
   if (move_geom_1_to_000): x1, y1, z1 = translate_geom_to_000(geom1_center,x1,y1,z1)
   if (move_geom_2_to_000): x2, y2, z2 = translate_geom_to_000(geom2_center,x2,y2,z2)
   
   # -- Save new geometries in results folder
   if (move_geom_1_to_000): new_geom1_file = geom1_file[:-4] + '_000.xyz'
   if (move_geom_2_to_000): new_geom2_file = geom2_file[:-4] + '_000.xyz'
   
   if (move_geom_1_to_000): print_geom(new_geom1_file,n_geom1,atoms_1,x1,y1,z1)
   if (move_geom_2_to_000): print_geom(new_geom2_file,n_geom2,atoms_2,x2,y2,z2)
   
   if (move_geom_1_to_000): os.system('mv ' + new_geom1_file + ' results_translate/')
   if (move_geom_2_to_000): os.system('mv ' + new_geom2_file + ' results_translate/')
   
   
   
   # ==================  STEP 1: MOVE GEOM2 BELOW MIN_DIST ==================
   
   #
   #    Perform an initial shift to move geom2 below min_dist
   #       a) Initiate aligned geometries at big distances
   #       b) Check if dist_opt < min_dist to evaluate dir_axis sense (-->  or <--)
   #       c) If not, perform the same shift but along -dir_axis
   #       d) Once we are below min_dist, change the direction of translation
   
   
   # Initiate aligned geom2 by moving it by a big number along dir_axys
   x2,y2,z2 = translate_geom(99999999)
   
   # Calculate initial minimum distance
   dist_ini = calc_min_distance()
   #
   x2,y2,z2 = translate_geom(dist_ini - min_dist + 0.1) # + 0.5 to go below min_dist
   #
   dist_opt = calc_min_distance() # min. distance to geom1 after shift 
   #
   #
   if (dist_opt > dist_ini):
      #
      # Modify direction for the translation
      factor_x, factor_y, factor_z = change_trans_dir()
      #
      x2,y2,z2 = translate_geom(dist_opt - min_dist + 0.5)
      #
      dist_opt_2 = calc_min_distance()
      #
      if(dist_opt_2 > dist_opt): # Error message
         print(' ')
         print('  STOP: something wrong happened, please check the geometries and try again')
         print(' ')
         sys.exit()
   
      dist_opt = dist_opt_2
   
   
   # Now that we are below min_dist, change again the direction for translation of geom2
   factor_x, factor_y, factor_z = change_trans_dir()
   
   # Save the final minimum distance
   dist_pre = dist_opt
   
   
   
   # ================  STEP 2: OPTIMIZE GEOM2 TO OPTIMUM MIN DISTANCES =================
   #
   #    Move geom2 to the distances given in input
   #       a) Calculate the number of distances and save them in a list 
   #       b) Iterate over the list and optimize the geometry 
   # 
   
   print(' ')
   print(' ')
   print(' ===================================== ')
   print(' DISTANCE OPTIMIZATION PROCESS STARTED')
   print(' ===================================== ')
   print(' ')
   
   #
   #
   for distance in distances:
      #
      print(' ------ Optimizing d = ' + str(distance) + ' Å ------ ')  
      print(' ')
      #
      # Calculate difference between previous distance and desired one
      shift = distance - dist_pre
      #
      # Initial shift
      x2,y2,z2 = translate_geom(shift - 0.1) # -0.01 as small shift to ensure translation direction
      #
      # Calculate distance
      dist_new = calc_min_distance()   
      #
      if (dist_new > distance):
   
         # Another shift with less tolerance to avoid problems
         x2,y2,z2 = translate_geom(shift - 0.5) 
         #
         # Calculate distance
         dist_new = calc_min_distance()
         #
         if (dist_new > distance):
            # Another shift with less tolerance to avoid problems
            x2,y2,z2 = translate_geom(shift - 0.5) 
            #
            # Calculate distance
            dist_new = calc_min_distance()
            #
            if (dist_new > distance):
               # Another shift with less tolerance to avoid problems
               x2,y2,z2 = translate_geom(shift - 0.5 ) 
               #
               # Calculate distance
               dist_new = calc_min_distance()
               #
               if (dist_new > distance):
                  print('  STOP: something wrong happenned 1')
                  print('dist_new = ' + str(dist_new) + ' min dist = ' + str(distance))
                  sys.exit()
   
   
      #
      # Move slowly towards desired distance
      #
      diff_dist = abs(dist_new - distance)
   
      # If after first translation we are quite far from the desire distance
      # apply a new shift to be closer   
   
      if (diff_dist > convergence and diff_dist > 0.02):
   
         x2,y2,z2 = translate_geom(diff_dist - convergence)
   
         # Calculate distance
         dist_new = calc_min_distance()
         #
         if (dist_new > distance):
   
            print('  STOP: something wrong happenned 2')
            sys.exit()
   
      #
      while (diff_dist > convergence):
         x2,y2,z2 = translate_geom(convergence_step)
   
         # Recalculate minimum distance and check difference with desired distance
         dist_new  = calc_min_distance()
         diff_dist = abs(dist_new - distance)
   
         if (verbose):
            print('  Computed distance = ' + str(round(dist_new,4)) + ' Å')
   
         # Error
         if (dist_new > distance):
            print('  STOP: reduce convergence criteria for distance optimization')
            sys.exit()
      
         if(diff_dist < convergence):
            print('\n')
            print('  Convergence achieved to distance ' +  str(round(dist_new,4)) + ' Å')
            print('\n')
   
            #
            # Save to logfile
            out_log.write('\n')
            out_log.write(' %22s'   % ' ------ Optimizing d =')
            out_log.write(' %20.8f' % distance)
            out_log.write(' %12s'   % 'Å ------ ')
            out_log.write('\n')
            out_log.write('\n')
            out_log.write(' %34s' % '  Convergence achieved to distance')
            out_log.write(' %20.8f' % dist_new)
            out_log.write(' %5s' % ' Å')
            out_log.write('\n')
            out_log.write('\n')
            out_log.write('\n')
            #
            # Save distance-optimized geometry
            dist_new_rounded = math.ceil(dist_new*100)/100
            new_geom2_file = geom2_file[:-4] + '_'+ dir_axis_input + '_d_' + str(dist_new_rounded) + '.xyz'
            #
            print_geom(new_geom2_file,n_geom2,atoms_2,x2,y2,z2)
            # 
            # Save geometry in "results" folder
            os.system('mv ' + new_geom2_file + ' results_translate/')
   
      dist_pre = dist_new
   
   
   # -- Close and save Logfile
   out_log.close()
   os.system('mv logfile.txt results_translate/')



#
#     ______                      __      __          ___
#    /_  __/________ _____  _____/ /___ _/ /____     <  /
#     / / / ___/ __ `/ __ \/ ___/ / __ `/ __/ _ \    / / 
#    / / / /  / /_/ / / / (__  ) / /_/ / /_/  __/   / /  
#   /_/ /_/   \__,_/_/ /_/____/_/\__,_/\__/\___/   /_/  
#   
#

if (translate_1):

   # ========================================================================
   # =========================== INPUT CHECKS ===============================
   
   # ------- geom files ------- #
   
   if (geom2_file[-4:] != '.xyz'):
      print(' ')
      print('  STOP: .xyz extension not found in "' + geom2_file + ' file')
      print(' ')
      sys.exit()
   
   if (not os.path.exists(geom2_file)):
      print(' ')
      print('  STOP: "' + geom2_file + '" is not in the current folder' )
      print(' ')
      sys.exit()
   
   if (origin_CM_2 == 'origin_CM_yes'):
      move_geom_2_to_000 = True
   
   # ------- dir axis ------- #
   
   if (len(dir_axis_input) < 2):
      print(' ')
      print(' ERROR: Sense or direction axis ' + dir_axis_input + ' not supported')
      print(' ')
      print('    Options:')
      print('    --------')
      print('      +x, +y, +z')
      print('      -x, -y, -z')
      print(' ')
      sys.exit()
   
   if (dir_axis_input[1] != 'x' and dir_axis_input[1] != 'y' and dir_axis_input[1] != 'z' or
       dir_axis_input[0] != '+' and dir_axis_input[0] != '-'):
      print(' ')
      print(' ERROR: Sense or direction axis ' + dir_axis_input + ' not supported')
      print(' ')
      print('    Options:')
      print('    --------')
      print('      +x, +y, +z')
      print('      -x, -y, -z')
      print(' ')
      sys.exit()
   
   # -- Results folder and Logfile
   #if (os.path.exists('results_translate')):
   #   print(' ')
   #   print(' -----------------------------------------------------')
   #   print('  WARNING: "results_translate" folder already exists"')
   #   print(' -----------------------------------------------------')
   #   print(' ')
   #   erase_results = input('  Do you want to delete it and continue? (y/n)  ')
   #   if(erase_results == "y" or erase_results == "yes"):
   #      os.system('rm -rf results_translate/')
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
   
   if not (os.path.exists('results_translate')): os.system('mkdir results_translate')
   
   


   # ========================================================================
   # ========================  INITIALIZE VARIABLES =========================
   
   # Direction
   if dir_axis_input[0] == '-':
      direction = -one
   elif dir_axis_input[0] == '+':
      direction = one
   
   # Axis
   if dir_axis_input[1]=='x':
   	factor_x = direction
   	factor_y = zero
   	factor_z = zero
   elif dir_axis_input[1]=='y':
           factor_x = zero
           factor_y = direction
           factor_z = zero
   elif dir_axis_input[1]=='z':
           factor_x = zero
           factor_y = zero
           factor_z = direction
   
   dist     = zero
   
   # Translational coordinates
   x2 = []
   y2 = []
   z2 = []
   
 
   # ========================================================================
   # ========================================================================
   # ===========================  MAIN PROGRAM ==============================
   # ========================================================================
   # ========================================================================
   
   
   # ========================================================================
   # ============================  READ GEOMETRY ============================
   
   n_geom2, atoms_2, x2, y2, z2 = read_geom(geom2_file)
   
   
   # ========================================================================
   # ==========  MOVE GEOM2 TO THE ORIGIN OF COORDINATES ==========
   
   geom2_center = []
   
   # -- Calculate geometrical centers
   geom2_center.append(np.mean(x2,0))
   geom2_center.append(np.mean(y2,0))
   geom2_center.append(np.mean(z2,0))
   
   
   # -- Translate to the origin of coordinates
   if (move_geom_2_to_000): 
      x2, y2, z2 = translate_geom_to_000(geom2_center,x2,y2,z2)
   
      new_geom2_file = geom2_file[:-4] + '_000.xyz'
      
      print_geom(new_geom2_file,n_geom2,atoms_2,x2,y2,z2)
      
      os.system('mv ' + new_geom2_file + ' results_translate/')
   
   # -- Apply desired shift and save geometry
   x2,y2,z2 = translate_geom(shift_t1)

   new_geom2_file = geom2_file[:-4] + '_'+ dir_axis_input + '_d_' + str(round(shift_t1,4)) + '.xyz'
   #
   print_geom(new_geom2_file,n_geom2,atoms_2,x2,y2,z2)
   #
   # Save geometry in "results" folder
   os.system('mv ' + new_geom2_file + ' results_translate/')

 


#       ___  ____  _________ ______________  _  __
#      / _ \/ __ \/_  __/ _ /_  __/  _/ __ \/ |/ /
#     / , _/ /_/ / / / / __ |/ / _/ // /_/ /    / 
#    /_/|_|\____/ /_/ /_/ |_/_/ /___/\____/_/|_/ 
#    

elif (rotate):

   # ========================================================================
   # =========================== INPUT CHECKS ===============================
   
   # ------- angles file ------- #
   if (os.path.exists(angles_input)):
      with open(angles_input, 'r') as infile:
   
         for line in infile:
            # Direction
            if dir_axis_input[0] == '-':
               angles.append(360.0 - float(line))
            elif dir_axis_input[0] == '+':
               direction = one
               angles.append(float(line))
 
         angles.sort()

   elif (not os.path.exists(angles_input)):
      print(' ')
      print('  STOP: angles input file "' + angles_input + '" is not in the current folder')
      print(' ')
      sys.exit()
   
   
   # ------- geom files ------- #
   
   if (geom1_file[-4:] != '.xyz'):
      print(' ')
      print('  STOP: .xyz extension not found in "' + geom1_file + ' file')
      print(' ')
      sys.exit()
   
   if (not os.path.exists(geom1_file)):
      print(' ')
      print('  STOP: "' + geom1_file + '" is not in the current folder' )
      print(' ')
      sys.exit()
   
   if (origin_CM == 'origin_CM_yes'):
      move_geom_to_000 = True
   
   # ------- dir axis ------- #
   
   if (len(dir_axis_input) < 2):
      print(' ')
      print(' ERROR: Sense or direction axis ' + dir_axis_input + ' not supported')
      print(' ')
      print('    Options:')
      print('    --------')
      print('      +x, +y, +z')
      print('      -x, -y, -z')
      print(' ')
      sys.exit()
   
   if (dir_axis_input[1] != 'x' and dir_axis_input[1] != 'y' and dir_axis_input[1] != 'z' or
       dir_axis_input[0] != '+' and dir_axis_input[0] != '-'):
      print(' ')
      print(' ERROR: Sense or direction axis ' + dir_axis_input + ' not supported')
      print(' ')
      print('    Options:')
      print('    --------')
      print('      +x, +y, +z')
      print('      -x, -y, -z')
      print(' ')
      sys.exit()
   
   # -- Results folder and Logfile
   if (os.path.exists('results_rotate')):
      print(' ')
      print(' -------------------------------------------------')
      print('  WARNING: "results_rotate" folder already exists"')
      print(' -------------------------------------------------')
      print(' ')
      erase_results = input('  Do you want to delete it and continue? (y/n)  ')
      if(erase_results == "y" or erase_results == "yes"):
         os.system('rm -rf results_rotate/')
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
   
   if not (os.path.exists('results_rotate')): os.system('mkdir results_rotate')
   
   
   # ========================================================================
   # ========================  INITIALIZE VARIABLES =========================
   
  
   # Fixed coordinates
   x1 = []
   y1 = []
   z1 = []
   
   # Rotational coordinates
   x2 = []
   y2 = []
   z2 = []
   

   # ========================================================================
   # ========================================================================
   # ===========================  MAIN PROGRAM ==============================
   # ========================================================================
   # ========================================================================
   
   
   # ========================================================================
   # ===========================  READ GEOMETRIES ===========================
   
   n_geom1, atoms_1, x1, y1, z1 = read_geom(geom1_file)
   
   
   # ========================================================================
   # ==========  MOVE GEOM1 AND GEOM2 TO THE ORIGIN OF COORDINATES ==========
   
   if (move_geom_to_000): 

      geom1_center = []
      
      # -- Calculate geometrical centers
      geom1_center.append(np.mean(x1,0))
      geom1_center.append(np.mean(y1,0))
      geom1_center.append(np.mean(z1,0))
      
      # -- Translate to the origin of coordinates
      x1, y1, z1 = translate_geom_to_000(geom1_center,x1,y1,z1)
      
      # -- Save new geometries in results folder
      new_geom1_file = geom1_file[:-4] + '_000.xyz'
      
      print_geom(new_geom1_file,n_geom1,atoms_1,x1,y1,z1)
      
      os.system('mv ' + new_geom1_file + ' results_rotate/')
      

   for angle in angles:

      if dir_axis_input[1] == 'x': x2, y2, z2 = rotate_x(x1, y1, z1, angle)
      if dir_axis_input[1] == 'y': x2, y2, z2 = rotate_y(x1, y1, z1, angle)
      if dir_axis_input[1] == 'z': x2, y2, z2 = rotate_z(x1, y1, z1, angle)

      if dir_axis_input[0] == '-':
         new_geom_file = geom1_file[:-4] + '_'+ dir_axis_input + '_degree_' + str(abs(angle - 360)) + '.xyz'
      elif dir_axis_input[0] == '+':
         new_geom_file = geom1_file[:-4] + '_'+ dir_axis_input + '_degree_' + str(angle) + '.xyz'

      #
      print_geom(new_geom_file,n_geom1,atoms_1,x2,y2,z2)

      # Save geometry in "results" folder
      os.system('mv ' + new_geom_file + ' results_rotate/')




#    
#       ____        __        __          ___
#      / __ \____  / /_____ _/ /____     <  /
#     / /_/ / __ \/ __/ __ `/ __/ _ \    / / 
#    / _, _/ /_/ / /_/ /_/ / /_/  __/   / /  
#   /_/ |_|\____/\__/\__,_/\__/\___/   /_/   
#                                          
#   


elif (rotate_1):

   # ========================================================================
   # =========================== INPUT CHECKS ===============================
   
   # ------- geom files ------- #
   
   if (geom1_file[-4:] != '.xyz'):
      print(' ')
      print('  STOP: .xyz extension not found in "' + geom1_file + ' file')
      print(' ')
      sys.exit()
   
   if (not os.path.exists(geom1_file)):
      print(' ')
      print('  STOP: "' + geom1_file + '" is not in the current folder' )
      print(' ')
      sys.exit()
   
   if (origin_CM == 'origin_CM_yes'):
      move_geom_to_000 = True
   
   # ------- dir axis ------- #
   
   if (len(dir_axis_input) < 2):
      print(' ')
      print(' ERROR: Sense or direction axis ' + dir_axis_input + ' not supported')
      print(' ')
      print('    Options:')
      print('    --------')
      print('      +x, +y, +z')
      print('      -x, -y, -z')
      print(' ')
      sys.exit()
   
   if (dir_axis_input[1] != 'x' and dir_axis_input[1] != 'y' and dir_axis_input[1] != 'z' or
       dir_axis_input[0] != '+' and dir_axis_input[0] != '-'):
      print(' ')
      print(' ERROR: Sense or direction axis ' + dir_axis_input + ' not supported')
      print(' ')
      print('    Options:')
      print('    --------')
      print('      +x, +y, +z')
      print('      -x, -y, -z')
      print(' ')
      sys.exit()
   
   # -- Results folder and Logfile
   if (os.path.exists('results_rotate')):
      print(' ')
      print(' -------------------------------------------------')
      print('  WARNING: "results_rotate" folder already exists"')
      print(' -------------------------------------------------')
      print(' ')
      erase_results = input('  Do you want to delete it and continue? (y/n)  ')
      if(erase_results == "y" or erase_results == "yes"):
         os.system('rm -rf results_rotate/')
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
   
   if not (os.path.exists('results_rotate')): os.system('mkdir results_rotate')
   
   
   # ========================================================================
   # ========================  INITIALIZE VARIABLES =========================
   
  
   # Fixed coordinates
   x1 = []
   y1 = []
   z1 = []
   
   # Rotational coordinates
   x2 = []
   y2 = []
   z2 = []
   

   # ========================================================================
   # ========================================================================
   # ===========================  MAIN PROGRAM ==============================
   # ========================================================================
   # ========================================================================
   
   
   # ========================================================================
   # ===========================  READ GEOMETRIES ===========================
   
   n_geom1, atoms_1, x1, y1, z1 = read_geom(geom1_file)
   
   
   # ========================================================================
   # ==========  MOVE GEOM1 AND GEOM2 TO THE ORIGIN OF COORDINATES ==========
   
   if (move_geom_to_000): 

      geom1_center = []
      
      # -- Calculate geometrical centers
      geom1_center.append(np.mean(x1,0))
      geom1_center.append(np.mean(y1,0))
      geom1_center.append(np.mean(z1,0))
      
      # -- Translate to the origin of coordinates
      x1, y1, z1 = translate_geom_to_000(geom1_center,x1,y1,z1)
      
      # -- Save new geometries in results folder
      new_geom1_file = geom1_file[:-4] + '_000.xyz'
      
      print_geom(new_geom1_file,n_geom1,atoms_1,x1,y1,z1)
      
      os.system('mv ' + new_geom1_file + ' results_rotate/')
      
   # Direction
   if dir_axis_input[0] == '-':
      angle = 360.0 - angle

   if dir_axis_input[1] == 'x': x2, y2, z2 = rotate_x(x1, y1, z1, angle)
   if dir_axis_input[1] == 'y': x2, y2, z2 = rotate_y(x1, y1, z1, angle)
   if dir_axis_input[1] == 'z': x2, y2, z2 = rotate_z(x1, y1, z1, angle)

   if dir_axis_input[0] == '-':
      new_geom_file = geom1_file[:-4] + '_'+ dir_axis_input + '_degree_' + str(abs(angle - 360)) + '.xyz'
   elif dir_axis_input[0] == '+':
      new_geom_file = geom1_file[:-4] + '_'+ dir_axis_input + '_degree_' + str(angle) + '.xyz'

   #
   print_geom(new_geom_file,n_geom1,atoms_1,x2,y2,z2)

   # Save geometry in "results" folder
   os.system('mv ' + new_geom_file + ' results_rotate/')





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

if (minimum_distance):

   # ========================================================================
   # =========================== INPUT CHECKS ===============================
   
   
   # ------- geom files ------- #
   
   if (geom1_file[-4:] != '.xyz'):
      print(' ')
      print('  STOP: .xyz extension not found in "' + geom1_file + ' file')
      print(' ')
      sys.exit()
   
   if (not os.path.exists(geom1_file)):
      print(' ')
      print('  STOP: "' + geom1_file + '" is not in the current folder' )
      print(' ')
      sys.exit()
   
   if (geom2_file[-4:] != '.xyz'):
      print(' ')
      print('  STOP: .xyz extension not found in "' + geom2_file + ' file')
      print(' ')
      sys.exit()
   
   if (not os.path.exists(geom2_file)):
      print(' ')
      print('  STOP: ' + geom2_file + ' is not in the current folder' )
      print(' ')
      sys.exit()
   
   
   # ========================================================================
   # ============================ MAIN PROGRAM ==============================
   
   # Read geoms
   n_geom1, atoms_1, x1, y1, z1 = read_geom(geom1_file)
   n_geom2, atoms_2, x2, y2, z2 = read_geom(geom2_file)

   # Calc min distance
   distance = calc_min_distance()

   print('')
   print('  -------------------------------')
   print('    Geometry 1: ' + geom1_file)
   print('    Geometry 2: ' + geom2_file)
   print('')
   print('    Minimum\n' + 
         '    distance  : ' + str(round(distance,4)) + ' Å')
   print('  -------------------------------')
   


#
#       ______           __                    ______     _     __
#      / ____/__  ____  / /____  __________   / ____/____(_)___/ /
#     / /   / _ \/ __ \/ __/ _ \/ ___/ ___/  / / __/ ___/ / __  / 
#    / /___/  __/ / / / /_/  __/ /  (__  )  / /_/ / /  / / /_/ /  
#    \____/\___/_/ /_/\__/\___/_/  /____/   \____/_/  /_/\__,_/   
#                                                                 
#

if (centers_grid):

   # ========================================================================
   # =========================== INPUT CHECKS ===============================

   with open(input_geom_files, 'r') as geom_files:

      for line in geom_files:

         geom_file = line.strip()

         if (not os.path.exists(input_geom_files)):
            print(' ')
            print('  STOP: geometry files list "' + geom_files + '" is not in the current folder')
            print(' ')
            sys.exit()

         if (geom_file[-4:] != '.xyz'):
            print(geom_file)
            print(geom_file[-4:])
            print(' ')
            print('  STOP: .xyz extension not found in "' + geom_file + ' file')
            print(' ')
            sys.exit()
         
         if (not os.path.exists(geom_file)):
            print(' ')
            print('  STOP: "' + geom_file + '" is not in the current folder' )
            print(' ')
            sys.exit()

      
   # ========================================================================
   # ============================ MAIN PROGRAM ==============================

   # Geometrical centers coordinates
   x2 = []
   y2 = []
   z2 = []
   
   with open(input_geom_files, 'r') as geom_files:
   
      for line in geom_files:

         geom_file = line.strip()
   
         # Read geoms
         dum = []
         dum_int, dum_lst, x, y, z = read_geom(geom_file)
     
         # -- Calculate geometrical centers
         x2.append(np.mean(x,0))
         y2.append(np.mean(y,0))
         z2.append(np.mean(z,0))
   
      # Create ficticious H atoms list for each geometrical center
      n_centers = len(x2)
      atoms = ['H'] * n_centers
         
      print_geom('centers_grid.xyz',n_centers,atoms,x2,y2,z2)


   




print(' ')
print(' ===================================== ')
print('           NORMAL TERMINATION          ')
print(' ===================================== ')
print(' ')
