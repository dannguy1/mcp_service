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

# Get the absolute path to the backend directory
BACKEND_DIR="$(cd "$(dirname "$0")/.." && pwd)/backend"

# Navigate to the backend directory
cd "$BACKEND_DIR"

# Function to stop existing backend process
stop_backend() {
    if [ -f "backend.pid" ]; then
        PID=$(cat backend.pid)
        if ps -p $PID > /dev/null; then
            echo "Stopping existing backend process (PID: $PID)..."
            kill $PID
            # Wait for process to stop
            while ps -p $PID > /dev/null; do
                sleep 1
            done
            echo "Backend process stopped."
        else
            echo "Found stale PID file. Removing..."
        fi
        rm -f backend.pid
    fi
}

# Stop any existing backend process
stop_backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install requirements
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
else
    # Activate existing virtual environment
    source venv/bin/activate
fi

# Set environment variables
export FLASK_ENV=development
export FLASK_APP=app
export FLASK_DEBUG=1
export REDIS_URL=redis://localhost:6379/0
export CORS_ORIGINS=http://localhost:3000
export SOCKETIO_MESSAGE_QUEUE=redis://localhost:6379/0
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Start the Flask development server
echo "Starting backend development server..."
if [ "$BACKGROUND" = true ]; then
    # Run in background and redirect output to a log file
    LOG_FILE="backend.log"
    echo "Running in background mode. Logs will be written to $LOG_FILE"
    nohup flask run --host=0.0.0.0 --port=5000 > "$LOG_FILE" 2>&1 &
    echo $! > backend.pid
    echo "Backend server started in background. PID: $(cat backend.pid)"
    echo "To stop the server, run: kill $(cat backend.pid)"
else
    # Run in foreground
    flask run --host=0.0.0.0 --port=5000
fi