Installation
------------

GEOM requires **Python 3.6+** and the following dependencies:

- gmsh==4.11.1
- ase==3.22.1
- numpy==1.24.3
- pytest==8.3.4
- launchpadlib==2.1.0

To set up your environment, run the following script:

```
./install.sh
```

This script will:
- Check if **Miniconda** or **Anaconda** is installed. If not, it will prompt you to install Miniconda.
- Set up a Conda virtual environment named **geom_env** with the necessary dependencies.
- Configure environment variables and aliases for running **GEOM**.

Activate the Environment
-------------------------

After running the install.sh script, you need to load the GEOM environment:

```
geom_load
```


This will activate the **Conda environment**, set up the necessary aliases, and configure the environment variables needed to run **GEOM**.


