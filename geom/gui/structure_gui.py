"""Native Qt GUI for creating and visualizing GEOM XYZ structures."""

from __future__ import annotations

import math
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path

try:
    from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QThread, Signal
    from PySide6.QtGui import (
        QColor,
        QFont,
        QFontDatabase,
        QGuiApplication,
        QLinearGradient,
        QPainter,
        QPen,
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
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSizePolicy,
        QSpinBox,
        QTabWidget,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - exercised by users without GUI deps.
    missing_dependency = exc
    QPoint = QPointF = QRectF = Qt = QGuiApplication = QApplication = QFileDialog = QMessageBox = None
    QColor = lambda *args, **kwargs: None
    QLinearGradient = QPainter = QPen = QRadialGradient = None

    class QFont:
        DemiBold = 63

    QFontDatabase = None
    QCheckBox = QComboBox = QDoubleSpinBox = QFrame = QGridLayout = QHBoxLayout = QLabel = QLineEdit = None
    QPushButton = QSizePolicy = QSpinBox = QTabWidget = QToolButton = QVBoxLayout = None
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
    cleanup_gui_tmp,
    convert_molecule_to_xyz,
    generate_structure,
    read_xyz,
    smiles_to_xyz,
    supported_atomistic_metals,
    supported_fcc_metals,
)


APP_TITLE = "GEOM Structure Studio"
SUPPORTED_VIEWER_SUFFIXES = {".xyz", ".pdb", ".smi"}

