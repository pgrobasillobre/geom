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

# Install Python3 if missing
if ! command_exists python3; then
    echo "Python3 is not installed. Installing..."
    case "$OS_TYPE" in
        Linux*)
            sudo apt update && sudo apt install -y python3 || sudo dnf install -y python3
            ;;
        Darwin*)
            echo "Installing Python3 using Homebrew..."
            if ! command_exists brew; then
                echo "Homebrew not found. Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install python3
            ;;
        MINGW* | MSYS* | CYGWIN*)
            echo "Please install Python3 manually from https://www.python.org/downloads/"
            exit 1
            ;;
        *)
            echo "Unsupported OS. Please install Python3 manually."
            exit 1
            ;;
    esac
else
    echo "Python3 is already installed."
fi

# Install pip3 if missing
if ! command_exists pip3; then
    echo "pip3 is not installed. Installing..."
    case "$OS_TYPE" in
        Linux*)
            sudo apt install -y python3-pip || sudo dnf install -y python3-pip
            ;;
        Darwin*)
            echo "Installing pip3 using Homebrew..."
            brew install python3  # Homebrew installs pip3 with Python3
            ;;
        MINGW* | MSYS* | CYGWIN*)
            echo "Please install Python and ensure pip3 is available."
            exit 1
            ;;
        *)
            echo "Unsupported OS. Please install pip3 manually."
            exit 1
            ;;
    esac
else
    echo "pip3 is already installed."
    echo "Upgrading pip3..."
    sudo pip3 install --upgrade pip
fi

# Install required dependencies **globally**
echo "Installing dependencies globally..."
sudo pip3 install -r requirements.txt

# Install the GEOM package globally using setup.py
echo "Installing GEOM globally..."
sudo pip3 install .

# Ensure the correct path is available
if [[ ":$PATH:" != *":/usr/local/bin:"* ]]; then
    export PATH="/usr/local/bin:$PATH"
    echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
    echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
fi

# Run tests if available
if [ -f "./tests/run_all_tests.sh" ]; then
    echo "Running tests..."
    chmod +x ./tests/run_all_tests.sh
    ./tests/run_all_tests.sh
else
    echo "No test script found at ./tests/run_all_tests.sh. Skipping tests."
fi

echo "Installation complete."

