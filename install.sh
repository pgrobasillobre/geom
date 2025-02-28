#!/bin/bash

echo "Setting up GEOM project..."

# Ensure the script stops on any error
set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS type
OS_TYPE="$(uname -s)"

# Check if Python3 is installed
if ! command_exists python3; then
    echo "Error: Python3 is not installed. Please install Python3 manually from https://www.python.org/downloads/."
    exit 1
else
    echo "Python3 is already installed."
fi

# Check if pip3 is installed
if ! command_exists pip3; then
    echo "Error: pip3 is not installed. Please install pip3 manually."
    exit 1
else
    echo "pip3 is already installed."
fi

# Install required dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Append geom_load function to shell configuration file
if [ "$SHELL" = "/bin/zsh" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ "$SHELL" = "/bin/bash" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ "$SHELL" = "/bin/fish" ]; then
    SHELL_RC="$HOME/.config/fish/config.fish"
else
    SHELL_RC="$HOME/.profile"
fi

# Define the path and geom_load function
GEOM_PATH="$(dirname "$(realpath "$0")")"
GEOM_LOAD_FUNCTION="function geom_load {\n    export PYTHONPATH=\"$GEOM_PATH:\$PYTHONPATH\"\n    alias geom=\"python3 -m geom\"\n}"

# Check if the function geom_load is already in the shell config
if ! grep -q "function geom_load" "$SHELL_RC"; then
    echo "Adding geom_load function to $SHELL_RC..."
    echo -e "\n$GEOM_LOAD_FUNCTION" >> "$SHELL_RC"
fi

# Run tests if available
if [ -f "./geom/tests/run_all_tests.sh" ]; then
    echo "Running tests..."
    chmod +x ./geom/tests/run_all_tests.sh
    ./geom/tests/run_all_tests.sh
    if [ $? -ne 0 ]; then
        echo "Tests failed. Aborting installation."
        exit 1
    fi
else
    echo "No test script found at ./geom/tests/run_all_tests.sh. Skipping tests."
fi

# Source the shell configuration to apply the changes immediately
echo "Applying changes to your shell configuration..."

# Source the shell config file to apply the changes in the current shell
source "$SHELL_RC"

# Highlighting the final instructions with color and spacing
echo -e "\n\n\033[1;32mInstallation complete!\033[0m"

echo -e "\n\033[1;33mIf 'geom_load' doesn't work right away, please run the following command based on your shell:\033[0m"

if [ "$SHELL" = "/bin/zsh" ]; then
    echo -e "\n\033[1;34mRun: source ~/.zshrc\033[0m"
elif [ "$SHELL" = "/bin/bash" ]; then
    echo -e "\n\033[1;34mRun: source ~/.bashrc\033[0m"
elif [ "$SHELL" = "/bin/fish" ]; then
    echo -e "\n\033[1;34mRun: source ~/.config/fish/config.fish\033[0m"
else
    echo -e "\n\033[1;34mRun: source ~/.profile\033[0m"
fi

echo -e "\n\033[1;33mThen, you can run 'geom_load' to set up your environment and 'geom -h' to check the help menu for available options.\033[0m"

