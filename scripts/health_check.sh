#!/bin/bash

# Health check utility script

# Default configuration
DEFAULT_BACKEND_URL="http://localhost:5000"
DEFAULT_MCP_URL="http://localhost:5555"
DEFAULT_FRONTEND_URL="http://localhost:3000"
DEFAULT_REDIS_HOST="localhost"
DEFAULT_REDIS_PORT="6379"

# Parse command line arguments
BACKEND_URL=${1:-$DEFAULT_BACKEND_URL}
MCP_URL=${2:-$DEFAULT_MCP_URL}
FRONTEND_URL=${3:-$DEFAULT_FRONTEND_URL}
REDIS_HOST=${4:-$DEFAULT_REDIS_HOST}
REDIS_PORT=${5:-$DEFAULT_REDIS_PORT}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Health Check Report${NC}"
echo "================================"
echo ""

# Function to check HTTP endpoint
check_http_endpoint() {
    local url=$1
    local service=$2
    local timeout=${3:-10}
    
    echo -n "Checking $service ($url)... "
    
    if curl -s --max-time $timeout "$url/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ HEALTHY${NC}"
        return 0
    elif curl -s --max-time $timeout "$url" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  RESPONDING (no /health endpoint)${NC}"
        return 0
    else
        echo -e "${RED}❌ UNHEALTHY${NC}"
        return 1
    fi
}

# Function to check Redis
check_redis() {
    local host=$1
    local port=$2
    
    echo -n "Checking Redis ($host:$port)... "
    
    if command -v redis-cli > /dev/null 2>&1; then
        if redis-cli -h $host -p $port ping > /dev/null 2>&1; then
            echo -e "${GREEN}✅ HEALTHY${NC}"
            return 0
        else
            echo -e "${RED}❌ UNHEALTHY${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  SKIPPED (redis-cli not available)${NC}"
        return 0
    fi
}

# Function to check process
check_process() {
    local process_pattern=$1
    local service=$2
    
    echo -n "Checking $service process... "
    
    if pgrep -f "$process_pattern" > /dev/null 2>&1; then
        local pids=$(pgrep -f "$process_pattern")
        echo -e "${GREEN}✅ RUNNING (PIDs: $pids)${NC}"
        return 0
    else
        echo -e "${RED}❌ NOT RUNNING${NC}"
        return 1
    fi
}

# Function to check port
check_port() {
    local port=$1
    local service=$2
    
    echo -n "Checking $service port ($port)... "
    
    if lsof -Pi :$port -sTCP:LISTEN -t > /dev/null 2>&1; then
        echo -e "${GREEN}✅ LISTENING${NC}"
        return 0
    else
        echo -e "${RED}❌ NOT LISTENING${NC}"
        return 1
    fi
}

# Initialize counters
healthy_count=0
total_count=0

# Check Backend
echo -e "${BLUE}Backend Service:${NC}"
check_process "uvicorn.*app.main:app" "Backend" && ((healthy_count++))
((total_count++))
check_port 5000 "Backend" && ((healthy_count++))
((total_count++))
check_http_endpoint "$BACKEND_URL" "Backend" && ((healthy_count++))
((total_count++))

echo ""

# Check MCP Service
echo -e "${BLUE}MCP Service:${NC}"
check_process "python.*mcp_service.py" "MCP Service" && ((healthy_count++))
((total_count++))
check_port 5555 "MCP Service" && ((healthy_count++))
((total_count++))
check_http_endpoint "$MCP_URL" "MCP Service" && ((healthy_count++))
((total_count++))

echo ""

# Check Frontend
echo -e "${BLUE}Frontend Service:${NC}"
check_process "npm.*dev.*3000" "Frontend" && ((healthy_count++))
((total_count++))
check_port 3000 "Frontend" && ((healthy_count++))
((total_count++))
check_http_endpoint "$FRONTEND_URL" "Frontend" && ((healthy_count++))
((total_count++))

echo ""

# Check Redis
echo -e "${BLUE}Redis Service:${NC}"
check_process "redis-server" "Redis" && ((healthy_count++))
((total_count++))
check_port 6379 "Redis" && ((healthy_count++))
((total_count++))
check_redis "$REDIS_HOST" "$REDIS_PORT" && ((healthy_count++))
((total_count++))

echo ""

# Check Prometheus
echo -e "${BLUE}Prometheus Service:${NC}"
check_process "prometheus" "Prometheus" && ((healthy_count++))
((total_count++))
check_port 9090 "Prometheus" && ((healthy_count++))
((total_count++))
check_http_endpoint "http://localhost:9090" "Prometheus" && ((healthy_count++))
((total_count++))

echo ""

# Check Grafana
echo -e "${BLUE}Grafana Service:${NC}"
check_process "grafana-server" "Grafana" && ((healthy_count++))
((total_count++))
check_port 3001 "Grafana" && ((healthy_count++))
((total_count++))
check_http_endpoint "http://localhost:3001" "Grafana" && ((healthy_count++))
((total_count++))

echo ""
echo "================================"

# Calculate health percentage
health_percentage=$((healthy_count * 100 / total_count))

echo -e "${BLUE}Overall Health: $healthy_count/$total_count checks passed ($health_percentage%)${NC}"

if [ $health_percentage -eq 100 ]; then
    echo -e "${GREEN}🎉 All services are healthy!${NC}"
    exit 0
elif [ $health_percentage -ge 80 ]; then
    echo -e "${YELLOW}⚠️  Most services are healthy, but some issues detected${NC}"
    exit 0
else
    echo -e "${RED}❌ Multiple services are unhealthy${NC}"
    echo ""
    echo "Troubleshooting tips:"
    echo "1. Check if all services are started: ./scripts/start_all.sh"
    echo "2. Check logs for errors: tail -f *.log"
    echo "3. Restart services: ./scripts/stop_all.sh && ./scripts/start_all.sh"
    echo "4. Check system resources: ./scripts/monitor_resources.sh"
    exit 1
fi 