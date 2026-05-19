"""Native Qt GUI for creating and visualizing GEOM XYZ structures."""

from __future__ import annotations

import math
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path

try:
    from PySide6.QtCore import QPoint, QRectF, Qt, QThread, Signal
    from PySide6.QtGui import (
        QColor,
        QFont,
        QFontDatabase,
        QGuiApplication,
        QLinearGradient,
        QPainter,
        QRadialGradient,
    )
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDoubleSpinBox,
        QFileDialog,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - exercised by users without GUI deps.
    missing_dependency = exc
    QPoint = QRectF = Qt = QGuiApplication = QApplication = QFileDialog = QMessageBox = None
    QColor = lambda *args, **kwargs: None
    QLinearGradient = QPainter = QRadialGradient = None

    class QFont:
        DemiBold = 63

    QFontDatabase = None
    QCheckBox = QComboBox = QDoubleSpinBox = QFrame = QGridLayout = QHBoxLayout = QLabel = None
    QPushButton = QSizePolicy = QVBoxLayout = None
    QMainWindow = QWidget = object

    class QThread:
        pass

    def Signal(*args, **kwargs):
        return None
else:
    missing_dependency = None

from geom.gui.structure_generator import (
    AtomRecord,
    StructureResult,
    generate_structure,
    supported_atomistic_metals,
    supported_fcc_metals,
)


APP_TITLE = "GEOM Structure Studio"

CHATGPT_GREEN = "#10A37F"
TEXT = "#202123"
MUTED = "#6E6E80"
SURFACE = "#FFFFFF"
CANVAS = "#F7F7F8"
BORDER = "#D9D9E3"
SIDEBAR = "#ECECF1"
SOFT_BORDER = "#ECECF1"

# VMD's periodic table VDW radii in Angstrom.
# Source: VMD PeriodicTable.C, pte_vdw_radius/get_pte_vdw_radius.
VMD_ELEMENT_LABELS = (
    "X", "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
    "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca", "Sc",
    "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge",
    "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc",
    "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe",
    "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb",
    "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Hf", "Ta", "W", "Re", "Os",
    "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr",
    "Ra", "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf",
    "Es", "Fm", "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt",
    "Ds", "Rg",
)

VMD_VDW_RADII = (
    1.50, 1.00, 1.40, 1.82, 2.00, 2.00,
    1.70, 1.55, 1.52, 1.47, 1.54,
    1.36, 1.18, 2.00, 2.10, 1.80,
    1.80, 2.27, 1.88, 1.76, 1.37, 2.00,
    2.00, 2.00, 2.00, 2.00, 2.00, 2.00,
    1.63, 1.40, 1.39, 1.07, 2.00, 1.85,
    1.90, 1.85, 2.02, 2.00, 2.00, 2.00,
    2.00, 2.00, 2.00, 2.00, 2.00, 2.00,
    1.63, 1.72, 1.58, 1.93, 2.17, 2.00,
    2.06, 1.98, 2.16, 2.10, 2.00,
    2.00, 2.00, 2.00, 2.00, 2.00, 2.00,
    2.00, 2.00, 2.00, 2.00, 2.00,
    2.00, 2.00, 2.00, 2.00, 2.00, 2.00,
    2.00, 2.00, 2.00, 2.00, 1.72, 1.66,
    1.55, 1.96, 2.02, 2.00, 2.00, 2.00, 2.00,
    2.00, 2.00, 2.00, 2.00, 2.00, 1.86,
    2.00, 2.00, 2.00, 2.00, 2.00, 2.00, 2.00, 2.00,
    2.00, 2.00, 2.00, 2.00, 2.00, 2.00, 2.00, 2.00,
    2.00, 2.00, 2.00,
)

VDW_RADII = dict(zip(VMD_ELEMENT_LABELS, VMD_VDW_RADII))

DEFAULT_VMD_PINK = QColor("#F2C7CF")
ELEMENT_COLORS = {}

