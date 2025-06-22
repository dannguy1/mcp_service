#!/bin/bash

# Parse command line arguments
BACKGROUND=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -b|--background) BACKGROUND=true ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Navigate to the frontend directory
cd "$(dirname "$0")/../frontend"

# Load environment variables from .env or example.env
if [ -f ".env" ]; then
    echo "[INFO] Loading environment variables from .env"
    set -a
    source .env
    set +a
elif [ -f "example.env" ]; then
    echo "[INFO] Loading environment variables from example.env"
    set -a
    source example.env
    set +a
else
    echo "[WARN] No .env or example.env found. Proceeding with current environment."
fi

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Check if port 3000 is available
if ! check_port 3000; then
    if [ "$BACKGROUND" = true ]; then
        LOG_FILE="frontend.log"
        echo "[INFO] Starting frontend in background mode. Logs: $LOG_FILE"
        nohup npm run dev > "$LOG_FILE" 2>&1 &
        echo $! > frontend.pid
        echo "[INFO] Frontend started in background. PID: $(cat frontend.pid)"
        echo "To stop the service, run: kill $(cat frontend.pid)"
        echo "To view logs: tail -f $LOG_FILE"
        exit 0
    else
        echo "Starting frontend development server on port 3000..."
        npm run dev
        exit 0
    fi
else
    echo "Error: Port 3000 is already in use"
    exit 1
fi