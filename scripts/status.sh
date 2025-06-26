#!/bin/bash

# =============================================================================
# MCP Service - Status Check Script
# =============================================================================
# This script checks the status of all MCP service components
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

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to check process by PID file
check_process_by_pid() {
    local service_name=$1
    local pid_file=$2
    local port=$3
    local url=$4
    
    echo -n "$service_name: "
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            if check_port $port; then
                print_success "Running (PID: $pid, Port: $port)"
                if [ ! -z "$url" ]; then
                    echo "  URL: $url"
                fi
            else
                print_warning "Process running but port $port not listening (PID: $pid)"
            fi
        else
            print_error "Stale PID file (PID: $pid not running)"
        fi
    else
        if check_port $port; then
            local port_pid=$(lsof -ti :$port 2>/dev/null)
            print_warning "Port $port in use by process $port_pid (no PID file)"
        else
            print_error "Not running"
        fi
    fi
}

# Function to check Redis
check_redis() {
    echo -n "Redis: "
    if redis-cli ping >/dev/null 2>&1; then
        print_success "Running (Port: 6379)"
    else
        if check_port 6379; then
            local port_pid=$(lsof -ti :6379 2>/dev/null)
            print_warning "Port 6379 in use by process $port_pid (Redis not responding)"
        else
            print_error "Not running"
        fi
    fi
}

# Main status check
main() {
    print_status "Checking MCP Service component status..."
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    echo
    echo "Service Status:"
    echo "==============="
    
    # Check each service
    check_redis
    check_process_by_pid "Backend" "backend/backend.pid" 5000 "http://localhost:5000/api/v1/docs"
    check_process_by_pid "Frontend" "frontend/frontend.pid" 3000 "http://localhost:3000"
    
    echo
    echo "Quick Commands:"
    echo "==============="
    echo "Start all:     ./scripts/start_all.sh"
    echo "Stop all:      ./scripts/stop_all.sh"
    echo "Restart all:   ./scripts/stop_all.sh && ./scripts/start_all.sh"
    echo "View logs:     tail -f [service].log"
    echo
    echo "Individual services:"
    echo "  Redis:       ./scripts/start_redis.sh"
    echo "  Backend:     ./scripts/start_backend.sh"
    echo "  Frontend:    ./scripts/start_frontend.sh"
}

# Run the main function
main "$@" 