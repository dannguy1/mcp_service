#!/bin/bash

# Function to handle script termination
cleanup() {
    echo "Shutting down development environment..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# Set up trap for cleanup on script termination
trap cleanup SIGINT SIGTERM

# Check if Node.js is installed before starting
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install it first:"
    echo "   Run: ./scripts/install_nodejs.sh"
    echo "   Or manually install Node.js from https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js found: $(node --version)"

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
echo "Starting Backend..."
./scripts/start_backend.sh &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start frontend
echo "Starting Frontend..."
./scripts/start_frontend.sh &
FRONTEND_PID=$!

# Wait for all background processes
wait 