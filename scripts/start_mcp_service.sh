#!/bin/bash

set -e

# Print debug info
echo "[INFO] Current directory: $(pwd)"
echo "[INFO] Python version: $(python3 --version)"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "[INFO] Activating Python virtual environment..."
    source venv/bin/activate
fi

# Load environment variables from .env or backend/example.env
if [ -f .env ]; then
    echo "[INFO] Loading environment variables from .env"
    # Read each line and export if it's not empty and doesn't start with #
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip empty lines and comments
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        # Export the variable
        export "$line"
    done < .env
elif [ -f backend/example.env ]; then
    echo "[INFO] Loading environment variables from backend/example.env"
    while IFS= read -r line || [ -n "$line" ]; do
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        export "$line"
    done < backend/example.env
else
    echo "[WARN] No .env or backend/example.env found. Proceeding with current environment."
fi

# Set PYTHONPATH to include backend directory for module imports
export PYTHONPATH="$(pwd)/backend:$(pwd):$PYTHONPATH"
echo "[INFO] PYTHONPATH set to: $PYTHONPATH"

# Start the MCP service
CMD="python3 backend/app/core/mcp_service.py"
echo "[INFO] Starting MCP service: $CMD"
exec $CMD 