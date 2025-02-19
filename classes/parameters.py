
class parameters:
   #
   """Parameters class"""
   #
   def __init__(self):
       
      # -- Convergence options
      self.convergence      = 0.010
      self.convergence_step = 0.001

      # -- Lattice parameters of metals / graphene (units = Angstroms)
      self.lattice_constant = {
      "ag": 4.09000,
      "au": 4.09000,
      "na": 4.22500,
      "c" : 2.46 # Graphene
      }

      # -- Merge cutoff as minimum interatomic distance given the lattice constants above (units = Angstroms)
      self.min_dist = {
      "ag": 2.88,
      "au": 2.88,
      "na": 3.65,
      "c" : 1.42 
      }
 
      # -- Atomic packing of metals
      self.atomic_arrangement = {
      "ag": "FCC",
      "au": "FCC",
      "na": "BCC"
      }
      
      # -- General parameters (units = Angstroms)
      self.min_dist_translate = 1.0


