#!/bin/bash

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo "Redis is not installed. Please install Redis first."
    echo "On Ubuntu/Debian: sudo apt-get install redis-server"
    echo "On macOS: brew install redis"
    exit 1
fi

# Start Redis server
echo "Starting Redis server..."
redis-server --port 6379 