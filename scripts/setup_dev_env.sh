#!/bin/bash

set -e

echo "[INFO] Setting up development environment..."

# Install system dependencies
sudo apt-get update
sudo apt-get install -y redis-server postgresql-client sqlite3

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[INFO] Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "[INFO] Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "[INFO] Installing Python dependencies..."
pip install -r backend/requirements.txt

# Install development dependencies if they exist
if [ -f "backend/requirements-dev.txt" ]; then
    echo "[INFO] Installing development dependencies..."
    pip install -r backend/requirements-dev.txt
fi

echo "[INFO] Development environment setup complete!"
echo "[INFO] Remember to activate the virtual environment before running scripts:"
echo "[INFO]   source venv/bin/activate"
echo "[INFO] You can now run ./scripts/start_dev.sh or ./scripts/start_optimized.sh" 