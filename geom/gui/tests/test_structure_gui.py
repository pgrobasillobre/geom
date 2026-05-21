import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from geom.gui import structure_generator
from geom.gui.structure_generator import AtomRecord, manipulate_xyz, read_xyz
from geom.gui.structure_gui import GRAPHENE_VARIANTS, STRUCTURES, StructureWindow, VdwCanvas, atom_matches_selection


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
    assert not window.optional_label.isHidden()
    assert not window.options_card.isHidden()
    assert combo_items(window.structure_combo) == [
        "Sphere",
        "Rod",
        "Tip",
        "Pyramid",
        "Cone",
        "Microscope",
        "Icosahedron",
        "Cuboctahedron",
        "Decahedron",
    ]

    window.metal_combo.setCurrentText("Graphene")
    assert window.optional_label.isHidden()
    assert window.options_card.isHidden()
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

    window.alloy_check.setChecked(True)
    assert window.alloy_atom.isHidden()
    assert window._build_command_args() == [
        "-create",
        "-sphere",
        "-core",
        "Au",
        "20",
        "-shell",
        "Ag",
        "30",
        "-alloy",
        "-percentual",
        "20",
    ]

    window.core_shell_check.setChecked(False)
    assert not window.alloy_atom.isHidden()
    window.alloy_check.setChecked(False)
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


def test_core_shell_generation_reports_au_ag_counts(window):
    window.metal_combo.setCurrentText("Au")
    window.structure_combo.setCurrentText("Sphere")
    window.core_shell_check.setChecked(True)
    window.pending_generation_meta = window._generation_metadata()

    metadata = window._metadata_for_generated_atoms(
        (
            AtomRecord("Au", 0.0, 0.0, 0.0),
            AtomRecord("Ag", 1.0, 0.0, 0.0),
            AtomRecord("Ag", 2.0, 0.0, 0.0),
        )
    )

    assert metadata["au_count"] == 1
    assert metadata["ag_count"] == 2


def test_smiles_tab_uses_typed_title(window):
    atoms = (AtomRecord("C", 0.0, 0.0, 0.0),)
    window._add_structure_tab("C[C@H](O)N", atoms, None)
    assert window.tabs.tabText(window.tabs.currentIndex()) == "C[C@H](O)N"


def test_viewer_atom_selection_filters_current_structure(window):
    atoms = (
        AtomRecord("C", 1.0, 1.0, 0.0),
        AtomRecord("O", 1.0, -1.0, 0.0),
        AtomRecord("H", -1.0, 1.0, 0.0),
    )
    window._add_structure_tab("selection", atoms, None)
    window.atom_selection_input.setText("x > 0 and y > 0")

    canvas = window.tabs.currentWidget()
    assert isinstance(canvas, VdwCanvas)
    assert canvas.atoms == atoms

    window._apply_atom_selection()
    assert canvas.atoms == (atoms[0],)
    assert canvas.source_atoms == atoms
    assert canvas.selection_expression == "x > 0 and y > 0"
    assert canvas.property("atom_count") == 1

    window.atom_selection_input.setText("all")
    window._apply_atom_selection()
    assert canvas.atoms == atoms
    assert canvas.selection_expression == "all"
    assert canvas.property("atom_count") == 3


def test_atom_selection_supports_negative_comparisons():
    atom = AtomRecord("C", -2.0, 1.0, 0.0)
    assert atom_matches_selection(atom, "x < -1 and y >= 1")
    assert atom_matches_selection(atom, "X < -1 AND Y >= 1")
    assert not atom_matches_selection(atom, "x > 0 or z != 0")
    assert atom_matches_selection(atom, "name c")
    assert atom_matches_selection(atom, "NAME C and X < -1")
    assert not atom_matches_selection(atom, "name Ag")
    assert atom_matches_selection(atom, "ALL")
    with pytest.raises(ValueError):
        atom_matches_selection(atom, "x")


def test_atom_selection_is_stored_per_tab(window):
    first_atoms = (
        AtomRecord("Ag", 1.0, 0.0, 0.0),
        AtomRecord("Au", -1.0, 0.0, 0.0),
    )
    second_atoms = (
        AtomRecord("C", 1.0, 0.0, 0.0),
        AtomRecord("Ag", 2.0, 0.0, 0.0),
    )
    window._add_structure_tab("first", first_atoms, None)
    first_index = window.tabs.currentIndex()
    window.atom_selection_input.setText("name Ag")
    window._apply_atom_selection()

    window._add_structure_tab("second", second_atoms, None)
    second_index = window.tabs.currentIndex()
    assert window.atom_selection_input.text() == ""
    window.atom_selection_input.setText("name C")
    window._apply_atom_selection()

    window.tabs.setCurrentIndex(first_index)
    assert window.atom_selection_input.text() == "name Ag"
    assert window.tabs.currentWidget().atoms == (first_atoms[0],)

    window.tabs.setCurrentIndex(second_index)
    assert window.atom_selection_input.text() == "name C"
    assert window.tabs.currentWidget().atoms == (second_atoms[0],)


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


