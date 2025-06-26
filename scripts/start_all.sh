#!/bin/bash

# =============================================================================
# MCP Service - Complete Startup Script
# =============================================================================
# This script starts all required services for the MCP service:
# 1. Redis (required for caching and session management)
# 2. MCP Service (WiFi anomaly detection and model management)
# 3. Backend API (FastAPI server)
# 4. Frontend (React development server)
# =============================================================================

set -e

# Parse command line arguments
BACKGROUND=false
SKIP_FRONTEND=false
SKIP_MCP=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -b|--background) BACKGROUND=true ;;
        --skip-frontend) SKIP_FRONTEND=true ;;
        --skip-mcp) SKIP_MCP=true ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -b, --background     Start all services in background mode"
            echo "  --skip-frontend      Skip starting the frontend"
            echo "  --skip-mcp           Skip starting the MCP service"
            echo "  -h, --help           Show this help message"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

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

# Function to wait for a service to be ready
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=0
    
    print_status "Waiting for $service_name to be ready on port $port..."
    
    while [ $attempt -lt $max_attempts ]; do
        if check_port $port; then
            print_success "$service_name is ready on port $port"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start on port $port after $max_attempts attempts"
    return 1
}

# Function to handle script termination
cleanup() {
    print_status "Shutting down all services..."
    
    # Kill background processes
    if [ ! -z "$REDIS_PID" ]; then
        print_status "Stopping Redis (PID: $REDIS_PID)..."
        kill $REDIS_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$MCP_PID" ]; then
        print_status "Stopping MCP Service (PID: $MCP_PID)..."
        kill $MCP_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$BACKEND_PID" ]; then
        print_status "Stopping Backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        print_status "Stopping Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Remove PID files
    rm -f redis.pid mcp_service.pid backend.pid frontend.pid
    
    print_success "All services stopped"
    exit 0
}

# Set up trap for cleanup on script termination
trap cleanup SIGINT SIGTERM

# Function to start a service in background mode
start_service_background() {
    local service_name=$1
    local script_path=$2
    local port=$3
    local pid_file=$4
    local log_file=$5
    
    print_status "Starting $service_name in background mode..."
    
    if [ "$BACKGROUND" = true ]; then
        # Use the service's own background mode
        $script_path -b &
        local service_pid=$!
        
        # Wait a moment for the service to start
        sleep 2
        
        # Check if the service started successfully
        if [ -f "$pid_file" ]; then
            local actual_pid=$(cat "$pid_file")
            print_success "$service_name started in background (PID: $actual_pid)"
            echo $actual_pid  # Return the PID
        else
            print_error "$service_name failed to start"
            return 1
        fi
    else
        # Start in background manually
        $script_path > "$log_file" 2>&1 &
        local service_pid=$!
        echo $service_pid > "$pid_file"
        print_success "$service_name started in background (PID: $service_pid)"
        echo $service_pid  # Return the PID
    fi
}

# Function to start a service in foreground mode
start_service_foreground() {
    local service_name=$1
    local script_path=$2
    
    print_status "Starting $service_name in foreground mode..."
    exec $script_path
}

# Main startup sequence
main() {
    print_status "Starting MCP Service complete environment..."
    print_status "Background mode: $BACKGROUND"
    print_status "Skip frontend: $SKIP_FRONTEND"
    print_status "Skip MCP service: $SKIP_MCP"
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Check if Redis is installed
    if ! command -v redis-server &> /dev/null; then
        print_error "Redis is not installed. Please install Redis first."
        echo "On Ubuntu/Debian: sudo apt-get install redis-server"
        echo "On macOS: brew install redis"
        exit 1
    fi
    
    # Check if required ports are available
    local required_ports=(6379 5000 3000)
    for port in "${required_ports[@]}"; do
        if check_port $port; then
            print_warning "Port $port is already in use. Make sure no other services are running."
        fi
    done
    
    # Start Redis
    print_status "Starting Redis server..."
    
    # Check if Redis is already running
    if redis-cli ping >/dev/null 2>&1; then
        print_success "Redis is already running"
    else
        if [ "$BACKGROUND" = true ]; then
            redis-server --port 6379 --daemonize yes
            sleep 2
            if redis-cli ping >/dev/null 2>&1; then
                print_success "Redis started successfully"
            else
                print_error "Redis failed to start"
                exit 1
            fi
        else
            redis-server --port 6379 &
            REDIS_PID=$!
            wait_for_service "Redis" 6379 || exit 1
        fi
    fi
    
    # Start Backend
    print_status "Starting Backend API..."
    if [ "$BACKGROUND" = true ]; then
        BACKEND_PID=$(start_service_background "Backend" "./scripts/start_backend.sh" 5000 "backend.pid" "backend.log")
        if [ $? -ne 0 ]; then
            print_error "Failed to start Backend"
            cleanup
            exit 1
        fi
    else
        ./scripts/start_backend.sh &
        BACKEND_PID=$!
    fi
    
    # Wait for backend to be ready
    wait_for_service "Backend" 5000 || {
        print_error "Backend failed to start properly"
        cleanup
        exit 1
    }
    
    # Start Frontend (if not skipped)
    if [ "$SKIP_FRONTEND" = false ]; then
        print_status "Starting Frontend..."
        if [ "$BACKGROUND" = true ]; then
            FRONTEND_PID=$(start_service_background "Frontend" "./scripts/start_frontend.sh" 3000 "frontend.pid" "frontend.log")
            if [ $? -ne 0 ]; then
                print_error "Failed to start Frontend"
                cleanup
                exit 1
            fi
        else
            ./scripts/start_frontend.sh &
            FRONTEND_PID=$!
        fi
        
        # Wait for frontend to be ready
        wait_for_service "Frontend" 3000 || {
            print_error "Frontend failed to start properly"
            cleanup
            exit 1
        }
    else
        print_status "Skipping Frontend startup"
    fi
    
    # Final status
    print_success "All services started successfully!"
    echo
    echo "Service Status:"
    echo "  Redis:     http://localhost:6379"
    echo "  Backend:   http://localhost:5000/api/v1/docs"
    echo "  Frontend:  http://localhost:3000"
    echo
    echo "To stop all services, press Ctrl+C"
    echo "To view logs:"
    echo "  Backend:   tail -f backend.log"
    echo "  Frontend:  tail -f frontend.log"
    echo
    
    # Wait for all background processes if not in background mode
    if [ "$BACKGROUND" = false ]; then
        wait
    else
        print_status "All services are running in background mode"
        print_status "Use 'ps aux | grep -E \"(redis|backend|frontend)\"' to see running processes"
    fi
}

# Run the main function
main "$@" 