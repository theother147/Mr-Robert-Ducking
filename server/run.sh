#!/bin/bash
echo "Checking environment..."

# Change to server directory
cd server

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Now that we're in venv, check installation and install dependencies if needed
python -c "from modules.install.install import verify_installation, install_dependencies_in_venv; install_dependencies_in_venv() if not verify_installation() else None"
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies"
    exit 1
fi

echo "Starting server..."
python main.py 