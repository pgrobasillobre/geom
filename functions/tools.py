import numpy as np
import math
import copy

from classes import molecule

# ------------------------------------------ #
# ------- Calculate minimum distance ------- #

def calc_min_distance(geom1,geom2):
   #
   """
   Calculate the minimum distance between two molecule classes

   :geom1: molecule class 1
   :geom2: molecule class 2

   :return: dist: minimum distance between the two geometries
   """ 
   #
   distIJ_min = 999999999999.9 # Initialize
 
   for i in range(geom2.nAtoms):
      for j in range(geom1.nAtoms):
         x_IJ =  geom2.xyz[0][i] - geom1.xyz[0][j] 
         y_IJ =  geom2.xyz[1][i] - geom1.xyz[1][j]
         z_IJ =  geom2.xyz[2][i] - geom1.xyz[2][j]
 
         distIJ = math.sqrt(x_IJ**2.0 + y_IJ**2.0 + z_IJ**2.0)
 
         if(distIJ < distIJ_min): distIJ_min = distIJ
 
   return (distIJ_min)

# ------------------------------- #
# ------- Rotate geometry ------- #

def rotate(mol,angle,dir_axis_input,mol_rot):
   #
   """
   Rotate molecule geometry

   :mol           : initial geometry
   :angle         : rotation angle (degrees)
   :dir_axis_input: rotation axis and sense {+-}{xyz}

   :return: mol_rot: rotated geometry
   """ 
   #
   mol_rot = copy.deepcopy(mol)

   theta = math.radians(angle)

   cos_theta = math.cos(theta)
   sin_theta = math.sin(theta)

   if (dir_axis_input[1]=='x'):
      mol_rot.xyz[1, :] =  mol.xyz[1, :] * cos_theta - mol.xyz[2, :] * sin_theta
      mol_rot.xyz[2, :] =  mol.xyz[1, :] * sin_theta + mol.xyz[2, :] * cos_theta

   elif (dir_axis_input[1]=='y'): 
      mol_rot.xyz[0, :] =  mol.xyz[0, :] * cos_theta + mol.xyz[2, :] * sin_theta
      mol_rot.xyz[2, :] = -mol.xyz[0, :] * sin_theta + mol.xyz[2, :] * cos_theta

   elif (dir_axis_input[1]=='z'):
      mol_rot.xyz[0, :] =  mol.xyz[0, :] * cos_theta - mol.xyz[1, :] * sin_theta
      mol_rot.xyz[1, :] =  mol.xyz[0, :] * sin_theta + mol.xyz[1, :] * cos_theta

   return(mol_rot)

# ---------------------------------------- #
# ------- Create specular geometry ------- #

def create_specular_geom(mol,mol_spec):
   #
   """
   Create specular geometry.

   Mirror considered in the yz plane, with 
   x mirror coordinate = maximum molecule x coordinate + 2.50 Å

   :mol     : initial geometry
   :mol_spec: empty molecule class

   :return: mol_spec: specular geometry
   """ 
   #
   mol_spec = copy.deepcopy(mol)

   # Save fixed x-coordinate for mirror
   mirror = mol.xyz_max[0] +  2.50

   # Compute atom-to-mirror distances along x
   mol_mirror_distances = np.zeros(mol.nAtoms)
   mol_mirror_distances[:] = (mirror - mol.xyz[0,:])*2.0

   # Create dummy molecule class containing one atom and initialize some attributes
   mol_1 = molecule.molecule()

   mol_1.nAtoms = 1
   mol_1.xyz    = np.zeros((3,mol_1.nAtoms))

   dir_factor = [1.0,0.0,0.0] # Translate along x

   # Iterate over mol atoms, save to mol_1, apply mirror_distances shifts along x
   for i in range(mol.nAtoms):
      mol_1.xyz[:,0] = mol.xyz[:,i]
      mol_1.translate_geom(mol_mirror_distances[i],dir_factor)
      mol_spec.xyz[:,i] = mol_1.xyz[:,0]

   return(mol_spec)

