#!/bin/bash

# Function to handle script termination
cleanup() {
    echo "Shutting down development environment..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# Set up trap for cleanup on script termination
trap cleanup SIGINT SIGTERM

# Start Redis in the background
echo "Starting Redis..."
./scripts/start_redis.sh &
REDIS_PID=$!

# Wait for Redis to start
sleep 2

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