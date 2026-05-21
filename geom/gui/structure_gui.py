"""Native Qt GUI for creating and visualizing GEOM XYZ structures."""

from __future__ import annotations

import ast
import math
import re
import shutil
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QThread, QTimer, Signal
    from PySide6.QtGui import (
        QColor,
        QFont,
        QFontDatabase,
        QGuiApplication,
        QIcon,
        QImage,
        QKeySequence,
        QLinearGradient,
        QPainter,
        QPen,
        QPixmap,
        QRadialGradient,
        QShortcut,
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
        QListView,
        QMainWindow,
        QMenu,
        QMessageBox,
        QPushButton,
        QSizePolicy,
        QSpinBox,
        QTabBar,
        QTabWidget,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtOpenGL import QOpenGLFunctions_1_1
    from PySide6.QtOpenGLWidgets import QOpenGLWidget
except ModuleNotFoundError as exc:  # pragma: no cover - exercised by users without GUI deps.
    missing_dependency = exc
    QPoint = QPointF = QRectF = Qt = QGuiApplication = QApplication = QFileDialog = QMessageBox = None
    QColor = lambda *args, **kwargs: None
    QIcon = QImage = QKeySequence = QLinearGradient = QPainter = QPen = QPixmap = QRadialGradient = QShortcut = None

    class QFont:
        DemiBold = 63

    QFontDatabase = None
    QCheckBox = QComboBox = QDoubleSpinBox = QFrame = QGridLayout = QHBoxLayout = QLabel = QLineEdit = None
    QPushButton = QSizePolicy = QMenu = QSpinBox = QTabBar = QTabWidget = QToolButton = QVBoxLayout = None
    QListView = None
    QMainWindow = QWidget = QOpenGLWidget = object
    QOpenGLFunctions_1_1 = None

    class QThread:
        pass

    class QTimer:
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
    GUI_TMP_ROOT,
    manipulate_xyz,
    read_xyz,
    smiles_to_xyz,
    supported_atomistic_metals,
    supported_fcc_metals,
    translate_pair_controlled_distance,
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

GL_COLOR_BUFFER_BIT = 0x00004000
GL_DEPTH_BUFFER_BIT = 0x00000100
GL_TRIANGLE_STRIP = 0x0005
GL_COMPILE = 0x1300
GL_LEQUAL = 0x0203
GL_FRONT_AND_BACK = 0x0408
GL_FRONT = 0x0404
GL_BACK = 0x0405
GL_CULL_FACE = 0x0B44
GL_DEPTH_TEST = 0x0B71
GL_LIGHTING = 0x0B50
GL_LIGHT0 = 0x4000
GL_COLOR_MATERIAL = 0x0B57
GL_NORMALIZE = 0x0BA1
GL_POLYGON_OFFSET_FILL = 0x8037
GL_LINE = 0x1B01
GL_FILL = 0x1B02
GL_MODELVIEW = 0x1700
GL_PROJECTION = 0x1701
GL_AMBIENT = 0x1200
GL_DIFFUSE = 0x1201
GL_POSITION = 0x1203
GL_SPECULAR = 0x1202
GL_SHININESS = 0x1601
GL_AMBIENT_AND_DIFFUSE = 0x1602
GL_SMOOTH = 0x1D01

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
ELEMENT_COLORS = {
    "Au": QColor("#D4AF37"),
    "Ag": QColor("#C8C8C8"),
}
CPK_COLORS = {
    "H": QColor("#FFFFFF"),
    "C": QColor("#8A8A8A"),
    "N": QColor("#3050F8"),
    "O": QColor("#FF0D0D"),
    "F": QColor("#90E050"),
    "P": QColor("#FF8000"),
    "S": QColor("#FFFF30"),
    "Cl": QColor("#1FF01F"),
    "Br": QColor("#A62929"),
    "I": QColor("#940094"),
}
CPK_DEFAULT = QColor("#F2C7CF")
METAL_ELEMENTS = {
    "Li", "Na", "K", "Rb", "Cs", "Fr", "Be", "Mg", "Ca", "Sr", "Ba", "Ra",
    "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Y", "Zr",
    "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "La", "Hf", "Ta", "W",
    "Re", "Os", "Ir", "Pt", "Au", "Hg", "Al", "Ga", "In", "Sn", "Tl", "Pb",
    "Bi",
}
COVALENT_RADII = {
    "H": 0.31, "C": 0.76, "N": 0.71, "O": 0.66, "F": 0.57, "P": 1.07,
    "S": 1.05, "Cl": 1.02, "Br": 1.20, "I": 1.39, "Na": 1.66, "Ag": 1.45,
    "Au": 1.36,
}

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
    "Cone": {
        "flag": "-cone",
        "metals": "bulk",
        "bowtie": True,
        "fields": (("z_max", "Height", 50.0, 2.0, 500.0), ("radius", "Radius", 30.0, 2.0, 300.0)),
    },
    "Microscope": {
        "flag": "-microscope",
        "metals": "bulk",
        "bowtie": True,
        "fields": (
            ("z_max_paraboloid", "Paraboloid height", 40.0, 2.0, 500.0),
            ("a", "a", 0.02, 0.001, 2.0),
            ("b", "b", 0.02, 0.001, 2.0),
            ("z_max_pyramid", "Pyramid height", 26.0, 2.0, 500.0),
            ("side", "Base side", 33.0, 2.0, 500.0),
        ),
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
}

GRAPHENE_VARIANTS = {
    "Disk": {
        "graphene": "disk",
        "fields": (("radius", "Radius", 30.0, 2.0, 300.0),),
    },
    "Triangle": {
        "graphene": "triangle",
        "fields": (("side_length", "Side length", 50.0, 2.0, 500.0),),
    },
    "Ribbon": {
        "graphene": "rib",
        "fields": (("x_length", "X length", 40.0, 2.0, 500.0), ("y_length", "Y length", 20.0, 2.0, 500.0)),
    },
    "Ring": {
        "graphene": "ring",
        "fields": (("radius_out", "Outer radius", 60.0, 3.0, 500.0), ("radius_in", "Inner radius", 30.0, 1.0, 499.0)),
    },
}


@dataclass(frozen=True)
class ProjectedAtom:
    index: int
    element: str
    x: float
    y: float
    z: float
    radius: float
    depth_radius: float
    cpk: bool
    ox: float
    oy: float
    oz: float


@dataclass(frozen=True)
class ProjectedBond:
    first: ProjectedAtom
    second: ProjectedAtom
    z: float
    width: float


def atom_matches_selection(atom: AtomRecord, expression: str) -> bool:
    """Evaluate a VMD-like coordinate selection expression for one atom."""

    expression = expression.strip()
    if not expression or expression.lower() == "all":
        return True
    expression = _normalize_selection_expression(expression)
    tree = ast.parse(expression, mode="eval")
    result = _evaluate_selection_node(tree.body, {"x": atom.x, "y": atom.y, "z": atom.z, "name": atom.element.lower()})
    if not isinstance(result, bool):
        raise ValueError("Use a comparison such as x > 0.")
    return result


def _normalize_selection_expression(expression: str) -> str:
    expression = re.sub(
        r"\bname\s+([A-Za-z][A-Za-z0-9]*)\b",
        lambda match: f"name == '{match.group(1).lower()}'",
        expression,
        flags=re.IGNORECASE,
    )
    replacements = {
        "and": "and",
        "or": "or",
        "x": "x",
        "y": "y",
        "z": "z",
        "name": "name",
    }
    pattern = re.compile(r"\b(and|or|x|y|z|name)\b", re.IGNORECASE)
    return pattern.sub(lambda match: replacements[match.group(1).lower()], expression)


def _evaluate_selection_node(node: ast.AST, values: dict[str, float | str]) -> bool | float | str:
    if isinstance(node, ast.BoolOp):
        results = [_evaluate_selection_node(value, values) for value in node.values]
        if isinstance(node.op, ast.And):
            return all(bool(result) for result in results)
        if isinstance(node.op, ast.Or):
            return any(bool(result) for result in results)
    if isinstance(node, ast.Compare):
        left = _evaluate_selection_node(node.left, values)
        for operator, comparator in zip(node.ops, node.comparators):
            right = _evaluate_selection_node(comparator, values)
            if not _compare_selection_values(left, operator, right):
                return False
            left = right
        return True
    if isinstance(node, ast.Name) and node.id in values:
        return values[node.id]
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, str)):
        return node.value.lower() if isinstance(node.value, str) else float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        value = float(_evaluate_selection_node(node.operand, values))
        return -value if isinstance(node.op, ast.USub) else value
    raise ValueError("Use coordinate conditions such as x > 0 and y < 2.")


def _compare_selection_values(left: bool | float | str, operator: ast.cmpop, right: bool | float | str) -> bool:
    if isinstance(operator, ast.Gt):
        return float(left) > float(right)
    if isinstance(operator, ast.GtE):
        return float(left) >= float(right)
    if isinstance(operator, ast.Lt):
        return float(left) < float(right)
    if isinstance(operator, ast.LtE):
        return float(left) <= float(right)
    if isinstance(operator, ast.Eq):
        return left == right
    if isinstance(operator, ast.NotEq):
        return left != right
    raise ValueError("Use comparisons such as >, >=, <, <=, ==, or !=.")


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


