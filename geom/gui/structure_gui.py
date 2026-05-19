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
    QComboBox = QDoubleSpinBox = QFrame = QGridLayout = QHBoxLayout = QLabel = None
    QPushButton = QSizePolicy = QVBoxLayout = None
    QMainWindow = QWidget = object

    class QThread:
        pass

    def Signal(*args, **kwargs):
        return None
else:
    missing_dependency = None

from geom.gui.structure_generator import AtomRecord, StructureResult, generate_sphere, supported_sphere_metals


APP_TITLE = "GEOM Structure Studio"

CHATGPT_GREEN = "#10A37F"
TEXT = "#202123"
MUTED = "#6E6E80"
SURFACE = "#FFFFFF"
CANVAS = "#F7F7F8"
BORDER = "#D9D9E3"
SIDEBAR = "#ECECF1"

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


@dataclass(frozen=True)
class ProjectedAtom:
    element: str
    x: float
    y: float
    z: float
    radius: float


class SphereWorker(QThread):
    generated = Signal(object)
    failed = Signal(str)

    def __init__(self, atomtype: str, radius: float, output_root: Path, parent=None):
        super().__init__(parent)
        self.atomtype = atomtype
        self.radius = radius
        self.output_root = output_root

    def run(self):
        try:
            self.generated.emit(generate_sphere(self.atomtype, self.radius, self.output_root))
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
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor("#FFFFFF"))
        gradient.setColorAt(1.0, QColor(CANVAS))
        painter.fillRect(self.rect(), gradient)

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
            radius = VDW_RADII.get(element, VDW_RADII["X"]) * scale * 0.52
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
        self.worker: SphereWorker | None = None
        self.current_result: StructureResult | None = None
        self.output_root = Path.cwd()
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
        sidebar.setFixedWidth(340)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(24, 24, 24, 24)
        side.setSpacing(18)

        title = QLabel("GEOM")
        title.setObjectName("appTitle")
        subtitle = QLabel("Structure generation")
        subtitle.setObjectName("subtitle")

        self.structure_combo = QComboBox()
        self.structure_combo.addItem("Sphere")
        self.metal_combo = QComboBox()
        self.metal_combo.addItems(supported_sphere_metals())
        self.metal_combo.setCurrentText("Ag")

        self.radius_spin = QDoubleSpinBox()
        self.radius_spin.setRange(2.0, 300.0)
        self.radius_spin.setDecimals(2)
        self.radius_spin.setSingleStep(1.0)
        self.radius_spin.setValue(20.0)
        self.radius_spin.setSuffix(" Å")

        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(12)
        form.addWidget(self._field_label("Structure"), 0, 0)
        form.addWidget(self.structure_combo, 0, 1)
        form.addWidget(self._field_label("Metal"), 1, 0)
        form.addWidget(self.metal_combo, 1, 1)
        form.addWidget(self._field_label("Radius"), 2, 0)
        form.addWidget(self.radius_spin, 2, 1)

        self.create_button = QPushButton("Create structure")
        self.create_button.setObjectName("primaryButton")
        self.create_button.clicked.connect(self.create_structure)

        self.open_output_button = QPushButton("Choose output folder")
        self.open_output_button.clicked.connect(self.choose_output_folder)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("status")
        self.status_label.setWordWrap(True)

        side.addWidget(title)
        side.addWidget(subtitle)
        side.addSpacing(14)
        side.addLayout(form)
        side.addWidget(self.create_button)
        side.addWidget(self.open_output_button)
        side.addStretch(1)
        side.addWidget(self.status_label)

        main = QFrame()
        main.setObjectName("main")
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(14)

        header = QHBoxLayout()
        self.view_title = QLabel("VdW representation")
        self.view_title.setObjectName("viewTitle")
        self.meta_label = QLabel("No atoms")
        self.meta_label.setObjectName("meta")
        header.addWidget(self.view_title)
        header.addStretch(1)
        header.addWidget(self.meta_label)

        self.canvas = VdwCanvas()
        self.canvas.setObjectName("canvas")
        main_layout.addLayout(header)
        main_layout.addWidget(self.canvas)

        layout.addWidget(sidebar)
        layout.addWidget(main, 1)
        self._apply_styles()

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QWidget#root {{
                background: {CANVAS};
                color: {TEXT};
            }}
            QFrame#sidebar {{
                background: {SIDEBAR};
                border-right: 1px solid {BORDER};
            }}
            QFrame#main {{
                background: {CANVAS};
            }}
            QLabel#appTitle {{
                color: {TEXT};
                font-size: 34px;
                font-weight: 750;
                letter-spacing: 0;
            }}
            QLabel#subtitle, QLabel#fieldLabel, QLabel#meta {{
                color: {MUTED};
                font-size: 13px;
            }}
            QLabel#viewTitle {{
                color: {TEXT};
                font-size: 22px;
                font-weight: 700;
            }}
            QLabel#status {{
                color: {MUTED};
                font-size: 12px;
                line-height: 1.4;
            }}
            QComboBox, QDoubleSpinBox {{
                background: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                min-height: 34px;
                padding: 4px 10px;
            }}
            QPushButton {{
                background: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                min-height: 38px;
                padding: 6px 12px;
                font-weight: 600;
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
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)

    def choose_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose GEOM output folder", str(self.output_root))
        if folder:
            self.output_root = Path(folder)
            self.status_label.setText(f"Output folder: {self.output_root}")

    def create_structure(self):
        atomtype = self.metal_combo.currentText()
        radius = self.radius_spin.value()
        self.create_button.setEnabled(False)
        self.status_label.setText(f"Creating {atomtype} sphere, radius {radius:.2f} Å...")

        self.worker = SphereWorker(atomtype, radius, self.output_root, self)
        self.worker.generated.connect(self._structure_ready)
        self.worker.failed.connect(self._structure_failed)
        self.worker.start()

    def _structure_ready(self, result: StructureResult):
        self.current_result = result
        self.canvas.set_atoms(result.atoms)
        self.meta_label.setText(f"{result.atom_count:,} atoms")
        self.status_label.setText(f"Saved XYZ: {result.xyz_path}")
        self.create_button.setEnabled(True)
        self.worker = None

    def _structure_failed(self, details: str):
        self.create_button.setEnabled(True)
        self.worker = None
        self.status_label.setText("Structure generation failed.")
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
