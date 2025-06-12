#!/bin/bash

set -e

echo "[INFO] Setting up development environment..."

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

echo "[INFO] Development environment setup complete!"
echo "[INFO] You can now run ./scripts/start_mcp_service.sh" 