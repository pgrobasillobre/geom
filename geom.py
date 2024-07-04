import sys 

from classes import input_class
from functions import general, output, translate, rotate, various


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
# PURPOSE: Managing xyz files to translate, rotate, and more.
#
# EXECUTION details: python3 geom.py -h 
# -----------------------------------------------------------

# -- Input initialize and read command line
inp = input_class.input_class()
general.read_command_line(sys.argv,inp)

# -- Select geom code case
if (inp.translate_controlled_distance):
   translate.translate_controlled_distance(inp)

elif (inp.translate_1):
   translate.translate_1(inp)

elif(inp.rotate_angles):
   rotate.rotate_angles(inp)

elif(inp.rotate_1):
   rotate.rotate_1(inp)

elif(inp.min_dist):
   various.min_dist(inp)

elif(inp.geom_center):
   various.geom_center(inp)

elif(inp.geom_specular):
   various.geom_specular(inp)

# -- Close
output.print_normal_termination(inp)
