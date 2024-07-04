import numpy as np

from functions import output

class molecule:
   # 
   """Molecule class"""
   # 
   def __init__(self):
       
      self.atoms = []

      self.nAtoms = 0

      self.xyz_center = np.zeros(3)
      self.xyz_max    = np.zeros(3)

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

      # Translate to geometrical center and save, if requested  
      if (translate_geom_to_000):
         for i in range(self.nAtoms):
            self.xyz[0][i] = self.xyz[0][i] - self.xyz_center[0] 
            self.xyz[1][i] = self.xyz[1][i] - self.xyz_center[1]
            self.xyz[2][i] = self.xyz[2][i] - self.xyz_center[2]

         output.print_geom(self,geom_file[:-4]+'_000')

      # Save maximun coordinates limits
      self.xyz_max[0] = np.max(self.xyz[0,:])
      self.xyz_max[1] = np.max(self.xyz[1,:])
      self.xyz_max[2] = np.max(self.xyz[2,:])

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




