#!/bin/bash

set -e

ENV_NAME="geom_env"

echo " Setting up GEOM with conda environment..."

# Check for conda
if ! command -v conda &> /dev/null; then
    echo -e "\n Conda was not found in your system."

    # Check if Miniconda is already installed
    if [[ -x "$HOME/miniconda/bin/conda" ]]; then
        echo " Detected Miniconda installed at $HOME/miniconda. Using it."
        export PATH="$HOME/miniconda/bin:$PATH"
        eval "$($HOME/miniconda/bin/conda shell.bash hook)"
    else
        echo " Conda is required to continue."
        echo " You can install it manually from:"
        echo "   Anaconda (full): https://www.anaconda.com/products/distribution"
        echo "   Miniconda (lightweight): https://docs.conda.io/en/latest/miniconda.html"
        echo
        read -p " Would you like to automatically install Miniconda now? (y/N): " INSTALL_MINICONDA
        if [[ "$INSTALL_MINICONDA" =~ ^[Yy]$ ]]; then
            OS_TYPE="$(uname -s)"
            echo " Downloading Miniconda installer..."
            curl -L https://repo.anaconda.com/miniconda/Miniconda3-latest-$([[ $OS_TYPE == "Darwin" ]] && echo "MacOSX" || echo "Linux")-x86_64.sh -o miniconda.sh

            echo " Running Miniconda installer..."
            bash miniconda.sh -b -p "$HOME/miniconda"

            echo " Initializing Miniconda..."
            export PATH="$HOME/miniconda/bin:$PATH"
            eval "$($HOME/miniconda/bin/conda shell.bash hook)"
            "$HOME/miniconda/bin/conda" init
            source "$HOME/.bashrc"
        else
            echo " Installation aborted. Please install Conda manually and re-run this script."
            exit 1
        fi
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

# Set up shell config file
SHELL_RC="$HOME/.bashrc"
if [[ "$SHELL" == *"zsh" ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == *"fish" ]]; then
    SHELL_RC="$HOME/.config/fish/config.fish"
fi

# Add conda init and geom_load if missing
if ! grep -q "conda initialize" "$SHELL_RC"; then
    echo "Adding conda init block to $SHELL_RC..."
    cat << 'EOF' >> "$SHELL_RC"
# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('$HOME/miniconda/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "$HOME/miniconda/etc/profile.d/conda.sh" ]; then
        . "$HOME/miniconda/etc/profile.d/conda.sh"
    else
        export PATH="$HOME/miniconda/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<
EOF
fi

if ! grep -q "function geom_load" "$SHELL_RC"; then
    echo "Adding geom_load function to $SHELL_RC..."
    
    MAIN_PATH="$(realpath ./geom/ai_agent/desktop_chat_qt.py)"
    ENV_PYTHON="$(conda run -n $ENV_NAME which python)"

    cat << EOF >> "$SHELL_RC"

function geom_load {
    conda activate geom_env
    alias geom='$ENV_PYTHON -m geom'
    alias ai_geom='$ENV_PYTHON $MAIN_PATH'
}
EOF
fi

echo " Running tests..."
conda run -n $ENV_NAME bash ./geom/tests/run_all_tests.sh || echo " Some tests failed."

echo  "  Installation complete!"
echo  " "
echo  "  Run: source $SHELL_RC"
echo  "  Then load the environment with: geom_load"
echo  " "
echo  "  Check GEOM options using: geom -h"
echo  " "
