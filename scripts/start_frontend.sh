#!/bin/bash

# Navigate to the frontend directory
cd "$(dirname "$0")/../frontend"

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Check if port 3000 is available
if ! check_port 3000; then
    echo "Starting frontend development server on port 3000..."
    npm run dev
    exit 0
else
    echo "Error: Port 3000 is already in use"
    exit 1
fi