#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from app.mcp_service.agents.wifi_agent import WiFiAgent

async def test_wifi_agent_simple():
    """Simple test to verify WiFiAgent can start."""
    
    # Create a minimal config
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
    class MockDataService:
        async def get_recent_logs(self, programs, minutes):
            return []
    
    data_service = MockDataService()
    
    print("Creating WiFiAgent...")
    agent = WiFiAgent(config, data_service)
    
    print(f"Agent model_path: {agent.model_path}")
    print(f"Model path exists: {os.path.exists(agent.model_path)}")
    print(f"Model path is directory: {os.path.isdir(agent.model_path)}")
    print(f"Agent model: {type(agent.model)}")
    print(f"Agent model is valid: {agent._is_valid_model(agent.model)}")
    
    # Test agent start
    print("\nTesting agent start...")
    try:
        await agent.start()
        print(f"Agent started successfully")
        print(f"Agent status: {agent.status}")
        print(f"Agent is_running: {agent.is_running}")
        print("✅ WiFiAgent test PASSED")
    except Exception as e:
        print(f"Error starting agent: {e}")
        import traceback
        traceback.print_exc()
        print("❌ WiFiAgent test FAILED")

if __name__ == "__main__":
    asyncio.run(test_wifi_agent_simple()) 