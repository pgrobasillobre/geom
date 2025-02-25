#!/bin/bash

echo "📦 Setting up the project..."

# Ensure the script stops on any error
set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Python3 and pip3 if not installed
if ! command_exists python3; then
    echo "❌ Python3 not found. Installing..."
    sudo apt update && sudo apt install -y python3
else
    echo "✅ Python3 is already installed."
fi

if ! command_exists pip3; then
    echo "❌ pip3 not found. Installing..."
    sudo apt install -y python3-pip
else
    echo "✅ pip3 is already installed."
fi

# Create a virtual environment (recommended)
if [ ! -d "venv" ]; then
    echo "🌱 Creating a virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists."
fi

# Activate the virtual environment
echo "🔁 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip3 install --upgrade pip

# Install required dependencies
echo "📦 Installing dependencies from requirements.txt..."
pip3 install -r requirements.txt

# Run tests
if [ -f "./tests/run_all_tests.sh" ]; then
    echo "🧪 Running tests..."
    chmod +x ./tests/run_all_tests.sh
    ./tests/run_all_tests.sh
else
    echo "⚠️ No test script found at ./tests/run_all_tests.sh. Skipping tests."
fi

echo "🎉 Installation complete! To activate the virtual environment, run:"
echo "source venv/bin/activate"