class VdwCanvas(QOpenGLWidget):
    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.atoms: tuple[AtomRecord, ...] = ()
        self.source_atoms: tuple[AtomRecord, ...] = ()
        self.selection_expression = ""
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.vdw_scale = 1.45
        self.bond_width_scale = 1.65
        self.render_resolution = 1
        self.translate_mode = False
        self._is_interacting = False
        self._last_pos: QPoint | None = None
        self._sphere_cache: dict[tuple[str, int, int, bool], QPixmap] = {}
        self._gl = None
        self._sphere_list = 0
        self._sphere_mesh = self._build_sphere_mesh(6, 8)
        self._interaction_timer = QTimer(self)
        self._interaction_timer.setSingleShot(True)
        self._interaction_timer.timeout.connect(self._finish_interaction)
        self.setMinimumSize(560, 420)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.StrongFocus)

    def set_atoms(self, atoms: tuple[AtomRecord, ...]):
        self.source_atoms = atoms
        self.atoms = atoms
        self.reset_view()
        self.update()

    def set_visible_atoms(self, atoms: tuple[AtomRecord, ...]):
        self.atoms = atoms
        self.update()

    def reset_view(self):
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.update()

    def set_vdw_scale(self, value: float):
        self.vdw_scale = value
        self.update()

    def set_bond_width_scale(self, value: float):
        self.bond_width_scale = value
        self.update()

    def set_render_resolution(self, value: int):
        self.render_resolution = max(1, value)
        self.update()

    def _begin_interaction(self):
        self._is_interacting = True
        self._interaction_timer.start(110)

    def _finish_interaction(self):
        if self._is_interacting:
            self._is_interacting = False
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
            self._begin_interaction()
            self.pan_x += delta.x()
            self.pan_y += delta.y()
        elif should_rotate:
            self._begin_interaction()
            self.rotation_y += delta.x() * 0.01
            self.rotation_x += delta.y() * 0.01
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._last_pos = None
            self._interaction_timer.start(80)

    def wheelEvent(self, event):
        delta = event.pixelDelta().y() if not event.pixelDelta().isNull() else event.angleDelta().y()
        if abs(delta) < 1:
            event.accept()
            return
        factor = math.exp(delta / 900.0)
        self._begin_interaction()
        self.zoom = min(4.0, max(0.35, self.zoom * factor))
        self.update()
        event.accept()

    def keyPressEvent(self, event):
        if self._is_reset_view_key(event):
            self.reset_view()
            event.accept()
            return
        if event.key() == Qt.Key_T:
            self.translate_mode = not self.translate_mode
            self.update()
            event.accept()
            return
        if event.key() == Qt.Key_R:
            self.translate_mode = False
            self.update()
            event.accept()
            return
        super().keyPressEvent(event)

    def _is_reset_view_key(self, event) -> bool:
        key = event.key()
        text = event.text()
        modifiers = event.modifiers()
        return (
            (key == Qt.Key_0 and bool(modifiers & Qt.ShiftModifier))
            or key == Qt.Key_ParenRight
            or text == ")"
        )

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

    def initializeGL(self):
        self._gl = QOpenGLFunctions_1_1()
        self._gl.initializeOpenGLFunctions()
        self._gl.glClearColor(1.0, 1.0, 1.0, 1.0)
        self._gl.glEnable(GL_DEPTH_TEST)
        self._gl.glDepthFunc(GL_LEQUAL)
        self._gl.glEnable(GL_NORMALIZE)
        self._gl.glShadeModel(GL_SMOOTH)
        self._sphere_list = self._gl.glGenLists(1)
        self._gl.glNewList(self._sphere_list, GL_COMPILE)
        self._draw_unit_sphere_mesh(self._gl)
        self._gl.glEndList()

    def resizeGL(self, width: int, height: int):
        if self._gl is not None:
            dpr = self.devicePixelRatioF()
            self._gl.glViewport(0, 0, max(1, int(width * dpr)), max(1, int(height * dpr)))

    def paintGL(self):
        projected = self._project_atoms() if self.atoms else []
        if self._uses_vdw_opengl(projected):
            self._paint_vdw_opengl(projected)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)
            self._paint_axes(painter)
            return
        if self._uses_mixed_vdw_cpk(projected):
            self._paint_mixed_vdw_cpk(projected)
            return

        painter = QPainter(self)
        fine_render = self.render_resolution > 1 or self._scene_has_cpk()
        painter.setRenderHint(QPainter.Antialiasing, fine_render)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, fine_render)
        self._paint_background(painter)

        if not self.atoms:
            self._paint_axes(painter)
            return

        for bond in self._projected_bonds(projected):
            self._paint_bond(painter, bond)
        for atom in projected:
            self._paint_atom(painter, atom)
        self._paint_axes(painter)

    def _paint_background(self, painter: QPainter):
        painter.fillRect(self.rect(), QColor("#FFFFFF"))

    def _paint_empty_state(self, painter: QPainter):
        return

    def _project_atoms(self) -> list[ProjectedAtom]:
        cx = sum(atom.x for atom in self.atoms) / len(self.atoms)
        cy = sum(atom.y for atom in self.atoms) / len(self.atoms)
        cz = sum(atom.z for atom in self.atoms) / len(self.atoms)
        rotated: list[tuple[AtomRecord, float, float, float]] = []
        model_radius = 1.0
        for atom in self.atoms:
            x, y, z = atom.x - cx, atom.y - cy, atom.z - cz
            model_radius = max(model_radius, math.sqrt(x * x + y * y + z * z))
            xz, yz, zz2 = self._rotate_point(x, y, z)
            rotated.append((atom, xz, yz, zz2))

        scale = min(self.width(), self.height()) * 0.40 * self.zoom / model_radius
        center_x = self.width() * 0.50 + self.pan_x
        center_y = self.height() * 0.50 + self.pan_y

        atoms = []
        for index, (atom, x, y, z) in enumerate(rotated):
            element = atom.element.capitalize()
            cpk_mode = self._atom_uses_cpk(element)
            if cpk_mode:
                depth_radius = COVALENT_RADII.get(element, 0.77) * 0.32 * self.vdw_scale
            else:
                depth_radius = VDW_RADII.get(element, VDW_RADII["X"]) * 0.68 * self.vdw_scale
            radius = depth_radius * scale
            atoms.append(ProjectedAtom(index, element, center_x + x * scale, center_y - y * scale, z, radius, depth_radius, cpk_mode, atom.x, atom.y, atom.z))

        atoms.sort(key=lambda item: item.z)
        return atoms

    def _atom_uses_cpk(self, element: str) -> bool:
        return element not in METAL_ELEMENTS

    def _scene_has_cpk(self) -> bool:
        return any(self._atom_uses_cpk(atom.element.capitalize()) for atom in self.atoms)

    def _uses_vdw_opengl(self, projected: list[ProjectedAtom]) -> bool:
        return bool(projected) and self._gl is not None and not any(atom.cpk for atom in projected)

    def _uses_mixed_vdw_cpk(self, projected: list[ProjectedAtom]) -> bool:
        return bool(projected) and self._gl is not None and any(atom.cpk for atom in projected) and any(not atom.cpk for atom in projected)

    def _paint_mixed_vdw_cpk(self, projected: list[ProjectedAtom]):
        metal_atoms = [atom for atom in projected if not atom.cpk]
        cpk_atoms = [atom for atom in projected if atom.cpk]

        self._paint_vdw_opengl(metal_atoms)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        for bond in self._projected_bonds(projected):
            self._paint_bond(painter, bond)
        for atom in cpk_atoms:
            self._paint_atom(painter, atom)
        self._paint_axes(painter)

    def _paint_vdw_opengl(self, projected: list[ProjectedAtom]):
        gl = self._gl
        if gl is None:
            return

        width = max(1, self.width())
        height = max(1, self.height())
        dpr = self.devicePixelRatioF()
        far = max(1000.0, max(abs(atom.z) * (atom.radius / max(atom.depth_radius, 1.0e-6)) + atom.radius for atom in projected) + 100.0)
        gl.glViewport(0, 0, max(1, int(width * dpr)), max(1, int(height * dpr)))
        gl.glClearColor(1.0, 1.0, 1.0, 1.0)
        gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        gl.glMatrixMode(GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0.0, float(width), float(height), 0.0, -far, far)
        gl.glMatrixMode(GL_MODELVIEW)
        gl.glLoadIdentity()

        gl.glEnable(GL_DEPTH_TEST)
        gl.glDepthFunc(GL_LEQUAL)
        gl.glEnable(GL_LIGHTING)
        gl.glEnable(GL_LIGHT0)
        gl.glEnable(GL_COLOR_MATERIAL)
        gl.glEnable(GL_NORMALIZE)
        gl.glDisable(GL_CULL_FACE)
        gl.glShadeModel(GL_SMOOTH)
        light_x, light_y, light_z = 0.50, -0.62, 0.74
        gl.glLightfv(GL_LIGHT0, GL_POSITION, [light_x, light_y, light_z, 0.0])
        gl.glLightfv(GL_LIGHT0, GL_AMBIENT, [0.32, 0.32, 0.32, 1.0])
        gl.glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.76, 0.76, 0.76, 1.0])
        gl.glLightfv(GL_LIGHT0, GL_SPECULAR, [0.06, 0.06, 0.06, 1.0])
        gl.glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        gl.glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.08, 0.08, 0.08, 1.0])
        gl.glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 14.0)

        for atom in projected:
            base = ELEMENT_COLORS.get(atom.element, DEFAULT_VMD_PINK)
            scale = atom.radius / max(atom.depth_radius, 1.0e-6)
            gl.glPushMatrix()
            gl.glTranslatef(float(atom.x), float(atom.y), float(atom.z * scale))
            gl.glScalef(float(atom.radius), float(atom.radius), float(atom.radius))
            gl.glColor3f(base.redF(), base.greenF(), base.blueF())
            self._draw_unit_sphere(gl)
            gl.glPopMatrix()

        gl.glDisable(GL_LIGHTING)
        gl.glDisable(GL_COLOR_MATERIAL)

    def _build_sphere_mesh(self, stacks: int, slices: int) -> list[list[tuple[float, float, float]]]:
        strips = []
        for stack in range(stacks):
            phi0 = math.pi * stack / stacks
            phi1 = math.pi * (stack + 1) / stacks
            strip = []
            for slice_index in range(slices + 1):
                theta = 2.0 * math.pi * slice_index / slices
                for phi in (phi1, phi0):
                    x = math.sin(phi) * math.cos(theta)
                    y = math.cos(phi)
                    z = math.sin(phi) * math.sin(theta)
                    strip.append((x, y, z))
            strips.append(strip)
        return strips

    def _draw_unit_sphere(self, gl):
        if self._sphere_list:
            gl.glCallList(self._sphere_list)
            return
        self._draw_unit_sphere_mesh(gl)

    def _draw_unit_sphere_mesh(self, gl):
        for strip in self._sphere_mesh:
            gl.glBegin(GL_TRIANGLE_STRIP)
            for x, y, z in strip:
                gl.glNormal3f(float(x), float(y), float(z))
                gl.glVertex3f(float(x), float(y), float(z))
            gl.glEnd()

    def _uses_vdw_impostors(self, projected: list[ProjectedAtom]) -> bool:
        return bool(projected) and not any(atom.cpk for atom in projected)

    def _uses_vdw_surface_buffer(self, projected: list[ProjectedAtom]) -> bool:
        return bool(projected) and not any(atom.cpk for atom in projected)

    def _paint_vdw_surface_buffer(self, painter: QPainter, projected: list[ProjectedAtom]):
        width = self.width()
        height = self.height()
        render_scale = self._vdw_surface_render_scale(width, height, len(projected))
        render_width = max(1, int(width * render_scale))
        render_height = max(1, int(height * render_scale))
        rgba = np.zeros((render_height, render_width, 4), dtype=np.uint8)
        zbuffer = np.full((render_height, render_width), -np.inf, dtype=np.float32)

        z_min = min(atom.z - atom.depth_radius for atom in projected)
        z_max = max(atom.z + atom.depth_radius for atom in projected)
        z_span = max(1.0e-6, z_max - z_min)
        light_x, light_y, light_z = self._view_light_vector()
        light_len = math.sqrt(light_x * light_x + light_y * light_y + light_z * light_z)
        light_x, light_y, light_z = light_x / light_len, light_y / light_len, light_z / light_len

        for atom in projected:
            base = ELEMENT_COLORS.get(atom.element, DEFAULT_VMD_PINK)
            base_rgb = np.array([base.red(), base.green(), base.blue()], dtype=np.float32)
            center_x = atom.x * render_scale
            center_y = atom.y * render_scale
            radius = max(1.0, atom.radius * render_scale)
            x_min = max(0, int(center_x - radius - 1))
            x_max = min(render_width - 1, int(center_x + radius + 1))
            y_min = max(0, int(center_y - radius - 1))
            y_max = min(render_height - 1, int(center_y + radius + 1))
            if x_min > x_max or y_min > y_max:
                continue

            yy, xx = np.ogrid[y_min:y_max + 1, x_min:x_max + 1]
            dx = (xx + 0.5 - center_x) / radius
            dy = (yy + 0.5 - center_y) / radius
            dist_sq = dx * dx + dy * dy
            inside = dist_sq <= 1.0
            if not np.any(inside):
                continue

            nz = np.sqrt(np.maximum(0.0, 1.0 - dist_sq))
            surface_z = atom.z + nz * atom.depth_radius
            current_z = zbuffer[y_min:y_max + 1, x_min:x_max + 1]
            visible = inside & (surface_z > current_z)
            if not np.any(visible):
                continue

            normal_y = -dy
            ndotl = np.maximum(0.0, dx * light_x + normal_y * light_y + nz * light_z)
            depth = (surface_z - z_min) / z_span
            shade = 0.60 + 0.30 * ndotl + 0.10 * depth
            edge = np.clip((1.0 - np.sqrt(np.maximum(0.0, dist_sq))) / 0.12, 0.0, 1.0)
            shade *= 0.86 + 0.14 * edge
            spec = np.power(ndotl, 26) * 46.0
            color = np.clip(base_rgb * shade[..., None] + spec[..., None], 0, 255).astype(np.uint8)

            tile = rgba[y_min:y_max + 1, x_min:x_max + 1]
            tile[visible, :3] = color[visible]
            tile[visible, 3] = 255
            current_z[visible] = surface_z[visible]

        image = QImage(rgba.data, render_width, render_height, render_width * 4, QImage.Format_RGBA8888).copy()
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.drawImage(QRectF(0.0, 0.0, width, height), image)

    def _vdw_surface_render_scale(self, width: int, height: int, atom_count: int) -> float:
        max_dimension = max(width, height, 1)
        target_dimension = 900
        if atom_count > 1500:
            target_dimension = min(target_dimension, 380)
        elif atom_count > 700:
            target_dimension = min(target_dimension, 520)
        elif atom_count > 250:
            target_dimension = min(target_dimension, 700)
        if self.render_resolution > 1:
            target_dimension = min(1300, target_dimension + 180)
        return min(1.0, target_dimension / max_dimension)

    def _paint_vdw_impostors(self, painter: QPainter, projected: list[ProjectedAtom]):
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        atoms = sorted(projected, key=lambda atom: (round(atom.z, 2), atom.y, atom.x))
        for atom in atoms:
            pixmap = self._sphere_pixmap(atom)
            size = atom.radius * 2.0 + 2.0
            painter.drawPixmap(
                QRectF(atom.x - size / 2.0, atom.y - size / 2.0, size, size),
                pixmap,
                QRectF(0.0, 0.0, pixmap.width(), pixmap.height()),
            )

    def _sphere_pixmap(self, atom: ProjectedAtom) -> QPixmap:
        diameter = max(4, int(atom.radius * 2))
        light_x, light_y, light_z = self._view_light_vector()
        quadrant = 0 if light_x < 0 and light_y >= 0 else 1 if light_x >= 0 and light_y >= 0 else 2 if light_x >= 0 else 3
        cache_key = (atom.element, diameter, quadrant, self.render_resolution > 1, self._is_interacting)
        cached = self._sphere_cache.get(cache_key)
        if cached is not None:
            return cached

        supersample = 2 if self._is_interacting else 3
        size = (diameter + 2) * supersample
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        base = ELEMENT_COLORS.get(atom.element, DEFAULT_VMD_PINK)
        rect = QRectF(float(supersample), float(supersample), diameter * supersample, diameter * supersample)
        scaled_radius = atom.radius * supersample
        offset_x = -0.34 if light_x < 0 else 0.34
        offset_y = -0.38 if light_y >= 0 else 0.38
        gradient = QRadialGradient(
            rect.center() + QPointF(offset_x * scaled_radius, offset_y * scaled_radius),
            scaled_radius * 1.12,
        )
        gradient.setColorAt(0.0, QColor(255, 255, 255, 190))
        gradient.setColorAt(0.22, base.lighter(114))
        gradient.setColorAt(0.78, base)
        gradient.setColorAt(1.0, base.darker(112))
        painter.setPen(QPen(base.darker(125), max(1.0, supersample * 0.45)))
        painter.setBrush(gradient)
        painter.drawEllipse(rect)
        painter.end()

        if len(self._sphere_cache) > 256:
            self._sphere_cache.clear()
        scaled = pixmap.scaled(diameter + 2, diameter + 2, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._sphere_cache[cache_key] = scaled
        return scaled

    def _paint_vdw_depth_buffer(self, painter: QPainter, projected: list[ProjectedAtom]):
        width = self.width()
        height = self.height()
        render_scale = self._vdw_depth_render_scale(width, height, len(projected))
        render_width = max(1, int(width * render_scale))
        render_height = max(1, int(height * render_scale))
        image = QImage(render_width, render_height, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        zbuffer = [-float("inf")] * (render_width * render_height)
        z_min = min(atom.z - atom.depth_radius for atom in projected)
        z_max = max(atom.z + atom.depth_radius for atom in projected)
        z_span = max(1.0e-6, z_max - z_min)
        light_x, light_y, light_z = self._view_light_vector()
        light_len = math.sqrt(light_x * light_x + light_y * light_y + light_z * light_z)
        light_x, light_y, light_z = light_x / light_len, light_y / light_len, light_z / light_len

        for atom in projected:
            base = ELEMENT_COLORS.get(atom.element, DEFAULT_VMD_PINK)
            center_x = atom.x * render_scale
            center_y = atom.y * render_scale
            radius = max(1.0, atom.radius * render_scale)
            x_min = max(0, int(center_x - radius - 1))
            x_max = min(render_width - 1, int(center_x + radius + 1))
            y_min = max(0, int(center_y - radius - 1))
            y_max = min(render_height - 1, int(center_y + radius + 1))

            for py in range(y_min, y_max + 1):
                dy = (py + 0.5 - center_y) / radius
                dy_sq = dy * dy
                row = py * render_width
                for px in range(x_min, x_max + 1):
                    dx = (px + 0.5 - center_x) / radius
                    dist_sq = dx * dx + dy_sq
                    if dist_sq > 1.0:
                        continue
                    nz = math.sqrt(max(0.0, 1.0 - dist_sq))
                    surface_z = atom.z + nz * atom.depth_radius
                    index = row + px
                    if surface_z <= zbuffer[index]:
                        continue

                    zbuffer[index] = surface_z
                    normal_y = -dy
                    ndotl = max(0.0, dx * light_x + normal_y * light_y + nz * light_z)
                    depth = (surface_z - z_min) / z_span
                    shade = 0.62 + 0.30 * ndotl + 0.08 * depth
                    edge = max(0.0, min(1.0, (1.0 - math.sqrt(dist_sq)) / 0.10))
                    shade *= 0.88 + 0.12 * edge
                    spec = max(0.0, ndotl) ** 24
                    red = min(255, int(base.red() * shade + 255 * spec * 0.20))
                    green = min(255, int(base.green() * shade + 255 * spec * 0.20))
                    blue = min(255, int(base.blue() * shade + 255 * spec * 0.20))
                    if dist_sq > 0.992:
                        red = int(red * 0.55)
                        green = int(green * 0.55)
                        blue = int(blue * 0.55)
                    image.setPixel(px, py, QColor(red, green, blue).rgba())

        painter.drawImage(QRectF(0.0, 0.0, width, height), image)

    def _vdw_depth_render_scale(self, width: int, height: int, atom_count: int) -> float:
        max_dimension = max(width, height, 1)
        target_dimension = 420 if self._is_interacting else 680
        if atom_count > 1200:
            target_dimension = min(target_dimension, 300)
        elif atom_count > 500:
            target_dimension = min(target_dimension, 380)
        elif atom_count > 180:
            target_dimension = min(target_dimension, 480)
        if self.render_resolution > 1 and not self._is_interacting:
            target_dimension = min(900, target_dimension + 180)
        return min(1.0, target_dimension / max_dimension)

    def _view_light_vector(self) -> tuple[float, float, float]:
        # Keep the light in molecular space so highlights move as the structure rotates.
        return self._rotate_point(-0.38, 0.55, 0.74)

    def _projected_bonds(self, projected: list[ProjectedAtom]) -> list[ProjectedBond]:
        bonds = []
        by_index = {atom.index: atom for atom in projected}
        for i, atom_a in enumerate(self.atoms):
            element_a = atom_a.element.capitalize()
            if not self._atom_uses_cpk(element_a):
                continue
            radius_a = COVALENT_RADII.get(element_a, 0.77)
            for j in range(i + 1, len(self.atoms)):
                atom_b = self.atoms[j]
                element_b = atom_b.element.capitalize()
                if not self._atom_uses_cpk(element_b):
                    continue
                radius_b = COVALENT_RADII.get(element_b, 0.77)
                dx = atom_a.x - atom_b.x
                dy = atom_a.y - atom_b.y
                dz = atom_a.z - atom_b.z
                distance = math.sqrt(dx * dx + dy * dy + dz * dz)
                if 0.25 < distance <= (radius_a + radius_b) * 1.22 + 0.18:
                    first = by_index[i]
                    second = by_index[j]
                    width = min(14.0, max(1.15, min(first.radius, second.radius) * 0.22 * self.bond_width_scale))
                    bonds.append(ProjectedBond(first, second, (first.z + second.z) / 2.0, width))
        bonds.sort(key=lambda item: item.z)
        return bonds

    def _paint_bond(self, painter: QPainter, bond: ProjectedBond):
        start = QPointF(bond.first.x, bond.first.y)
        end = QPointF(bond.second.x, bond.second.y)
        middle = QPointF((bond.first.x + bond.second.x) * 0.5, (bond.first.y + bond.second.y) * 0.5)

        outline = QPen(QColor(35, 35, 35, 105), bond.width + 0.75)
        outline.setCapStyle(Qt.RoundCap)
        painter.setPen(outline)
        painter.drawLine(start, end)

        first_color = CPK_COLORS.get(bond.first.element, CPK_DEFAULT)
        second_color = CPK_COLORS.get(bond.second.element, CPK_DEFAULT)
        first_pen = QPen(first_color.darker(108), bond.width)
        first_pen.setCapStyle(Qt.RoundCap)
        second_pen = QPen(second_color.darker(108), bond.width)
        second_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(first_pen)
        painter.drawLine(start, middle)
        painter.setPen(second_pen)
        painter.drawLine(middle, end)

    def _paint_atom(self, painter: QPainter, atom: ProjectedAtom):
        base = CPK_COLORS.get(atom.element, CPK_DEFAULT) if atom.cpk else ELEMENT_COLORS.get(atom.element, DEFAULT_VMD_PINK)
        shaded = QColor(base)

        rect = QRectF(atom.x - atom.radius, atom.y - atom.radius, atom.radius * 2, atom.radius * 2)
        outline_color = QColor(20, 20, 20, 150 if atom.cpk else 190)
        outline = QPen(outline_color, 0.65 if atom.cpk else 0.8)
        if self._use_lit_atom_rendering(atom):
            gradient = QRadialGradient(rect.center() - QPointF(atom.radius * 0.34, atom.radius * 0.38), atom.radius * 1.05)
            gradient.setColorAt(0.0, QColor(255, 255, 255, 128))
            gradient.setColorAt(0.18, shaded.lighter(110))
            gradient.setColorAt(0.72, shaded)
            gradient.setColorAt(1.0, shaded.darker(112))
            painter.setPen(outline)
            painter.setBrush(gradient)
            painter.drawEllipse(rect)
        else:
            painter.setPen(outline)
            painter.setBrush(shaded)
            painter.drawEllipse(rect)
            highlight_size = max(1.6, atom.radius * 0.18)
            highlight = QRectF(
                rect.center().x() - atom.radius * 0.36,
                rect.center().y() - atom.radius * 0.40,
                highlight_size,
                highlight_size,
            )
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 255, 255, 62))
            painter.drawEllipse(highlight)

    def _use_lit_atom_rendering(self, atom: ProjectedAtom) -> bool:
        if self.render_resolution > 1:
            return True
        if atom.cpk:
            return len(self.atoms) <= 1400
        return not self._is_interacting

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
            ("X", QColor("#C7352E"), self._rotate_point(1.0, 0.0, 0.0)),
            ("Y", QColor("#208246"), self._rotate_point(0.0, 1.0, 0.0)),
            ("Z", QColor("#3158A7"), self._rotate_point(0.0, 0.0, 1.0)),
        ]
        axes.sort(key=lambda item: item[2][2])

        font = QFontDatabase.systemFont(QFontDatabase.GeneralFont)
        font.setPointSize(9)
        font.setWeight(QFont.Bold)
        painter.setFont(font)

        for label, color, (x, y, z) in axes:
            end = QPointF(origin.x() + x * axis_length, origin.y() - y * axis_length)
            direction = QPointF(end.x() - origin.x(), end.y() - origin.y())
            length = math.hypot(direction.x(), direction.y())
            if length < 2.0:
                radius = 5.8 if z >= 0 else 4.4
                alpha = 235 if z >= 0 else 120
                painter.setPen(QPen(QColor("#0E0E0E"), 1.2))
                painter.setBrush(QColor(color.red(), color.green(), color.blue(), alpha))
                painter.drawEllipse(origin, radius, radius)
                if z >= 0:
                    painter.setBrush(QColor(255, 255, 255, 120))
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(origin.x() - 1.4, origin.y() - 1.4, 2.4, 2.4)
                painter.setPen(QColor("#111111"))
                painter.drawText(QRectF(origin.x() + 7.0, origin.y() - 15.0, 14.0, 14.0), Qt.AlignCenter, label)
                continue
            unit = QPointF(direction.x() / length, direction.y() / length)
            normal = QPointF(-unit.y(), unit.x())
            label_pos = QPointF(origin.x() + unit.x() * (axis_length + 4.5), origin.y() + unit.y() * (axis_length + 4.5))
            shaft_end = QPointF(end.x() - unit.x() * 7.4, end.y() - unit.y() * 7.4)
            arrow_back = 9.2
            arrow_half_width = 4.5
            left = QPointF(
                end.x() - unit.x() * arrow_back + normal.x() * arrow_half_width,
                end.y() - unit.y() * arrow_back + normal.y() * arrow_half_width,
            )
            right = QPointF(
                end.x() - unit.x() * arrow_back - normal.x() * arrow_half_width,
                end.y() - unit.y() * arrow_back - normal.y() * arrow_half_width,
            )
            alpha = 130 if z < -0.25 else 240
            outline = QPen(QColor("#0D0D0D"), 5.4)
            outline.setCapStyle(Qt.RoundCap)
            painter.setPen(outline)
            painter.drawLine(origin, shaft_end)
            pen = QPen(QColor(color.red(), color.green(), color.blue(), alpha), 3.8)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(origin, shaft_end)
            painter.setBrush(QColor("#0D0D0D"))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon([end, left, right])
            painter.setBrush(QColor(color.red(), color.green(), color.blue(), alpha))
            painter.setPen(QPen(QColor("#0D0D0D"), 1.05))
            painter.drawPolygon([end, left, right])
            painter.setPen(QColor("#111111"))
            painter.drawText(QRectF(label_pos.x() - 6.0, label_pos.y() - 7.0, 12.0, 14.0), Qt.AlignCenter, label)

        painter.setPen(QPen(QColor("#0D0D0D"), 1.0))
        painter.setBrush(QColor("#BFC3C9"))
        painter.drawEllipse(origin, 2.9, 2.9)


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


