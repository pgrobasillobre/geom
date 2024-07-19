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
    merged_atoms = []
    merged_xyz   = [[], [], []]
    added_atoms  = set()  # Set to keep track of already added atoms

    # Add all atoms from geom1 to geom3
    for j in range(geom1.nAtoms):
        merged_atoms.append(geom1.atoms[j])

        x = geom1.xyz[0][j]
        y = geom1.xyz[1][j]
        z = geom1.xyz[2][j]
        merged_xyz[0].append(x)
        merged_xyz[1].append(y)
        merged_xyz[2].append(z)
        added_atoms.add((x, y, z))  # Add atom to the set

    # Add atoms from geom2 to geom3 if they are not within the cutoff distance from any atom in geom1
    for i in range(geom2.nAtoms):
        keep_atom = True
        
        for j in range(geom1.nAtoms):
            x_IJ = geom2.xyz[0][i] - geom1.xyz[0][j]
            y_IJ = geom2.xyz[1][i] - geom1.xyz[1][j]
            z_IJ = geom2.xyz[2][i] - geom1.xyz[2][j]

            distIJ = math.sqrt(x_IJ**2.0 + y_IJ**2.0 + z_IJ**2.0)

            if distIJ + 0.0001 < inp.merge_cutoff:
                keep_atom = False
                break
        
        # Add atom if it is not within cutoff distance and not already added
        if keep_atom and (geom2.xyz[0][i], geom2.xyz[1][i], geom2.xyz[2][i]) not in added_atoms:
            merged_atoms.append(geom1.atoms[i])

            merged_xyz[0].append(geom2.xyz[0][i])
            merged_xyz[1].append(geom2.xyz[1][i])
            merged_xyz[2].append(geom2.xyz[2][i])
            added_atoms.add((geom2.xyz[0][i], geom2.xyz[1][i], geom2.xyz[2][i]))  # Add atom to the set

    # Fill merged geometry
    geom3 = molecule.molecule()

    geom3.nAtoms = len(merged_xyz[0])

    geom3.atoms = copy.deepcopy(merged_atoms) 

    geom3.xyz_center = np.zeros(3)
    geom3.xyz_min    = np.zeros(3)
    geom3.xyz_max    = np.zeros(3)

    geom3.xyz = np.zeros((3,geom3.nAtoms))
    geom3.xyz = np.vstack(merged_xyz)

    # Calculate geometrical center
    geom3.xyz_center = np.mean(geom3.xyz, axis=1)

    # Save maximum/minimum coordinates limits
    geom3.xyz_max = np.max(geom3.xyz, axis=1)
    geom3.xyz_min = np.min(geom3.xyz, axis=1)

    return geom3
