# GEOM – Geometry File Management

**GEOM** is a command-line tool for creating, modifying, and analyzing XYZ geometry files. It provides **geometry transformations, nanoparticle generation, and graphene structure creation** for computational research.

**[View the Documentation](https://geom-grobas.readthedocs.io/en/branch-v1.0.0)**

<p align="center">
  <img src="https://raw.githubusercontent.com/pgrobasillobre/geom/master/docs/_static/geom-logo.png" width="600">
</p>


## Features

- **Geometry Transformations**: Translation, rotation, merging, and specular (mirror) transformations.
- **Nanoparticle Generation**: Sphere, rod, core-shell, tip, pyramid, cone, icosahedron, and more.
- **Graphene Structures**: Ribbons, disks, rings, and triangles.
- **Advanced Options**: Alloying, dimer formation, and bowtie configurations.
- **Minimum Distance Calculation** between XYZ geometries.
- **Geometrical Center Computation**.

## Installation

GEOM requires **Python 3.6+** and the following dependencies:

- `gmsh==4.11.1`
- `ase==3.22.1`
- `numpy==1.24.3`
- `pytest==8.3.4`
- `launchpadlib==2.1.0`

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

## Running Tests

The `./install.sh` script automatically runs tests to ensure everything is set up correctly.


To manually run the tests again:

```
./geom/tests/run_all_tests.sh
```

## License

GEOM is licensed under the **GNU General Public License v3.0**.

## Funding

This project has been supported by the **FARE 2020** program — *"Framework per l’attrazione e il rafforzamento delle eccellenze per la ricerca in Italia."*

## Contact

For issues or contributions:

- Email: **pgrobasillobre@gmail.com**
- Github issues: https://github.com/pgrobasillobre/geom/issues