class ViewerTabBar(QTabBar):
    """Compact tab bar with drag reordering and wheel navigation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setExpanding(False)
        self.setDrawBase(False)
        self.setMovable(True)
        self.setUsesScrollButtons(True)
        self.setElideMode(Qt.ElideRight)
        self.setCursor(Qt.OpenHandCursor)
        self.setToolTip("Drag tabs to reorder. Scroll over tabs to navigate.")
        self.setContentsMargins(0, 0, 0, 0)

    def wheelEvent(self, event):
        if self.count() < 2:
            event.ignore()
            return
        delta = event.angleDelta().x() or event.angleDelta().y()
        if delta == 0:
            event.ignore()
            return
        next_index = self.currentIndex() - 1 if delta > 0 else self.currentIndex() + 1
        self.setCurrentIndex(max(0, min(self.count() - 1, next_index)))
        event.accept()


class StructureWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker: GenerationWorker | None = None
        self.current_result: StructureResult | None = None
        self.output_root: Path | None = None
        self.empty_canvas: VdwCanvas | None = None
        self.pending_generation_meta: dict[str, object] = {}
        self.vdw_scale = 1.45
        self.bond_width_scale = 1.65
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
        side.setSpacing(0)

        logo_header = QWidget()
        logo_header.setObjectName("logoHeader")
        logo_header_layout = QVBoxLayout(logo_header)
        logo_header_layout.setContentsMargins(0, 0, 0, 0)
        logo_header_layout.setSpacing(0)
        title = QLabel("GEOM")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignHCenter)
        title.setFixedHeight(58)
        title_font = QFont("Times New Roman")
        title_font.setPointSize(50)
        title_font.setWeight(QFont.Bold)
        title.setFont(title_font)

        logo_lines = QWidget()
        logo_lines.setObjectName("logoLines")
        logo_lines.setFixedHeight(19)
        logo_lines_layout = QVBoxLayout(logo_lines)
        logo_lines_layout.setContentsMargins(0, 0, 0, 0)
        logo_lines_layout.setSpacing(3)
        for name, width in (("logoLineLong", 126), ("logoLineMid", 66), ("logoLineShort", 38)):
            line = QFrame()
            line.setObjectName(name)
            line.setFixedSize(width, 4)
            logo_lines_layout.addWidget(line, 0, Qt.AlignHCenter)
        logo_header_layout.addWidget(title)
        logo_header_layout.addWidget(logo_lines)

        self.metal_combo = QComboBox()
        self.metal_combo.addItems(self._material_items())
        self.metal_combo.currentTextChanged.connect(self._refresh_material_controls)
        self.metal_label = self._field_label("Material")
        self.structure_combo = QComboBox()
        self.structure_combo.addItems(STRUCTURES.keys())
        self.structure_combo.currentTextChanged.connect(self._refresh_structure_controls)
        self.structure_label = self._field_label("Structure")

        self.axis_label = self._field_label("Axis")
        self.axis_combo = QComboBox()
        self.axis_combo.addItems(("x", "y", "z"))
        self.axis_combo.setCurrentText("z")
        self.graphene_variant_label = self._field_label("Graphene")
        self.graphene_variant_combo = QComboBox()
        self.graphene_variant_combo.addItems(GRAPHENE_VARIANTS.keys())
        self.graphene_variant_combo.currentTextChanged.connect(self._refresh_structure_controls)
        self.graphene_edge_label = self._field_label("Edge")
        self.graphene_edge_combo = QComboBox()
        self.graphene_edge_combo.addItems(("armchair", "zigzag"))

        self.param_labels: list[QLabel] = []
        self.param_spins: list[QDoubleSpinBox] = []
        for _ in range(5):
            label = self._field_label("")
            spin = QDoubleSpinBox()
            spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
            spin.setDecimals(3)
            spin.setSingleStep(1.0)
            spin.setSuffix(" Å")
            self.param_labels.append(label)
            self.param_spins.append(spin)

        controls = QFrame()
        controls.setObjectName("controlCard")
        form = QGridLayout(controls)
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(14)
        form.addWidget(self.metal_label, 0, 0)
        form.addWidget(self.metal_combo, 0, 1, 1, 3)
        form.addWidget(self.structure_label, 1, 0)
        form.addWidget(self.structure_combo, 1, 1, 1, 3)
        form.addWidget(self.graphene_variant_label, 1, 0)
        form.addWidget(self.graphene_variant_combo, 1, 1, 1, 3)
        form.addWidget(self.axis_label, 2, 0)
        form.addWidget(self.axis_combo, 2, 1, 1, 3)
        form.addWidget(self.graphene_edge_label, 2, 0)
        form.addWidget(self.graphene_edge_combo, 2, 1, 1, 3)
        self.generator_form = form
        for index, (label, spin) in enumerate(zip(self.param_labels, self.param_spins), start=3):
            form.addWidget(label, index, 0)
            form.addWidget(spin, index, 1)

        options = QFrame()
        options.setObjectName("controlCard")
        option_layout = QGridLayout(options)
        self.option_layout = option_layout
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

        self.core_shell_check = QCheckBox("Core-shell")
        self.core_shell_check.toggled.connect(self._refresh_structure_controls)
        self.core_atom = QComboBox()
        self.core_atom.addItems(("Au", "Ag"))
        self.shell_atom = QComboBox()
        self.shell_atom.addItems(("Ag", "Au"))
        self.core_shell_widgets = (self.core_shell_check, self.core_atom, self.shell_atom)

        option_layout.addWidget(self.dimer_check, 0, 0)
        option_layout.addWidget(self.dimer_distance, 0, 1)
        option_layout.addWidget(self.dimer_axis, 0, 2)
        option_layout.addWidget(self.alloy_check, 1, 0)
        option_layout.addWidget(self.alloy_atom, 1, 1)
        option_layout.addWidget(self.alloy_percent, 1, 2)
        option_layout.addWidget(self.bowtie_check, 2, 0)
        option_layout.addWidget(self.bowtie_distance, 2, 1, 1, 2)
        option_layout.addWidget(self.core_shell_check, 3, 0)
        option_layout.addWidget(self.core_atom, 3, 1)
        option_layout.addWidget(self.shell_atom, 3, 2)

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

        self.vdw_scale_input = self._make_viewer_spin(145, 60, 260, "%")
        self.vdw_scale_input.valueChanged.connect(self._set_vdw_scale_from_input)

        self.resolution_input = self._make_viewer_spin(1, 1, 4, "x")
        self.resolution_input.valueChanged.connect(self._set_render_resolution_from_input)

        self.bond_width_input = self._make_viewer_spin(165, 40, 260, "%")
        self.bond_width_input.valueChanged.connect(self._set_bond_width_from_input)
        self.atom_selection_input = QLineEdit()
        self.atom_selection_input.setObjectName("atomSelectionInput")
        self.atom_selection_input.setPlaceholderText("e.g. x > 0 and y > 0")
        self.atom_selection_input.returnPressed.connect(self._apply_atom_selection)

        self.manipulator_source = QComboBox()
        self.manipulator_source.setObjectName("manipulatorSource")
        self.manipulator_source.currentIndexChanged.connect(self._refresh_manipulator_actions)
        self.center_button = QPushButton("Center to origin")
        self.center_button.setObjectName("loadButton")
        self.center_button.clicked.connect(self.center_selected_structure)
        self.enantiomer_button = QPushButton("Enantiomer")
        self.enantiomer_button.setObjectName("smilesButton")
        self.enantiomer_button.clicked.connect(self.mirror_selected_structure)
        self.rotate_axis = QComboBox()
        self.rotate_axis.addItems(("+x", "-x", "+y", "-y", "+z", "-z"))
        self.rotate_angle = self._make_manipulator_spin(90.0, -360.0, 360.0, "°")
        self.rotate_button = QPushButton("Rotate")
        self.rotate_button.setObjectName("smilesButton")
        self.rotate_button.clicked.connect(self.rotate_selected_structure)
        self.translate_axis = QComboBox()
        self.translate_axis.addItems(("+x", "-x", "+y", "-y", "+z", "-z"))
        self.translate_distance = self._make_manipulator_spin(5.0, -10000.0, 10000.0, " Å")
        self.translate_button = QPushButton("Translate")
        self.translate_button.setObjectName("smilesButton")
        self.translate_button.clicked.connect(self.translate_selected_structure)
        self.pair_fixed_source = QComboBox()
        self.pair_moving_source = QComboBox()
        self.pair_axis = QComboBox()
        self.pair_axis.addItems(("+x", "-x", "+y", "-y", "+z", "-z"))
        self.pair_distance = self._make_manipulator_spin(5.0, 0.01, 10000.0, " Å")
        self.pair_translate_button = QPushButton("Translate at distance")
        self.pair_translate_button.setObjectName("loadButton")
        self.pair_translate_button.clicked.connect(self.translate_pair_selected_structures)

        generator_page = QWidget()
        generator_page.setObjectName("sidePage")
        generator_layout = QVBoxLayout(generator_page)
        generator_layout.setContentsMargins(0, 18, 0, 0)
        generator_layout.setSpacing(14)
        generator_layout.addWidget(self._section_label("Structure"))
        generator_layout.addWidget(controls)
        generator_layout.addWidget(self._section_label("Optional"))
        generator_layout.addWidget(options)
        generator_layout.addStretch(1)
        generator_layout.addWidget(self.create_button)

        viewer_page = QWidget()
        viewer_page.setObjectName("sidePage")
        viewer_layout = QVBoxLayout(viewer_page)
        viewer_layout.setContentsMargins(0, 18, 0, 0)
        viewer_layout.setSpacing(14)
        load_card = QFrame()
        load_card.setObjectName("controlCard")
        load_layout = QVBoxLayout(load_card)
        load_layout.setContentsMargins(0, 0, 0, 0)
        load_layout.setSpacing(10)
        load_layout.addWidget(self.load_button)
        load_layout.addWidget(self.file_hint)
        load_layout.addSpacing(4)
        load_layout.addWidget(self._section_label("SMILES"))
        load_layout.addWidget(self.smiles_input)
        load_layout.addWidget(self.smiles_button)
        viewer_layout.addWidget(self._section_label("Load"))
        viewer_layout.addWidget(load_card)

        appearance_card = QFrame()
        appearance_card.setObjectName("controlCard")
        appearance_layout = QVBoxLayout(appearance_card)
        appearance_layout.setContentsMargins(0, 0, 0, 0)
        appearance_layout.setSpacing(12)
        vdw_row = QHBoxLayout()
        vdw_label = self._field_label("Sphere size")
        vdw_row.addWidget(vdw_label)
        vdw_row.addStretch(1)
        vdw_row.addWidget(self.vdw_scale_input)
        appearance_layout.addLayout(vdw_row)

        resolution_row = QHBoxLayout()
        resolution_row.addWidget(self._field_label("Resolution"))
        resolution_row.addStretch(1)
        resolution_row.addWidget(self.resolution_input)
        appearance_layout.addLayout(resolution_row)
        bond_row = QHBoxLayout()
        bond_row.addWidget(self._field_label("Bond width"))
        bond_row.addStretch(1)
        bond_row.addWidget(self.bond_width_input)
        appearance_layout.addLayout(bond_row)
        viewer_layout.addWidget(self._section_label("Appearance"))
        viewer_layout.addWidget(appearance_card)
        select_card = QFrame()
        select_card.setObjectName("controlCard")
        select_layout = QVBoxLayout(select_card)
        select_layout.setContentsMargins(0, 0, 0, 0)
        select_layout.setSpacing(10)
        select_layout.addWidget(self.atom_selection_input)
        viewer_layout.addWidget(self._section_label("Select atoms"))
        viewer_layout.addWidget(select_card)
        viewer_layout.addStretch(1)

        single_page = QWidget()
        single_page.setObjectName("sidePage")
        single_layout = QVBoxLayout(single_page)
        single_layout.setContentsMargins(0, 10, 0, 0)
        single_layout.setSpacing(8)
        single_layout.addWidget(self._section_label("Loaded structure"))
        source_group = QFrame()
        source_group.setObjectName("controlCard")
        source_group_layout = QVBoxLayout(source_group)
        source_group_layout.setContentsMargins(0, 0, 0, 0)
        source_group_layout.addWidget(self.manipulator_source)
        single_layout.addWidget(source_group)
        single_layout.addSpacing(4)
        single_layout.addWidget(self._section_label("Translate"))
        translate_group = QFrame()
        translate_group.setObjectName("toolGroup")
        translate_group_layout = QVBoxLayout(translate_group)
        translate_group_layout.setContentsMargins(0, 0, 0, 0)
        translate_group_layout.setSpacing(7)
        translate_row = QHBoxLayout()
        translate_row.setSpacing(8)
        translate_row.addWidget(self.translate_axis)
        translate_row.addWidget(self.translate_distance)
        translate_group_layout.addLayout(translate_row)
        translate_group_layout.addWidget(self.translate_button)
        single_layout.addWidget(translate_group)
        single_layout.addSpacing(4)
        single_layout.addWidget(self._section_label("Rotate"))
        rotate_group = QFrame()
        rotate_group.setObjectName("toolGroup")
        rotate_group_layout = QVBoxLayout(rotate_group)
        rotate_group_layout.setContentsMargins(0, 0, 0, 0)
        rotate_group_layout.setSpacing(7)
        rotate_row = QHBoxLayout()
        rotate_row.setSpacing(8)
        rotate_row.addWidget(self.rotate_axis)
        rotate_row.addWidget(self.rotate_angle)
        rotate_group_layout.addLayout(rotate_row)
        rotate_group_layout.addWidget(self.rotate_button)
        single_layout.addWidget(rotate_group)
        single_layout.addSpacing(4)
        enantiomer_group = QFrame()
        enantiomer_group.setObjectName("controlCard")
        enantiomer_group_layout = QVBoxLayout(enantiomer_group)
        enantiomer_group_layout.setContentsMargins(0, 0, 0, 0)
        enantiomer_group_layout.addWidget(self.enantiomer_button)
        single_layout.addWidget(self._section_label("Mirror"))
        single_layout.addWidget(enantiomer_group)
        single_layout.addSpacing(4)
        center_group = QFrame()
        center_group.setObjectName("controlCard")
        center_group_layout = QVBoxLayout(center_group)
        center_group_layout.setContentsMargins(0, 0, 0, 0)
        center_group_layout.addWidget(self.center_button)
        single_layout.addWidget(self._section_label("Center"))
        single_layout.addWidget(center_group)
        single_layout.addStretch(1)

        pair_page = QWidget()
        pair_page.setObjectName("sidePage")
        pair_layout = QVBoxLayout(pair_page)
        pair_layout.setContentsMargins(0, 10, 0, 0)
        pair_layout.setSpacing(8)
        pair_layout.addWidget(self._section_label("Controlled distance"))
        pair_group = QFrame()
        pair_group.setObjectName("toolGroup")
        pair_group_layout = QVBoxLayout(pair_group)
        pair_group_layout.setContentsMargins(0, 0, 0, 0)
        pair_group_layout.setSpacing(7)
        pair_group_layout.addWidget(self._field_label("Fixed"))
        pair_group_layout.addWidget(self.pair_fixed_source)
        pair_group_layout.addWidget(self._field_label("Translated"))
        pair_group_layout.addWidget(self.pair_moving_source)
        pair_row = QHBoxLayout()
        pair_row.setSpacing(8)
        pair_row.addWidget(self.pair_axis)
        pair_row.addWidget(self.pair_distance)
        pair_group_layout.addLayout(pair_row)
        pair_group_layout.addWidget(self.pair_translate_button)
        pair_layout.addWidget(pair_group)
        pair_layout.addStretch(1)

        manipulator_page = QWidget()
        manipulator_layout = QVBoxLayout(manipulator_page)
        manipulator_layout.setContentsMargins(0, 24, 0, 0)
        manipulator_layout.setSpacing(0)
        self.manipulator_tabs = QTabWidget()
        self.manipulator_tabs.setObjectName("manipulatorTabs")
        self.manipulator_tabs.addTab(single_page, "Single")
        self.manipulator_tabs.addTab(pair_page, "Pair")
        manipulator_layout.addWidget(self.manipulator_tabs)

        self.side_tabs = QTabWidget()
        self.side_tabs.setObjectName("sideTabs")
        self.side_tabs.addTab(viewer_page, "Viewer")
        self.side_tabs.addTab(generator_page, "Generator")
        self.side_tabs.addTab(manipulator_page, "Manipulator")

        side.addWidget(logo_header)
        side.addSpacing(40)
        side.addWidget(self.side_tabs, 1)

        main = QFrame()
        main.setObjectName("main")
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(24, 0, 24, 24)
        main_layout.setSpacing(0)
        self.meta_label = QLabel("")
        self.meta_label.setObjectName("meta")

        self.tabs = QTabWidget()
        self.tabs.setObjectName("viewerTabs")
        self.tabs.setTabBar(ViewerTabBar())
        self.tabs.setDocumentMode(False)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.setElideMode(Qt.ElideRight)
        self.tabs.setCornerWidget(self.meta_label, Qt.TopRightCorner)
        self.tabs.currentChanged.connect(self._sync_current_tab_meta)
        self.tabs.currentChanged.connect(self._refresh_manipulator_sources)
        self.tabs.currentChanged.connect(self._sync_atom_selection_input)
        self.tabs.currentChanged.connect(self._refresh_manipulator_actions)
        self.canvas = self._make_canvas()
        self.empty_canvas = self.canvas
        self.tabs.addTab(self.canvas, "")
        self.tabs.tabBar().hide()
        main_layout.addWidget(self.tabs)

        layout.addWidget(sidebar)
        layout.addWidget(main, 1)
        self._configure_dropdown_popups()
        self._apply_styles()
        self.reset_view_shortcut = QShortcut(QKeySequence("Shift+0"), self)
        self.reset_view_shortcut.activated.connect(self.reset_current_view)
        self._refresh_material_controls()
        self._refresh_smiles_button_state()
        self._refresh_manipulator_sources()

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _configure_dropdown_popups(self):
        for combo in self.findChildren(QComboBox):
            popup = QListView(combo)
            popup.setObjectName("comboPopup")
            popup.setMouseTracking(True)
            popup.setUniformItemSizes(True)
            popup.setSpacing(2)
            combo.setView(popup)

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionLabel")
        return label

    def _make_canvas(self) -> VdwCanvas:
        canvas = VdwCanvas()
        canvas.setObjectName("canvas")
        canvas.set_vdw_scale(self.vdw_scale)
        canvas.set_bond_width_scale(self.bond_width_scale)
        canvas.set_render_resolution(self.render_resolution)
        canvas.files_dropped.connect(self.load_files)
        return canvas

    def _make_viewer_spin(self, value: int, minimum: int, maximum: int, suffix: str) -> ViewerStepper:
        return ViewerStepper(value, minimum, maximum, suffix)

    def reset_current_view(self):
        current = self.tabs.currentWidget()
        if isinstance(current, VdwCanvas):
            current.reset_view()

    def keyPressEvent(self, event):
        current = self.tabs.currentWidget()
        if isinstance(current, VdwCanvas) and current._is_reset_view_key(event):
            current.reset_view()
            event.accept()
            return
        super().keyPressEvent(event)

    def _make_manipulator_spin(self, value: float, minimum: float, maximum: float, suffix: str) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
        spin.setRange(minimum, maximum)
        spin.setDecimals(2)
        spin.setSingleStep(1.0)
        spin.setValue(value)
        spin.setSuffix(suffix)
        spin.setAlignment(Qt.AlignCenter)
        return spin

    def _make_option_spin(self, value: float, minimum: float, maximum: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setButtonSymbols(QDoubleSpinBox.NoButtons)
        spin.setRange(minimum, maximum)
        spin.setDecimals(2)
        spin.setSingleStep(1.0)
        spin.setValue(value)
        spin.setSuffix(" Å")
        return spin

    def _material_items(self) -> list[str]:
        metals = supported_atomistic_metals()
        priority = ["Au", "Ag", "Graphene", "Na"]
        rest = [metal for metal in metals if metal not in priority]
        return [item for item in priority if item == "Graphene" or item in metals] + rest

    def _refresh_material_controls(self):
        material = self.metal_combo.currentText()
        current_structure = self.structure_combo.currentText()
        available_structures = self._available_structures_for_material(material)

        self.structure_combo.blockSignals(True)
        self.structure_combo.clear()
        self.structure_combo.addItems(available_structures)
        if current_structure in available_structures:
            self.structure_combo.setCurrentText(current_structure)
        elif available_structures:
            self.structure_combo.setCurrentText(available_structures[0])
        self.structure_combo.blockSignals(False)
        self._refresh_structure_controls()

    def _available_structures_for_material(self, material: str) -> list[str]:
        if material == "Graphene":
            return []
        fcc_metals = set(supported_fcc_metals())
        return [
            name
            for name, definition in STRUCTURES.items()
            if definition["metals"] != "fcc" or material in fcc_metals
        ]

    def _refresh_structure_controls(self):
        is_graphene = self.metal_combo.currentText() == "Graphene"
        definition = STRUCTURES[self.structure_combo.currentText()] if not is_graphene else {"fields": (), "graphene": True}
        active_definition = GRAPHENE_VARIANTS[self.graphene_variant_combo.currentText()] if is_graphene else definition
        structure_name = self.structure_combo.currentText() if not is_graphene else ""
        core_shell_active = (
            not is_graphene
            and self.metal_combo.currentText() in {"Au", "Ag"}
            and structure_name in {"Sphere", "Rod"}
            and self.core_shell_check.isChecked()
        )

        if core_shell_active and structure_name == "Sphere":
            active_definition = {
                "fields": (
                    ("core_radius", "Core radius", 20.0, 2.0, 300.0),
                    ("shell_radius", "Shell radius", 30.0, 3.0, 500.0),
                )
            }
        elif core_shell_active and structure_name == "Rod":
            active_definition = {
                "fields": (
                    ("core_length", "Core length", 20.0, 4.0, 500.0),
                    ("core_width", "Core width", 10.0, 2.0, 300.0),
                    ("shell_length", "Shell length", 50.0, 5.0, 700.0),
                    ("shell_width", "Shell width", 20.0, 3.0, 500.0),
                )
            }

        has_axis = bool(definition.get("axis")) and not is_graphene
        self.structure_label.setVisible(not is_graphene)
        self.structure_combo.setVisible(not is_graphene)
        self.axis_label.setVisible(has_axis)
        self.axis_combo.setVisible(has_axis)
        self.graphene_variant_label.setVisible(is_graphene)
        self.graphene_variant_combo.setVisible(is_graphene)
        has_graphene_edge = is_graphene and active_definition.get("graphene") == "triangle"
        self.graphene_edge_label.setVisible(has_graphene_edge)
        self.graphene_edge_combo.setVisible(has_graphene_edge)

        fields = active_definition["fields"]
        for label, spin in zip(self.param_labels, self.param_spins):
            self.generator_form.removeWidget(label)
            self.generator_form.removeWidget(spin)

        paired_rows = {"a", "b"}
        layout_row = 3
        index = 0
        while index < len(fields):
            field_name, text, value, minimum, maximum = fields[index]
            label = self.param_labels[index]
            spin = self.param_spins[index]
            if (
                field_name == "a"
                and index + 1 < len(fields)
                and fields[index + 1][0] == "b"
            ):
                next_field_name, next_text, next_value, next_minimum, next_maximum = fields[index + 1]
                next_label = self.param_labels[index + 1]
                next_spin = self.param_spins[index + 1]

                self._configure_parameter_widget(label, spin, text, value, minimum, maximum)
                self._configure_parameter_widget(next_label, next_spin, next_text, next_value, next_minimum, next_maximum)
                self.generator_form.addWidget(label, layout_row, 0)
                self.generator_form.addWidget(spin, layout_row, 1)
                self.generator_form.addWidget(next_label, layout_row, 2)
                self.generator_form.addWidget(next_spin, layout_row, 3)
                index += 2
            else:
                self._configure_parameter_widget(label, spin, text, value, minimum, maximum)
                self.generator_form.addWidget(label, layout_row, 0)
                self.generator_form.addWidget(spin, layout_row, 1, 1, 3 if text not in paired_rows else 1)
                index += 1
            layout_row += 1

        for index, (label, spin) in enumerate(zip(self.param_labels, self.param_spins)):
            if index >= len(fields):
                label.setVisible(False)
                spin.setVisible(False)

        self._refresh_option_controls()

    def _configure_parameter_widget(
        self,
        label: QLabel,
        spin: QDoubleSpinBox,
        text: str,
        value: float,
        minimum: float,
        maximum: float,
    ):
        label.setText(text)
        label.setVisible(True)
        spin.setVisible(True)
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        spin.setSuffix("" if text in {"a", "b"} else " Å")
        spin.setSingleStep(0.01 if text in {"a", "b"} else 1.0)

    def _ordered_metals(self, metals: list[str]) -> list[str]:
        priority = ["Au", "Ag", "Na"]
        return [metal for metal in priority if metal in metals] + [metal for metal in metals if metal not in priority]

    def _refresh_option_controls(self):
        metal = self.metal_combo.currentText()
        is_graphene = metal == "Graphene"
        structure_name = self.structure_combo.currentText() if not is_graphene else ""
        alloy_allowed = metal in {"Ag", "Au"}
        bowtie_allowed = bool(STRUCTURES[self.structure_combo.currentText()].get("bowtie")) if not is_graphene else False
        core_shell_allowed = not is_graphene and metal in {"Au", "Ag"} and structure_name in {"Sphere", "Rod"}
        core_shell_active = core_shell_allowed and self.core_shell_check.isChecked()

        if is_graphene:
            self.dimer_check.setChecked(False)
            self.alloy_check.setChecked(False)
            self.bowtie_check.setChecked(False)
            self.core_shell_check.setChecked(False)
        elif alloy_allowed:
            self.alloy_atom.setCurrentText("Au" if metal == "Ag" else "Ag")
        else:
            self.alloy_check.setChecked(False)

        if not bowtie_allowed:
            self.bowtie_check.setChecked(False)
        if not core_shell_allowed:
            self.core_shell_check.setChecked(False)
        elif not self.core_shell_check.isChecked():
            self.core_atom.setCurrentText(metal)
            self.shell_atom.setCurrentText("Au" if metal == "Ag" else "Ag")

        if self.dimer_check.isChecked() and self.bowtie_check.isChecked():
            sender = self.sender()
            if sender is self.bowtie_check:
                self.dimer_check.setChecked(False)
            else:
                self.bowtie_check.setChecked(False)

        self._set_optional_row_enabled(self.dimer_widgets, not is_graphene and self.dimer_check.isChecked())
        self.dimer_check.setEnabled(not is_graphene)

        self.option_layout.removeWidget(self.alloy_percent)
        self.alloy_atom.setVisible(not core_shell_active)
        if core_shell_active:
            self.option_layout.addWidget(self.alloy_percent, 1, 1, 1, 2)
        else:
            self.option_layout.addWidget(self.alloy_percent, 1, 2)

        self._set_optional_row_enabled(self.alloy_widgets, not is_graphene and alloy_allowed and self.alloy_check.isChecked())
        self.alloy_check.setEnabled(not is_graphene and alloy_allowed)

        for widget in self.bowtie_widgets:
            widget.setVisible(not is_graphene and bowtie_allowed)
        self._set_optional_row_enabled(self.bowtie_widgets, not is_graphene and bowtie_allowed and self.bowtie_check.isChecked())
        self.bowtie_check.setEnabled(not is_graphene and bowtie_allowed)

        for widget in self.core_shell_widgets:
            widget.setVisible(core_shell_allowed)
        self._set_optional_row_enabled(self.core_shell_widgets, core_shell_allowed and self.core_shell_check.isChecked())
        self.core_shell_check.setEnabled(core_shell_allowed)

    def _set_optional_row_enabled(self, widgets, enabled: bool):
        for widget in widgets:
            widget.setEnabled(enabled)

    def _apply_atom_selection(self, *_args):
        if not hasattr(self, "atom_selection_input"):
            return
        canvas = self.tabs.currentWidget()
        if not isinstance(canvas, VdwCanvas):
            return
        expression = self.atom_selection_input.text().strip()
        if not expression or expression.lower() == "all":
            canvas.set_visible_atoms(canvas.source_atoms)
            canvas.setProperty("atom_count", len(canvas.source_atoms))
            canvas.selection_expression = expression
            self._set_atom_selection_invalid(False)
            self._sync_current_tab_meta()
            return
        try:
            selected = tuple(atom for atom in canvas.source_atoms if atom_matches_selection(atom, expression))
        except Exception:
            self._set_atom_selection_invalid(True)
            return
        canvas.set_visible_atoms(selected)
        canvas.setProperty("atom_count", len(selected))
        canvas.selection_expression = expression
        self._set_atom_selection_invalid(False)
        self._sync_current_tab_meta()

    def _sync_atom_selection_input(self):
        if not hasattr(self, "atom_selection_input"):
            return
        canvas = self.tabs.currentWidget()
        expression = canvas.selection_expression if isinstance(canvas, VdwCanvas) else ""
        self.atom_selection_input.blockSignals(True)
        self.atom_selection_input.setText(expression)
        self.atom_selection_input.blockSignals(False)
        self._set_atom_selection_invalid(False)

    def _set_atom_selection_invalid(self, invalid: bool):
        if self.atom_selection_input.property("invalid") == invalid:
            return
        self.atom_selection_input.setProperty("invalid", invalid)
        self.atom_selection_input.style().unpolish(self.atom_selection_input)
        self.atom_selection_input.style().polish(self.atom_selection_input)

    def _set_vdw_scale_from_input(self, value: int):
        self.vdw_scale = value / 100.0
        for canvas in self._all_canvases():
            canvas.set_vdw_scale(self.vdw_scale)

    def _set_render_resolution_from_input(self, value: int):
        self.render_resolution = value
        for canvas in self._all_canvases():
            canvas.set_render_resolution(self.render_resolution)

    def _set_bond_width_from_input(self, value: int):
        self.bond_width_scale = value / 100.0
        for canvas in self._all_canvases():
            canvas.set_bond_width_scale(self.bond_width_scale)

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
                background: #FBFBFD;
                border-right: 1px solid #F1F1F4;
            }}
            QFrame#main {{
                background: {SURFACE};
            }}
            QWidget#logoHeader, QWidget#logoLines {{
                background: transparent;
            }}
            QFrame#logoLineLong, QFrame#logoLineMid, QFrame#logoLineShort {{
                border: 0;
                border-radius: 1px;
                background: #050509;
            }}
            QWidget#sidePage {{
                background: transparent;
            }}
            QFrame#controlCard {{
                background: #FFFFFF;
                border: 1px solid #EEEAF4;
                border-radius: 18px;
                padding: 10px;
            }}
            QFrame#toolGroup {{
                background: #FFFFFF;
                border: 1px solid #EEEAF4;
                border-radius: 18px;
                padding: 10px;
            }}
            QLabel#appTitle {{
                color: #050509;
                font-family: "Times New Roman";
                font-size: 50px;
                font-weight: 800;
                letter-spacing: 0;
            }}
            QLabel#subtitle, QLabel#fieldLabel {{
                color: #7C7C88;
                font-size: 13px;
            }}
            QLabel#sectionLabel {{
                color: {TEXT};
                font-size: 13px;
                font-weight: 720;
                margin-top: 2px;
                margin-left: 2px;
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
            QTabWidget#sideTabs QTabBar {{
                background: #F4F3F8;
                border: 1px solid #EEEAF4;
                border-radius: 17px;
                padding: 3px;
            }}
            QTabWidget#sideTabs QTabBar::tab {{
                background: transparent;
                color: #7C7C88;
                border: 0;
                border-radius: 13px;
                padding: 8px 13px;
                margin: 0;
                font-size: 13px;
                font-weight: 650;
            }}
            QTabWidget#sideTabs QTabBar::tab:selected {{
                color: {TEXT};
                background: #FFFFFF;
                border: 1px solid #E8E4F2;
            }}
            QTabWidget#sideTabs QTabBar::tab:hover:!selected {{
                color: {TEXT};
                background: #FFFFFF;
            }}
            QTabWidget#manipulatorTabs::pane {{
                border: 0;
            }}
            QTabWidget#manipulatorTabs QTabBar {{
                background: #F4F3F8;
                border: 1px solid #EEEAF4;
                border-radius: 15px;
                padding: 3px;
            }}
            QTabWidget#manipulatorTabs QTabBar::tab {{
                background: transparent;
                color: #7C7C88;
                border: 0;
                border-radius: 11px;
                padding: 7px 18px;
                margin: 0;
                font-size: 13px;
                font-weight: 650;
            }}
            QTabWidget#manipulatorTabs QTabBar::tab:selected {{
                color: #000000;
                background: #FFFFFF;
                border: 1px solid #E8E4F2;
            }}
            QTabWidget#manipulatorTabs QTabBar::tab:disabled {{
                color: #BAB8C3;
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
            QComboBox:hover {{
                color: #000000;
                border-bottom: 2px solid {ACCENT_VIOLET};
                background: {ACCENT_SOFT};
            }}
            QComboBox::drop-down {{
                border: 0;
                width: 28px;
            }}
            QComboBox QAbstractItemView {{
                background: #FFFFFF;
                color: {TEXT};
                border: 1px solid #E8E4F2;
                border-radius: 10px;
                padding: 6px;
                selection-background-color: {ACCENT_SOFT};
                selection-color: #000000;
                outline: 0;
            }}
            QListView#comboPopup {{
                background: #FFFFFF;
                border: 1px solid #E8E4F2;
                border-radius: 10px;
                padding: 6px;
                outline: 0;
            }}
            QComboBox QAbstractItemView::item,
            QListView#comboPopup::item {{
                min-height: 30px;
                padding: 5px 10px;
                border-radius: 7px;
            }}
            QComboBox QAbstractItemView::item:hover,
            QComboBox QAbstractItemView::item:selected,
            QListView#comboPopup::item:hover,
            QListView#comboPopup::item:selected {{
                background: {ACCENT_SOFT};
                color: #000000;
            }}
            QFrame#toolGroup QComboBox,
            QFrame#toolGroup QDoubleSpinBox {{
                background: #FFFFFF;
                border: 1px solid #E8E4F2;
                border-radius: 14px;
                min-height: 36px;
                padding: 0 10px;
                font-weight: 600;
            }}
            QFrame#toolGroup QComboBox:focus,
            QFrame#toolGroup QDoubleSpinBox:focus {{
                border: 1px solid {ACCENT_VIOLET};
            }}
            QFrame#toolGroup QComboBox:hover {{
                background: {ACCENT_SOFT};
                border: 1px solid {ACCENT_VIOLET};
            }}
            QFrame#toolGroup QComboBox::drop-down {{
                border: 0;
                width: 28px;
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
            QPushButton#loadButton:disabled {{
                background: #F3F1F8;
                color: #A8A2B8;
                border-color: #E6E0F2;
            }}
            QLineEdit#smilesInput, QLineEdit#atomSelectionInput {{
                background: #FFFFFF;
                color: {TEXT};
                border: 1px solid #E8E4F2;
                border-radius: 16px;
                min-height: 40px;
                padding: 0 13px;
                font-size: 14px;
                selection-background-color: {ACCENT_SOFT};
            }}
            QLineEdit#smilesInput:focus, QLineEdit#atomSelectionInput:focus {{
                border-color: {ACCENT_VIOLET};
            }}
            QLineEdit#atomSelectionInput[invalid="true"] {{
                border-color: #D94A4A;
                color: #A62626;
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
            QToolButton#tabMenuButton {{
                background: #FFFFFF;
                color: #7C7C88;
                border: 1px solid #EEEAF7;
                border-radius: 11px;
                min-width: 28px;
                max-width: 28px;
                min-height: 22px;
                max-height: 22px;
                padding: 0;
                font-size: 13px;
                font-weight: 900;
            }}
            QToolButton#tabMenuButton::menu-indicator {{
                image: none;
                width: 0;
                height: 0;
            }}
            QToolButton#tabMenuButton:hover {{
                background: {ACCENT_SOFT};
                color: {ACCENT_VIOLET};
            }}
            QMenu {{
                background: #FFFFFF;
                color: {TEXT};
                border: 1px solid #E8E4F2;
                border-radius: 10px;
                padding: 6px;
            }}
            QMenu::item {{
                padding: 7px 26px 7px 12px;
                border-radius: 7px;
                font-size: 13px;
            }}
            QMenu::item:selected {{
                background: {ACCENT_SOFT};
                color: {ACCENT_VIOLET};
            }}
            QTabWidget#viewerTabs::pane {{
                border: 0;
                top: -1px;
                background: #FFFFFF;
            }}
            QTabWidget#viewerTabs::tab-bar {{
                left: 0;
                top: 8px;
            }}
            QTabWidget#viewerTabs QTabBar {{
                alignment: left;
                left: 0;
                top: 0;
                min-height: 38px;
                background: #FFFFFF;
                padding-left: 24px;
            }}
            QTabWidget#viewerTabs QTabBar::tab {{
                background: #FFFFFF;
                color: #7C7C88;
                border: 1px solid transparent;
                border-bottom: 2px solid transparent;
                border-radius: 10px 10px 0 0;
                padding: 8px 28px 8px 18px;
                margin: 0 2px 0 0;
                min-width: 90px;
                max-width: 138px;
                font-size: 13px;
                font-weight: 600;
            }}
            QTabWidget#viewerTabs QTabBar::tab:selected {{
                color: {TEXT};
                background: #FFFFFF;
                border-color: #F0EDF7;
                border-bottom: 2px solid {ACCENT_VIOLET};
            }}
            QTabWidget#viewerTabs QTabBar::tab:hover {{
                color: {TEXT};
                background: {ACCENT_SOFT};
            }}
            QTabWidget#viewerTabs QTabBar QToolButton {{
                background: #FFFFFF;
                color: {ACCENT_VIOLET};
                border: 1px solid #E3DAF5;
                border-radius: 9px;
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
                max-height: 28px;
                margin: 4px 5px 0 0;
                padding: 0;
                font-size: 16px;
                font-weight: 900;
            }}
            QTabWidget#viewerTabs QTabBar QToolButton:hover {{
                background: {ACCENT_SOFT};
                color: {ACCENT_INDIGO};
            }}
            QWidget#canvas {{
                background: {SURFACE};
                border: 0;
                border-radius: 0;
            }}
        """)

    def create_structure(self):
        self.output_root = GUI_TMP_ROOT

        try:
            command_args = self._build_command_args()
            self.pending_generation_meta = self._generation_metadata()
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

        self._add_structure_tab(smiles, atoms, xyz_path)
        self.smiles_input.clear()

    def _add_structure_tab(
        self,
        title: str,
        atoms: tuple[AtomRecord, ...],
        path: Path | None = None,
        metadata: dict[str, object] | None = None,
    ):
        if self.empty_canvas is not None and self.tabs.count() == 1 and not self.empty_canvas.atoms:
            self.tabs.removeTab(0)
            self.empty_canvas = None

        canvas = self._make_canvas()
        canvas.set_atoms(atoms)
        canvas.setProperty("atom_count", len(atoms))
        if path is not None:
            canvas.setProperty("path", str(path))
        if metadata:
            for key, value in metadata.items():
                canvas.setProperty(key, value)

        tab_index = self.tabs.addTab(canvas, self._short_tab_title(title))
        self._install_tab_menu(tab_index, canvas)
        self.tabs.tabBar().show()
        self.tabs.setCurrentIndex(tab_index)
        self.canvas = canvas
        self._sync_atom_selection_input()
        self._sync_current_tab_meta()
        self._refresh_manipulator_sources()

    def _install_tab_menu(self, tab_index: int, canvas: VdwCanvas):
        button = QToolButton()
        button.setObjectName("tabMenuButton")
        button.setText("···")
        button.setPopupMode(QToolButton.InstantPopup)
        button.setAutoRaise(True)
        menu = QMenu(button)
        save_action = menu.addAction("Save")
        save_action.triggered.connect(lambda checked=False, source=canvas: self.save_structure(source))
        menu.addSeparator()
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda checked=False, source=canvas: self.delete_structure_tab(source))
        button.setMenu(menu)
        self.tabs.tabBar().setTabButton(tab_index, QTabBar.RightSide, button)

    def save_structure(self, canvas: VdwCanvas):
        source_path = self._save_source_for_canvas(canvas)
        if source_path is False:
            return
        default_name = (source_path.stem if source_path else "structure") + ".xyz"
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Save structure as XYZ",
            str(Path.cwd() / default_name),
            "XYZ files (*.xyz)",
        )
        if not destination:
            return

        destination_path = Path(destination)
        if destination_path.suffix.lower() != ".xyz":
            destination_path = destination_path.with_suffix(".xyz")

        try:
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            if source_path is not None and source_path.exists():
                shutil.copyfile(source_path, destination_path)
            else:
                self._write_xyz(destination_path, canvas.atoms)
        except Exception as exc:
            QMessageBox.warning(self, "Could not save structure", f"{destination_path}\n\n{exc}")

    def _save_source_for_canvas(self, canvas: VdwCanvas) -> Path | None | bool:
        fixed_path = canvas.property("fixed_path")
        translated_path = canvas.property("translated_path")
        if fixed_path and translated_path:
            message = QMessageBox(self)
            message.setIcon(QMessageBox.Question)
            message.setWindowTitle("Save joint visualization")
            message.setText("Which structure do you want to save?")
            translated_button = message.addButton("Translated", QMessageBox.AcceptRole)
            fixed_button = message.addButton("Fixed", QMessageBox.AcceptRole)
            cancel_button = message.addButton("Cancel", QMessageBox.RejectRole)
            message.setDefaultButton(translated_button)
            message.setEscapeButton(cancel_button)
            message.exec()
            clicked = message.clickedButton()
            if clicked is translated_button:
                return Path(translated_path)
            if clicked is fixed_button:
                return Path(fixed_path)
            return False

        return Path(canvas.property("path")) if canvas.property("path") else None

    def _write_xyz(self, path: Path, atoms: tuple[AtomRecord, ...]):
        with path.open("w", encoding="utf-8") as handle:
            handle.write(f"{len(atoms)}\n")
            handle.write("Generated with GEOM GUI\n")
            for atom in atoms:
                handle.write(f"{atom.element.capitalize():2} {atom.x:20.8f} {atom.y:20.8f} {atom.z:20.8f}\n")

    def delete_structure_tab(self, canvas: VdwCanvas):
        index = self.tabs.indexOf(canvas)
        if index < 0:
            return

        title = self.tabs.tabText(index)
        answer = QMessageBox.question(
            self,
            "Delete structure tab",
            f'Delete "{title}" from the viewer?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        self.tabs.removeTab(index)
        canvas.deleteLater()

        if self.tabs.count() == 0:
            self.canvas = self._make_canvas()
            self.empty_canvas = self.canvas
            self.tabs.addTab(self.canvas, "")
            self.tabs.tabBar().hide()
        else:
            current = self.tabs.currentWidget()
            if isinstance(current, VdwCanvas):
                self.canvas = current
        self._sync_current_tab_meta()
        self._refresh_manipulator_sources()

    def _refresh_manipulator_sources(self):
        if not hasattr(self, "manipulator_source"):
            return

        current_path = self.manipulator_source.currentData()
        fixed_path = self.pair_fixed_source.currentData()
        moving_path = self.pair_moving_source.currentData()
        entries: list[tuple[str, str]] = []
        self.manipulator_source.blockSignals(True)
        self.pair_fixed_source.blockSignals(True)
        self.pair_moving_source.blockSignals(True)
        self.manipulator_source.clear()
        self.pair_fixed_source.clear()
        self.pair_moving_source.clear()
        for index in range(self.tabs.count()):
            widget = self.tabs.widget(index)
            if not isinstance(widget, VdwCanvas) or not widget.atoms:
                continue
            path = widget.property("path")
            if not path:
                continue
            entries.append((self.tabs.tabText(index), path))
            self.manipulator_source.addItem(self.tabs.tabText(index), path)
            self.pair_fixed_source.addItem(self.tabs.tabText(index), path)
            self.pair_moving_source.addItem(self.tabs.tabText(index), path)
        if current_path:
            found = self.manipulator_source.findData(current_path)
            if found >= 0:
                self.manipulator_source.setCurrentIndex(found)
        if fixed_path:
            found = self.pair_fixed_source.findData(fixed_path)
            if found >= 0:
                self.pair_fixed_source.setCurrentIndex(found)
        if moving_path:
            found = self.pair_moving_source.findData(moving_path)
            if found >= 0:
                self.pair_moving_source.setCurrentIndex(found)
        elif len(entries) > 1:
            self.pair_moving_source.setCurrentIndex(1)
        if len(entries) > 1 and self.pair_moving_source.currentData() == self.pair_fixed_source.currentData():
            self.pair_moving_source.setCurrentIndex(1 if self.pair_fixed_source.currentIndex() != 1 else 0)
        self.manipulator_source.blockSignals(False)
        self.pair_fixed_source.blockSignals(False)
        self.pair_moving_source.blockSignals(False)

        has_sources = self.manipulator_source.count() > 0
        has_pair_sources = self.manipulator_source.count() > 0
        for widget in (
            self.manipulator_source,
            self.enantiomer_button,
            self.rotate_axis,
            self.rotate_angle,
            self.rotate_button,
            self.translate_axis,
            self.translate_distance,
            self.translate_button,
        ):
            widget.setEnabled(has_sources)
        for widget in (
            self.pair_fixed_source,
            self.pair_moving_source,
            self.pair_axis,
            self.pair_distance,
            self.pair_translate_button,
        ):
            widget.setEnabled(has_pair_sources)
        if hasattr(self, "manipulator_tabs"):
            self.manipulator_tabs.setTabEnabled(1, has_pair_sources)
            if not has_pair_sources and self.manipulator_tabs.currentIndex() == 1:
                self.manipulator_tabs.setCurrentIndex(0)
        self._refresh_manipulator_actions()

    def _refresh_manipulator_actions(self, *_args):
        if not hasattr(self, "center_button"):
            return
        self.center_button.setEnabled(self._center_to_origin_available())

    def _center_to_origin_available(self) -> bool:
        path = self.manipulator_source.currentData()
        if not path or self._current_viewer_tab_is_joint():
            return False
        try:
            return not self._atoms_are_centered(read_xyz(Path(path)))
        except Exception:
            return False

    def _current_viewer_tab_is_joint(self) -> bool:
        canvas = self.tabs.currentWidget()
        return isinstance(canvas, VdwCanvas) and bool(canvas.property("fixed_path") and canvas.property("translated_path"))

    def _atoms_are_centered(self, atoms: tuple[AtomRecord, ...], tolerance: float = 1e-6) -> bool:
        if not atoms:
            return True
        center_x = sum(atom.x for atom in atoms) / len(atoms)
        center_y = sum(atom.y for atom in atoms) / len(atoms)
        center_z = sum(atom.z for atom in atoms) / len(atoms)
        return abs(center_x) <= tolerance and abs(center_y) <= tolerance and abs(center_z) <= tolerance

    def _selected_manipulator_path(self) -> Path:
        path = self.manipulator_source.currentData()
        if not path:
            raise ValueError("Load a structure before using the manipulator.")
        return Path(path)

    def _run_manipulation(self, command_builder):
        try:
            xyz_path = manipulate_xyz(self._selected_manipulator_path(), command_builder)
            atoms = read_xyz(xyz_path)
        except Exception as exc:
            QMessageBox.warning(self, "Could not manipulate structure", str(exc))
            return
        self._add_structure_tab(xyz_path.stem, atoms, xyz_path)

    def center_selected_structure(self):
        self._run_manipulation(lambda filename: ["-tc", filename])

    def mirror_selected_structure(self):
        try:
            mirror_path = manipulate_xyz(self._selected_manipulator_path(), lambda filename: ["-mirror", filename])
            xyz_path = manipulate_xyz(mirror_path, lambda filename: ["-tc", filename])
            atoms = read_xyz(xyz_path)
        except Exception as exc:
            QMessageBox.warning(self, "Could not create enantiomer", str(exc))
            return
        self._add_structure_tab(xyz_path.stem, atoms, xyz_path)

    def rotate_selected_structure(self):
        angle = self._fmt(self.rotate_angle.value())
        axis = self.rotate_axis.currentText()
        self._run_manipulation(lambda filename: ["-r1", angle, filename, "origin_CM_no", axis])

    def translate_selected_structure(self):
        distance = self._fmt(self.translate_distance.value())
        axis = self.translate_axis.currentText()
        self._run_manipulation(lambda filename: ["-t1", distance, filename, "origin_CM_no", axis])

    def translate_pair_selected_structures(self):
        fixed_path = self.pair_fixed_source.currentData()
        moving_path = self.pair_moving_source.currentData()
        if not fixed_path or not moving_path:
            QMessageBox.warning(self, "Controlled distance", "Load two structures before using controlled distance.")
            return
        try:
            fixed_xyz, translated_xyz = translate_pair_controlled_distance(
                Path(fixed_path),
                Path(moving_path),
                self.pair_distance.value(),
                self.pair_axis.currentText(),
            )
            fixed_atoms = read_xyz(fixed_xyz)
            translated_atoms = read_xyz(translated_xyz)
        except Exception as exc:
            QMessageBox.warning(self, "Could not translate pair", str(exc))
            return

        joint_atoms = fixed_atoms + translated_atoms
        min_distance = self._minimum_distance(fixed_atoms, translated_atoms)
        title = f"{Path(fixed_path).stem}+{translated_xyz.stem}"
        self._add_structure_tab(title, joint_atoms, None)
        canvas = self.tabs.currentWidget()
        if isinstance(canvas, VdwCanvas):
            canvas.setProperty("fixed_path", str(fixed_xyz))
            canvas.setProperty("translated_path", str(translated_xyz))
            canvas.setProperty("min_distance", min_distance)
            self._sync_current_tab_meta()

    def _minimum_distance(self, first: tuple[AtomRecord, ...], second: tuple[AtomRecord, ...]) -> float:
        min_distance = float("inf")
        for atom_a in first:
            for atom_b in second:
                distance = math.sqrt(
                    (atom_a.x - atom_b.x) ** 2
                    + (atom_a.y - atom_b.y) ** 2
                    + (atom_a.z - atom_b.z) ** 2
                )
                min_distance = min(min_distance, distance)
        return min_distance

    def _short_tab_title(self, title: str) -> str:
        return title if len(title) <= 40 else f"{title[:18]}...{title[-16:]}"

    def _sync_current_tab_meta(self):
        widget = self.tabs.currentWidget()
        if not widget:
            self.meta_label.setText("")
            return
        atom_count = widget.property("atom_count")
        min_distance = widget.property("min_distance")
        assembly_distance = widget.property("assembly_distance")
        au_count = widget.property("au_count")
        ag_count = widget.property("ag_count")
        parts = []
        if atom_count:
            parts.append(f"{atom_count} atoms")
        if au_count is not None:
            parts.append(f"Au {int(au_count)}")
        if ag_count is not None:
            parts.append(f"Ag {int(ag_count)}")
        if assembly_distance is not None:
            parts.append(f"distance {float(assembly_distance):.2f} Å")
        if min_distance is not None:
            parts.append(f"distance {float(min_distance):.2f} Å")
        self.meta_label.setText("  |  ".join(parts))

    def _generation_metadata(self) -> dict[str, object]:
        metadata: dict[str, object] = {}
        if self.dimer_check.isChecked():
            metadata["assembly_distance"] = self.dimer_distance.value()
        if self.bowtie_check.isChecked():
            metadata["assembly_distance"] = self.bowtie_distance.value()
        if self.alloy_check.isChecked():
            metadata["is_alloy"] = True
        return metadata

    def _metadata_for_generated_atoms(self, atoms: tuple[AtomRecord, ...]) -> dict[str, object]:
        metadata = dict(self.pending_generation_meta)
        if metadata.get("is_alloy"):
            counts: dict[str, int] = {}
            for atom in atoms:
                element = atom.element.capitalize()
                counts[element] = counts.get(element, 0) + 1
            metadata["au_count"] = counts.get("Au", 0)
            metadata["ag_count"] = counts.get("Ag", 0)
            metadata.pop("is_alloy", None)
        return metadata

    def _build_command_args(self) -> list[str]:
        atomtype = self.metal_combo.currentText()
        is_graphene = atomtype == "Graphene"
        structure = self.structure_combo.currentText()
        definition = STRUCTURES[structure] if not is_graphene else {"graphene": True}
        active_definition = GRAPHENE_VARIANTS[self.graphene_variant_combo.currentText()] if is_graphene else definition
        core_shell_active = (
            not is_graphene
            and atomtype in {"Au", "Ag"}
            and structure in {"Sphere", "Rod"}
            and self.core_shell_check.isChecked()
        )
        if core_shell_active and structure == "Sphere":
            active_definition = {
                "fields": (
                    ("core_radius", "Core radius", 20.0, 2.0, 300.0),
                    ("shell_radius", "Shell radius", 30.0, 3.0, 500.0),
                )
            }
        elif core_shell_active and structure == "Rod":
            active_definition = {
                "fields": (
                    ("core_length", "Core length", 20.0, 4.0, 500.0),
                    ("core_width", "Core width", 10.0, 2.0, 300.0),
                    ("shell_length", "Shell length", 50.0, 5.0, 700.0),
                    ("shell_width", "Shell width", 20.0, 3.0, 500.0),
                )
            }
        values = {field[0]: self.param_spins[index].value() for index, field in enumerate(active_definition["fields"])}
        if active_definition.get("graphene") == "rib":
            return ["-create", "-graphene", "rib", self._fmt(values["x_length"]), self._fmt(values["y_length"])]
        if active_definition.get("graphene") == "disk":
            return ["-create", "-graphene", "disk", self._fmt(values["radius"])]
        if active_definition.get("graphene") == "ring":
            if values["radius_in"] >= values["radius_out"]:
                raise ValueError("Graphene ring inner radius must be smaller than outer radius.")
            return ["-create", "-graphene", "ring", self._fmt(values["radius_out"]), self._fmt(values["radius_in"])]
        if active_definition.get("graphene") == "triangle":
            return [
                "-create",
                "-graphene",
                "triangle",
                self.graphene_edge_combo.currentText(),
                self._fmt(values["side_length"]),
            ]
        if core_shell_active:
            core_atom = self.core_atom.currentText()
            shell_atom = self.shell_atom.currentText()
            if core_atom == shell_atom:
                raise ValueError("Core and shell atom types must be different.")
            if structure == "Sphere":
                if values["core_radius"] >= values["shell_radius"]:
                    raise ValueError("Shell radius must be greater than core radius.")
                args = [
                    "-create",
                    definition["flag"],
                    "-core",
                    core_atom,
                    self._fmt(values["core_radius"]),
                    "-shell",
                    shell_atom,
                    self._fmt(values["shell_radius"]),
                ]
            else:
                if values["core_length"] >= values["shell_length"]:
                    raise ValueError("Shell length must be greater than core length.")
                if values["core_width"] >= values["shell_width"]:
                    raise ValueError("Shell width must be greater than core width.")
                args = [
                    "-create",
                    definition["flag"],
                    self.axis_combo.currentText(),
                    "-core",
                    core_atom,
                    self._fmt(values["core_length"]),
                    self._fmt(values["core_width"]),
                    "-shell",
                    shell_atom,
                    self._fmt(values["shell_length"]),
                    self._fmt(values["shell_width"]),
                ]
        else:
            args = ["-create", definition["flag"], atomtype]

        if core_shell_active:
            pass
        elif structure == "Sphere":
            args.append(self._fmt(values["radius"]))
        elif structure == "Rod":
            args.extend([self.axis_combo.currentText(), self._fmt(values["length"]), self._fmt(values["width"])])
        elif structure == "Tip":
            args.extend([self._fmt(values["z_max"]), self._fmt(values["a"]), self._fmt(values["b"])])
        elif structure == "Pyramid":
            args.extend([self._fmt(values["z_max"]), self._fmt(values["side"])])
        elif structure == "Cone":
            args.extend([self._fmt(values["z_max"]), self._fmt(values["radius"])])
        elif structure == "Microscope":
            args.extend([
                self._fmt(values["z_max_paraboloid"]),
                self._fmt(values["a"]),
                self._fmt(values["b"]),
                self._fmt(values["z_max_pyramid"]),
                self._fmt(values["side"]),
            ])
        elif structure in {"Icosahedron", "Cuboctahedron", "Decahedron"}:
            args.append(self._fmt(values["radius"]))
        else:
            raise ValueError(f'Structure "{structure}" is not supported.')

        if self.alloy_check.isChecked():
            if not core_shell_active and atomtype not in {"Ag", "Au"}:
                raise ValueError("Alloy generation is only available for Ag and Au.")
            if core_shell_active:
                args.extend(["-alloy", "-percentual", self._fmt(self.alloy_percent.value())])
            else:
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
        self._add_structure_tab(
            result.xyz_path.stem,
            result.atoms,
            result.xyz_path,
            self._metadata_for_generated_atoms(result.atoms),
        )
        self.pending_generation_meta = {}
        self.create_button.setEnabled(True)
        self.create_button.setText("Create structure")
        self.worker = None

    def _structure_failed(self, details: str):
        self.pending_generation_meta = {}
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
    logo_path = Path(__file__).resolve().parents[2] / "docs" / "_static" / "geom-logo-cloud.png"
    if not logo_path.exists():
        logo_path = Path(__file__).resolve().parents[2] / "docs" / "_static" / "geom-logo-desktop.png"
    if logo_path.exists():
        app.setWindowIcon(QIcon(str(logo_path)))
    window = StructureWindow()
    if logo_path.exists():
        window.setWindowIcon(QIcon(str(logo_path)))
    window.show()
    try:
        return app.exec()
    finally:
        cleanup_gui_tmp()


if __name__ == "__main__":
    raise SystemExit(main())
