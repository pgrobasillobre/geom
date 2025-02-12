import pytest
import sys
import os
import filecmp

# Add the project root to sys.path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
test_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))

from classes import input_class
from functions import general, create_geom, various

# -------------------------------------------------------------------------------------
def move_input_geom(folder,xyz_file):

   """
   Move input geometry into scratch folder 
   """

   file_path_xyz = os.path.join(os.path.dirname(__file__), folder, xyz_file)

   os.system(f'cp {file_path_xyz} .')
# -------------------------------------------------------------------------------------
def move_created_geom(folder):

   """
   Move created geometry to folder and remove results_geom folder
   """

   file_path = os.path.join(os.path.dirname(__file__))
   file_path_results = os.path.join(file_path, "results_geom")
   file_path_results_xyz  = os.path.join(file_path_results, "*xyz")

   os.system(f'mv {file_path_results_xyz} {folder}')
   os.system(f'rm -rf {file_path}/*xyz {file_path_results} ')
# -------------------------------------------------------------------------------------
def test_specular_geometry(monkeypatch):

   """
   Test creation of specular geometry.
   """

   # Test folder
   test_folder    = 'specular'
   xyz_input_file = 'doxorubicin.xyz'
   
   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", "-mirror", xyz_input_file]
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)

   # Temporaly move input file
   move_input_geom(test_folder,xyz_input_file)

   # Create specular geometry
   various.geom_specular(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "doxorubicin_000_mirror.xyz")
   generated_file = f"{test_folder}/{inp.geom_file[:-4]}_000_mirror.xyz"

   move_created_geom(test_folder)
   
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
# -------------------------------------------------------------------------------------
