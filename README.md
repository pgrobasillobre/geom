# GEOM – Geometry File Management

**GEOM** is a tool for creating, modifying, and analyzing XYZ geometry files. It provides **geometry transformations, nanoparticle generation, and graphene structure creation** for computational research, with both a command-line interface and a native desktop GUI.

**[View the Documentation](https://geom-grobas.readthedocs.io/en/branch-v2.1.0)**

<p align="center">
  <img src="https://raw.githubusercontent.com/pgrobasillobre/geom/master/docs/_static/geom-logo-rdkit.png" width="600">
</p>


## Features

- **GEOM Structure Studio**: native desktop GUI for interactive nanoparticle and graphene generation, 3D visualization, and structure manipulation.
- **RDKit tools**: molecular visualization, file conversion, force field optimization, and conformers generation.
- **AI Assistant for nanoparticle and graphene creation**
- **Geometry Transformations**: Translation, rotation, merging, and specular (mirror) transformations.
- **Nanoparticle Generation**: Sphere, rod, core-shell, tip, pyramid, cone, icosahedron, and more.
- **Graphene Structures**: Ribbons, disks, rings, and triangles.
- **Advanced Options**: Alloying, dimer formation, and bowtie configurations.
- **Minimum Distance Calculation** between XYZ geometries.
- **Geometrical Center Computation**.


## Installation

GEOM requires **Python 3.8+**. All dependencies are managed by conda via `environment.yml`.

### Set up the environment

```

Quick sanity check:

```bash
python -c "import geom; print('geom imported OK')"
geom -h
```

### Option B — Install via Conda (recommended for full scientific setups)

GEOM uses **Conda** to set up a virtual environment for your project. To install it and set up your environment, run:

```bash
./install.sh
```

This script will:

- Check if **Miniconda** or **Anaconda** is installed. If not, it will prompt you to install Miniconda.
- Set up a conda environment named `geom_env` with all dependencies.
- Configure shell aliases for running GEOM.
- Build the **GEOM Structure Studio** desktop app (macOS and Linux/WSL).


## Quick Start

Load the GEOM environment:

```
geom_load
```

See all available options:

```
geom -h
```

Example commands:

- **RDKit conformers generation**
```
geom -rdkit -i tyrosine.mol -confs
```

- **RDKit file conversion**
```
geom -rdkit -i tyrosine.mol -o tyrosine.pdb
```

- **Rotate geometry 90 degrees** around the Y-axis:
```
geom -r1 90 geom.xyz origin_CM_yes +y
```

- **Generate a nanoparticle sphere:**
```
geom -create -sphere Ag 30
```

- **Generate a graphene ribbon:**
```
geom -create -graphene rib 50 20
```


## GEOM Structure Studio

GEOM includes a native desktop GUI — **GEOM Structure Studio** — for interactive nanoparticle and graphene creation, 3D visualization, and structure manipulation.

### Launch

- **Terminal** — load the environment with `geom_load`, then run `geomapp`.
- **macOS** — open `~/Applications/GEOM.app` directly from Finder or Spotlight.
- **Linux / WSL** — open GEOM from your desktop application launcher (the installer registers a `.desktop` entry).

### What you can do

- **Generator** — create nanoparticles (sphere, rod, tip, pyramid, cone, icosahedron, and more) and graphene structures (disk, ribbon, ring, triangle) with interactive parameter controls. Supports alloy, dimer, bowtie, and core-shell configurations.
- **Viewer** — load XYZ, PDB, or SMILES structures via file picker or drag-and-drop. Interactive 3D view with VdW/CPK rendering, atom selection expressions (`x > 0 and name C`), and adjustable sphere size, bond width, and resolution.
- **Manipulator** — translate, rotate, mirror (enantiomer), and center structures. Pair mode sets a controlled distance between two loaded structures along any axis.

<p align="center">
  <img src="https://raw.githubusercontent.com/pgrobasillobre/geom/branch-v2.1.0/docs/_static/geomapp.png" width="800">
</p>


## Starting the AI Assistant

GEOM includes an **AI-powered assistant** that understands natural language, translates it into valid GEOM CLI commands, and executes them automatically.

This assistant is built using [Microsoft's AutoGen framework](https://github.com/microsoft/autogen), which enables a multi-agent system to interface with OpenAI's language models and run commands dynamically.

### 1. Export your OpenAI API key

```
export OPENAI_API_KEY=your-api-key-here
```

> Obtain an API key at https://platform.openai.com/account/api-keys

### 2. Start the assistant

```
ai_geom
```

<p align="center">
  <img src="https://raw.githubusercontent.com/pgrobasillobre/geom/master/docs/_static/ai_assistant.png" width="600">
</p>

The assistant will automatically create and execute the corresponding GEOM command for you.


## Running Tests

Tests run automatically during installation. To run them manually:

```
./geom/tests/run_all_tests.sh
```


## License

GEOM is licensed under the **GNU General Public License v3.0**.


## Funding

This project has been supported by the **FARE 2020** program — *"Framework per l'attrazione e il rafforzamento delle eccellenze per la ricerca in Italia."*


## Publications

GEOM has been used in the following research paper(s):

- Giovannini, T.; **Grobas Illobre, P.**; Lafiosca, P.; Nicoli, L.; Bonatti, L.; Corni, S.; Cappelli, C. *plasmonX: an Open-Source Code for Nanoplasmonics.* **Comput. Phys. Commun.** *2026*, **110035**. https://doi.org/10.1016/j.cpc.2026.110035


## Contact

For issues or contributions:

- Email: **pgrobasillobre@gmail.com**
- Github issues: https://github.com/pgrobasillobre/geom/issues
