# GEOM – Geometry File Management

**GEOM** is a command-line tool for creating, modifying, and analyzing XYZ geometry files. It provides **geometry transformations, nanoparticle generation, and graphene structure creation** for computational research.

**[View the Documentation](https://geom-grobas.readthedocs.io/en/branch-v1.1.0)**

<p align="center">
  <img src="https://raw.githubusercontent.com/pgrobasillobre/geom/ai_agent/docs/_static/geom-logo-autogen.png" width="600">
</p>


## Features

- **AI Assistant for nanoparticle and graphene creation** *(new in v1.1.0)*
- **Geometry Transformations**: Translation, rotation, merging, and specular (mirror) transformations.
- **Nanoparticle Generation**: Sphere, rod, core-shell, tip, pyramid, cone, icosahedron, and more.
- **Graphene Structures**: Ribbons, disks, rings, and triangles.
- **Advanced Options**: Alloying, dimer formation, and bowtie configurations.
- **Minimum Distance Calculation** between XYZ geometries.
- **Geometrical Center Computation**.

## Installation

GEOM requires **Python 3.8+** and the following dependencies:

- `gmsh==4.11.1`
- `ase==3.22.1`
- `numpy==1.24.3`
- `pytest==8.3.4`
- `launchpadlib==2.1.0`
- `pyautogen==0.2.18`
- `flaml[automl]==2.1.1`
- `httpx==0.27.2`

### Setting Up the Virtual Environment
GEOM uses **Conda** to set up a virtual environment for your project. To install it and set up your environment, run the following:
```bash
./install.sh
```

This script will:

 - Check if **Miniconda** or **Anaconda** is installed. If not, it will prompt you to install Miniconda.
 - Set up a virtual environment named geom_env with the necessary dependencies.
 - Configure environment variables and aliases for running **GEOM**.

## Activate the Environment

After installation, load the GEOM environment by running:

```
geom_load
```

This will set the necessary aliases and environment variables to run the tool properly.

Once the environment is set up, run the following command to see the available options:

```
geom -h
```

This will display the help menu with all the available commands and their descriptions.

Example commands:

- **Rotate geometry 90 degrees** around the Y-axis:

```
geom -r1 90 geom.xyz origin_CM_yes +y
```

- Generate a nanoparticle sphere:

```
geom -create -sphere Ag 30
```

- Generate a graphene ribbon: 

```
geom -create -graphene rib 50 20
```

## Starting the AI Assistant *(new in v1.1.0)*

GEOM now includes an **AI assistant** that understands natural language, translates it into valid GEOM CLI commands, and automatically executes them.

### 1. Export your OpenAI API key

The assistant requires access to **OpenAI's LLMs**. Make sure you have an API key:

```bash
export OPENAI_API_KEY=your-api-key-here
```

> You can obtain an API key from https://platform.openai.com/account/api-keys

### 2. Start the assistant

To launch the chat-based assistant, load the GEOM environment (i.e., `geom_load`) and run:

```bash
ai_geom
```

You can then type natural-language requests like:

```
Create a gold nanorod that is 40 angstroms long and 10 angstroms wide along the z axis.
```

The assistant will automatically create and execute the corresponding GEOM command for you.


## Running Tests

The `./install.sh` script automatically runs tests to ensure everything is set up correctly.


To manually run the tests again:

```
./geom/tests/run_all_tests.sh
```

## License

GEOM is licensed under the **GNU General Public License v3.0**.

## Contact

For issues or contributions:

- Email: **pgrobasillobre@gmail.com**
- Github issues: https://github.com/pgrobasillobre/geom/issues
