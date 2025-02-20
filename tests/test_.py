import pytest
import sys
import os
import filecmp

# Add the project root to sys.path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
test_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))

from classes import input_class
from functions import general, various, translate, rotate, create_geom

# -------------------------------------------------------------------------------------
def move_input_geom(folder,xyz_file,optional_file=None):
   """
   Move input geometry into scratch folder 
   If an optional file is provided, it is also copied
   """

   file_path_xyz = os.path.join(os.path.dirname(__file__), folder, xyz_file)

   os.system(f'cp {file_path_xyz} .')

   if optional_file:
      file_path_optional = os.path.join(os.path.dirname(__file__), folder, optional_file)
      os.system(f'cp {file_path_optional} .')
# -------------------------------------------------------------------------------------
def move_managed_geom(folder, remove_optional_file = None):
   """
   Move created geometry to folder and remove results_geom folder
   If an optional file is provided, it is removed
   """

   file_path = os.path.join(os.path.dirname(__file__))
   file_path_results = os.path.join(file_path, "results_geom")
   file_path_results_xyz  = os.path.join(file_path_results, "*xyz")

   os.system(f'mv {file_path_results_xyz} {folder}')
   os.system(f'rm -rf {file_path}/*xyz {file_path_results} ')

   if remove_optional_file: os.system(f'rm -rf {remove_optional_file}')
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
def test_create_sphere_core_shell(monkeypatch):
   """
   Test if the generated sphere core-shell geometry matches the expected XYZ file.
   """

   # Test folder
   test_folder = 'sphere_core_shell'
   
   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", "-create", "-sphere", "-core", "20.0", "au", "-shell", "30", "ag"]
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)
   
   # Run the geometry creation
   create_geom.select_case(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "sphere_core_au_r_20.0_shell_ag_r_30.0.xyz")
   generated_file = f"{test_folder}/sphere_core_{inp.atomtype_in}_r_{inp.radius_in}_shell_{inp.atomtype_out}_r_{inp.radius_out}{inp.alloy_string}.xyz"

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
def test_create_rod_core_shell(monkeypatch):
   """
   Test if the generated rod core-shell geometry matches the expected XYZ file.
   """

   # Test folder
   test_folder = 'rod_core_shell'
   
   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", "-create", "-rod", 'x', '-core', 'au', '20.0', '10.0', '-shell', 'ag', '50.0', '20.0']
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)
   
   # Run the geometry creation
   create_geom.select_case(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "rod_core_au_L_20.0_R_10.0_shell_ag_L_50.0_R_20.0_shell_ag.xyz")
   generated_file = f"{test_folder}/rod_core_{inp.atomtype_in}_L_{inp.rod_length_in}_R_{inp.rod_width_in}_shell_{inp.atomtype_out}_L_{inp.rod_length_out}_R_{inp.rod_width_out}_shell_{inp.atomtype_out}{inp.alloy_string}.xyz"

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
def test_create_icosahedra(monkeypatch):
   """
   Test if the generated icosahedral geometry matches the expected XYZ file.
   """

   # Test folder
   test_folder = 'icosahedron'
   
   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", '-create', '-ico', 'au', '50.0']
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)
   
   # Run the geometry creation
   create_geom.select_case(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "icosahedron_au_r_50.0.xyz")
   generated_file = f"{test_folder}/icosahedron_{inp.atomtype}_r_{inp.radius}{inp.alloy_string}.xyz"

   move_created_geom(test_folder)
   
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
# -------------------------------------------------------------------------------------
def test_create_cuboctahedra(monkeypatch):
   """
   Test if the generated cuboctahedral geometry matches the expected XYZ file.
   """

   # Test folder
   test_folder = 'cuboctahedron'
   
   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", '-create', '-cto', 'au', '50.0']
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)
   
   # Run the geometry creation
   create_geom.select_case(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "cuboctahedron_au_r_50.0.xyz")
   generated_file = f"{test_folder}/cuboctahedron_{inp.atomtype}_r_{inp.radius}{inp.alloy_string}.xyz"

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
   mock_args = ["dummy", '-create', '-microscope', 'ag', '40.0', '0.02', '0.02', '26.0', '33.0']
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)
   
   # Run the geometry creation
   create_geom.select_case(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "microscope_parabola_26.0_0.02_0.02_pyramid_26.0_33.0.xyz")
   generated_file = f"{test_folder}/microscope_parabola_{inp.z_max}_{inp.elliptic_parabola_a}_{inp.elliptic_parabola_b}_pyramid_{inp.z_max}_{inp.side_length}{inp.alloy_string}.xyz"

   move_created_geom(test_folder)
   
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
# -------------------------------------------------------------------------------------
def test_create_graphene_ribbon(monkeypatch):
   """
   Test if the generated graphene ribbon geometry matches the expected XYZ file.
   """

   # Test folder
   test_folder = 'graphene_ribbon'
   
   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", "-create", "-graphene", "rib", "40.0", "20.0"]
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)
   
   # Run the geometry creation
   create_geom.select_case(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "graphene_ribbon_40.0_20.0.xyz")
   generated_file = f"{test_folder}/graphene_ribbon_{inp.X_length}_{inp.Y_length}.xyz"

   move_created_geom(test_folder)
   
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
# -------------------------------------------------------------------------------------
def test_create_graphene_disk(monkeypatch):
   """
   Test if the generated graphene disk geometry matches the expected XYZ file.
   """

   # Test folder
   test_folder = 'graphene_disk'
   
   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", "-create", "-graphene", "disk", "30.0"]
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)
   
   # Run the geometry creation
   create_geom.select_case(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "graphene_disk_30.0.xyz")
   generated_file = f"{test_folder}/graphene_disk_{inp.radius}.xyz"

   move_created_geom(test_folder)
   
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
# -------------------------------------------------------------------------------------
def test_create_graphene_ring(monkeypatch):
   """
   Test if the generated graphene ring geometry matches the expected XYZ file.
   """

   # Test folder
   test_folder = 'graphene_ring'
   
   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", "-create", "-graphene", "ring", "60.0", "30.0"]
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)
   
   # Run the geometry creation
   create_geom.select_case(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "graphene_ring_Out_60.0_In_30.0.xyz")
   generated_file = f"{test_folder}/graphene_ring_Out_{inp.radius_out}_In_{inp.radius_in}.xyz"

   move_created_geom(test_folder)
   
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
# -------------------------------------------------------------------------------------
def test_create_graphene_triangle_armchair(monkeypatch):
   """
   Test if the generated graphene triangle armchair geometry matches the expected XYZ file.
   """

   # Test folder
   test_folder = 'graphene_triangle_armchair'
   
   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", "-create", "-graphene", "triangle", "armchair", "50.0"]
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)
   
   # Run the geometry creation
   create_geom.select_case(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "graphene_triangle_armchair_50.0.xyz")
   generated_file = f"{test_folder}/graphene_triangle_{inp.graphene_edge_type}_{inp.side_length}.xyz"

   move_created_geom(test_folder)
   
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
# -------------------------------------------------------------------------------------
def test_create_graphene_triangle_zigzag(monkeypatch):
   """
   Test if the generated graphene triangle zigzag geometry matches the expected XYZ file.
   """

   # Test folder
   test_folder = 'graphene_triangle_zigzag'
   
   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", "-create", "-graphene", "triangle", "zigzag", "50.0"]
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)
   
   # Run the geometry creation
   create_geom.select_case(inp)
   
   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "graphene_triangle_zigzag_50.0.xyz")
   generated_file = f"{test_folder}/graphene_triangle_{inp.graphene_edge_type}_{inp.side_length}.xyz"

   move_created_geom(test_folder)
   
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
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

   move_managed_geom(test_folder)
   
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
# -------------------------------------------------------------------------------------
def test_controlled_distance(monkeypatch):
   """
   Test controlled distance.
   """

   # Test folder
   test_folder      = 'control_distance'
   xyz_input_file_1 = 'doxorubicin.xyz'
   xyz_input_file_2 = 'sphere_r_10.0_center_0.0_0.0_0.0.xyz'
   distances_input  = 'distances_input'

   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", "-t", "distances_input", "doxorubicin.xyz", "no", "sphere_r_10.0_center_0.0_0.0_0.0.xyz", "no", "+x", "verbose_no"]
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)

   # Temporaly move input file
   move_input_geom(test_folder,xyz_input_file_1, optional_file = distances_input)
   move_input_geom(test_folder,xyz_input_file_2)

   # Translate controlled distance
   translate.translate_controlled_distance(inp)

   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "sphere_r_10.0_center_0.0_0.0_0.0_+x_d_10.00.xyz")
   generated_file = f"{test_folder}/sphere_r_10.0_center_0.0_0.0_0.0_+x_d_10.00.xyz"

   move_managed_geom(test_folder, remove_optional_file = distances_input)
   
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
# -------------------------------------------------------------------------------------
def test_r1_rotation(monkeypatch):
   """
   Test r1 rotation
   """

   # Test folder
   test_folder    = 'r1_rotation'
   xyz_input_file = 'doxorubicin.xyz'

   # Mock sys.argv to simulate the command line input
   mock_args = ["dummy", "-r1", "30.0", "doxorubicin.xyz", "no", "-y"]
   monkeypatch.setattr(sys, "argv", mock_args)
   
   # Manually create and populate the input class
   inp = input_class.input_class()
   general.read_command_line(sys.argv, inp)

   # Temporaly move input file
   move_input_geom(test_folder,xyz_input_file)

   # Translate controlled distance
   rotate.rotate_1(inp)

   # Define the expected and actual output files
   expected_file = os.path.join(os.path.dirname(__file__), test_folder, "reference", "doxorubicin_-y_degree_30.0.xyz")
   generated_file = f"{test_folder}/doxorubicin_-y_degree_30.0.xyz"

   move_managed_geom(test_folder)
 
   # Compare the generated file with the reference
   assert filecmp.cmp(generated_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"
# -------------------------------------------------------------------------------------
