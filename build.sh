#!/bin/bash
# build.sh - Build script for Linux/Mac

echo "Building Risk Manager..."

# Activate virtual environment if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install PyInstaller if not already installed
pip show pyinstaller > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Clean previous builds
rm -rf build dist

# Build with PyInstaller
echo "Building executable..."
pyinstaller --onefile --windowed --name "RiskManager" --add-data "src:src" src/main.py

echo "Build complete!"
echo "Executable located in: dist/RiskManager"