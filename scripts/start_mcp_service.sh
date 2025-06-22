#!/bin/bash

set -e

# Parse command line arguments
BACKGROUND=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -b|--background) BACKGROUND=true ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

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

# Set PYTHONPATH to include backend directory for module imports
export PYTHONPATH="$(pwd)/backend:$(pwd):$PYTHONPATH"
echo "[INFO] PYTHONPATH set to: $PYTHONPATH"

# Start the MCP service
CMD="python3 backend/app/core/mcp_service.py"

if [ "$BACKGROUND" = true ]; then
    LOG_FILE="mcp_service.log"
    echo "[INFO] Starting MCP service in background mode. Logs: $LOG_FILE"
    nohup $CMD > "$LOG_FILE" 2>&1 &
    echo $! > mcp_service.pid
    echo "[INFO] MCP service started in background. PID: $(cat mcp_service.pid)"
    echo "To stop the service, run: kill $(cat mcp_service.pid)"
    echo "To view logs: tail -f $LOG_FILE"
else
    echo "[INFO] Starting MCP service in foreground mode."
    exec $CMD
fi 