import numpy as np
import random

from functions import output

class molecule:
   # 
   """Molecule class"""
   # 
   def __init__(self):
       
      self.atoms = []

      self.nAtoms = 0

      self.xyz_center = np.zeros(3)
      self.xyz_min    = np.zeros(3)
      self.xyz_max    = np.zeros(3)

   # ----------------------------------------- #
   # ------- Translate geometry to 000 ------- #
   
   def trans_geom_center_to_000(self):
      # 
      """
      Translate geometrical center to 000
      """
      for i in range(self.nAtoms):
         self.xyz[0][i] = self.xyz[0][i] - self.xyz_center[0] 
         self.xyz[1][i] = self.xyz[1][i] - self.xyz_center[1]
         self.xyz[2][i] = self.xyz[2][i] - self.xyz_center[2]

   # ----------------------------- #
   # ------- Read geometry ------- #
   
   def read_geom(self,geom_file,translate_geom_to_000):
      # 
      """
      Read geometries from xyz file
   
      :geom_file: file with geometry in xyz format
      """
      #
      with open(geom_file, 'r') as infile:
         self.nAtoms = int(infile.readline())
         infile.readline()
       
         if self.nAtoms <= 0: output.error('Corrupt geometry file "' + geom_file + '"')
    
         self.atoms = []
         self.xyz = np.zeros((3,self.nAtoms))
       
         i = 0
         for line in infile:
            line = line.split()

            self.atoms.append(line[0])
            self.xyz[0][i] = float(line[1])
            self.xyz[1][i] = float(line[2])
            self.xyz[2][i] = float(line[3])

            i += 1

            if i > self.nAtoms: output.error('Corrupt geometry file "' + geom_file + '"')

      # Calculate geometrical center
      self.xyz_center[0] = np.mean(self.xyz[0,:]) 
      self.xyz_center[1] = np.mean(self.xyz[1,:]) 
      self.xyz_center[2] = np.mean(self.xyz[2,:]) 

      # Translate geometrical center to 000 and save, if requested  
      if (translate_geom_to_000):
         self.trans_geom_center_to_000()
         output.print_geom(self,geom_file[:-4]+'_000')

      # Save maximun/minimum coordinates limits
      self.xyz_max[0] = np.max(self.xyz[0,:])
      self.xyz_max[1] = np.max(self.xyz[1,:])
      self.xyz_max[2] = np.max(self.xyz[2,:])

      self.xyz_min[0] = np.min(self.xyz[0,:])
      self.xyz_min[1] = np.min(self.xyz[1,:])
      self.xyz_min[2] = np.min(self.xyz[2,:])

      return(self)

   # ------------------------------------------------- #
   # ------- Translate geometry along dir_axis ------- #
   
   def translate_geom(self,shift,dir_factor):
      #
      """
      Translate molecular geometry along dir_axis
   
      :shift     : geometrical shift in Å
      :dir_factor: {+-} x,y,z direction 
      """ 
      #
      for i in range(self.nAtoms):
         self.xyz[0,i] = self.xyz[0,i] + dir_factor[0] * shift  
         self.xyz[1,i] = self.xyz[1,i] + dir_factor[1] * shift 
         self.xyz[2,i] = self.xyz[2,i] + dir_factor[2] * shift 
   
      return(self)

   # ------------------------------------------------ #
   # ------- Filter XYZ within a ribbon shape ------- #
   
   def filter_xyz_graphene_to_ribbon(self, inp):
       """
       Filter the graphene sheet to create a ribbon with specified X and Y lengths.
       
       :inp: input class
       """
   
       x = self.xyz[0, :]
       y = self.xyz[1, :]
       z = self.xyz[2, :]
   
       # Define X and Y bounds based on inp parameters
       x_min, x_max = -inp.X_length / 2, inp.X_length / 2
       y_min, y_max = -inp.Y_length / 2, inp.Y_length / 2

       # Condition for points to be within the ribbon
       condition = (
           (x_min <= x) & (x <= x_max) &
           (y_min <= y) & (y <= y_max)
       )
   
       # Filter coordinates based on condition
       x_filtered = x[condition]
       y_filtered = y[condition]
       z_filtered = z[condition]
   
       # Update the atom list and geometry based on filtered data
       self.nAtoms = len(x_filtered)
       self.atoms = [inp.atomtype] * self.nAtoms  # Atom types remain consistent
   
       self.xyz_center = np.zeros(3)
       self.xyz_min    = np.zeros(3)
       self.xyz_max    = np.zeros(3)
   
       self.xyz = np.zeros((3, self.nAtoms))
       self.xyz = np.vstack((x_filtered, y_filtered, z_filtered))
   
       # Calculate geometrical center
       self.xyz_center = np.mean(self.xyz, axis=1)
   
       # Save maximum/minimum coordinate limits
       self.xyz_max = np.max(self.xyz, axis=1)
       self.xyz_min = np.min(self.xyz, axis=1)
   
       return self

   # ---------------------------------------------- #
   # ------- Filter XYZ within a disk shape ------- #
    
   def filter_xyz_graphene_to_disk(self, inp):
       """
       Filter the graphene sheet to create a disk of specified radius centered at (0.0, 0.0, 0.0).
       
       :inp: input class
       """
   
       x = self.xyz[0, :]
       y = self.xyz[1, :]
       z = self.xyz[2, :]
   
       # Condition for points to be within the disk
       condition = (x**2 + y**2 <= inp.radius**2)
   
       # Filter coordinates based on condition
       x_filtered = x[condition]
       y_filtered = y[condition]
       z_filtered = z[condition]
   
       # Update the atom list and geometry based on filtered data
       self.nAtoms = len(x_filtered)
       self.atoms = [inp.atomtype] * self.nAtoms  # Atom types remain consistent
   
       self.xyz_center = np.zeros(3)
       self.xyz_min    = np.zeros(3)
       self.xyz_max    = np.zeros(3)
   
       self.xyz = np.zeros((3, self.nAtoms))
       self.xyz = np.vstack((x_filtered, y_filtered, z_filtered))
   
       # Calculate geometrical center
       self.xyz_center = np.mean(self.xyz, axis=1)
   
       # Save maximum/minimum coordinate limits
       self.xyz_max = np.max(self.xyz, axis=1)
       self.xyz_min = np.min(self.xyz, axis=1)
   
       return self

   # ---------------------------------------------- #
   # ------- Filter XYZ within a ring shape ------- #

   def filter_xyz_graphene_to_ring(self, inp):
       """
       Filter the graphene sheet to create a ring of specified inner and outer radii.
       
       :inp: input class
       """
       x = self.xyz[0, :]
       y = self.xyz[1, :]
       z = self.xyz[2, :]
   
       # Condition for points to be within the ring (between radius_in and radius_out)
       condition = (inp.radius_in**2 <= x**2 + y**2) & (x**2 + y**2 <= inp.radius_out**2)
   
       # Filter coordinates based on condition
       x_filtered = x[condition]
       y_filtered = y[condition]
       z_filtered = z[condition]
   
       # Update the atom list and geometry based on filtered data
       self.nAtoms = len(x_filtered)
       self.atoms = [inp.atomtype] * self.nAtoms  # Atom types remain consistent
   
       self.xyz_center = np.zeros(3)
       self.xyz_min    = np.zeros(3)
       self.xyz_max    = np.zeros(3)
   
       self.xyz = np.zeros((3, self.nAtoms))
       self.xyz = np.vstack((x_filtered, y_filtered, z_filtered))
   
       # Calculate geometrical center
       self.xyz_center = np.mean(self.xyz, axis=1)
   
       # Save maximum/minimum coordinate limits
       self.xyz_max = np.max(self.xyz, axis=1)
       self.xyz_min = np.min(self.xyz, axis=1)
   
       return self 

   # -------------------------------------------------- #
   # ------- Filter XYZ within a triangle shape ------- #

   def filter_xyz_graphene_to_triangle(self, inp):
       """
       Filter the graphene sheet to create a triangular shape with specified edge type.
       
       :inp: input class
       """
   
       x = self.xyz[0, :]
       y = self.xyz[1, :]
       z = self.xyz[2, :]
   
       # Define triangular region based on edge type
       if inp.graphene_edge_type == 'armchair':
           # Armchair triangle aligned with the armchair direction
           condition = (
               (y >= 0) &
               (y <= inp.side_length * np.sqrt(3) / 2) &
               (x >= -y / np.sqrt(3)) &
               (x <= y / np.sqrt(3))
           )
       elif inp.graphene_edge_type == 'zigzag':
           # Zigzag triangle aligned with the zigzag direction
           condition = (
               (x >= 0) &
               (x <= inp.side_length) &
               (y >= -x / np.sqrt(3)) &
               (y <= x / np.sqrt(3))
           )
       else:
           raise ValueError("Invalid edge type. Must be 'armchair' or 'zigzag'.")
   
       # Filter coordinates based on condition
       x_filtered = x[condition]
       y_filtered = y[condition]
       z_filtered = z[condition]
   
       # Update the atom list and geometry based on filtered data
       self.nAtoms = len(x_filtered)
       self.atoms = [inp.atomtype] * self.nAtoms  # Atom types remain consistent
   
       self.xyz_center = np.zeros(3)
       self.xyz_min    = np.zeros(3)
       self.xyz_max    = np.zeros(3)
   
       self.xyz = np.zeros((3, self.nAtoms))
       self.xyz = np.vstack((x_filtered, y_filtered, z_filtered))
   
       # Calculate geometrical center
       self.xyz_center = np.mean(self.xyz, axis=1)
   
       # Save maximum/minimum coordinate limits
       self.xyz_max = np.max(self.xyz, axis=1)
       self.xyz_min = np.min(self.xyz, axis=1)
   
       return self

   # ---------------------------------------------- #
   # ------- Remove graphene dangling bonds ------- #

   def remove_dangling_bonds_graphene(self, inp):
       """
       Remove dangling bonds from generated graphene structure by eliminating atoms with fewer than 2 neighbors.
       Perform up to 3 iterations to ensure no dangling bonds remain.
   
       :inp: input class
       """

       print("  Removing dangling C atoms on generated structure...")
       print("")
   
       def get_neighbors(atom_index, cutoff=1.5):
           """Find neighbors of an atom within a distance cutoff."""
           distances = np.linalg.norm(self.xyz.T - self.xyz.T[atom_index], axis=1)
           neighbors = np.where((distances > 0) & (distances <= cutoff))[0]
           return neighbors
   
       max_iterations = 3
       for iteration in range(max_iterations):
           dangling_atoms = []
           for i in range(self.nAtoms):
               neighbors = get_neighbors(i)
               if len(neighbors) < 2:  # Dangling bond if fewer than 2 neighbors
                   dangling_atoms.append(i)
   
           # If no dangling atoms are found, exit the loop
           if not dangling_atoms:
               print("")
               print(f"  --> All dangling bonds removed after {iteration + 1} iteration(s).")
               return self
   
           # Remove dangling atoms
           keep_atoms = np.setdiff1d(np.arange(self.nAtoms), dangling_atoms)
           self.xyz = self.xyz[:, keep_atoms]
           self.nAtoms = len(keep_atoms)
           self.atoms = [self.atoms[i] for i in keep_atoms]
   
           # Recalculate geometry
           self.xyz_center = np.mean(self.xyz, axis=1)
           self.xyz_max = np.max(self.xyz, axis=1)
           self.xyz_min = np.min(self.xyz, axis=1)
   
           print(f"  - Iteration {iteration + 1}: Removed {len(dangling_atoms)} dangling atom(s).")
   
       # If dangling bonds remain after 3 iterations, raise an error
       dangling_atoms = []
       for i in range(self.nAtoms):
           neighbors = get_neighbors(i)
           if len(neighbors) < 2:
               dangling_atoms.append(i)
   
       if dangling_atoms:
           output.error(f"{len(dangling_atoms)} dangling bonds on generated graphene sheet could not be eliminated after {max_iterations} iterations.")
   
       return self


   # ---------------------------------------- #
   # ------- Filter XYZ within sphere ------- #
   
   def filter_xyz_in_sphere(self,inp):
      #
      """
      Consider xyz points within an sphere 
   
      :inp: input class
      """ 
      #

      x = self.xyz[0, :]
      y = self.xyz[1, :]
      z = self.xyz[2, :]
      
      # Condition for points to be within the sphere 
      condition = ((x-inp.sphere_center[0])**2 + 
                   (y-inp.sphere_center[1])**2 + 
                   (z-inp.sphere_center[2])**2 <= (inp.radius)**2)

      x_filtered = self.xyz[0, condition]
      y_filtered = self.xyz[1, condition]
      z_filtered = self.xyz[2, condition]

      # Fill previous geometry with current structure
      self.nAtoms = len(x_filtered)

      self.atoms = []
      self.atoms = [inp.atomtype] * self.nAtoms

      self.xyz_center = np.zeros(3)
      self.xyz_min    = np.zeros(3)
      self.xyz_max    = np.zeros(3)

      self.xyz = np.zeros((3,self.nAtoms))
      self.xyz = np.vstack((x_filtered, y_filtered, z_filtered))

      # Calculate geometrical center
      self.xyz_center = np.mean(self.xyz, axis=1)

      # Save maximum/minimum coordinates limits
      self.xyz_max = np.max(self.xyz, axis=1)
      self.xyz_min = np.min(self.xyz, axis=1)

      return(self)


   # ------------------------------------------ #
   # ------- Filter XYZ within cylinder ------- #
   
   def filter_xyz_in_cylinder(self,inp):
      #
      """
      Consider xyz points within an cylinder
   
      :inp: input class
      """ 
      #

      x = self.xyz[0, :]
      y = self.xyz[1, :]
      z = self.xyz[2, :]
       
      # Compute base radius from the rod width
      # and length subtracting the radius of the spheres at the extremes
      inp.sphere_center = [0.0,0.0,0.0]
      radius = inp.rod_width / 2.0
      length = inp.rod_length - inp.rod_width 

      # Condition for points to be within the cylinder 
      if inp.main_axis == "x":
        condition = (
            ((y - inp.sphere_center[1])**2 + (z - inp.sphere_center[2])**2 <= radius**2) &
            (x >= inp.sphere_center[0] - length/2.0) &
            (x <= inp.sphere_center[0] + length/2.0)
        )

      elif inp.main_axis == "y":
          condition = (
              ((x - inp.sphere_center[0])**2 + (z - inp.sphere_center[2])**2 <= radius**2) &
              (y >= inp.sphere_center[1] - length/2.0) &
              (y <= inp.sphere_center[1] + length/2.0)
          )

      elif inp.main_axis == "z":
          condition = (
              ((x - inp.sphere_center[0])**2 + (y - inp.sphere_center[1])**2 <= radius**2) &
              (z >= inp.sphere_center[2] - length/2.0) &
              (z <= inp.sphere_center[2] + length/2.0)
          )

      x_filtered = self.xyz[0, condition]
      y_filtered = self.xyz[1, condition]
      z_filtered = self.xyz[2, condition]

      # Fill previous geometry with current structure
      self.nAtoms = len(x_filtered)

      self.atoms = []
      self.atoms = [inp.atomtype] * self.nAtoms

      self.xyz_center = np.zeros(3)
      self.xyz_min    = np.zeros(3)
      self.xyz_max    = np.zeros(3)

      self.xyz = np.zeros((3,self.nAtoms))
      self.xyz = np.vstack((x_filtered, y_filtered, z_filtered))

      # Calculate geometrical center
      self.xyz_center = np.mean(self.xyz, axis=1)

      # Save maximum/minimum coordinates limits
      self.xyz_max = np.max(self.xyz, axis=1)
      self.xyz_min = np.min(self.xyz, axis=1)

      return(self)


   # ----------------------------------------------------- #
   # ------- Filter XYZ within elliptic paraboloid ------- #
   
   def filter_xyz_in_elliptic_paraboloid(self,inp):
      #
      """
      Consider xyz points within an elliptic paraboloid 
   
      :inp: input class
      """ 
      #

      x = self.xyz[0, :]
      y = self.xyz[1, :]
      z = self.xyz[2, :]
      
      # Calculate the paraboloid limit for each (x, y)
      paraboloid_limit = inp.elliptic_parabola_a * x**2 + inp.elliptic_parabola_b * y**2 + inp.elliptic_parabola_c

      # Condition for points to be within the paraboloid 
      condition = ((z >= inp.z_min) &
                   (z <= inp.z_max) &
                   (z >= paraboloid_limit))

      x_filtered = self.xyz[0, condition]
      y_filtered = self.xyz[1, condition]
      z_filtered = self.xyz[2, condition]

      # Fill previous geometry with current structure
      self.nAtoms = len(x_filtered)

      self.atoms = []
      self.atoms = [inp.atomtype] * self.nAtoms

      self.xyz_center = np.zeros(3)
      self.xyz_min    = np.zeros(3)
      self.xyz_max    = np.zeros(3)

      self.xyz = np.zeros((3,self.nAtoms))
      self.xyz = np.vstack((x_filtered, y_filtered, z_filtered))

      # Calculate geometrical center
      self.xyz_center = np.mean(self.xyz, axis=1)

      # Save maximum/minimum coordinates limits
      self.xyz_max = np.max(self.xyz, axis=1)
      self.xyz_min = np.min(self.xyz, axis=1)

      return(self)


   # ----------------------------------------------------- #
   # ------- Filter XYZ within square-base pyramid ------- #
   
   def filter_xyz_in_pyramid(self,inp,centers,planes):
      #
      """
      Consider xyz points within a pyramid with square base
   
      :inp    : input class
      :centers: vertices delimiting structure 
      :planes : surfaces conecting centers
      """ 
      #

      x = self.xyz[0, :]
      y = self.xyz[1, :]
      z = self.xyz[2, :]

      # Condition for points to be within the pyramid
      condition = (
          (centers["center_1"][2] <= z) & (z <= centers["center_5"][2]) &
          (centers["center_4"][0] <= x) & (x <= centers["center_1"][0]) &
          (centers["center_3"][1] <= y) & (y <= centers["center_4"][1]) &
          (planes["n_125"][0][0] * x + planes["n_125"][0][1] * y + planes["n_125"][0][2] * z >= -planes["n_125"][1]) &
          (planes["n_235"][0][0] * x + planes["n_235"][0][1] * y + planes["n_235"][0][2] * z >= -planes["n_235"][1]) &
          (planes["n_345"][0][0] * x + planes["n_345"][0][1] * y + planes["n_345"][0][2] * z >= -planes["n_345"][1]) &
          (planes["n_415"][0][0] * x + planes["n_415"][0][1] * y + planes["n_415"][0][2] * z >= -planes["n_415"][1])
      )

      x_filtered = x[condition]
      y_filtered = y[condition]
      z_filtered = z[condition]

      # Fill previous geometry with current structure
      self.nAtoms = len(x_filtered)

      self.atoms = []
      self.atoms = [inp.atomtype] * self.nAtoms

      self.xyz_center = np.zeros(3)
      self.xyz_min    = np.zeros(3)
      self.xyz_max    = np.zeros(3)

      self.xyz = np.zeros((3,self.nAtoms))
      self.xyz = np.vstack((x_filtered, y_filtered, z_filtered))

      # Calculate geometrical center
      self.xyz_center = np.mean(self.xyz, axis=1)

      # Save maximum/minimum coordinates limits
      self.xyz_max = np.max(self.xyz, axis=1)
      self.xyz_min = np.min(self.xyz, axis=1)

      return(self)


   # -------------------------------------- #
   # ------- Filter XYZ within cone ------- #
   
   def filter_xyz_in_cone(self,inp):
      #
      """
      Consider xyz points within cone 
   
      :inp: input class
      """ 
      #

      x = self.xyz[0, :]
      y = self.xyz[1, :]
      z = self.xyz[2, :]
 
      # Condition for points inside the cone
      condition = (x**2 + y**2 <= (inp.radius / inp.z_max)**2 * z**2) & (z >= 0) & (z <= inp.z_max)
      
      # Select the points that satisfy the condition
      x_filtered = x[condition]
      y_filtered = y[condition]
      z_filtered = z[condition]
      
      # Fill previous geometry with current structure
      self.nAtoms = len(x_filtered)

      self.atoms = []
      self.atoms = [inp.atomtype] * self.nAtoms

      self.xyz_center = np.zeros(3)
      self.xyz_min    = np.zeros(3)
      self.xyz_max    = np.zeros(3)

      self.xyz = np.zeros((3,self.nAtoms))
      self.xyz = np.vstack((x_filtered, y_filtered, z_filtered))

      # Calculate geometrical center
      self.xyz_center = np.mean(self.xyz, axis=1)

      # Save maximum/minimum coordinates limits
      self.xyz_max = np.max(self.xyz, axis=1)
      self.xyz_min = np.min(self.xyz, axis=1)

      return(self)


   # ----------------------------------- #
   # ------- Create random alloy ------- #

   def create_alloy(self,inp):
      """
      Modify the molecule by randomly replacing a percentage of specified atoms with the alloy type.

      :inp: input class

      """
      # Number of atoms to replace 
      replace_indices = [i for i, atom in enumerate(self.atoms)]
      n_replace = int(self.nAtoms * (inp.alloy_perc / 100.0))

      if n_replace > 0:
         # Randomly select indices to replace
         selected_indices = random.sample(replace_indices, n_replace)

         # Replace the selected atoms with the alloy type
         for idx in selected_indices:
             self.atoms[idx] = inp.atomtype_alloy.lower()

         print(f"Replaced {n_replace} {inp.atomtype} atoms with {inp.atomtype_alloy}")

      else:
         output.error('number of atoms to replace in alloy creation n_replace{}')


