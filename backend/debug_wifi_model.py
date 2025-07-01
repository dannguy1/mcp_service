#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import joblib
from app.mcp_service.agents.wifi_agent import WiFiAgent
from app.mcp_service.data_service import DataService

async def debug_wifi_model():
    """Debug WiFiAgent model loading."""
    
    print("=== WiFiAgent Model Loading Debug ===")
    
    # Test 1: Check if model files exist
    model_dir = "/home/dannguyen/WNC/mcp_service/backend/models/model_tmpo3jl9ugx.zip"
    model_file = os.path.join(model_dir, 'model.joblib')
    scaler_file = os.path.join(model_dir, 'scaler.joblib')
    
    print(f"Model directory: {model_dir}")
    print(f"Model directory exists: {os.path.isdir(model_dir)}")
    print(f"Model file: {model_file}")
    print(f"Model file exists: {os.path.exists(model_file)}")
    print(f"Scaler file: {scaler_file}")
    print(f"Scaler file exists: {os.path.exists(scaler_file)}")
    
    # Test 2: Try to load model directly
    try:
        print("\n=== Loading model directly ===")
        model = joblib.load(model_file)
        print(f"Model loaded successfully: {type(model)}")
        print(f"Model has predict: {hasattr(model, 'predict')}")
        print(f"Model has predict_proba: {hasattr(model, 'predict_proba')}")
    except Exception as e:
        print(f"Error loading model directly: {e}")
    
    # Test 3: Create WiFiAgent and check model loading
    try:
        print("\n=== Creating WiFiAgent ===")
        config = {
            'model_path': model_dir,
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
                'lookback_minutes': 5,
                'severity_mapping': {}
            }
        }
        
        data_service = DataService()
        agent = WiFiAgent(config, data_service)
        
        print(f"Agent created successfully")
        print(f"Agent model: {agent.model}")
        print(f"Agent model type: {type(agent.model) if agent.model else None}")
        print(f"Agent model has predict: {hasattr(agent.model, 'predict') if agent.model else False}")
        print(f"Agent model is valid: {agent._is_valid_model(agent.model) if agent.model else False}")
        
        # Test 4: Try to start the agent
        print("\n=== Testing agent start ===")
        await agent.start()
        print(f"Agent status: {agent.status}")
        print(f"Agent is_running: {agent.is_running}")
        
    except Exception as e:
        print(f"Error creating/testing WiFiAgent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_wifi_model()) 