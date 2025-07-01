#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import joblib
from app.mcp_service.agents.wifi_agent import WiFiAgent
from app.mcp_service.data_service import DataService

async def test_wifi_agent():
    """Test WiFiAgent model loading."""
    
    # Create a mock config
    config = {
        'model_path': '/home/dannguyen/WNC/mcp_service/backend/models/model_tmpo3jl9ugx.zip',
        'agent_id': 'wifi_agent',
        'name': 'WiFiAgent',
        'description': 'WiFi anomaly detection agent',
        'capabilities': [
            "Authentication failure detection",
            "Deauthentication flood detection",
            "Beacon frame flood detection"
        ],
        'process_filters': ['hostapd', 'wlceventd', 'acsd'],
        'analysis_rules': {
            'analysis_interval': 60,
            'lookback_minutes': 5
        }
    }
    
    # Create a mock data service
    data_service_config = {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'mcp_service',
            'username': 'postgres',
            'password': 'password'
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 0
        }
    }
    data_service = DataService(data_service_config)
    
    print("Creating WiFiAgent...")
    agent = WiFiAgent(config, data_service)
    
    print(f"Agent model_path: {agent.model_path}")
    print(f"Model path exists: {os.path.exists(agent.model_path)}")
    print(f"Model path is directory: {os.path.isdir(agent.model_path)}")
    
    # Test model loading directly
    print("\nTesting model loading directly...")
    model_file = os.path.join(agent.model_path, 'model.joblib')
    print(f"Model file path: {model_file}")
    print(f"Model file exists: {os.path.exists(model_file)}")
    
    if os.path.exists(model_file):
        try:
            model = joblib.load(model_file)
            print(f"Model loaded successfully: {type(model)}")
            print(f"Has predict method: {hasattr(model, 'predict')}")
        except Exception as e:
            print(f"Error loading model: {e}")
    
    # Test agent's model loading method
    print("\nTesting agent's model loading method...")
    model_loaded = agent._load_model_from_directory(agent.model_path)
    print(f"Model loaded by agent: {model_loaded}")
    print(f"Agent model: {agent.model}")
    print(f"Agent model has predict: {hasattr(agent.model, 'predict') if agent.model else False}")
    
    # Test agent start
    print("\nTesting agent start...")
    try:
        await agent.start()
        print(f"Agent started successfully")
        print(f"Agent status: {agent.status}")
        print(f"Agent is_running: {agent.is_running}")
    except Exception as e:
        print(f"Error starting agent: {e}")

if __name__ == "__main__":
    asyncio.run(test_wifi_agent()) 