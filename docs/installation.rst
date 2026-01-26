Installation
------------

GEOM requires **Python 3.8+** and the following dependencies:

- `gmsh==4.11.1`
- `ase==3.22.1`
- `numpy==1.24.3`
- `pytest==8.3.4`
- `launchpadlib==2.1.0`
- `pyautogen==0.2.18`
- `flaml[automl]==2.1.1`
- `httpx==0.27.2`
- `openai==1.3.8`
- `python-dotenv>=1.0.1`

Setting Up the Virtual Environment
GEOM uses **Conda** to set up a virtual environment for your project. To install it and set up your environment, run the following:
```
./install.sh
```

This script will:

 - Check if **Miniconda** or **Anaconda** is installed. If not, it will prompt you to install Miniconda.
 - Set up a virtual environment named geom_env with the necessary dependencies.
 - Configure environment variables and aliases for running **GEOM**.

