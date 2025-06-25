#!/bin/bash

# =============================================================================
# MCP Service - Stop All Services Script
# =============================================================================
# This script stops all running services for the MCP service:
# 1. Redis
# 2. MCP Service
# 3. Backend API
# 4. Frontend
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to stop a process by PID file
stop_process_by_pid() {
    local service_name=$1
    local pid_file=$2
    local port=$3
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            print_status "Stopping $service_name (PID: $pid)..."
            kill $pid
            
            # Wait for process to stop gracefully
            local count=0
            while ps -p $pid > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                print_warning "Force killing $service_name (PID: $pid)..."
                kill -9 $pid
                sleep 1
            fi
            
            print_success "$service_name stopped"
        else
            print_warning "Found stale PID file for $service_name. Removing..."
        fi
        rm -f "$pid_file"
    fi
    
    # Also check for any process using the specified port
    if [ ! -z "$port" ]; then
        local port_pid=$(lsof -ti :$port 2>/dev/null)
        if [ ! -z "$port_pid" ]; then
            print_status "Found process $port_pid using port $port. Stopping..."
            kill $port_pid
            sleep 2
        fi
    fi
}

# Function to stop Redis
stop_redis() {
    print_status "Stopping Redis..."
    
    # Try to stop Redis gracefully
    if redis-cli ping >/dev/null 2>&1; then
        redis-cli shutdown
        sleep 2
        print_success "Redis stopped gracefully"
    fi
    
    # Check if Redis is still running and force stop
    if redis-cli ping >/dev/null 2>&1; then
        print_warning "Redis still running, force stopping..."
        pkill -f redis-server || true
        sleep 2
    fi
    
    # Check for any process using port 6379
    local redis_pid=$(lsof -ti :6379 2>/dev/null)
    if [ ! -z "$redis_pid" ]; then
        print_status "Found process $redis_pid using port 6379. Stopping..."
        kill $redis_pid
        sleep 2
    fi
}

# Main stop sequence
main() {
    print_status "Stopping all MCP Service components..."
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Stop services in reverse order of dependency
    print_status "Stopping Frontend..."
    stop_process_by_pid "Frontend" "frontend/frontend.pid" 3000
    
    print_status "Stopping Backend..."
    stop_process_by_pid "Backend" "backend/backend.pid" 5000
    
    print_status "Stopping MCP Service..."
    stop_process_by_pid "MCP Service" "mcp_service.pid" 5555
    
    print_status "Stopping Redis..."
    stop_redis
    
    # Clean up any remaining PID files
    rm -f frontend/frontend.pid backend/backend.pid mcp_service.pid redis.pid
    
    print_success "All services stopped successfully!"
    
    # Verify no services are still running
    print_status "Verifying all services are stopped..."
    
    local running_services=()
    
    if redis-cli ping >/dev/null 2>&1; then
        running_services+=("Redis")
    fi
    
    if lsof -Pi :5555 -sTCP:LISTEN -t >/dev/null 2>&1; then
        running_services+=("MCP Service")
    fi
    
    if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        running_services+=("Backend")
    fi
    
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        running_services+=("Frontend")
    fi
    
    if [ ${#running_services[@]} -eq 0 ]; then
        print_success "All services confirmed stopped"
    else
        print_warning "The following services are still running:"
        for service in "${running_services[@]}"; do
            echo "  - $service"
        done
        print_status "You may need to manually stop these services"
    fi
}

# Run the main function
main "$@" 