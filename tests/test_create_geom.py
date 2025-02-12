import pytest
import sys
import filecmp
from classes import * 
from functions import *

def test_create_sphere(monkeypatch):
    """Test if the generated sphere geometry matches the expected XYZ file."""

    # 1. Mock sys.argv to simulate the command line input
    mock_args = ["geom", "-create", "-sphere", "Ag", "20.0", "0.0", "0.0", "0.0"]
    monkeypatch.setattr(sys, "argv", mock_args)

    # 2. Manually create and populate the input class
    inp = input_class.input_class()
    general.read_command_line(sys.argv, inp)

    # 3. Run the geometry creation
    create_geom.select_case(inp)

    # 4. Define the expected and actual output files
    expected_file = "reference/sphere_r_20.0_center_0.0_0.0_0.0.xyz"
    actual_file = f"sphere_r_{inp.radius}_center_{inp.sphere_center[0]}_{inp.sphere_center[1]}_{inp.sphere_center[2]}{inp.alloy_string}.xyz"

    # 5. Compare the generated file with the reference
    assert filecmp.cmp(actual_file, expected_file, shallow=False), "Generated XYZ file does not match the expected output"

