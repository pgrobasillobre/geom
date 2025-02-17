
class parameters:
   #
   """Parameters class"""
   #
   def __init__(self):
       
      # -- Convergence options
      self.convergence      = 0.010
      self.convergence_step = 0.001

      # -- Lattice parameters of metals / graphene
      self.lattice_constant = {
      "ag": 4.09000,
      "au": 4.09000,
      "na": 4.2906,
      "c" : 2.46 # Graphene
      }
 
      self.atomic_arrangement = {
      "ag": "FCC",
      "au": "FCC",
      "na": "BCC"
      }
      
      # -- General parameters
      self.zero = 0.0
      self.one  = 1.0
      self.two  = 2.0
      
      self.min_dist = 1.0


