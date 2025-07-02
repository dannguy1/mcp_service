#!/usr/bin/env python3
"""
Debug script to test agent model loading for SystemAgent and DNSAgent.
"""

import sys
import os
import asyncio
import yaml
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.mcp_service.components.agent_registry import AgentRegistry
from app.mcp_service.data_service import DataService
from app.components.model_manager import ModelManager
from app.models.config import ModelConfig

async def test_agent_loading():
    """Test agent model loading for SystemAgent and DNSAgent."""
    
    print("=== Testing Agent Model Loading ===")
    
    # Initialize components
    config = ModelConfig()
    model_manager = ModelManager.get_instance(config)
    data_service = DataService(config)
    agent_registry = AgentRegistry()
    
    # Test SystemAgent
    print("\n--- Testing SystemAgent ---")
    system_config_path = Path("app/config/agents/system_agent.yaml")
    if system_config_path.exists():
        with open(system_config_path, 'r') as f:
            system_config = yaml.safe_load(f)
        
        print(f"SystemAgent config loaded: {system_config['name']}")
        print(f"Model path: {system_config['model_path']}")
        
        # Check if model path exists
        model_path = system_config['model_path']
        print(f"Model path exists: {os.path.exists(model_path)}")
        print(f"Model path is directory: {os.path.isdir(model_path)}")
        
        if os.path.isdir(model_path):
            model_file = os.path.join(model_path, 'model.joblib')
            print(f"Model file exists: {os.path.exists(model_file)}")
            
            if os.path.exists(model_file):
                try:
                    import joblib
                    model = joblib.load(model_file)
                    print(f"Model loaded successfully: {type(model)}")
                    print(f"Model has predict: {hasattr(model, 'predict')}")
                except Exception as e:
                    print(f"Error loading model: {e}")
    
    # Test DNSAgent
    print("\n--- Testing DNSAgent ---")
    dns_config_path = Path("app/config/agents/dns_agent.yaml")
    if dns_config_path.exists():
        with open(dns_config_path, 'r') as f:
            dns_config = yaml.safe_load(f)
        
        print(f"DNSAgent config loaded: {dns_config['name']}")
        print(f"Model path: {dns_config['model_path']}")
        
        # Check if model path exists
        model_path = dns_config['model_path']
        print(f"Model path exists: {os.path.exists(model_path)}")
        print(f"Model path is directory: {os.path.isdir(model_path)}")
        
        if os.path.isdir(model_path):
            model_file = os.path.join(model_path, 'model.joblib')
            print(f"Model file exists: {os.path.exists(model_file)}")
            
            if os.path.exists(model_file):
                try:
                    import joblib
                    model = joblib.load(model_file)
                    print(f"Model loaded successfully: {type(model)}")
                    print(f"Model has predict: {hasattr(model, 'predict')}")
                except Exception as e:
                    print(f"Error loading model: {e}")
    
    # Test agent creation
    print("\n--- Testing Agent Creation ---")
    try:
        # Try to create SystemAgent
        from app.mcp_service.agents.ml_based_agent import MLBasedAgent
        
        if 'system_config' in locals():
            system_agent = MLBasedAgent(system_config, data_service, model_manager)
            print(f"SystemAgent created successfully")
            print(f"SystemAgent model: {system_agent.model}")
            print(f"SystemAgent model is valid: {system_agent._is_valid_model(system_agent.model) if system_agent.model else False}")
        
        if 'dns_config' in locals():
            dns_agent = MLBasedAgent(dns_config, data_service, model_manager)
            print(f"DNSAgent created successfully")
            print(f"DNSAgent model: {dns_agent.model}")
            print(f"DNSAgent model is valid: {dns_agent._is_valid_model(dns_agent.model) if dns_agent.model else False}")
            
    except Exception as e:
        print(f"Error creating agents: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_loading()) 