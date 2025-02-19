import numpy as np
import math
import copy
import sys # debug

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

# -------------------------------- #
# ------- Merge geometries ------- #

def merge_geoms(inp, geom1, geom2):
    #
    """
    Merge two geometries while avoiding overlap based on the cutoff distance.

    :inp  : input class with cutoff distance
    :geom1: molecule class 1 
    :geom2: molecule class 2
    
    :return: geom3: merged geometry 
    """
    #

    # Convert lists to NumPy arrays for efficiency
    geom1_xyz = np.array(geom1.xyz)  # (3, N1)
    geom2_xyz = np.array(geom2.xyz)  # (3, N2)

    # Compute pairwise distances efficiently using broadcasting
    diff = geom2_xyz[:, :, None] - geom1_xyz[:, None, :]
    dist_matrix = np.linalg.norm(diff, axis=0)  # Shape: (N2, N1)

    # Find atoms in geom2 that are farther than the cutoff from all atoms in geom1
    keep_atoms = np.all(dist_matrix >= inp.merge_cutoff, axis=1)

    # Merge atoms that are not overlapping
    merged_atoms = geom1.atoms + [geom2.atoms[i] for i in range(geom2.nAtoms) if keep_atoms[i]]

    # Merge XYZ coordinates
    merged_xyz = np.concatenate((geom1_xyz, geom2_xyz[:, keep_atoms]), axis=1)

    # Create new molecule
    geom3 = molecule.molecule()
    geom3.nAtoms = merged_xyz.shape[1]
    geom3.atoms = copy.deepcopy(merged_atoms)

    # Calculate geometrical properties
    geom3.xyz = merged_xyz
    geom3.xyz_center = np.mean(merged_xyz, axis=1)
    geom3.xyz_max = np.max(merged_xyz, axis=1)
    geom3.xyz_min = np.min(merged_xyz, axis=1)

    # Calculate geometrical center
    geom3.xyz_center = np.mean(geom3.xyz, axis=1)

    # Save maximum/minimum coordinates limits
    geom3.xyz_max = np.max(geom3.xyz, axis=1)
    geom3.xyz_min = np.min(geom3.xyz, axis=1)

    return geom3

# ---------------------------------------------------- #
# ------- Determine sphere's center within rod ------- #

def determine_sphere_center(inp,sense):
   #
   """
   Calculate sphere center within a rod

   :inp  : input class
   :sense: + or - direction

   :return: inp.sphere_center: center of the sphere updated
   """ 
   #
   inp.sphere_center = [0.0,0.0,0.0]
   inp.radius = inp.rod_width/2.0
   #
   axis_map = {'x': 0, 'y': 1, 'z': 2}
   #
   index = axis_map[inp.main_axis]
   if sense == '+':
       inp.sphere_center[index] = +((inp.rod_length - inp.rod_width)/2.0)
   elif sense == '-':
       inp.sphere_center[index] = -((inp.rod_length - inp.rod_width)/2.0)

