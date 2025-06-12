#!/bin/bash

# Navigate to the backend directory
cd "$(dirname "$0")/../backend"

# Remove existing virtual environment
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi
    
# Create new virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing backend dependencies..."
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export FLASK_APP=app
export FLASK_DEBUG=1
export REDIS_URL=redis://localhost:6379/0
export CORS_ORIGINS=http://localhost:3000
export SOCKETIO_MESSAGE_QUEUE=redis://localhost:6379/0
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Start the Flask development server
echo "Starting backend development server..."
cd "$(dirname "$0")/../backend"  # Ensure we're in the backend directory
flask run --host=0.0.0.0 --port=5000