def test_manipulator_enantiomer_uses_selected_structure_then_centers(window, monkeypatch, tmp_path):
    source = tmp_path / "input.xyz"
    source.write_text("1\nx\nC 2 0 0\n")
    atoms = (AtomRecord("C", 2.0, 0.0, 0.0),)
    window._add_structure_tab("input", atoms, source)
    window._refresh_manipulator_sources()

    mirror_output = tmp_path / "input_000_mirror.xyz"
    mirror_output.write_text("1\nmirror\nC 7 0 0\n", encoding="utf-8")
    centered_output = tmp_path / "input_000_mirror_000.xyz"
    centered_output.write_text("1\ncentered\nC 0 0 0\n", encoding="utf-8")
    captured = []

    def fake_manipulate(input_path, command_builder):
        captured.append(command_builder(Path(input_path).name))
        return mirror_output if len(captured) == 1 else centered_output

    monkeypatch.setattr("geom.gui.structure_gui.manipulate_xyz", fake_manipulate)
    window.mirror_selected_structure()
    assert captured == [["-mirror", "input.xyz"], ["-tc", "input_000_mirror.xyz"]]
    assert window.tabs.tabText(window.tabs.currentIndex()) == centered_output.stem


def test_center_to_origin_button_depends_on_selected_structure_center(window, tmp_path):
    off_center = tmp_path / "off.xyz"
    off_center.write_text("2\noff\nC 1 0 0\nH 3 0 0\n", encoding="utf-8")
    centered = tmp_path / "centered.xyz"
    centered.write_text("2\ncentered\nC -1 0 0\nH 1 0 0\n", encoding="utf-8")

    window._add_structure_tab("off", (AtomRecord("C", 1.0, 0.0, 0.0), AtomRecord("H", 3.0, 0.0, 0.0)), off_center)
    window._add_structure_tab("centered", (AtomRecord("C", -1.0, 0.0, 0.0), AtomRecord("H", 1.0, 0.0, 0.0)), centered)
    window._refresh_manipulator_sources()

    window.manipulator_source.setCurrentIndex(window.manipulator_source.findData(str(off_center)))
    assert window.center_button.isEnabled()

    window.manipulator_source.setCurrentIndex(window.manipulator_source.findData(str(centered)))
    assert not window.center_button.isEnabled()


def test_manipulator_source_tracks_selected_viewer_tab(window, tmp_path):
    first = tmp_path / "first.xyz"
    first.write_text("1\nfirst\nC 0 0 0\n", encoding="utf-8")
    second = tmp_path / "second.xyz"
    second.write_text("1\nsecond\nH 0 0 0\n", encoding="utf-8")

    window._add_structure_tab("first", (AtomRecord("C", 0.0, 0.0, 0.0),), first)
    first_index = window.tabs.currentIndex()
    window._add_structure_tab("second", (AtomRecord("H", 0.0, 0.0, 0.0),), second)

    assert window.manipulator_source.currentData() == str(second)

    window.tabs.setCurrentIndex(first_index)

    assert window.manipulator_source.currentData() == str(first)


def test_center_to_origin_disabled_for_joint_visualization(window, tmp_path):
    source = tmp_path / "off.xyz"
    source.write_text("1\noff\nC 2 0 0\n", encoding="utf-8")
    window._add_structure_tab("off", (AtomRecord("C", 2.0, 0.0, 0.0),), source)
    window._add_structure_tab("joint", (AtomRecord("C", 2.0, 0.0, 0.0),), None)
    joint = window.tabs.currentWidget()
    joint.setProperty("fixed_path", str(source))
    joint.setProperty("translated_path", str(source))
    window._refresh_manipulator_sources()
    assert not window.center_button.isEnabled()


def test_manipulator_enantiomer_generates_mirrored_xyz(monkeypatch, tmp_path):
    monkeypatch.setattr(structure_generator, "GUI_TMP_ROOT", tmp_path / "gui_tmp")
    source = tmp_path / "input.xyz"
    source.write_text("2\ninput\nC 0 0 0\nH 1 0 0\n", encoding="utf-8")

    output = manipulate_xyz(source, lambda filename: ["-mirror", filename])

    assert output.name.endswith("_000_mirror.xyz")
    atoms = read_xyz(output)
    assert len(atoms) == 2
    assert atoms[0].element == "C"
    assert atoms[1].element == "H"


def test_install_and_uninstall_scripts_parse():
    root = Path(__file__).resolve().parents[3]
    install_script = root / "install.sh"
    assert install_script.exists()
    assert "create_uninstall_script" in install_script.read_text(encoding="utf-8")
