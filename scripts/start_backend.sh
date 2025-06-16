#!/bin/bash

# Parse command line arguments
BACKGROUND=false
PORT=5000
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -b|--background) BACKGROUND=true ;;
        -p|--port) PORT="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Get the absolute path to the backend directory
BACKEND_DIR="$(cd "$(dirname "$0")/.." && pwd)/backend"

# Navigate to the backend directory
cd "$BACKEND_DIR"

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "Port $port is already in use. Please stop the process using this port or use a different port with -p option."
        return 1
    fi
    return 0
}

# Function to stop existing backend process
stop_backend() {
    if [ -f "backend.pid" ]; then
        PID=$(cat backend.pid)
        if ps -p $PID > /dev/null 2>&1; then
            echo "Stopping existing backend process (PID: $PID)..."
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
            echo "Backend process stopped."
        else
            echo "Found stale PID file. Removing..."
        fi
        rm -f backend.pid
    fi
    
    # Also check for any uvicorn processes on the target port
    local port_pid=$(lsof -ti :$PORT 2>/dev/null)
    if [ ! -z "$port_pid" ]; then
        echo "Found process $port_pid using port $PORT. Stopping..."
        kill $port_pid
        sleep 2
    fi
}

# Function to wait for port to be available
wait_for_port() {
    local port=$1
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    echo "Timeout waiting for port $port to become available"
    return 1
}

# Stop any existing backend process
stop_backend

# Check if port is available
if ! check_port $PORT; then
    exit 1
fi

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
export ENVIRONMENT=development
export HOST=0.0.0.0
export PORT=$PORT
export LOG_LEVEL=info
export RELOAD=true
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export DB_HOST=192.168.10.14
export DB_PORT=5432
export DB_NAME=netmonitor_db
export DB_USER=netmonitor_user
export DB_PASSWORD=netmonitor_password
export DB_MIN_CONNECTIONS=5
export DB_MAX_CONNECTIONS=20
export DB_POOL_TIMEOUT=30
export CORS_ORIGINS=http://localhost:3000
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Start the FastAPI development server
echo "Starting backend development server on port $PORT..."
if [ "$BACKGROUND" = true ]; then
    # Run in background and redirect output to a log file
    LOG_FILE="backend.log"
    echo "Running in background mode. Logs will be written to $LOG_FILE"
    nohup uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload --log-level info > "$LOG_FILE" 2>&1 &
    echo $! > backend.pid
    
    # Wait for server to start
    if wait_for_port $PORT; then
        echo "Backend server started in background. PID: $(cat backend.pid)"
        echo "To stop the server, run: kill $(cat backend.pid)"
        echo "API documentation available at: http://localhost:$PORT/api/v1/docs"
        echo "Health check available at: http://localhost:$PORT/api/v1/health"
    else
        echo "Failed to start backend server. Check logs in $LOG_FILE"
        exit 1
    fi
else
    # Run in foreground
    echo "Starting FastAPI development server..."
    echo "API documentation available at: http://localhost:$PORT/api/v1/docs"
    echo "Health check available at: http://localhost:$PORT/api/v1/health"
    uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload --log-level info
fi