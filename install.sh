#!/bin/bash

set -e

ENV_NAME="geom_env"

echo " Setting up GEOM with conda environment..."

# Check for conda
if ! command -v conda &> /dev/null; then
    echo -e "\n Conda not found.\n"

    # Detect OS
    OS_TYPE="$(uname -s)"
    if [[ "$OS_TYPE" == "Linux" || "$OS_TYPE" == "Darwin" ]]; then
        read -p " Would you like to install Miniconda automatically? (y/N): " INSTALL_CONDA
        if [[ "$INSTALL_CONDA" =~ ^[Yy]$ ]]; then
            echo " Downloading Miniconda installer..."
            curl -L https://repo.anaconda.com/miniconda/Miniconda3-latest-$([[ $OS_TYPE == "Darwin" ]] && echo "MacOSX" || echo "Linux")-x86_64.sh -o miniconda.sh

            if [[ -d "$HOME/miniconda" ]]; then
                echo " Miniconda is already installed at $HOME/miniconda."
                read -p " Do you want to update it? (y/N): " UPDATE_MINICONDA
                if [[ "$UPDATE_MINICONDA" =~ ^[Yy]$ ]]; then
                    bash miniconda.sh -b -u -p $HOME/miniconda
                else
                    echo " Skipping Miniconda installation."
                fi
            else
                echo " Running Miniconda installer..."
                bash miniconda.sh -b -p $HOME/miniconda
            fi

            echo " Initializing conda..."
            eval "$($HOME/miniconda/bin/conda shell.bash hook)"
            $HOME/miniconda/bin/conda init

            export PATH="$HOME/miniconda/bin:$PATH"
            source "$HOME/.bashrc"
        else
            echo
            echo " Please install Conda manually from one of the following:"
            echo "  Anaconda (full): https://www.anaconda.com/products/distribution"
            echo "  Miniconda (lightweight): https://docs.conda.io/en/latest/miniconda.html"
            exit 1
        fi
    else
        echo " Please install Conda manually:"
        echo "  Anaconda (full): https://www.anaconda.com/products/distribution"
        echo "  Miniconda (lightweight): https://docs.conda.io/en/latest/miniconda.html"
        echo
        echo " After installing, restart your terminal and re-run this script."
        exit 1
    fi
fi

# Create conda environment if it doesn't exist
if conda info --envs | grep -q "^$ENV_NAME"; then
    echo " Conda environment '$ENV_NAME' already exists. Skipping creation."
else
    echo " Creating conda environment..."
    conda env create -f environment.yml
fi

echo " Installing Python package inside the conda environment..."
conda run -n $ENV_NAME python -m pip install --upgrade pip setuptools wheel
conda run -n $ENV_NAME python -m pip install gmsh==4.11.1
conda run -n $ENV_NAME python -m pip install --editable . --config-settings editable_mode=compat

# Set up shell function (manual activation)
SHELL_RC="$HOME/.bashrc"
if [[ "$SHELL" == *"zsh" ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == *"fish" ]]; then
    SHELL_RC="$HOME/.config/fish/config.fish"
fi

GEOM_LOAD_FUNCTION="function geom_load {
    conda activate $ENV_NAME
    alias geom='python -m geom'
}"

if ! grep -q "function geom_load" "$SHELL_RC"; then
    echo "Adding geom_load function to $SHELL_RC..."
    echo -e "\\n$GEOM_LOAD_FUNCTION" >> "$SHELL_RC"
fi

echo " Running tests..."
conda run -n $ENV_NAME bash ./geom/tests/run_all_tests.sh || echo " Some tests failed."

echo -e "\n  Installation complete!\n"
echo -e "  Run: source $SHELL_RC"
echo -e "  Then load the environment with: geom_load"
echo -e "  And run the CLI using: geom -h"

