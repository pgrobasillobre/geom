"""Programmatic structure generation helpers used by the native GUI."""

from __future__ import annotations

import subprocess
import shutil
import sys
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from geom.classes.parameters import parameters


_GENERATION_LOCK = threading.Lock()
_CONVERSION_LOCK = threading.Lock()
GUI_TMP_ROOT = Path(__file__).resolve().parent / "tmp"


@dataclass(frozen=True)
class AtomRecord:
    element: str
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class StructureResult:
    xyz_path: Path
    atoms: tuple[AtomRecord, ...]
    command: tuple[str, ...]

    @property
    def atom_count(self) -> int:
        return len(self.atoms)


def supported_metals(arrangements: set[str] | None = None) -> list[str]:
    """Return metals supported by GEOM, optionally filtered by crystal arrangement."""

    param = parameters()
    return [
        atom.capitalize()
        for atom in param.metal_atomtypes
        if atom != "c" and (arrangements is None or param.atomic_arrangement.get(atom) in arrangements)
    ]


def supported_atomistic_metals() -> list[str]:
    """Return FCC/BCC metals supported by the bulk-lattice atomistic generators."""

    return supported_metals({"FCC", "BCC"})


def supported_fcc_metals() -> list[str]:
    """Return FCC metals used by the ASE cluster generators."""

    return supported_metals({"FCC"})


def generate_structure(command_args: list[str], output_root: Path) -> StructureResult:
    """Run GEOM's existing CLI generator and return the newest generated XYZ file."""

    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    results_dir = output_root / "results_geom"
    before = _xyz_snapshot(results_dir)
    runner = (
        "import sys; "
        "from geom.classes import input_class; "
        "from geom.functions import general, create_geom; "
        "inp = input_class.input_class(); "
        "general.read_command_line(['geom', *sys.argv[1:]], inp); "
        "create_geom.select_case(inp)"
    )
    command = (sys.executable, "-c", runner, *command_args)

    with _GENERATION_LOCK:
        completed = subprocess.run(
            command,
            cwd=output_root,
            text=True,
            capture_output=True,
            check=False,
        )

    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "GEOM command failed."
        raise RuntimeError(message)

    xyz_path = _newest_generated_xyz(results_dir, before)
    return StructureResult(xyz_path=xyz_path, atoms=read_xyz(xyz_path), command=tuple(command))


def convert_molecule_to_xyz(input_path: Path) -> Path:
    """Convert a PDB/SMI-like molecule file to XYZ through GEOM's RDKit command path."""

    input_path = Path(input_path)
    if input_path.suffix.lower() == ".xyz":
        return input_path

    GUI_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    results_dir = GUI_TMP_ROOT / "results_geom"
    before = _xyz_snapshot(results_dir)
    output_name = f"{input_path.stem}_{uuid.uuid4().hex[:8]}.xyz"
    runner = (
        "import sys; "
        "from geom.classes import input_class; "
        "from geom.functions import general, rdkit_module; "
        "inp = input_class.input_class(); "
        "general.read_command_line(['geom', *sys.argv[1:]], inp); "
        "rdkit_module.select_case(inp)"
    )
    command = (
        sys.executable,
        "-c",
        runner,
        "-rdkit",
        "-i",
        str(input_path),
        "-o",
        output_name,
    )

    with _CONVERSION_LOCK:
        completed = subprocess.run(
            command,
            cwd=GUI_TMP_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "GEOM RDKit conversion failed."
        raise RuntimeError(message)

    expected = results_dir / output_name
    return expected if expected.exists() else _newest_generated_xyz(results_dir, before)


def smiles_to_xyz(smiles: str) -> Path:
    """Write a SMILES string into GEOM's GUI temp folder and convert it to XYZ."""

    smiles = smiles.strip()
    if not smiles:
        raise ValueError("Enter a SMILES string first.")

    input_dir = GUI_TMP_ROOT / "smiles"
    input_dir.mkdir(parents=True, exist_ok=True)
    smi_path = input_dir / f"smiles_{uuid.uuid4().hex[:8]}.smi"
    smi_path.write_text(smiles + "\n", encoding="utf-8")
    return convert_molecule_to_xyz(smi_path)


def manipulate_xyz(input_path: Path, command_args: Callable[[str], list[str]]) -> Path:
    """Run an existing GEOM manipulation command in the GUI temp folder."""

    input_path = Path(input_path)
    if input_path.suffix.lower() != ".xyz":
        raise ValueError("GEOM manipulation requires an XYZ file.")

    GUI_TMP_ROOT.mkdir(parents=True, exist_ok=True)
    results_dir = GUI_TMP_ROOT / "results_geom"
    before = _xyz_snapshot(results_dir)
    local_input = GUI_TMP_ROOT / f"{input_path.stem}_{uuid.uuid4().hex[:8]}.xyz"
    shutil.copy2(input_path, local_input)

    runner = (
        "import sys; "
        "from geom.classes import input_class; "
        "from geom.functions import general, translate, rotate; "
        "inp = input_class.input_class(); "
        "general.read_command_line(['geom', *sys.argv[1:]], inp); "
        "translate.select_case(inp) if inp.translate else rotate.select_case(inp)"
    )
    command = (sys.executable, "-c", runner, *command_args(local_input.name))

    with _CONVERSION_LOCK:
        completed = subprocess.run(
            command,
            cwd=GUI_TMP_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "GEOM manipulation failed."
        raise RuntimeError(message)

    return _newest_generated_xyz(results_dir, before)


def cleanup_gui_tmp() -> None:
    """Remove GUI-generated temporary conversion files."""

    if GUI_TMP_ROOT.exists():
        shutil.rmtree(GUI_TMP_ROOT)


def _xyz_snapshot(results_dir: Path) -> dict[Path, int]:
    if not results_dir.exists():
        return {}
    return {path: path.stat().st_mtime_ns for path in results_dir.glob("*.xyz")}


def _newest_generated_xyz(results_dir: Path, before: dict[Path, int]) -> Path:
    candidates = []
    if results_dir.exists():
        for path in results_dir.glob("*.xyz"):
            mtime = path.stat().st_mtime_ns
            if before.get(path) != mtime:
                candidates.append(path)

    if not candidates and results_dir.exists():
        candidates = list(results_dir.glob("*.xyz"))

    if not candidates:
        raise RuntimeError("GEOM finished without producing an XYZ file.")

    return max(candidates, key=lambda path: path.stat().st_mtime_ns)


def read_xyz(path: Path) -> tuple[AtomRecord, ...]:
    """Read the atom records from an XYZ file."""

    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()

    if len(lines) < 2:
        raise ValueError(f'Invalid XYZ file "{path}".')

    try:
        expected_atoms = int(lines[0].strip())
    except ValueError as exc:
        raise ValueError(f'Invalid atom count in "{path}".') from exc

    atoms: list[AtomRecord] = []
    for line in lines[2:]:
        parts = line.split()
        if len(parts) < 4:
            continue
        atoms.append(AtomRecord(parts[0], float(parts[1]), float(parts[2]), float(parts[3])))

    if len(atoms) != expected_atoms:
        raise ValueError(f'XYZ atom count mismatch in "{path}": expected {expected_atoms}, got {len(atoms)}.')

    return tuple(atoms)