CHATGPT_GREEN = "#10A37F"
TEXT = "#202123"
MUTED = "#6E6E80"
SURFACE = "#FFFFFF"
CANVAS = "#F7F7F8"
BORDER = "#D9D9E3"
SIDEBAR = "#ECECF1"
SOFT_BORDER = "#ECECF1"
PANEL = "#FFFFFF"
ACCENT_VIOLET = "#4F00B5"
ACCENT_INDIGO = "#0600A0"
ACCENT_SOFT = "#F4F0FF"

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
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.atoms: tuple[AtomRecord, ...] = ()
        self.rotation_x = math.radians(18.0)
        self.rotation_y = math.radians(-28.0)
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.vdw_scale = 1.0
        self.render_resolution = 1
        self.translate_mode = False
        self._last_pos: QPoint | None = None
        self.setMinimumSize(560, 420)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.StrongFocus)

    def set_atoms(self, atoms: tuple[AtomRecord, ...]):
        self.atoms = atoms
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.update()

    def set_vdw_scale(self, value: float):
        self.vdw_scale = value
        self.update()

    def set_render_resolution(self, value: int):
        self.render_resolution = max(1, value)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setFocus()
            self._last_pos = event.position().toPoint()

    def mouseMoveEvent(self, event):
        if self._last_pos is None:
            return
        current = event.position().toPoint()
        delta = current - self._last_pos
        self._last_pos = current
        modifiers = event.modifiers()
        should_translate = self.translate_mode or bool(modifiers & Qt.ShiftModifier)
        should_rotate = bool(modifiers & Qt.ControlModifier) or not should_translate
        if should_translate and not bool(modifiers & Qt.ControlModifier):
            self.pan_x += delta.x()
            self.pan_y += delta.y()
        elif should_rotate:
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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_T:
            self.translate_mode = not self.translate_mode
            self.update()
            event.accept()
            return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        if self._structure_paths_from_event(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        paths = self._structure_paths_from_event(event)
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _structure_paths_from_event(self, event) -> list[Path]:
        paths = []
        if not event.mimeData().hasUrls():
            return paths
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = Path(url.toLocalFile())
                if path.suffix.lower() in SUPPORTED_VIEWER_SUFFIXES:
                    paths.append(path)
        return paths

    def paintEvent(self, event):
        painter = QPainter(self)
        fine_render = self.render_resolution > 1
        painter.setRenderHint(QPainter.Antialiasing, fine_render)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, fine_render)
        self._paint_background(painter)

        if not self.atoms:
            self._paint_empty_state(painter)
            return

        projected = self._project_atoms()
        for atom in projected:
            self._paint_atom(painter, atom)
        self._paint_axes(painter)

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
        rotated: list[tuple[AtomRecord, float, float, float]] = []
        max_span = 1.0
        for atom in self.atoms:
            x, y, z = atom.x - cx, atom.y - cy, atom.z - cz
            xz, yz, zz2 = self._rotate_point(x, y, z)
            rotated.append((atom, xz, yz, zz2))
            max_span = max(max_span, abs(xz), abs(yz))

        scale = min(self.width(), self.height()) * 0.42 * self.zoom / max_span
        center_x = self.width() * 0.52 + self.pan_x
        center_y = self.height() * 0.50 + self.pan_y

        atoms = []
        for atom, x, y, z in rotated:
            element = atom.element.capitalize()
            radius = VDW_RADII.get(element, VDW_RADII["X"]) * scale * 0.68 * self.vdw_scale
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
        if self.render_resolution > 1:
            highlight = QColor(255, 255, 255, 230)
            gradient.setColorAt(0.0, highlight)
            gradient.setColorAt(0.18, shaded.lighter(132))
            gradient.setColorAt(0.76, shaded)
            gradient.setColorAt(1.0, shaded.darker(165))
            painter.setPen(QColor(0, 0, 0, 22))
        else:
            gradient.setColorAt(0.0, shaded.lighter(125))
            gradient.setColorAt(0.70, shaded)
            gradient.setColorAt(1.0, shaded.darker(150))
            painter.setPen(Qt.NoPen)
        painter.setBrush(gradient)
        painter.drawEllipse(rect)

    def _rotate_point(self, x: float, y: float, z: float) -> tuple[float, float, float]:
        cos_x, sin_x = math.cos(self.rotation_x), math.sin(self.rotation_x)
        cos_y, sin_y = math.cos(self.rotation_y), math.sin(self.rotation_y)
        xz = x * cos_y + z * sin_y
        zz = -x * sin_y + z * cos_y
        yz = y * cos_x - zz * sin_x
        zz2 = y * sin_x + zz * cos_x
        return xz, yz, zz2

    def _paint_axes(self, painter: QPainter):
        origin = QPointF(54.0, max(78.0, self.height() - 58.0))
        axis_length = 46.0
        axes = [
            ("X", QColor("#E25555"), self._rotate_point(1.0, 0.0, 0.0)),
            ("Y", QColor("#1F9D68"), self._rotate_point(0.0, 1.0, 0.0)),
            ("Z", QColor("#3A72E8"), self._rotate_point(0.0, 0.0, 1.0)),
        ]
        axes.sort(key=lambda item: item[2][2])

        font = QFontDatabase.systemFont(QFontDatabase.GeneralFont)
        font.setPointSize(11)
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)

        for label, color, (x, y, z) in axes:
            end = QPointF(origin.x() + x * axis_length, origin.y() - y * axis_length)
            label_pos = QPointF(origin.x() + x * (axis_length + 14.0), origin.y() - y * (axis_length + 14.0))
            direction = QPointF(end.x() - origin.x(), end.y() - origin.y())
            length = math.hypot(direction.x(), direction.y()) or 1.0
            unit = QPointF(direction.x() / length, direction.y() / length)
            normal = QPointF(-unit.y(), unit.x())
            arrow_back = 12.0
            arrow_half_width = 6.5
            left = QPointF(
                end.x() - unit.x() * arrow_back + normal.x() * arrow_half_width,
                end.y() - unit.y() * arrow_back + normal.y() * arrow_half_width,
            )
            right = QPointF(
                end.x() - unit.x() * arrow_back - normal.x() * arrow_half_width,
                end.y() - unit.y() * arrow_back - normal.y() * arrow_half_width,
            )
            alpha = 125 if z < -0.25 else 225
            pen = QPen(QColor(color.red(), color.green(), color.blue(), alpha), 5.0)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(origin, end)
            painter.setBrush(QColor(color.red(), color.green(), color.blue(), alpha))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon([end, left, right])
            painter.setPen(QColor("#202123"))
            painter.drawText(QRectF(label_pos.x() - 9.0, label_pos.y() - 9.0, 18.0, 18.0), Qt.AlignCenter, label)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#202123"))
        painter.drawEllipse(origin, 3.5, 3.5)


