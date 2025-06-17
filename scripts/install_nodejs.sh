#!/bin/bash

# Script to install Node.js and npm on Raspberry Pi
# This script installs the LTS version of Node.js

set -e

echo "Installing Node.js and npm on Raspberry Pi..."

# Check if already installed
if command -v node &> /dev/null && command -v npm &> /dev/null; then
    echo "Node.js and npm are already installed:"
    echo "  Node.js version: $(node --version)"
    echo "  npm version: $(npm --version)"
    exit 0
fi

# Update package list
echo "Updating package list..."
sudo apt-get update

# Install required dependencies
echo "Installing required dependencies..."
sudo apt-get install -y curl

# Add NodeSource repository for LTS version
echo "Adding NodeSource repository..."
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -

# Install Node.js (includes npm)
echo "Installing Node.js and npm..."
sudo apt-get install -y nodejs

# Verify installation
if command -v node &> /dev/null && command -v npm &> /dev/null; then
    echo "✅ Node.js and npm installed successfully!"
    echo "  Node.js version: $(node --version)"
    echo "  npm version: $(npm --version)"
else
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi

# Optional: Install additional useful tools
echo "Installing additional development tools..."
sudo npm install -g npm@latest

echo "🎉 Node.js installation complete!"
echo "You can now run the frontend development server." 