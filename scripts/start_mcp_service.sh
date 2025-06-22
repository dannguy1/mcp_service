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

# Function to stop existing MCP service process
stop_mcp_service() {
    if [ -f "mcp_service.pid" ]; then
        PID=$(cat mcp_service.pid)
        if ps -p $PID > /dev/null 2>&1; then
            echo "Stopping existing MCP service process (PID: $PID)..."
            kill $PID
            # Wait for process to stop
            local count=0
            while ps -p $PID > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            if ps -p $PID > /dev/null 2>&1; then
                echo "Force killing process..."
                kill -9 $PID
            fi
            echo "MCP service process stopped."
        else
            echo "Found stale PID file. Removing..."
        fi
        rm -f mcp_service.pid
    fi
    # Also check for any process using port 5555
    local port_pid=$(lsof -ti :5555 2>/dev/null)
    if [ ! -z "$port_pid" ]; then
        echo "Found process $port_pid using port 5555. Stopping..."
        kill $port_pid
        sleep 2
    fi
}

# Stop any existing MCP service process
stop_mcp_service

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