STRUCTURES = {
    "Sphere": {
        "flag": "-sphere",
        "metals": "bulk",
        "fields": (("radius", "Radius", 20.0, 2.0, 300.0),),
    },
    "Rod": {
        "flag": "-rod",
        "metals": "bulk",
        "axis": True,
        "fields": (("length", "Length", 50.0, 4.0, 500.0), ("width", "Width", 20.0, 2.0, 300.0)),
    },
    "Tip": {
        "flag": "-tip",
        "metals": "bulk",
        "bowtie": True,
        "fields": (("z_max", "Height", 50.0, 2.0, 500.0), ("a", "a", 0.02, 0.001, 2.0), ("b", "b", 0.02, 0.001, 2.0)),
    },
    "Pyramid": {
        "flag": "-pyramid",
        "metals": "bulk",
        "bowtie": True,
        "fields": (("z_max", "Height", 50.0, 2.0, 500.0), ("side", "Base side", 30.0, 2.0, 500.0)),
    },
    "Pentagonal Pyramid": {
        "flag": "-pentpyramid",
        "metals": "bulk",
        "bowtie": True,
        "fields": (("base", "Base width", 30.0, 2.0, 500.0), ("z_max", "Height", 50.0, 2.0, 500.0)),
    },
    "Cone": {
        "flag": "-cone",
        "metals": "bulk",
        "bowtie": True,
        "fields": (("z_max", "Height", 50.0, 2.0, 500.0), ("radius", "Radius", 30.0, 2.0, 300.0)),
    },
    "Icosahedron": {
        "flag": "-ico",
        "metals": "fcc",
        "fields": (("radius", "Radius", 50.0, 2.0, 300.0),),
    },
    "Cuboctahedron": {
        "flag": "-cto",
        "metals": "fcc",
        "fields": (("radius", "Radius", 50.0, 2.0, 300.0),),
    },
    "Decahedron": {
        "flag": "-idh",
        "metals": "fcc",
        "fields": (("radius", "Radius", 50.0, 2.0, 300.0),),
    },
    "Bipyramid": {
        "flag": "-bipyramid",
        "metals": "bulk",
        "fields": (("width", "Width", 30.0, 2.0, 300.0), ("length", "Length", 50.0, 4.0, 500.0)),
    },
}


@dataclass(frozen=True)
class ProjectedAtom:
    element: str
    x: float
    y: float
    z: float
    radius: float


class GenerationWorker(QThread):
    generated = Signal(object)
    failed = Signal(str)

    def __init__(self, command_args: list[str], output_root: Path, parent=None):
        super().__init__(parent)
        self.command_args = command_args
        self.output_root = output_root

    def run(self):
        try:
            self.generated.emit(generate_structure(self.command_args, self.output_root))
        except Exception:
            self.failed.emit(traceback.format_exc())


class VdwCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.atoms: tuple[AtomRecord, ...] = ()
        self.rotation_x = math.radians(18.0)
        self.rotation_y = math.radians(-28.0)
        self.zoom = 1.0
        self._last_pos: QPoint | None = None
        self.setMinimumSize(560, 420)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

    def set_atoms(self, atoms: tuple[AtomRecord, ...]):
        self.atoms = atoms
        self.zoom = 1.0
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._last_pos = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if self._last_pos is None:
            return
        current = event.position().toPoint()
        delta = current - self._last_pos
        self._last_pos = current
        self.rotation_y += delta.x() * 0.01
        self.rotation_x += delta.y() * 0.01
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._last_pos = None

    def wheelEvent(self, event):
        factor = 1.12 if event.angleDelta().y() > 0 else 0.89
        self.zoom = min(4.0, max(0.35, self.zoom * factor))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        self._paint_background(painter)

        if not self.atoms:
            self._paint_empty_state(painter)
            return

        projected = self._project_atoms()
        for atom in projected:
            self._paint_atom(painter, atom)

    def _paint_background(self, painter: QPainter):
        painter.fillRect(self.rect(), QColor("#FFFFFF"))

    def _paint_empty_state(self, painter: QPainter):
        painter.setPen(QColor(MUTED))
        font = QFontDatabase.systemFont(QFontDatabase.GeneralFont)
        font.setPointSize(18)
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "Create a structure")

    def _project_atoms(self) -> list[ProjectedAtom]:
        cx = sum(atom.x for atom in self.atoms) / len(self.atoms)
        cy = sum(atom.y for atom in self.atoms) / len(self.atoms)
        cz = sum(atom.z for atom in self.atoms) / len(self.atoms)
        cos_x, sin_x = math.cos(self.rotation_x), math.sin(self.rotation_x)
        cos_y, sin_y = math.cos(self.rotation_y), math.sin(self.rotation_y)

        rotated: list[tuple[AtomRecord, float, float, float]] = []
        max_span = 1.0
        for atom in self.atoms:
            x, y, z = atom.x - cx, atom.y - cy, atom.z - cz
            xz = x * cos_y + z * sin_y
            zz = -x * sin_y + z * cos_y
            yz = y * cos_x - zz * sin_x
            zz2 = y * sin_x + zz * cos_x
            rotated.append((atom, xz, yz, zz2))
            max_span = max(max_span, abs(xz), abs(yz))

        scale = min(self.width(), self.height()) * 0.42 * self.zoom / max_span
        center_x = self.width() * 0.52
        center_y = self.height() * 0.50

        atoms = []
        for atom, x, y, z in rotated:
            element = atom.element.capitalize()
            radius = VDW_RADII.get(element, VDW_RADII["X"]) * scale * 0.68
            atoms.append(ProjectedAtom(element, center_x + x * scale, center_y - y * scale, z, radius))

        atoms.sort(key=lambda item: item.z)
        return atoms

    def _paint_atom(self, painter: QPainter, atom: ProjectedAtom):
        base = ELEMENT_COLORS.get(atom.element, DEFAULT_VMD_PINK)
        depth = max(0.55, min(1.15, 0.84 + atom.z * 0.015))
        shaded = QColor(
            min(255, int(base.red() * depth)),
            min(255, int(base.green() * depth)),
            min(255, int(base.blue() * depth)),
        )

        rect = QRectF(atom.x - atom.radius, atom.y - atom.radius, atom.radius * 2, atom.radius * 2)
        gradient = QRadialGradient(rect.center() - QPoint(int(atom.radius * 0.35), int(atom.radius * 0.40)), atom.radius)
        highlight = QColor(255, 255, 255, 230)
        gradient.setColorAt(0.0, highlight)
        gradient.setColorAt(0.18, shaded.lighter(132))
        gradient.setColorAt(0.76, shaded)
        gradient.setColorAt(1.0, shaded.darker(165))
        painter.setPen(QColor(0, 0, 0, 34))
        painter.setBrush(gradient)
        painter.drawEllipse(rect)


class StructureWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker: GenerationWorker | None = None
        self.current_result: StructureResult | None = None
        self.output_root: Path | None = None
        self.setWindowTitle(APP_TITLE)
        self.resize(1180, 760)
        self._build_ui()

    def _build_ui(self):
        app_font = QFontDatabase.systemFont(QFontDatabase.GeneralFont)
        app_font.setPointSize(13)
        self.setFont(app_font)

        root = QWidget()
        root.setObjectName("root")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(root)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(380)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(24, 24, 24, 24)
        side.setSpacing(18)

        title = QLabel("GEOM")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignHCenter)
        subtitle = QLabel("Structure generation")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignHCenter)

        self.structure_combo = QComboBox()
        self.structure_combo.addItems(STRUCTURES.keys())
        self.structure_combo.currentTextChanged.connect(self._refresh_structure_controls)
        self.metal_combo = QComboBox()
        self.metal_combo.currentTextChanged.connect(self._refresh_option_controls)

        self.axis_label = self._field_label("Axis")
        self.axis_combo = QComboBox()
        self.axis_combo.addItems(("x", "y", "z"))
        self.axis_combo.setCurrentText("z")

        self.param_labels: list[QLabel] = []
        self.param_spins: list[QDoubleSpinBox] = []
        for _ in range(3):
            label = self._field_label("")
            spin = QDoubleSpinBox()
            spin.setDecimals(3)
            spin.setSingleStep(1.0)
            spin.setSuffix(" Å")
            self.param_labels.append(label)
            self.param_spins.append(spin)

        controls = QFrame()
        controls.setObjectName("controls")
        form = QGridLayout(controls)
        form.setContentsMargins(16, 16, 16, 16)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(14)
        form.addWidget(self._field_label("Structure"), 0, 0)
        form.addWidget(self.structure_combo, 0, 1)
        form.addWidget(self._field_label("Metal"), 1, 0)
        form.addWidget(self.metal_combo, 1, 1)
        form.addWidget(self.axis_label, 2, 0)
        form.addWidget(self.axis_combo, 2, 1)
        for index, (label, spin) in enumerate(zip(self.param_labels, self.param_spins), start=3):
            form.addWidget(label, index, 0)
            form.addWidget(spin, index, 1)

        options = QFrame()
        options.setObjectName("controls")
        option_layout = QGridLayout(options)
        option_layout.setContentsMargins(16, 16, 16, 16)
        option_layout.setHorizontalSpacing(12)
        option_layout.setVerticalSpacing(12)

        self.dimer_check = QCheckBox("Dimer")
        self.dimer_check.toggled.connect(self._refresh_option_controls)
        self.dimer_distance = self._make_option_spin(10.0, 0.1, 300.0)
        self.dimer_axis = QComboBox()
        self.dimer_axis.addItems(("+x", "-x", "+y", "-y", "+z", "-z"))
        self.dimer_axis.setCurrentText("+z")
        self.dimer_widgets = (self.dimer_check, self.dimer_distance, self.dimer_axis)

        self.alloy_check = QCheckBox("Alloy")
        self.alloy_check.toggled.connect(self._refresh_option_controls)
        self.alloy_atom = QComboBox()
        self.alloy_atom.addItems(("Au", "Ag"))
        self.alloy_percent = self._make_option_spin(20.0, 0.1, 99.9)
        self.alloy_percent.setSuffix(" %")
        self.alloy_widgets = (self.alloy_check, self.alloy_atom, self.alloy_percent)

        self.bowtie_check = QCheckBox("Bowtie")
        self.bowtie_check.toggled.connect(self._refresh_option_controls)
        self.bowtie_distance = self._make_option_spin(10.0, 0.1, 300.0)
        self.bowtie_widgets = (self.bowtie_check, self.bowtie_distance)

        option_layout.addWidget(self.dimer_check, 0, 0)
        option_layout.addWidget(self.dimer_distance, 0, 1)
        option_layout.addWidget(self.dimer_axis, 0, 2)
        option_layout.addWidget(self.alloy_check, 1, 0)
        option_layout.addWidget(self.alloy_atom, 1, 1)
        option_layout.addWidget(self.alloy_percent, 1, 2)
        option_layout.addWidget(self.bowtie_check, 2, 0)
        option_layout.addWidget(self.bowtie_distance, 2, 1, 1, 2)

        self.create_button = QPushButton("Create structure")
        self.create_button.setObjectName("primaryButton")
        self.create_button.clicked.connect(self.create_structure)

        side.addWidget(title)
        side.addWidget(subtitle)
        side.addSpacing(22)
        side.addWidget(controls)
        side.addWidget(options)
        side.addStretch(1)
        side.addWidget(self.create_button)

        main = QFrame()
        main.setObjectName("main")
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(8)

        header = QHBoxLayout()
        self.meta_label = QLabel("")
        self.meta_label.setObjectName("meta")
        header.addStretch(1)
        header.addWidget(self.meta_label)

        self.canvas = VdwCanvas()
        self.canvas.setObjectName("canvas")
        main_layout.addLayout(header)
        main_layout.addWidget(self.canvas)

        layout.addWidget(sidebar)
        layout.addWidget(main, 1)
        self._apply_styles()
        self._refresh_structure_controls()

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _make_option_spin(self, value: float, minimum: float, maximum: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(2)
        spin.setSingleStep(1.0)
        spin.setValue(value)
        spin.setSuffix(" Å")
        return spin

    def _refresh_structure_controls(self):
        definition = STRUCTURES[self.structure_combo.currentText()]
        metals = supported_fcc_metals() if definition["metals"] == "fcc" else supported_atomistic_metals()
        current_metal = self.metal_combo.currentText() or "Ag"

        self.metal_combo.blockSignals(True)
        self.metal_combo.clear()
        self.metal_combo.addItems(metals)
        self.metal_combo.setCurrentText(current_metal if current_metal in metals else metals[0])
        self.metal_combo.blockSignals(False)

        has_axis = bool(definition.get("axis"))
        self.axis_label.setVisible(has_axis)
        self.axis_combo.setVisible(has_axis)

        fields = definition["fields"]
        for index, (label, spin) in enumerate(zip(self.param_labels, self.param_spins)):
            if index < len(fields):
                _, text, value, minimum, maximum = fields[index]
                label.setText(text)
                label.setVisible(True)
                spin.setVisible(True)
                spin.setRange(minimum, maximum)
                spin.setValue(value)
                spin.setSuffix("" if text in {"a", "b"} else " Å")
                spin.setSingleStep(0.01 if text in {"a", "b"} else 1.0)
            else:
                label.setVisible(False)
                spin.setVisible(False)

        self._refresh_option_controls()

    def _refresh_option_controls(self):
        metal = self.metal_combo.currentText()
        alloy_allowed = metal in {"Ag", "Au"}
        bowtie_allowed = bool(STRUCTURES[self.structure_combo.currentText()].get("bowtie"))

        if alloy_allowed:
            self.alloy_atom.setCurrentText("Au" if metal == "Ag" else "Ag")
        else:
            self.alloy_check.setChecked(False)

        if not bowtie_allowed:
            self.bowtie_check.setChecked(False)

        if self.dimer_check.isChecked() and self.bowtie_check.isChecked():
            sender = self.sender()
            if sender is self.bowtie_check:
                self.dimer_check.setChecked(False)
            else:
                self.bowtie_check.setChecked(False)

        self._set_optional_row_enabled(self.dimer_widgets, self.dimer_check.isChecked())
        self.dimer_check.setEnabled(True)

        self._set_optional_row_enabled(self.alloy_widgets, alloy_allowed and self.alloy_check.isChecked())
        self.alloy_check.setEnabled(alloy_allowed)

        for widget in self.bowtie_widgets:
            widget.setVisible(bowtie_allowed)
        self._set_optional_row_enabled(self.bowtie_widgets, bowtie_allowed and self.bowtie_check.isChecked())
        self.bowtie_check.setEnabled(bowtie_allowed)

    def _set_optional_row_enabled(self, widgets, enabled: bool):
        for widget in widgets:
            widget.setEnabled(enabled)

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QWidget#root {{
                background: {SURFACE};
                color: {TEXT};
            }}
            QFrame#sidebar {{
                background: {SURFACE};
                border-right: 1px solid {SOFT_BORDER};
            }}
            QFrame#main {{
                background: {SURFACE};
            }}
            QFrame#controls {{
                background: {SURFACE};
                border: 1px solid {SOFT_BORDER};
                border-radius: 14px;
            }}
            QLabel#appTitle {{
                color: {TEXT};
                font-size: 38px;
                font-weight: 750;
                letter-spacing: 0;
            }}
            QLabel#subtitle, QLabel#fieldLabel {{
                color: {MUTED};
                font-size: 13px;
            }}
            QLabel#meta {{
                color: {TEXT};
                font-size: 20px;
                font-weight: 750;
            }}
            QComboBox, QDoubleSpinBox {{
                background: {SURFACE};
                color: {TEXT};
                border: 1px solid {SOFT_BORDER};
                border-radius: 10px;
                min-height: 40px;
                padding: 4px 12px;
                font-size: 14px;
            }}
            QComboBox:disabled, QDoubleSpinBox:disabled {{
                background: #F7F7F8;
                color: #A8A8B3;
                border-color: #EEEEF2;
            }}
            QCheckBox {{
                color: {TEXT};
                font-size: 14px;
                spacing: 8px;
            }}
            QCheckBox:unchecked {{
                color: {MUTED};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1px solid {SOFT_BORDER};
                border-radius: 5px;
                background: {SURFACE};
            }}
            QCheckBox::indicator:checked {{
                background: {CHATGPT_GREEN};
                border-color: {CHATGPT_GREEN};
            }}
            QCheckBox::indicator:disabled {{
                background: #F4F4F5;
            }}
            QPushButton {{
                background: {SURFACE};
                color: {TEXT};
                border: 1px solid {SOFT_BORDER};
                border-radius: 10px;
                min-height: 44px;
                padding: 6px 12px;
                font-weight: 600;
                font-size: 15px;
            }}
            QPushButton:hover {{
                border-color: {CHATGPT_GREEN};
            }}
            QPushButton#primaryButton {{
                background: {CHATGPT_GREEN};
                color: white;
                border-color: {CHATGPT_GREEN};
            }}
            QPushButton#primaryButton:disabled {{
                background: #9ED9C8;
                border-color: #9ED9C8;
            }}
            QWidget#canvas {{
                background: {SURFACE};
                border: 0;
                border-radius: 0;
            }}
        """)

    def create_structure(self):
        if self.output_root is None:
            folder = QFileDialog.getExistingDirectory(self, "Save generated XYZ structures in", str(Path.cwd()))
            if not folder:
                return
            self.output_root = Path(folder)

        try:
            command_args = self._build_command_args()
        except ValueError as exc:
            QMessageBox.warning(self, "GEOM structure options", str(exc))
            return

        self.create_button.setEnabled(False)
        self.create_button.setText("Creating...")

        self.worker = GenerationWorker(command_args, self.output_root, self)
        self.worker.generated.connect(self._structure_ready)
        self.worker.failed.connect(self._structure_failed)
        self.worker.start()

    def _build_command_args(self) -> list[str]:
        structure = self.structure_combo.currentText()
        definition = STRUCTURES[structure]
        atomtype = self.metal_combo.currentText()
        values = {field[0]: self.param_spins[index].value() for index, field in enumerate(definition["fields"])}
        args = ["-create", definition["flag"], atomtype]

        if structure == "Sphere":
            args.append(self._fmt(values["radius"]))
        elif structure == "Rod":
            args.extend([self.axis_combo.currentText(), self._fmt(values["length"]), self._fmt(values["width"])])
        elif structure == "Tip":
            args.extend([self._fmt(values["z_max"]), self._fmt(values["a"]), self._fmt(values["b"])])
        elif structure == "Pyramid":
            args.extend([self._fmt(values["z_max"]), self._fmt(values["side"])])
        elif structure == "Pentagonal Pyramid":
            args.extend([self._fmt(values["base"]), self._fmt(values["z_max"])])
        elif structure == "Cone":
            args.extend([self._fmt(values["z_max"]), self._fmt(values["radius"])])
        elif structure in {"Icosahedron", "Cuboctahedron", "Decahedron"}:
            args.append(self._fmt(values["radius"]))
        elif structure == "Bipyramid":
            args.extend([self._fmt(values["width"]), self._fmt(values["length"])])
        else:
            raise ValueError(f'Structure "{structure}" is not supported.')

        if self.alloy_check.isChecked():
            if atomtype not in {"Ag", "Au"}:
                raise ValueError("Alloy generation is only available for Ag and Au.")
            args.extend(["-alloy", self.alloy_atom.currentText(), "-percentual", self._fmt(self.alloy_percent.value())])

        if self.dimer_check.isChecked() and self.bowtie_check.isChecked():
            raise ValueError("Dimer and bowtie are alternative assembly modes. Select only one.")

        if self.dimer_check.isChecked():
            args.extend(["-dimer", self._fmt(self.dimer_distance.value()), self.dimer_axis.currentText()])

        if self.bowtie_check.isChecked():
            if not definition.get("bowtie"):
                raise ValueError(f"Bowtie is not available for {structure}.")
            args.extend(["-bowtie", self._fmt(self.bowtie_distance.value())])

        return args

    def _fmt(self, value: float) -> str:
        return f"{value:.6g}"

    def _structure_ready(self, result: StructureResult):
        self.current_result = result
        self.canvas.set_atoms(result.atoms)
        self.meta_label.setText(f"{result.atom_count:,} atoms")
        self.create_button.setEnabled(True)
        self.create_button.setText("Create structure")
        self.worker = None

    def _structure_failed(self, details: str):
        self.create_button.setEnabled(True)
        self.create_button.setText("Create structure")
        self.worker = None
        QMessageBox.critical(self, "GEOM structure generation failed", details)


def main() -> int:
    if missing_dependency is not None:
        print(
            "GEOM GUI requires PySide6. Install the UI extra with:\n\n"
            "  python -m pip install 'geom[ui]'\n",
            file=sys.stderr,
        )
        print(f"Missing dependency: {missing_dependency}", file=sys.stderr)
        return 1

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    window = StructureWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
