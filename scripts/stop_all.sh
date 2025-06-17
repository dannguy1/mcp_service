#!/bin/bash

set -e

# Get the absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Navigate to the project root
cd "$PROJECT_ROOT"

echo "[INFO] Stopping all services..."

# Function to stop a service by PID file
stop_service_by_pid() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "[INFO] Stopping $service_name (PID: $pid)..."
            kill -TERM "$pid" 2>/dev/null || true
            
            # Wait for graceful shutdown
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "[WARN] Force killing $service_name (PID: $pid)..."
                kill -KILL "$pid" 2>/dev/null || true
            fi
            
            rm -f "$pid_file"
            echo "[INFO] $service_name stopped"
        else
            echo "[INFO] $service_name is not running (PID: $pid)"
            rm -f "$pid_file"
        fi
    else
        echo "[INFO] $service_name PID file not found"
    fi
}

# Function to stop services by process name
stop_service_by_name() {
    local service_name=$1
    local process_pattern=$2
    
    echo "[INFO] Stopping $service_name..."
    
    # Find and kill processes
    local pids=$(pgrep -f "$process_pattern" 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo "[INFO] Found $service_name processes: $pids"
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        
        # Wait for graceful shutdown
        sleep 3
        
        # Force kill if still running
        local remaining_pids=$(pgrep -f "$process_pattern" 2>/dev/null || true)
        if [ -n "$remaining_pids" ]; then
            echo "[WARN] Force killing remaining $service_name processes: $remaining_pids"
            echo "$remaining_pids" | xargs kill -KILL 2>/dev/null || true
        fi
        
        echo "[INFO] $service_name stopped"
    else
        echo "[INFO] $service_name is not running"
    fi
}

# Stop application services first (reverse order of startup)
echo "[INFO] Stopping application services..."

# Stop Frontend
stop_service_by_pid "Frontend" "frontend_start.pid"
stop_service_by_name "Frontend" "npm.*dev.*3000"

# Stop MCP Service
stop_service_by_pid "MCP Service" "mcp_start.pid"
stop_service_by_name "MCP Service" "python.*mcp_service.py"

# Stop Backend
stop_service_by_pid "Backend" "backend_start.pid"
stop_service_by_name "Backend" "uvicorn.*app.main:app"

# Note: External services (Redis, Prometheus, Grafana) are managed outside this script
echo "[INFO] External services (Redis, Prometheus, Grafana) are managed externally. Use systemctl or your preferred method to stop them if needed."

# Clean up any remaining PID files
echo "[INFO] Cleaning up PID files..."
rm -f *.pid

# Check if any services are still running
echo "[INFO] Checking for any remaining processes..."
remaining_processes=$(pgrep -f "uvicorn\|mcp_service\|npm.*dev" 2>/dev/null || true)

if [ -n "$remaining_processes" ]; then
    echo "[WARN] Some processes are still running:"
    echo "$remaining_processes" | while read pid; do
        ps -p "$pid" -o pid,ppid,cmd --no-headers 2>/dev/null || true
    done
    echo "[INFO] You may need to manually stop these processes"
else
    echo "[INFO] All application services have been stopped successfully"
fi

# Clean up temporary files
echo "[INFO] Cleaning up temporary files..."
rm -f *.log
rm -f nohup.out

echo "[SUCCESS] All application services stopped and cleaned up" 