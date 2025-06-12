#!/bin/bash

set -e

# Print debug info
echo "[INFO] Current directory: $(pwd)"
echo "[INFO] Python version: $(python --version)"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "[INFO] Activating Python virtual environment..."
    source venv/bin/activate
fi

# Load environment variables from .env or backend/example.env
if [ -f .env ]; then
    echo "[INFO] Loading environment variables from .env"
    set -a
    source .env
    set +a
elif [ -f backend/example.env ]; then
    echo "[INFO] Loading environment variables from backend/example.env"
    set -a
    source backend/example.env
    set +a
else
    echo "[WARN] No .env or backend/example.env found. Proceeding with current environment."
fi

# Set PYTHONPATH to include backend/app and current directory
export PYTHONPATH="$(pwd)/backend/app:$(pwd):$PYTHONPATH"
echo "[INFO] PYTHONPATH set to: $PYTHONPATH"

# Start the MCP service
CMD="python3 backend/app/core/mcp_service.py"
echo "[INFO] Starting MCP service: $CMD"
exec $CMD 