class ViewerStepper(QWidget):
    valueChanged = Signal(int)

    def __init__(self, value: int, minimum: int, maximum: int, suffix: str, parent=None):
        super().__init__(parent)
        self.setObjectName("viewerStepper")
        self.spin = QSpinBox()
        self.spin.setObjectName("viewerSpin")
        self.spin.setButtonSymbols(QSpinBox.NoButtons)
        self.spin.setRange(minimum, maximum)
        self.spin.setSingleStep(1)
        self.spin.setValue(value)
        self.spin.setSuffix(f" {suffix}")
        self.spin.setAlignment(Qt.AlignCenter)
        self.spin.valueChanged.connect(self.valueChanged)

        self.up_button = QToolButton()
        self.up_button.setObjectName("stepperButton")
        self.up_button.setText("▲")
        self.up_button.clicked.connect(self.spin.stepUp)

        self.down_button = QToolButton()
        self.down_button.setObjectName("stepperButton")
        self.down_button.setText("▼")
        self.down_button.clicked.connect(self.spin.stepDown)

        arrows = QVBoxLayout()
        arrows.setContentsMargins(0, 3, 5, 3)
        arrows.setSpacing(0)
        arrows.addWidget(self.up_button)
        arrows.addWidget(self.down_button)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.spin, 1)
        layout.addLayout(arrows)

    def setValue(self, value: int):
        self.spin.setValue(value)

    def value(self) -> int:
        return self.spin.value()


class StructureWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker: GenerationWorker | None = None
        self.current_result: StructureResult | None = None
        self.output_root: Path | None = None
        self.empty_canvas: VdwCanvas | None = None
        self.vdw_scale = 1.0
        self.render_resolution = 1
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
        sidebar.setFixedWidth(390)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(32, 34, 32, 24)
        side.setSpacing(20)

        title = QLabel("GEOM")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignHCenter)
        accent_bar = QFrame()
        accent_bar.setObjectName("accentBar")
        accent_bar.setFixedHeight(4)

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
            spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
            spin.setDecimals(3)
            spin.setSingleStep(1.0)
            spin.setSuffix(" Å")
            self.param_labels.append(label)
            self.param_spins.append(spin)

        controls = QFrame()
        controls.setObjectName("controls")
        form = QGridLayout(controls)
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(18)
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
        option_layout.setContentsMargins(0, 0, 0, 0)
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
        self.load_button = QPushButton("Choose file")
        self.load_button.setObjectName("loadButton")
        self.load_button.clicked.connect(self.load_files_from_dialog)
        self.file_hint = QLabel("XYZ, PDB, SMI")
        self.file_hint.setObjectName("helperText")
        self.file_hint.setAlignment(Qt.AlignHCenter)
        self.smiles_input = QLineEdit()
        self.smiles_input.setObjectName("smilesInput")
        self.smiles_input.setPlaceholderText("e.g. CCO")
        self.smiles_input.textChanged.connect(self._refresh_smiles_button_state)
        self.smiles_input.returnPressed.connect(self.load_smiles_from_input)
        self.smiles_button = QPushButton("Load SMILES")
        self.smiles_button.setObjectName("smilesButton")
        self.smiles_button.clicked.connect(self.load_smiles_from_input)

        self.vdw_scale_input = self._make_viewer_spin(100, 60, 180, "%")
        self.vdw_scale_input.valueChanged.connect(self._set_vdw_scale_from_input)

        self.resolution_input = self._make_viewer_spin(1, 1, 4, "x")
        self.resolution_input.valueChanged.connect(self._set_render_resolution_from_input)

        generator_page = QWidget()
        generator_layout = QVBoxLayout(generator_page)
        generator_layout.setContentsMargins(0, 24, 0, 0)
        generator_layout.setSpacing(18)
        generator_layout.addWidget(controls)
        generator_layout.addSpacing(6)
        generator_layout.addWidget(options)
        generator_layout.addStretch(1)
        generator_layout.addWidget(self.create_button)

        viewer_page = QWidget()
        viewer_layout = QVBoxLayout(viewer_page)
        viewer_layout.setContentsMargins(0, 24, 0, 0)
        viewer_layout.setSpacing(14)
        viewer_layout.addWidget(self.load_button)
        viewer_layout.addWidget(self.file_hint)
        viewer_layout.addSpacing(8)
        viewer_layout.addWidget(self._section_label("Load from SMILES"))
        viewer_layout.addWidget(self.smiles_input)
        viewer_layout.addWidget(self.smiles_button)
        viewer_layout.addSpacing(12)

        vdw_row = QHBoxLayout()
        vdw_label = self._field_label("VdW radius")
        vdw_row.addWidget(vdw_label)
        vdw_row.addStretch(1)
        vdw_row.addWidget(self.vdw_scale_input)
        viewer_layout.addLayout(vdw_row)

        resolution_row = QHBoxLayout()
        resolution_row.addWidget(self._field_label("Resolution"))
        resolution_row.addStretch(1)
        resolution_row.addWidget(self.resolution_input)
        viewer_layout.addLayout(resolution_row)
        viewer_layout.addStretch(1)

        self.side_tabs = QTabWidget()
        self.side_tabs.setObjectName("sideTabs")
        self.side_tabs.addTab(viewer_page, "Viewer")
        self.side_tabs.addTab(generator_page, "Generator")

        side.addWidget(title)
        side.addWidget(accent_bar)
        side.addWidget(self.side_tabs, 1)

        main = QFrame()
        main.setObjectName("main")
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(28, 22, 24, 24)
        main_layout.setSpacing(8)

        header = QHBoxLayout()
        self.meta_label = QLabel("")
        self.meta_label.setObjectName("meta")
        header.addStretch(1)
        header.addWidget(self.meta_label)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("viewerTabs")
        self.tabs.currentChanged.connect(self._sync_current_tab_meta)
        self.canvas = self._make_canvas()
        self.empty_canvas = self.canvas
        self.tabs.addTab(self.canvas, "Visualizer")
        main_layout.addLayout(header)
        main_layout.addWidget(self.tabs)

        layout.addWidget(sidebar)
        layout.addWidget(main, 1)
        self._apply_styles()
        self._refresh_structure_controls()
        self._refresh_smiles_button_state()

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionLabel")
        return label

    def _make_canvas(self) -> VdwCanvas:
        canvas = VdwCanvas()
        canvas.setObjectName("canvas")
        canvas.set_vdw_scale(self.vdw_scale)
        canvas.set_render_resolution(self.render_resolution)
        canvas.files_dropped.connect(self.load_files)
        return canvas

    def _make_viewer_spin(self, value: int, minimum: int, maximum: int, suffix: str) -> ViewerStepper:
        return ViewerStepper(value, minimum, maximum, suffix)

    def _make_option_spin(self, value: float, minimum: float, maximum: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
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

    def _set_vdw_scale_from_input(self, value: int):
        self.vdw_scale = value / 100.0
        for canvas in self._all_canvases():
            canvas.set_vdw_scale(self.vdw_scale)

    def _set_render_resolution_from_input(self, value: int):
        self.render_resolution = value
        for canvas in self._all_canvases():
            canvas.set_render_resolution(self.render_resolution)

    def _refresh_smiles_button_state(self):
        has_smiles = bool(self.smiles_input.text().strip())
        self.smiles_button.setProperty("active", has_smiles)
        self.smiles_button.style().unpolish(self.smiles_button)
        self.smiles_button.style().polish(self.smiles_button)

    def _all_canvases(self) -> list[VdwCanvas]:
        return [
            self.tabs.widget(index)
            for index in range(self.tabs.count())
            if isinstance(self.tabs.widget(index), VdwCanvas)
        ]

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QWidget#root {{
                background: {SURFACE};
                color: {TEXT};
            }}
            QFrame#sidebar {{
                background: #FCFCFE;
                border-right: 1px solid #F1F1F4;
            }}
            QFrame#main {{
                background: {SURFACE};
            }}
            QFrame#accentBar {{
                border: 0;
                border-radius: 2px;
                margin-left: 112px;
                margin-right: 112px;
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {ACCENT_VIOLET},
                    stop: 1 {ACCENT_INDIGO}
                );
            }}
            QFrame#controls {{
                background: transparent;
                border: 0;
                border-radius: 0;
            }}
            QLabel#appTitle {{
                color: {TEXT};
                font-size: 42px;
                font-weight: 760;
                letter-spacing: 0;
            }}
            QLabel#subtitle, QLabel#fieldLabel {{
                color: #7C7C88;
                font-size: 13px;
            }}
            QLabel#sectionLabel {{
                color: {TEXT};
                font-size: 13px;
                font-weight: 700;
                margin-top: 4px;
            }}
            QLabel#helperText {{
                color: #8A8795;
                font-size: 12px;
                font-weight: 500;
            }}
            QLabel#valueLabel {{
                color: {TEXT};
                font-size: 13px;
                font-weight: 650;
            }}
            QLabel#meta {{
                color: {TEXT};
                font-size: 20px;
                font-weight: 750;
            }}
            QTabWidget#sideTabs::pane {{
                border: 0;
            }}
            QTabWidget#sideTabs QTabBar::tab {{
                background: transparent;
                color: #7C7C88;
                border: 0;
                border-bottom: 2px solid transparent;
                padding: 9px 16px 8px 16px;
                margin-right: 8px;
                font-size: 13px;
                font-weight: 650;
            }}
            QTabWidget#sideTabs QTabBar::tab:selected {{
                color: {TEXT};
                border-bottom: 2px solid {ACCENT_VIOLET};
            }}
            QComboBox, QDoubleSpinBox {{
                background: transparent;
                color: {TEXT};
                border: 0;
                border-bottom: 1px solid #E8E5F1;
                border-radius: 0;
                min-height: 38px;
                padding: 4px 4px;
                font-size: 14px;
            }}
            QComboBox:disabled, QDoubleSpinBox:disabled {{
                background: transparent;
                color: #A8A8B3;
                border-bottom: 1px solid #F0F0F3;
            }}
            QComboBox:focus, QDoubleSpinBox:focus {{
                border-bottom: 2px solid {ACCENT_VIOLET};
                background: transparent;
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
                border: 1px solid #E0DCEA;
                border-radius: 9px;
                background: {SURFACE};
            }}
            QCheckBox::indicator:checked {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {ACCENT_VIOLET},
                    stop: 1 {ACCENT_INDIGO}
                );
                border-color: {ACCENT_VIOLET};
            }}
            QCheckBox::indicator:disabled {{
                background: #F4F4F5;
            }}
            QPushButton {{
                background: {SURFACE};
                color: {TEXT};
                border: 1px solid #ECEAF3;
                border-radius: 24px;
                min-height: 48px;
                padding: 6px 12px;
                font-weight: 600;
                font-size: 15px;
            }}
            QPushButton:hover {{
                border-color: {ACCENT_VIOLET};
            }}
            QPushButton#primaryButton {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {ACCENT_VIOLET},
                    stop: 1 {ACCENT_INDIGO}
                );
                color: white;
                border-color: {ACCENT_VIOLET};
                border-radius: 24px;
            }}
            QPushButton#primaryButton:disabled {{
                background: #D9D2EA;
                border-color: #D9D2EA;
            }}
            QPushButton#secondaryButton {{
                background: transparent;
                color: {ACCENT_VIOLET};
                border: 0;
                min-height: 36px;
                font-weight: 650;
                text-align: center;
            }}
            QPushButton#secondaryButton:hover {{
                color: {ACCENT_INDIGO};
            }}
            QPushButton#loadButton {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {ACCENT_VIOLET},
                    stop: 1 {ACCENT_INDIGO}
                );
                color: #FFFFFF;
                border: 1px solid {ACCENT_VIOLET};
                border-radius: 20px;
                min-height: 44px;
                padding: 4px 16px;
                font-weight: 750;
            }}
            QPushButton#loadButton:hover {{
                border-color: {ACCENT_INDIGO};
            }}
            QLineEdit#smilesInput {{
                background: #FFFFFF;
                color: {TEXT};
                border: 1px solid #E8E4F2;
                border-radius: 16px;
                min-height: 40px;
                padding: 0 13px;
                font-size: 14px;
                selection-background-color: {ACCENT_SOFT};
            }}
            QLineEdit#smilesInput:focus {{
                border-color: {ACCENT_VIOLET};
            }}
            QPushButton#smilesButton {{
                background: #FFFFFF;
                color: {ACCENT_VIOLET};
                border: 1px solid #DED8EF;
                border-radius: 16px;
                min-height: 40px;
                padding: 0 14px;
                font-weight: 700;
                font-size: 13px;
            }}
            QPushButton#smilesButton:hover {{
                border-color: {ACCENT_VIOLET};
                background: #FAF8FF;
            }}
            QPushButton#smilesButton[active="true"] {{
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {ACCENT_VIOLET},
                    stop: 1 {ACCENT_INDIGO}
                );
                color: #FFFFFF;
                border-color: {ACCENT_VIOLET};
            }}
            QPushButton#smilesButton[active="true"]:hover {{
                border-color: {ACCENT_INDIGO};
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {ACCENT_VIOLET},
                    stop: 1 {ACCENT_INDIGO}
                );
            }}
            QWidget#viewerStepper {{
                background: #FFFFFF;
                border: 1px solid #E8E4F2;
                border-radius: 14px;
                min-width: 88px;
                min-height: 34px;
            }}
            QWidget#viewerStepper:focus-within {{
                border-color: {ACCENT_VIOLET};
            }}
            QSpinBox#viewerSpin {{
                background: transparent;
                color: {TEXT};
                border: 0;
                min-width: 66px;
                min-height: 34px;
                padding: 0 4px 0 12px;
                font-weight: 700;
                selection-background-color: {ACCENT_SOFT};
            }}
            QToolButton#stepperButton {{
                background: transparent;
                color: {ACCENT_VIOLET};
                border: 0;
                min-width: 16px;
                max-width: 16px;
                min-height: 13px;
                max-height: 13px;
                padding: 0;
                font-size: 8px;
                font-weight: 900;
            }}
            QToolButton#stepperButton:hover {{
                color: {ACCENT_INDIGO};
                background: {ACCENT_SOFT};
                border-radius: 5px;
            }}
            QTabWidget#viewerTabs::pane {{
                border: 0;
                top: -1px;
            }}
            QTabWidget#viewerTabs QTabBar::tab {{
                background: transparent;
                color: #7C7C88;
                border: 0;
                border-bottom: 2px solid transparent;
                padding: 8px 12px;
                margin-right: 10px;
                font-size: 13px;
                font-weight: 600;
            }}
            QTabWidget#viewerTabs QTabBar::tab:selected {{
                color: {TEXT};
                border-bottom: 2px solid {ACCENT_VIOLET};
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

    def load_files_from_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Load structure",
            str(Path.cwd()),
            "Structure files (*.xyz *.pdb *.smi)",
        )
        if files:
            self.load_files([Path(file) for file in files])

    def load_files(self, paths: list[Path]):
        for path in paths:
            try:
                xyz_path = convert_molecule_to_xyz(path)
                atoms = read_xyz(xyz_path)
            except Exception as exc:
                QMessageBox.warning(self, "Could not load structure file", f"{path}\n\n{exc}")
                continue
            self._add_structure_tab(path.stem, atoms, xyz_path)

    def load_smiles_from_input(self):
        smiles = self.smiles_input.text().strip()
        try:
            xyz_path = smiles_to_xyz(smiles)
            atoms = read_xyz(xyz_path)
        except Exception as exc:
            QMessageBox.warning(self, "Could not load SMILES", str(exc))
            return

        self._add_structure_tab("SMILES", atoms, xyz_path)
        self.smiles_input.clear()

    def _add_structure_tab(self, title: str, atoms: tuple[AtomRecord, ...], path: Path | None = None):
        if self.empty_canvas is not None and self.tabs.count() == 1 and not self.empty_canvas.atoms:
            self.tabs.removeTab(0)
            self.empty_canvas = None

        canvas = self._make_canvas()
        canvas.set_atoms(atoms)
        canvas.setProperty("atom_count", len(atoms))
        if path is not None:
            canvas.setProperty("path", str(path))

        tab_index = self.tabs.addTab(canvas, self._short_tab_title(title))
        self.tabs.setCurrentIndex(tab_index)
        self.canvas = canvas
        self._sync_current_tab_meta()

    def _short_tab_title(self, title: str) -> str:
        return title if len(title) <= 24 else title[:21] + "..."

    def _sync_current_tab_meta(self):
        widget = self.tabs.currentWidget()
        if not widget:
            self.meta_label.setText("")
            return
        atom_count = widget.property("atom_count")
        self.meta_label.setText(f"{atom_count:,} atoms" if atom_count else "")

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
        self._add_structure_tab(result.xyz_path.stem, result.atoms, result.xyz_path)
        self.create_button.setEnabled(True)
        self.create_button.setText("Create structure")
        self.worker = None

    def _structure_failed(self, details: str):
        self.create_button.setEnabled(True)
        self.create_button.setText("Create structure")
        self.worker = None
        QMessageBox.critical(self, "GEOM structure generation failed", details)

    def closeEvent(self, event):
        cleanup_gui_tmp()
        super().closeEvent(event)


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
    try:
        return app.exec()
    finally:
        cleanup_gui_tmp()


if __name__ == "__main__":
    raise SystemExit(main())
