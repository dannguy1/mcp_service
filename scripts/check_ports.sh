#!/bin/bash

# Port checking utility script

# Default ports
DEFAULT_BACKEND_PORT=5000
DEFAULT_MCP_PORT=5555
DEFAULT_FRONTEND_PORT=3000
DEFAULT_REDIS_PORT=6379
DEFAULT_PROMETHEUS_PORT=9090
DEFAULT_GRAFANA_PORT=3001

# Parse command line arguments
BACKEND_PORT=${1:-$DEFAULT_BACKEND_PORT}
MCP_PORT=${2:-$DEFAULT_MCP_PORT}
FRONTEND_PORT=${3:-$DEFAULT_FRONTEND_PORT}
REDIS_PORT=${4:-$DEFAULT_REDIS_PORT}
PROMETHEUS_PORT=${5:-$DEFAULT_PROMETHEUS_PORT}
GRAFANA_PORT=${6:-$DEFAULT_GRAFANA_PORT}

echo "Checking port availability..."
echo "================================"

# Function to check port
check_port() {
    local port=$1
    local service=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        local process_info=$(lsof -Pi :$port -sTCP:LISTEN | grep LISTEN | head -1)
        echo "❌ Port $port ($service) - IN USE"
        echo "   Process: $process_info"
        return 1
    else
        echo "✅ Port $port ($service) - AVAILABLE"
        return 0
    fi
}

# Check all ports
all_available=true

check_port $BACKEND_PORT "Backend API" || all_available=false
check_port $MCP_PORT "MCP Service" || all_available=false
check_port $FRONTEND_PORT "Frontend" || all_available=false
check_port $REDIS_PORT "Redis" || all_available=false
check_port $PROMETHEUS_PORT "Prometheus" || all_available=false
check_port $GRAFANA_PORT "Grafana" || all_available=false

echo "================================"

if [ "$all_available" = true ]; then
    echo "✅ All ports are available!"
    exit 0
else
    echo "❌ Some ports are in use. Please stop the conflicting services."
    echo ""
    echo "To stop all services:"
    echo "  ./scripts/stop_all.sh"
    echo ""
    echo "To kill processes on specific ports:"
    echo "  sudo lsof -ti:$PORT | xargs kill -9"
    exit 1
fi 