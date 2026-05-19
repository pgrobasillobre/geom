"""Programmatic structure generation helpers used by the native GUI."""

from __future__ import annotations

import os
import shutil
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from geom.classes.input_class import input_class
from geom.classes.parameters import parameters
from geom.functions import create_geom


_GENERATION_LOCK = threading.Lock()


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

    @property
    def atom_count(self) -> int:
        return len(self.atoms)


@contextmanager
def _working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def supported_sphere_metals() -> list[str]:
    """Return FCC/BCC metals supported by the bulk-lattice sphere generator."""

    param = parameters()
    return [
        atom.capitalize()
        for atom in param.metal_atomtypes
        if param.atomic_arrangement.get(atom) in {"FCC", "BCC"}
    ]


def generate_sphere(atomtype: str, radius: float, output_root: Path | None = None) -> StructureResult:
    """Create a GEOM metallic sphere and return the generated XYZ path and atoms."""

    atomtype = atomtype.lower().strip()
    radius = float(radius)
    output_root = Path.cwd() if output_root is None else Path(output_root)

    param = parameters()
    if atomtype not in param.metal_atomtypes:
        raise ValueError(f'Atom type "{atomtype}" is not supported by GEOM.')
    if param.atomic_arrangement.get(atomtype) not in {"FCC", "BCC"}:
        raise ValueError(f'Atom type "{atomtype.capitalize()}" is not supported for sphere generation.')
    if radius <= 0:
        raise ValueError("Radius must be greater than zero.")

    inp = input_class()
    inp.create_geom = True
    inp.create_ase_bulk = True
    inp.gen_sphere = True
    inp.atomtype = atomtype
    inp.radius = radius
    inp.sphere_center = [0.0, 0.0, 0.0]

    with _GENERATION_LOCK:
        with _working_directory(output_root):
            create_geom.create_ase_bulk_metal(inp, str(output_root))
            try:
                create_geom.sphere(inp)
            finally:
                if inp.tmp_folder and os.path.exists(inp.tmp_folder):
                    shutil.rmtree(inp.tmp_folder)

        xyz_path = output_root / "results_geom" / f"{inp.xyz_output}.xyz"

    return StructureResult(xyz_path=xyz_path, atoms=read_xyz(xyz_path))


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

