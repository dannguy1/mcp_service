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
    export $(grep -v '^#' .env.low_performance | xargs)
else
    echo "[ERROR] Optimized environment file not found"
    exit 1
fi

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
    
    # Start Redis with optimized config
    if [ -f "data/redis/redis.low_performance.conf" ]; then
        echo "[INFO] Starting Redis with optimized configuration..."
        redis-server data/redis/redis.low_performance.conf &
        echo $! > redis.pid
        sleep 3
    fi
    
    # Start backend with minimal workers
    echo "[INFO] Starting backend with minimal workers..."
    cd backend
    source ../venv/bin/activate
    uvicorn app.main:app --host 0.0.0.0 --port 5000 --workers 1 --log-level warning &
    echo $! > ../backend.pid
    cd ..
    sleep 5
    
    # Start MCP service
    echo "[INFO] Starting MCP service..."
    cd backend
    source ../venv/bin/activate
    python app/core/mcp_service.py &
    echo $! > ../mcp_service.pid
    cd ..
    sleep 3
    
    # Start frontend only if enabled
    if [ "${ENABLE_FRONTEND:-false}" = "true" ]; then
        echo "[INFO] Starting frontend..."
        cd frontend
        npm run dev -- --port 3000 --host 0.0.0.0 &
        echo $! > ../frontend.pid
        cd ..
    fi
}

# Main execution
main() {
    check_system_resources
    start_services
    
    echo "[SUCCESS] All services started in optimized mode"
    echo "[INFO] Backend: http://localhost:5000"
    echo "[INFO] MCP Service: http://localhost:5555"
    if [ "${ENABLE_FRONTEND:-false}" = "true" ]; then
        echo "[INFO] Frontend: http://localhost:3000"
    fi
    echo "[INFO] Press Ctrl+C to stop all services"
    
    # Wait for interrupt
    trap 'echo "[INFO] Stopping services..."; ./scripts/stop_all.sh; exit 0' INT
    wait
}

main "$@" 