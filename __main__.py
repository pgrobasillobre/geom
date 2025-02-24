import sys 

from classes import input_class
from functions import general, translate, rotate, create_geom, various 


#                    ██████╗ ███████╗ ██████╗ ███╗   ███╗     ██████╗ ██████╗ ██████╗ ███████╗                
#                   ██╔════╝ ██╔════╝██╔═══██╗████╗ ████║    ██╔════╝██╔═══██╗██╔══██╗██╔════╝                
#   █████╗█████╗    ██║  ███╗█████╗  ██║   ██║██╔████╔██║    ██║     ██║   ██║██║  ██║█████╗      █████╗█████╗
#   ╚════╝╚════╝    ██║   ██║██╔══╝  ██║   ██║██║╚██╔╝██║    ██║     ██║   ██║██║  ██║██╔══╝      ╚════╝╚════╝
#                   ╚██████╔╝███████╗╚██████╔╝██║ ╚═╝ ██║    ╚██████╗╚██████╔╝██████╔╝███████╗                
#                    ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝     ╚═╝     ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝                
   

# ============================================================================================================ #
#                                        Program by Pablo Grobas Illobre                                       #
#                                                                                                              #
#                                       Contact: pgrobasillobre@gmail.com                                      #
# ============================================================================================================ #

# -----------------------------------------------------------
# PURPOSE: Create and manage XYZ files of metal nanoparticles 
#          and graphene structures
#
# EXECUTION details: python3 geom.py -h 
# -----------------------------------------------------------

# -- Input initialize and read command line
inp = input_class.input_class()
general.read_command_line(sys.argv,inp)

# -- Select geom code case
if (inp.translate):
   translate.select_case(inp)

elif(inp.rotate):
   rotate.select_case(inp)

elif(inp.create_geom):
   create_geom.select_case(inp)

elif(inp.small_tasks):
   various.select_case(inp)
