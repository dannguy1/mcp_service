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

# Try ports 3001-3010
for port in {3001..3010}; do
    if ! check_port $port; then
        echo "Starting frontend development server on port $port..."
        export VITE_PORT=$port
        npm run dev
        exit 0
    fi
done

echo "Error: No available ports found between 3001-3010"
exit 1