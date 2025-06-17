#!/bin/bash

set -e

# Parse command line arguments
BACKGROUND=false
BACKEND_PORT=5000
MCP_PORT=5555
FRONTEND_PORT=3000
REDIS_PORT=6379
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -b|--background) BACKGROUND=true ;;
        --backend-port) BACKEND_PORT="$2"; shift ;;
        --mcp-port) MCP_PORT="$2"; shift ;;
        --frontend-port) FRONTEND_PORT="$2"; shift ;;
        --redis-port) REDIS_PORT="$2"; shift ;;
        --prometheus-port) PROMETHEUS_PORT="$2"; shift ;;
        --grafana-port) GRAFANA_PORT="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Get the absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Navigate to the project root
cd "$PROJECT_ROOT"

echo "[INFO] Starting all services from: $(pwd)"
echo "[INFO] Backend port: $BACKEND_PORT"
echo "[INFO] MCP Service port: $MCP_PORT"
echo "[INFO] Frontend port: $FRONTEND_PORT"
echo "[INFO] Redis port: $REDIS_PORT"
echo "[INFO] Prometheus port: $PROMETHEUS_PORT"
echo "[INFO] Grafana port: $GRAFANA_PORT"

# Function to check if port is in use
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "[ERROR] Port $port is already in use by $service. Please stop the process using this port."
        return 1
    fi
    return 0
}

# Function to wait for port to be available
wait_for_port() {
    local port=$1
    local service=$2
    local max_attempts=30
    local attempt=0
    
    echo "[INFO] Waiting for $service to start on port $port..."
    while [ $attempt -lt $max_attempts ]; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "[INFO] $service is now available on port $port"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    echo "[ERROR] Timeout waiting for $service to start on port $port"
    return 1
}

# Function to check if a service is installed
check_service() {
    local service=$1
    local check_cmd=$2
    
    if ! command -v $check_cmd &> /dev/null; then
        echo "[ERROR] $service is not installed. Please install $service first."
        return 1
    fi
    return 0
}

# Function to start Redis
start_redis() {
    echo "[INFO] Starting Redis..."
    
    if ! check_service "Redis" "redis-server"; then
        echo "[WARN] Redis not found. Skipping Redis startup."
        return 0
    fi
    
    if ! check_port $REDIS_PORT "Redis"; then
        return 1
    fi
    
    if [ "$BACKGROUND" = true ]; then
        nohup redis-server --port $REDIS_PORT > redis.log 2>&1 &
        echo $! > redis.pid
        echo "[INFO] Redis started in background. PID: $(cat redis.pid)"
    else
        echo "[INFO] Starting Redis in foreground..."
        redis-server --port $REDIS_PORT &
        echo $! > redis.pid
    fi
    
    if wait_for_port $REDIS_PORT "Redis"; then
        echo "[INFO] Redis is ready on port $REDIS_PORT"
    else
        echo "[ERROR] Failed to start Redis"
        return 1
    fi
}

# Function to start Prometheus
start_prometheus() {
    echo "[INFO] Starting Prometheus..."
    
    if ! check_service "Prometheus" "prometheus"; then
        echo "[WARN] Prometheus not found. Skipping Prometheus startup."
        return 0
    fi
    
    if ! check_port $PROMETHEUS_PORT "Prometheus"; then
        return 1
    fi
    
    # Check if prometheus.yml exists
    if [ ! -f "prometheus/prometheus.yml" ]; then
        echo "[WARN] prometheus.yml not found. Skipping Prometheus startup."
        return 0
    fi
    
    if [ "$BACKGROUND" = true ]; then
        nohup prometheus --config.file=prometheus/prometheus.yml --web.listen-address=:$PROMETHEUS_PORT > prometheus.log 2>&1 &
        echo $! > prometheus.pid
        echo "[INFO] Prometheus started in background. PID: $(cat prometheus.pid)"
    else
        echo "[INFO] Starting Prometheus in foreground..."
        prometheus --config.file=prometheus/prometheus.yml --web.listen-address=:$PROMETHEUS_PORT &
        echo $! > prometheus.pid
    fi
    
    if wait_for_port $PROMETHEUS_PORT "Prometheus"; then
        echo "[INFO] Prometheus is ready on port $PROMETHEUS_PORT"
    else
        echo "[ERROR] Failed to start Prometheus"
        return 1
    fi
}

# Function to start Grafana
start_grafana() {
    echo "[INFO] Starting Grafana..."
    
    if ! check_service "Grafana" "grafana-server"; then
        echo "[WARN] Grafana not found. Skipping Grafana startup."
        return 0
    fi
    
    if ! check_port $GRAFANA_PORT "Grafana"; then
        return 1
    fi
    
    if [ "$BACKGROUND" = true ]; then
        nohup grafana-server --config=/etc/grafana/grafana.ini --homepath=/usr/share/grafana --pidfile=grafana.pid > grafana.log 2>&1 &
        echo $! > grafana.pid
        echo "[INFO] Grafana started in background. PID: $(cat grafana.pid)"
    else
        echo "[INFO] Starting Grafana in foreground..."
        grafana-server --config=/etc/grafana/grafana.ini --homepath=/usr/share/grafana --pidfile=grafana.pid &
        echo $! > grafana.pid
    fi
    
    if wait_for_port $GRAFANA_PORT "Grafana"; then
        echo "[INFO] Grafana is ready on port $GRAFANA_PORT"
    else
        echo "[ERROR] Failed to start Grafana"
        return 1
    fi
}

