#!/bin/bash

# Test script to verify startup improvements

echo "🧪 Testing startup improvements..."

# Test 1: Check if curl is available
echo "Test 1: Checking curl availability..."
if command -v curl &> /dev/null; then
    echo "✅ curl is available"
else
    echo "❌ curl is not available"
fi

# Test 2: Check if Node.js is available
echo "Test 2: Checking Node.js availability..."
if command -v node &> /dev/null; then
    echo "✅ Node.js is available: $(node --version)"
else
    echo "❌ Node.js is not available"
fi

# Test 3: Check if Redis is running
echo "Test 3: Checking Redis status..."
if redis-cli ping | grep -q PONG; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not running"
fi

# Test 4: Check port availability
echo "Test 4: Checking port availability..."
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is available
    fi
}

if check_port 5000; then
    echo "⚠️  Port 5000 is in use"
else
    echo "✅ Port 5000 is available"
fi

if check_port 3000; then
    echo "⚠️  Port 3000 is in use"
else
    echo "✅ Port 3000 is available"
fi

# Test 5: Test health check function (if curl is available)
if command -v curl &> /dev/null; then
    echo "Test 5: Testing health check function..."
    check_service_ready() {
        local url=$1
        local max_attempts=3
        local attempt=0
        
        echo "  Testing health check for $url..."
        while [ $attempt -lt $max_attempts ]; do
            if curl -s -f "$url" >/dev/null 2>&1; then
                echo "  ✅ Service is ready!"
                return 0
            fi
            echo "  ⏳ Waiting... (attempt $((attempt + 1))/$max_attempts)"
            sleep 1
            attempt=$((attempt + 1))
        done
        
        echo "  ❌ Service not ready after $max_attempts attempts"
        return 1
    }
    
    # Test with a non-existent service (should fail)
    if ! check_service_ready "http://localhost:9999"; then
        echo "✅ Health check correctly detected unavailable service"
    else
        echo "❌ Health check incorrectly reported unavailable service as ready"
    fi
else
    echo "Test 5: Skipped (curl not available)"
fi

echo "🧪 Startup tests completed!" 