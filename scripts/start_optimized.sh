#!/bin/bash

set -e

# Get the absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Navigate to the project root
cd "$PROJECT_ROOT"

echo "[INFO] Starting MCP Service in optimized mode for low-performance device..."

# Load optimized environment variables
if [ -f ".env.low_performance" ]; then
    echo "[INFO] Loading optimized environment variables..."
    set -a
    source .env.low_performance
    set +a
else
    echo "[ERROR] Optimized environment file not found"
    exit 1
fi

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Check system resources
check_system_resources() {
    echo "[INFO] Checking system resources..."
    
    # Check available memory
    available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
    if [ "$available_memory" -lt 512 ]; then
        echo "[WARN] Low memory available: ${available_memory}MB"
        echo "[INFO] Consider closing other applications"
    fi
    
    # Check available disk space
    available_disk=$(df -m . | awk 'NR==2{printf "%.0f", $4}')
    if [ "$available_disk" -lt 1024 ]; then
        echo "[WARN] Low disk space available: ${available_disk}MB"
        echo "[INFO] Consider cleaning up disk space"
    fi
    
    # Check CPU load
    cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    if (( $(echo "$cpu_load > 1.5" | bc -l) )); then
        echo "[WARN] High CPU load: $cpu_load"
    fi
}

# Start services in optimized order
start_services() {
    echo "[INFO] Starting services in optimized order..."
    
    # Check if Redis is running as a system service
    echo "[INFO] Checking if Redis is running..."
    if ! redis-cli ping | grep -q PONG; then
        echo "[ERROR] Redis is not running on port 6379."
        echo "[INFO] Please start Redis with: sudo systemctl start redis-server"
        echo "[INFO] Or check status with: sudo systemctl status redis-server"
        exit 1
    fi
    echo "[INFO] Redis is running and ready."

    # Wait for Redis to be ready
    echo "[INFO] Waiting for Redis to be ready..."
    until redis-cli ping | grep -q PONG; do
        echo "[INFO] Redis is not ready yet. Waiting..."
        sleep 1
    done
    echo "[INFO] Redis is ready. Starting backend..."

    # Start backend with minimal workers (port 5000)
    if check_port 5000; then
        echo "[WARN] Port 5000 is already in use. Skipping backend startup."
    else
        echo "[INFO] Starting backend with minimal workers..."
        cd backend
        source ../venv/bin/activate
        uvicorn app.main:app --host 0.0.0.0 --port 5000 --workers 1 --log-level warning &
        echo $! > ../backend.pid
        cd ..
        sleep 5
    fi
    
    # Start MCP service (background service, no web port)
    echo "[INFO] Starting MCP service..."
    cd backend
    source ../venv/bin/activate
    python -m app.core.mcp_service &
    echo $! > ../mcp_service.pid
    cd ..
    sleep 3
    
    # Start frontend only if enabled (port 3000)
    if [ "${ENABLE_FRONTEND:-false}" = "true" ]; then
        if check_port 3000; then
            echo "[WARN] Port 3000 is already in use. Skipping frontend startup."
        else
            echo "[INFO] Starting frontend..."
            cd frontend
            npm run dev -- --port 3000 --host 0.0.0.0 &
            echo $! > ../frontend.pid
            cd ..
        fi
    fi
}

# Main execution
main() {
    check_system_resources
    start_services
    
    echo "[SUCCESS] All services started in optimized mode"
    echo "[INFO] Backend: http://localhost:5000"
    echo "[INFO] MCP Service: Background service (no web interface)"
    if [ "${ENABLE_FRONTEND:-false}" = "true" ]; then
        echo "[INFO] Frontend: http://localhost:3000"
    fi
    echo "[INFO] Press Ctrl+C to stop all services"
    
    # Wait for interrupt
    trap 'echo "[INFO] Stopping services..."; ./scripts/stop_all.sh; exit 0' INT
    wait
}

main "$@" 