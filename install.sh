#!/bin/bash

echo -e "This script will install dependencies and set up the GEOM project using Python 3 only."
echo "If you prefer, you can install dependencies manually with:"
echo "    python3 -m venv geom_venv && source geom_venv/bin/activate"
echo "    pip install --upgrade pip && pip install -r requirements.txt"
echo
echo "Press Ctrl+C to cancel or wait 5 seconds to continue..."
sleep 5

echo "Setting up GEOM project with Python 3..."

# Ensure the script stops on any error
set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS type
OS_TYPE="$(uname -s)"
if [[ "$OS_TYPE" == "Darwin" ]]; then
    OS="macOS"
elif [[ "$OS_TYPE" == "Linux" ]]; then
    if grep -qi microsoft /proc/version; then
        OS="WSL"
    elif command_exists apt; then
        OS="Debian"
    elif command_exists dnf; then
        OS="Fedora"
    else
        OS="Linux-Other"
    fi
elif [[ "$OS_TYPE" =~ "MINGW" || "$OS_TYPE" =~ "CYGWIN" || "$OS_TYPE" =~ "MSYS" ]]; then
    OS="Windows"
else
    echo "Unsupported OS: $OS_TYPE"
    exit 1
fi

echo "Detected OS: $OS"

# Install Python 3 and Pip 3
if [[ "$OS" == "macOS" ]]; then
    echo "Using Homebrew to install Python 3..."
    if ! command_exists brew; then
        echo "Error: Homebrew is not installed. Install it from https://brew.sh/"
        exit 1
    fi
    if ! command_exists python3; then
        brew install python
    fi
    python3 -m pip install --upgrade pip setuptools wheel

elif [[ "$OS" == "Debian" || "$OS" == "WSL" ]]; then
    echo "Using APT to install Python 3..."
    sudo apt update
    sudo apt install -y python3 python3-pip
    python3 -m pip install --upgrade pip setuptools wheel

elif [[ "$OS" == "Fedora" ]]; then
    echo "Using DNF to install Python 3..."
    sudo dnf install -y python3 python3-pip
    python3 -m pip install --upgrade pip setuptools wheel

elif [[ "$OS" == "Windows" ]]; then
    echo "Using Windows package manager to install Python 3..."
    if ! command_exists python3; then
        echo "Installing Python 3 using winget..."
        winget install -e --id Python.Python
    fi
    python3 -m pip install --upgrade pip setuptools wheel

else
    echo "Unsupported Linux distribution. Please install Python 3 manually."
    exit 1
fi

# Ensure Python 3 is used
echo "Ensuring Python 3 is the default version..."
if command_exists python && [[ "$(python --version 2>&1)" =~ "Python 2" ]]; then
    echo "Warning: Python 2 detected. It is recommended to remove it."
    sudo apt remove -y python python-pip
fi

# Install project dependencies
echo "Installing Python dependencies..."
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -r requirements.txt

# Install Gmsh for Python 3
echo "Installing Gmsh for Python 3..."
python3 -m pip install --upgrade gmsh

# Check if Gmsh library is available
if ! python3 -c "import gmsh" 2>/dev/null; then
    echo "Error: Gmsh Python library is not found. Please check your installation."
    exit 1
fi

# Ensure the shared library is correctly linked
echo "Checking Gmsh shared library..."
if ! find /usr/lib /usr/local/lib -name "libgmsh.so*" | grep -q libgmsh; then
    echo "Warning: libgmsh.so is missing. You may need to manually set up library paths."
    echo "/usr/local/lib" | sudo tee -a /etc/ld.so.conf.d/gmsh.conf
    sudo ldconfig
fi

# Determine the correct shell configuration file
if [[ "$OS" == "Windows" ]]; then
    SHELL_RC="$HOME/Documents/PowerShell/Microsoft.PowerShell_profile.ps1"
elif [[ "$SHELL" == "/bin/zsh" ]]; then
    SHELL_RC="$HOME/.zshrc"
elif [[ "$SHELL" == "/bin/bash" ]]; then
    SHELL_RC="$HOME/.bashrc"
elif [[ "$SHELL" == "/bin/fish" ]]; then
    SHELL_RC="$HOME/.config/fish/config.fish"
else
    SHELL_RC="$HOME/.profile"
fi

# Define the geom_load function
GEOM_LOAD_FUNCTION="function geom_load {
    export PYTHONPATH=\"$PWD:\$PYTHONPATH\"
    alias geom=\"python3 -m geom\"
}"

# Add geom_load function if not already present
if ! grep -q "function geom_load" "$SHELL_RC"; then
    echo "Adding geom_load function to $SHELL_RC..."
    echo -e "\n$GEOM_LOAD_FUNCTION" >> "$SHELL_RC"
fi

# Run tests
if [ -f "./geom/tests/run_all_tests.sh" ]; then
    echo "Running tests..."
    chmod +x ./geom/tests/run_all_tests.sh
    ./geom/tests/run_all_tests.sh
else
    echo "No test script found at ./geom/tests/run_all_tests.sh. Skipping tests."
fi

# Final message
echo -e "\n\033[1;32m✔ Installation complete!\033[0m"
echo -e "\n\033[1;34m➡ Before using \`geom\`, you must first run:\033[0m"
echo -e "\033[1;33msource $SHELL_RC\033[0m   \033[0;37m# This sets up your environment\033[0m"
echo -e "\n\033[1;34m➡ After that, you can use:\033[0m"
echo -e "\033[1;33mgeom_load\033[0m   \033[0;37m# Loads the environment to use \`geom\` as a command\033[0m"
echo -e "\033[1;33mgeom -h\033[0m   \033[0;37m  # Shows available options\033[0m"
echo -e "\n\033[1;34m➡ Alternatively, you can always run:\033[0m"
echo -e "\033[1;33mpython3 -m geom -h\033[0m   \033[0;37m# Runs GEOM without loading the environment\033[0m\n"

