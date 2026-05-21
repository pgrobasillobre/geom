import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from geom.gui.structure_generator import AtomRecord
from geom.gui.structure_gui import GRAPHENE_VARIANTS, STRUCTURES, StructureWindow, VdwCanvas


@pytest.fixture(scope="session")
def app():
    instance = QApplication.instance()
    return instance or QApplication([])


@pytest.fixture
def window(app):
    widget = StructureWindow()
    widget.resize(900, 640)
    yield widget
    widget.close()


def combo_items(combo):
    return [combo.itemText(index) for index in range(combo.count())]


def test_gui_window_smoke_loads_main_sections(window):
    assert window.windowTitle()
    assert window.side_tabs.count() == 3
    assert window.side_tabs.tabText(0) == "Viewer"
    assert window.side_tabs.tabText(1) == "Generator"
    assert window.side_tabs.tabText(2) == "Manipulator"
    assert isinstance(window.canvas, VdwCanvas)


def test_generator_keeps_expected_metal_and_graphene_options(window):
    window.metal_combo.setCurrentText("Au")
    assert combo_items(window.structure_combo) == [
        "Sphere",
        "Rod",
        "Tip",
        "Pyramid square base",
        "Cone",
        "Microscope",
        "Icosahedron",
        "Cuboctahedron",
        "Decahedron",
    ]

    window.metal_combo.setCurrentText("Graphene")
    assert combo_items(window.graphene_variant_combo) == list(GRAPHENE_VARIANTS.keys())
    assert "Triangle" in combo_items(window.graphene_variant_combo)


def test_generator_builds_core_shell_and_microscope_commands(window):
    window.metal_combo.setCurrentText("Au")
    window.structure_combo.setCurrentText("Sphere")
    window.core_shell_check.setChecked(True)
    assert window._build_command_args() == [
        "-create",
        "-sphere",
        "-core",
        "Au",
        "20",
        "-shell",
        "Ag",
        "30",
    ]

    window.core_shell_check.setChecked(False)
    window.structure_combo.setCurrentText("Microscope")
    assert window._build_command_args() == [
        "-create",
        "-microscope",
        "Au",
        "40",
        "0.02",
        "0.02",
        "26",
        "33",
    ]


def test_smiles_tab_uses_typed_title(window):
    atoms = (AtomRecord("C", 0.0, 0.0, 0.0),)
    window._add_structure_tab("C[C@H](O)N", atoms, None)
    assert window.tabs.tabText(window.tabs.currentIndex()) == "C[C@H](O)N"


def test_mixed_metal_cpk_scene_uses_mixed_render_path(window):
    atoms = (
        AtomRecord("Au", 0.0, 0.0, 0.0),
        AtomRecord("Au", 1.0, 0.0, 0.0),
        AtomRecord("C", 3.0, 0.0, 0.0),
        AtomRecord("O", 4.2, 0.0, 0.0),
    )
    window.canvas.set_atoms(atoms)
    projected = window.canvas._project_atoms()
    assert any(atom.cpk for atom in projected)
    assert any(not atom.cpk for atom in projected)
    if window.canvas._gl is not None:
        assert window.canvas._uses_mixed_vdw_cpk(projected)


def test_manipulator_enantiomer_uses_mirror_command(window, monkeypatch, tmp_path):
    source = tmp_path / "input.xyz"
    source.write_text("1\nx\nC 0 0 0\n")
    atoms = (AtomRecord("C", 0.0, 0.0, 0.0),)
    window._add_structure_tab("input", atoms, source)
    window._refresh_manipulator_sources()

    captured = {}

    def fake_run(command_builder):
        captured["command"] = command_builder(str(source))

    monkeypatch.setattr(window, "_run_manipulation", fake_run)
    window.mirror_selected_structure()
    assert captured["command"] == ["-mirror", str(source)]


def test_install_and_uninstall_scripts_parse():
    root = Path(__file__).resolve().parents[3]
    assert (root / "install.sh").exists()
    assert (root / "uninstall.sh").exists()