# Function to start Backend
start_backend() {
    echo "[INFO] Starting Backend..."
    
    if ! check_port $BACKEND_PORT "Backend"; then
        return 1
    fi
    
    # Set environment variables for backend
    export PORT=$BACKEND_PORT
    
    if [ "$BACKGROUND" = true ]; then
        nohup ./scripts/start_backend.sh -b -p $BACKEND_PORT > backend_start.log 2>&1 &
        echo $! > backend_start.pid
        echo "[INFO] Backend startup initiated in background. PID: $(cat backend_start.pid)"
    else
        echo "[INFO] Starting Backend in foreground..."
        ./scripts/start_backend.sh -p $BACKEND_PORT &
        echo $! > backend_start.pid
    fi
    
    if wait_for_port $BACKEND_PORT "Backend"; then
        echo "[INFO] Backend is ready on port $BACKEND_PORT"
    else
        echo "[ERROR] Failed to start Backend"
        return 1
    fi
}

# Function to start MCP Service
start_mcp_service() {
    echo "[INFO] Starting MCP Service..."
    
    if ! check_port $MCP_PORT "MCP Service"; then
        return 1
    fi
    
    # Set environment variables for MCP service
    export PORT=$MCP_PORT
    
    if [ "$BACKGROUND" = true ]; then
        nohup ./scripts/start_mcp_service.sh -b -p $MCP_PORT > mcp_start.log 2>&1 &
        echo $! > mcp_start.pid
        echo "[INFO] MCP Service startup initiated in background. PID: $(cat mcp_start.pid)"
    else
        echo "[INFO] Starting MCP Service in foreground..."
        ./scripts/start_mcp_service.sh -p $MCP_PORT &
        echo $! > mcp_start.pid
    fi
    
    if wait_for_port $MCP_PORT "MCP Service"; then
        echo "[INFO] MCP Service is ready on port $MCP_PORT"
    else
        echo "[ERROR] Failed to start MCP Service"
        return 1
    fi
}

# Function to start Frontend
start_frontend() {
    echo "[INFO] Starting Frontend..."
    
    if ! check_port $FRONTEND_PORT "Frontend"; then
        return 1
    fi
    
    # Set environment variables for frontend
    export VITE_API_URL=http://localhost:$BACKEND_PORT
    export VITE_MCP_SERVICE_URL=http://localhost:$MCP_PORT
    
    if [ "$BACKGROUND" = true ]; then
        nohup ./scripts/start_frontend.sh -b -p $FRONTEND_PORT > frontend_start.log 2>&1 &
        echo $! > frontend_start.pid
        echo "[INFO] Frontend startup initiated in background. PID: $(cat frontend_start.pid)"
    else
        echo "[INFO] Starting Frontend in foreground..."
        ./scripts/start_frontend.sh -p $FRONTEND_PORT &
        echo $! > frontend_start.pid
    fi
    
    if wait_for_port $FRONTEND_PORT "Frontend"; then
        echo "[INFO] Frontend is ready on port $FRONTEND_PORT"
    else
        echo "[ERROR] Failed to start Frontend"
        return 1
    fi
}

# Main startup sequence
echo "[INFO] Starting all services..."

# Start infrastructure services first
start_redis
start_prometheus
start_grafana

# Wait a moment for infrastructure to be ready
sleep 2

# Start application services
start_backend
start_mcp_service
start_frontend

echo "[INFO] All services started successfully!"
echo "[INFO] Service URLs:"
echo "[INFO]   Frontend: http://localhost:$FRONTEND_PORT"
echo "[INFO]   Backend API: http://localhost:$BACKEND_PORT"
echo "[INFO]   MCP Service: http://localhost:$MCP_PORT"
echo "[INFO]   Prometheus: http://localhost:$PROMETHEUS_PORT"
echo "[INFO]   Grafana: http://localhost:$GRAFANA_PORT"
echo "[INFO]   Redis: localhost:$REDIS_PORT"

if [ "$BACKGROUND" = true ]; then
    echo "[INFO] All services are running in background mode."
    echo "[INFO] To stop all services, run: ./scripts/stop_all.sh"
    echo "[INFO] Check individual log files for service details."
else
    echo "[INFO] All services are running in foreground mode."
    echo "[INFO] Press Ctrl+C to stop all services."
    
    # Wait for user interrupt
    trap 'echo "[INFO] Stopping all services..."; ./scripts/stop_all.sh; exit 0' INT
    wait
fi 