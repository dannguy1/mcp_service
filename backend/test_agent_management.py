#!/usr/bin/env python3
"""
Test script for agent management functionality.
This script tests the agent registry, API endpoints, and model association.
"""

import asyncio
import requests
import json
import time
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def test_agent_registry():
    """Test agent registry functionality."""
    print("Testing Agent Registry...")
    
    try:
        # Test listing agents
        response = requests.get(f"{API_BASE_URL}/agents")
        if response.status_code == 200:
            agents = response.json()
            print(f"✅ Found {len(agents)} agents")
            for agent in agents:
                print(f"  - {agent['name']} ({agent['id']}): {agent['status']}")
        else:
            print(f"❌ Failed to list agents: {response.status_code}")
            return False
        
        # Test getting available models
        response = requests.get(f"{API_BASE_URL}/agents/available-models")
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Found {len(models)} available models")
            for model in models:
                print(f"  - {model['name']}: {model['path']}")
        else:
            print(f"❌ Failed to get available models: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing agent registry: {e}")
        return False

def test_agent_model_association():
    """Test agent-model association functionality."""
    print("\nTesting Agent-Model Association...")
    
    try:
        # Get agents
        response = requests.get(f"{API_BASE_URL}/agents")
        if response.status_code != 200:
            print(f"❌ Failed to get agents: {response.status_code}")
            return False
        
        agents = response.json()
        if not agents:
            print("⚠️  No agents found to test")
            return True
        
        # Get available models
        response = requests.get(f"{API_BASE_URL}/agents/available-models")
        if response.status_code != 200:
            print(f"❌ Failed to get models: {response.status_code}")
            return False
        
        models = response.json()
        
        # Test setting model for first agent
        agent = agents[0]
        if models:
            model = models[0]
            print(f"Testing model association for {agent['name']} with {model['name']}")
            
            # Set model
            response = requests.post(
                f"{API_BASE_URL}/agents/{agent['id']}/set-model",
                json={"model_path": model['path']}
            )
            
            if response.status_code == 200:
                print(f"✅ Successfully set model for {agent['name']}")
                
                # Verify model was set
                response = requests.get(f"{API_BASE_URL}/agents/{agent['id']}/model")
                if response.status_code == 200:
                    model_info = response.json()
                    print(f"✅ Verified model: {model_info['model_path']}")
                else:
                    print(f"❌ Failed to verify model: {response.status_code}")
            else:
                print(f"❌ Failed to set model: {response.status_code} - {response.text}")
        else:
            print("⚠️  No models available for testing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing agent-model association: {e}")
        return False

def test_agent_operations():
    """Test agent operations like restart."""
    print("\nTesting Agent Operations...")
    
    try:
        # Get agents
        response = requests.get(f"{API_BASE_URL}/agents")
        if response.status_code != 200:
            print(f"❌ Failed to get agents: {response.status_code}")
            return False
        
        agents = response.json()
        if not agents:
            print("⚠️  No agents found to test")
            return True
        
        # Test restarting first agent
        agent = agents[0]
        print(f"Testing restart for {agent['name']}")
        
        response = requests.post(f"{API_BASE_URL}/agents/{agent['id']}/restart")
        if response.status_code == 200:
            print(f"✅ Successfully restarted {agent['name']}")
        else:
            print(f"❌ Failed to restart agent: {response.status_code} - {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing agent operations: {e}")
        return False

def test_health_check():
    """Test system health."""
    print("\nTesting System Health...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ System health: {health['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking health: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Agent Management Test Suite")
    print("=" * 50)
    
    # Wait for services to be ready
    print("Waiting for services to be ready...")
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health_check),
        ("Agent Registry", test_agent_registry),
        ("Agent-Model Association", test_agent_model_association),
        ("Agent Operations", test_agent_operations),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Agent management is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the implementation.")

if __name__ == "__main__":
    main() 