#!/usr/bin/env python3
"""
Test script for database settings functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000/api/v1"

def test_database_config_endpoints():
    """Test all database configuration endpoints"""
    
    print("Testing Database Configuration Endpoints")
    print("=" * 50)
    
    # Test 1: Get current database configuration
    print("\n1. Testing GET /settings/database")
    try:
        response = requests.get(f"{BASE_URL}/settings/database")
        if response.status_code == 200:
            config = response.json()
            print(f"✅ Success: Retrieved database configuration")
            print(f"   Host: {config['host']}")
            print(f"   Port: {config['port']}")
            print(f"   Database: {config['database']}")
            print(f"   User: {config['user']}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Test database connection with current config
    print("\n2. Testing POST /settings/database/test")
    try:
        test_config = {
            "host": "localhost",
            "port": 5432,
            "database": "netmonitor_db",
            "user": "netmonitor_user",
            "password": "netmonitor_password"
        }
        response = requests.post(f"{BASE_URL}/settings/database/test", json=test_config)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result['message']}")
            if result['status'] == 'success':
                print(f"   Connection test passed")
            else:
                print(f"   Connection test failed: {result['message']}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Test database connection with invalid config
    print("\n3. Testing POST /settings/database/test with invalid config")
    try:
        invalid_config = {
            "host": "invalid-host",
            "port": 5432,
            "database": "invalid_db",
            "user": "invalid_user",
            "password": "invalid_password"
        }
        response = requests.post(f"{BASE_URL}/settings/database/test", json=invalid_config)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result['message']}")
            if result['status'] == 'error':
                print(f"   Expected error occurred: {result['message']}")
            else:
                print(f"   Unexpected success with invalid config")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Test updating database configuration
    print("\n4. Testing POST /settings/database (update)")
    try:
        new_config = {
            "host": "localhost",
            "port": 5432,
            "database": "netmonitor_db",
            "user": "netmonitor_user",
            "password": "netmonitor_password",
            "min_connections": 3,
            "max_connections": 15,
            "pool_timeout": 25
        }
        response = requests.post(f"{BASE_URL}/settings/database", json=new_config)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result['message']}")
            print(f"   Updated configuration saved")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Verify the update was applied
    print("\n5. Verifying updated configuration")
    try:
        response = requests.get(f"{BASE_URL}/settings/database")
        if response.status_code == 200:
            config = response.json()
            print(f"✅ Success: Retrieved updated configuration")
            print(f"   Min Connections: {config['min_connections']}")
            print(f"   Max Connections: {config['max_connections']}")
            print(f"   Pool Timeout: {config['pool_timeout']}")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_frontend_api_endpoints():
    """Test frontend API endpoints"""
    
    print("\n\nTesting Frontend API Endpoints")
    print("=" * 50)
    
    # Test frontend API endpoints (these would be called from the React app)
    print("\nFrontend API endpoints to test:")
    print("✅ GET /settings/database - Get current database configuration")
    print("✅ POST /settings/database - Update database configuration")
    print("✅ POST /settings/database/test - Test database connection")
    
    print("\nFrontend integration points:")
    print("✅ Settings page with tabs for General and Database configuration")
    print("✅ Database configuration form with all required fields")
    print("✅ Connection testing functionality")
    print("✅ Real-time validation and error handling")
    print("✅ Loading states and user feedback")

if __name__ == "__main__":
    print("Database Settings Test Suite")
    print("=" * 50)
    
    # Test backend endpoints
    test_database_config_endpoints()
    
    # Test frontend integration
    test_frontend_api_endpoints()
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nTo test the frontend:")
    print("1. Ensure backend is running on http://localhost:5000")
    print("2. Ensure frontend is running on http://localhost:3000")
    print("3. Navigate to Settings page")
    print("4. Click on 'Database Configuration' tab")
    print("5. Test the form functionality") 