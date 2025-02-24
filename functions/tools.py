import numpy as np
import math
import copy

from classes import molecule
# -------------------------------------------------------------------------------------
def calc_min_distance(geom1,geom2):
   """
   Calculates the minimum distance between two molecular geometries.

   Args:
       geom1 (molecule): The first molecule object.
       geom2 (molecule): The second molecule object.

   Returns:
       float: The minimum distance between the two geometries.

   Notes:
       - Uses NumPy broadcasting for efficient pairwise distance computation.
   """
   #
   # Compute pairwise distance matrix using broadcasting
   diffs = geom2.xyz[:, :, np.newaxis] - geom1.xyz[:, np.newaxis, :]
   dist_matrix = np.sqrt(np.sum(diffs**2, axis=0))

   # Return the minimum distance
   return np.min(dist_matrix)
# -------------------------------------------------------------------------------------
def rotate(mol,angle,dir_axis_input,mol_rot):
   """
   Rotates a molecular geometry by a given angle around a specified axis.

   Args:
       mol (molecule): The original molecule object.
       angle (float): The rotation angle in degrees.
       dir_axis_input (str): The rotation axis and sense (e.g., `+x`, `-y`).
       mol_rot (molecule): A new molecule object to store the rotated geometry.

   Returns:
       molecule: The rotated molecule object.

   Notes:
       - Rotation is performed using standard rotation matrices.
       - Supports rotation around x, y, and z axes.
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
# -------------------------------------------------------------------------------------
def merge_geoms(inp, geom1, geom2):
    """
    Merges two molecular geometries while avoiding overlap based on a cutoff distance.

    Args:
        inp (input_class): Input object containing cutoff distance.
        geom1 (molecule): The first molecule object.
        geom2 (molecule): The second molecule object.

    Returns:
        molecule: The merged molecular geometry.

    Notes:
        - Uses pairwise distance calculations to avoid overlapping atoms.
        - Atoms from `geom2` that are too close to `geom1` are removed.
        - The merged geometry retains properties such as center and bounding box.
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
    geom3.xyz = merged_xyz

    # Calculate geometrical properties
    geom3.xyz_center = np.mean(geom3.xyz, axis=1)
    geom3.xyz_max = np.max(geom3.xyz, axis=1)
    geom3.xyz_min = np.min(geom3.xyz, axis=1)

    return geom3
# -------------------------------------------------------------------------------------
def subtract_geoms(inp, geom1, geom2):
    """
    Subtracts one geometry from another based on a cutoff distance.

    Args:
        inp (input_class): Input object containing cutoff distance.
        geom1 (molecule): The first molecule object (to be subtracted).
        geom2 (molecule): The second molecule object.

    Returns:
        molecule: A new molecule object representing `geom2 - geom1`.

    Notes:
        - Atoms from `geom2` that are within the cutoff distance of `geom1` are removed.
        - The resulting geometry retains calculated properties such as center and bounding box.
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
    merged_atoms = [geom2.atoms[i] for i in range(geom2.nAtoms) if keep_atoms[i]]

    # Merge XYZ coordinates
    merged_xyz = geom2_xyz[:, keep_atoms]

    # Create new molecule
    geom3 = molecule.molecule()
    geom3.nAtoms = merged_xyz.shape[1]
    geom3.atoms = copy.deepcopy(merged_atoms)
    geom3.xyz = merged_xyz

    # Calculate geometrical properties
    geom3.xyz_center = np.mean(merged_xyz, axis=1)
    geom3.xyz_max = np.max(merged_xyz, axis=1)
    geom3.xyz_min = np.min(merged_xyz, axis=1)

    return geom3
# -------------------------------------------------------------------------------------
def determine_sphere_center(inp,sense):
   """
   Determines the center of a sphere within a rod-like structure.

   Args:
       inp (input_class): Input object containing rod and sphere dimensions.
       sense (str): Direction (`'+'` or `'-'`) to position the sphere.

   Returns:
       list[float]: The updated sphere center coordinates.

   Notes:
       - The sphere's radius is computed as half the rod width.
       - The center is positioned based on the rod's main axis.
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
# -------------------------------------------------------------------------------------
