#!/bin/bash

echo -e "This script will install dependencies and may modify or break system packages."
echo "If you prefer, you can manually install dependencies by running:"
echo "    python3 -m venv geom_venv && source geom_venv/bin/activate"
echo "    pip install --upgrade pip && pip install -r requirements.txt"
echo
echo "Press Ctrl+C to cancel or wait 5 seconds to continue..."
sleep 5

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
    echo "Error: Python3 is not installed. Please install it manually from https://www.python.org/downloads/"
    exit 1
else
    echo "Python3 is already installed."
fi

# Check if pip3 is installed
if ! command_exists pip3; then
    echo "Error: pip3 is not installed. Attempting to install..."
    sudo apt update && sudo apt install -y python3-pip || { echo "Failed to install pip3. Please install it manually."; exit 1; }
else
    echo "pip3 is already installed."
fi

# Install the required dependencies system-wide
echo "Installing dependencies globally..."
pip3 install --upgrade pip  # Ensure pip is up-to-date
pip3 install --break-system-packages -r requirements.txt

# Append the geom_load function to the shell's configuration file for automatic setup
SHELL_RC="$HOME/.bashrc"  # Change this if using another shell like zsh

# Define the geom_load function
GEOM_LOAD_FUNCTION="function geom_load {
    export PYTHONPATH=\"$PWD:\$PYTHONPATH\"
    alias geom=\"python3 -m geom\"
}"

# Check if geom_load is already in the shell config, if not, add it
if ! grep -q "function geom_load" "$SHELL_RC"; then
    echo "Adding geom_load function to $SHELL_RC..."
    echo -e "\n$GEOM_LOAD_FUNCTION" >> "$SHELL_RC"
fi

# Inform the user about sourcing the shell configuration file
echo "To apply changes, run the following command based on your shell:"
if [ "$SHELL" = "/bin/zsh" ]; then
    echo "source ~/.zshrc"
elif [ "$SHELL" = "/bin/bash" ]; then
    echo "source ~/.bashrc"
elif [ "$SHELL" = "/bin/fish" ]; then
    echo "source ~/.config/fish/config.fish"
else
    echo "source ~/.profile"
fi

# Final message
echo -e "\n\033[1;32mInstallation complete!\033[0m"
echo -e "\nYou can now run \`geom_load\` to set up your environment, and \`geom -h\` to check available options."
