import math

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

