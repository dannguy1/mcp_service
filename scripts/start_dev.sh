#!/bin/bash

# Function to handle script termination
cleanup() {
    echo "Shutting down development environment..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# Set up trap for cleanup on script termination
trap cleanup SIGINT SIGTERM

# Function to check if a service is ready
check_service_ready() {
    local url=$1
    local max_attempts=30
    local attempt=0
    
    echo "🔍 Checking if service is ready at $url..."
    
    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        echo "⚠️  curl not available, using fallback health check..."
        # Fallback: just wait and assume it's ready
        sleep 10
        echo "✅ Assuming service is ready (curl not available for verification)"
        return 0
    fi
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            echo "✅ Service is ready!"
            return 0
        fi
        echo "⏳ Waiting for service to be ready... (attempt $((attempt + 1))/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ Service failed to become ready after $max_attempts attempts"
    return 1
}

# Check if Node.js is installed before starting
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install it first:"
    echo "   Run: ./scripts/install_nodejs.sh"
    echo "   Or manually install Node.js from https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js found: $(node --version)"

# Check if curl is available for health checks
if ! command -v curl &> /dev/null; then
    echo "⚠️  curl is not installed. Installing curl for health checks..."
    sudo apt-get update && sudo apt-get install -y curl
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install curl. Health checks will be disabled."
        echo "   You can install curl manually: sudo apt-get install curl"
    fi
fi

# Check if Redis is running
echo "🔍 Checking if Redis is running..."
if ! redis-cli ping | grep -q PONG; then
    echo "❌ Redis is not running on port 6379."
    echo "   Please start Redis with: sudo systemctl start redis-server"
    echo "   Or check status with: sudo systemctl status redis-server"
    exit 1
fi
echo "✅ Redis is running and ready."

# Start backend in the background
echo "🚀 Starting Backend..."
./scripts/start_backend.sh -b &
BACKEND_PID=$!

# Wait for backend to be ready
echo "⏳ Waiting for backend to initialize..."
if ! check_service_ready "http://localhost:5000/api/v1/health"; then
    echo "❌ Backend failed to start properly. Check backend logs for details."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Backend is ready and responding to health checks."

# Start frontend
echo "🚀 Starting Frontend..."
./scripts/start_frontend.sh &
FRONTEND_PID=$!

# Wait for frontend to be ready
echo "⏳ Waiting for frontend to initialize..."
if ! check_service_ready "http://localhost:3000"; then
    echo "❌ Frontend failed to start properly. Check frontend logs for details."
    kill $FRONTEND_PID 2>/dev/null
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Frontend is ready and accessible."
echo "🎉 Development environment is fully started!"
echo "   Backend API: http://localhost:5000/api/v1/docs"
echo "   Frontend UI: http://localhost:3000"
echo "   Health Check: http://localhost:5000/api/v1/health"

# Wait for all background processes
wait 