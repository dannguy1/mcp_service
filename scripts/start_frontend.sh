#!/bin/bash

# Navigate to the frontend directory
cd "$(dirname "$0")/../frontend"

# Check if Node.js and npm are installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed."
    echo "Please install Node.js first:"
    echo "  For Raspberry Pi (ARM):"
    echo "    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -"
    echo "    sudo apt-get install -y nodejs"
    echo "  Or download from: https://nodejs.org/"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed."
    echo "Please install npm or use a Node.js installer that includes npm."
    exit 1
fi

# Display Node.js and npm versions
echo "Using Node.js version: $(node --version)"
echo "Using npm version: $(npm --version)"

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies. Please check your internet connection and try again."
        exit 1
    fi
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
    echo "Please stop the process using port 3000 or modify the frontend configuration to use a different port."
    exit 1
fi