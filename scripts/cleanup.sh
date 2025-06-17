#!/bin/bash

# Cleanup utility script

set -e

# Get the absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Navigate to the project root
cd "$PROJECT_ROOT"

echo "Cleaning up MCP Service environment..."
echo "======================================"

# Function to safely remove files/directories
safe_remove() {
    local target=$1
    local description=$2
    
    if [ -e "$target" ]; then
        echo "Removing $description: $target"
        rm -rf "$target"
    else
        echo "Skipping $description (not found): $target"
    fi
}

# Function to stop services if running
stop_services() {
    echo "Stopping any running services..."
    
    # Stop services using our stop script if it exists
    if [ -f "./scripts/stop_all.sh" ]; then
        ./scripts/stop_all.sh
    else
        # Manual cleanup if stop script doesn't exist
        echo "Manual service cleanup..."
        
        # Kill processes by pattern
        pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
        pkill -f "python.*mcp_service.py" 2>/dev/null || true
        pkill -f "npm.*dev.*3000" 2>/dev/null || true
        pkill -f "redis-server" 2>/dev/null || true
        pkill -f "prometheus" 2>/dev/null || true
        pkill -f "grafana-server" 2>/dev/null || true
        
        # Wait a moment for processes to terminate
        sleep 2
        
        # Force kill any remaining processes
        pkill -9 -f "uvicorn.*app.main:app" 2>/dev/null || true
        pkill -9 -f "python.*mcp_service.py" 2>/dev/null || true
        pkill -9 -f "npm.*dev.*3000" 2>/dev/null || true
        pkill -9 -f "redis-server" 2>/dev/null || true
        pkill -9 -f "prometheus" 2>/dev/null || true
        pkill -9 -f "grafana-server" 2>/dev/null || true
    fi
}

# Function to clean up logs
cleanup_logs() {
    echo "Cleaning up log files..."
    
    # Remove log files
    safe_remove "*.log" "log files"
    safe_remove "nohup.out" "nohup output"
    safe_remove "backend_start.log" "backend startup log"
    safe_remove "mcp_start.log" "MCP service startup log"
    safe_remove "frontend_start.log" "frontend startup log"
    safe_remove "redis.log" "Redis log"
    safe_remove "prometheus.log" "Prometheus log"
    safe_remove "grafana.log" "Grafana log"
    
    # Clean up logs directory
    if [ -d "logs" ]; then
        echo "Cleaning logs directory..."
        find logs -name "*.log" -type f -delete 2>/dev/null || true
        find logs -name "*.tmp" -type f -delete 2>/dev/null || true
    fi
}

# Function to clean up PID files
cleanup_pid_files() {
    echo "Cleaning up PID files..."
    
    safe_remove "*.pid" "PID files"
    safe_remove "backend.pid" "backend PID file"
    safe_remove "mcp_service.pid" "MCP service PID file"
    safe_remove "frontend.pid" "frontend PID file"
    safe_remove "redis.pid" "Redis PID file"
    safe_remove "prometheus.pid" "Prometheus PID file"
    safe_remove "grafana.pid" "Grafana PID file"
    safe_remove "backend_start.pid" "backend startup PID file"
    safe_remove "mcp_start.pid" "MCP service startup PID file"
    safe_remove "frontend_start.pid" "frontend startup PID file"
}

# Function to clean up temporary files
cleanup_temp_files() {
    echo "Cleaning up temporary files..."
    
    # Remove temporary files
    safe_remove "*.tmp" "temporary files"
    safe_remove "*.cache" "cache files"
    safe_remove ".DS_Store" "macOS system files"
    safe_remove "Thumbs.db" "Windows thumbnail files"
    
    # Clean up Python cache
    safe_remove "**/__pycache__" "Python cache directories"
    safe_remove "**/*.pyc" "Python compiled files"
    safe_remove "**/*.pyo" "Python optimized files"
    
    # Clean up Node.js cache
    if [ -d "frontend/node_modules" ]; then
        echo "Cleaning frontend node_modules cache..."
        find frontend/node_modules -name ".cache" -type d -exec rm -rf {} + 2>/dev/null || true
    fi
}

# Function to clean up data files (optional)
cleanup_data_files() {
    echo "Cleaning up data files..."
    
    # Ask user if they want to clean data files
    read -p "Do you want to clean up data files (databases, exports, etc.)? [y/N]: " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Cleaning up data files..."
        
        # Clean up SQLite databases
        safe_remove "data/sqlite/*.db" "SQLite database files"
        safe_remove "data/sqlite/*.db-journal" "SQLite journal files"
        safe_remove "data/sqlite/*.db-wal" "SQLite WAL files"
        
        # Clean up exports
        safe_remove "exports/*" "export files"
        
        # Clean up Redis dump files
        safe_remove "dump.rdb" "Redis dump file"
        safe_remove "appendonly.aof" "Redis AOF file"
        
        # Clean up Prometheus data
        safe_remove "data/prometheus/data/*" "Prometheus data"
        
        # Clean up Grafana data
        safe_remove "data/grafana/data/*" "Grafana data"
        
        echo "Data files cleaned up"
    else
        echo "Skipping data file cleanup"
    fi
}

# Function to clean up virtual environment (optional)
cleanup_venv() {
    echo "Checking virtual environment..."
    
    if [ -d "venv" ]; then
        read -p "Do you want to remove the virtual environment? [y/N]: " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            safe_remove "venv" "virtual environment"
            echo "Virtual environment removed"
        else
            echo "Keeping virtual environment"
        fi
    fi
}

# Function to clean up node_modules (optional)
cleanup_node_modules() {
    echo "Checking node_modules..."
    
    if [ -d "frontend/node_modules" ]; then
        read -p "Do you want to remove frontend node_modules? [y/N]: " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            safe_remove "frontend/node_modules" "frontend node_modules"
            echo "node_modules removed"
        else
            echo "Keeping node_modules"
        fi
    fi
}

# Function to reset configuration files (optional)
reset_configs() {
    echo "Checking configuration files..."
    
    read -p "Do you want to reset configuration files to defaults? [y/N]: " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Resetting configuration files..."
        
        # Backup existing configs
        if [ -f ".env" ]; then
            cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
            echo "Backed up .env to .env.backup.$(date +%Y%m%d_%H%M%S)"
        fi
        
        if [ -f ".env.low_performance" ]; then
            cp .env.low_performance .env.low_performance.backup.$(date +%Y%m%d_%H%M%S)
            echo "Backed up .env.low_performance to .env.low_performance.backup.$(date +%Y%m%d_%H%M%S)"
        fi
        
        # Remove config files (they will be recreated on next setup)
        safe_remove ".env" "environment file"
        safe_remove ".env.low_performance" "low performance environment file"
        
        echo "Configuration files reset"
    else
        echo "Keeping existing configuration files"
    fi
}

# Main cleanup function
main() {
    echo "Starting cleanup process..."
    echo ""
    
    # Stop services first
    stop_services
    
    # Clean up various file types
    cleanup_logs
    cleanup_pid_files
    cleanup_temp_files
    
    # Optional cleanups
    cleanup_data_files
    cleanup_venv
    cleanup_node_modules
    reset_configs
    
    echo ""
    echo "======================================"
    echo "Cleanup completed successfully!"
    echo ""
    echo "To restart the system:"
    echo "1. Run setup: ./scripts/setup_dev_env.sh"
    echo "2. Start services: ./scripts/start_all.sh"
    echo ""
    echo "Note: If you removed the virtual environment or node_modules,"
    echo "you'll need to reinstall dependencies first."
}

# Run main cleanup
main "$@" 