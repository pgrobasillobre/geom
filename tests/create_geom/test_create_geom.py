import pytest
import sys
import os
import filecmp

# Add the project root to sys.path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
test_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))

from classes import input_class
from functions import general, create_geom

# -------------------------------------------------------------------------------------
def move_created_geom(folder):
   """
   Move created geometry to folder and remove results_geom folder
   """
   file_path_results = os.path.join(os.path.dirname(__file__), "results_geom")
   file_path_results_xyz  = os.path.join(file_path_results, "*xyz")

   os.system(f'mv {file_path_results_xyz} {folder}')
   os.system(f'rm -rf {file_path_results}')
# -------------------------------------------------------------------------------------
def test_create_sphere(monkeypatch):

   """
   Test if the generated sphere geometry matches the expected XYZ file.
   """

   # Test folder
   test_folder = 'sphere'
   
   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", "-create", "-sphere", "Ag", "20.0", "0.0", "0.0", "0.0"]
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)
   
   # Run the geometry creation
   create_geom.select_case(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "sphere_r_20.0_center_0.0_0.0_0.0.xyz")
   generated_file = f"{test_folder}/sphere_r_{inp.radius}_center_{inp.sphere_center[0]}_{inp.sphere_center[1]}_{inp.sphere_center[2]}{inp.alloy_string}.xyz"

   move_created_geom(test_folder)
   
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
# -------------------------------------------------------------------------------------
def test_create_rod(monkeypatch):

   """
   Test if the generated rod geometry matches the expected XYZ file.
   """

   # Test folder
   test_folder = 'rod'
   
   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", '-create', '-rod', 'Ag', '50.0', '20.0', 'X']
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)
   
   # Run the geometry creation
   create_geom.select_case(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "rod_X_l_50.0_w_20.0.xyz")
   generated_file = f"{test_folder}/rod_{inp.main_axis.upper()}_l_{inp.rod_length}_w_{inp.rod_width}{inp.alloy_string}.xyz"

   move_created_geom(test_folder)
   
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
# -------------------------------------------------------------------------------------
def test_create_tip(monkeypatch):

   """
   Test if the generated tip geometry matches the expected XYZ file.
   """

   # Test folder
   test_folder = 'tip'
   
   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", '-create', '-tip', 'Ag', '50.0', '0.02', '0.02']
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)
   
   # Run the geometry creation
   create_geom.select_case(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "elliptic_paraboloid_a-0.02_b-0.02_zmin-0.0_zmax-50.0.xyz")
   generated_file = f"{test_folder}/elliptic_paraboloid_a-{inp.elliptic_parabola_a}_b-{inp.elliptic_parabola_b}_zmin-{inp.z_min}_zmax-{inp.z_max}{inp.alloy_string}.xyz"

   move_created_geom(test_folder)
   
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
# -------------------------------------------------------------------------------------
def test_create_pyramid(monkeypatch):

   """
   Test if the generated pyramid geometry matches the expected XYZ file.
   """

   # Test folder
   test_folder = 'pyramid'
   
   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", '-create', '-pyramid', 'Ag', '50.0', '30.0']
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)
   
   # Run the geometry creation
   create_geom.select_case(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "pyramid_length-30.0_zmin-0.0_zmax-50.0.xyz")
   generated_file = f"{test_folder}/pyramid_length-{inp.side_length}_zmin-{inp.z_min}_zmax-{inp.z_max}{inp.alloy_string}.xyz"

   move_created_geom(test_folder)
   
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
# -------------------------------------------------------------------------------------
def test_create_cone(monkeypatch):

   """
   Test if the generated cone geometry matches the expected XYZ file.
   """

   # Test folder
   test_folder = 'cone'
   
   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", '-create', '-cone', 'Ag', '50.0', '30.0']
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)
   
   # Run the geometry creation
   create_geom.select_case(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "cone_radius-30.0_zmin-0.0_zmax-50.0.xyz")
   generated_file = f"{test_folder}/cone_radius-{inp.radius}_zmin-{inp.z_min}_zmax-{inp.z_max}{inp.alloy_string}.xyz"

   move_created_geom(test_folder)
   
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
# -------------------------------------------------------------------------------------
def test_create_microscope(monkeypatch):

   """
   Test if the generated microscope geometry matches the expected XYZ file.
   """

   # Test folder
   test_folder = 'microscope'
   
   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", '-create', '-microscope', 'ag', '50.0', '0.02', '0.02', '35.0', '37.0']
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)
   
   # Run the geometry creation
   create_geom.select_case(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "microscope_parabola_35.0_0.02_0.02_pyramid_35.0_37.0.xyz")
   generated_file = f"{test_folder}/microscope_parabola_{inp.z_max}_{inp.elliptic_parabola_a}_{inp.elliptic_parabola_b}_pyramid_{inp.z_max}_{inp.side_length}{inp.alloy_string}.xyz"

   move_created_geom(test_folder)
   
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
# -
