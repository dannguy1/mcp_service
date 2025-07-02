#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=== WiFiAgent Creation Test ===")

try:
    # Test 1: Check if we can import the WiFiAgent
    print("\n1. Testing WiFiAgent import...")
    from app.mcp_service.agents.wifi_agent import WiFiAgent
    print("  ✅ WiFiAgent imported successfully")
    
    # Test 2: Check if we can import other components
    print("\n2. Testing component imports...")
    from app.mcp_service.data_service import DataService
    from app.components.model_manager import ModelManager
    from app.models.config import ModelConfig
    print("  ✅ All components imported successfully")
    
    # Test 3: Check WiFi agent configuration
    print("\n3. Testing WiFi agent configuration...")
    from app.mcp_service.components.agent_registry import agent_registry
    
    wifi_config = agent_registry.get_agent_config('wifi_agent')
    if wifi_config:
        print("  ✅ WiFi agent configuration found")
        print(f"  - Model path: {wifi_config.get('model_path')}")
        print(f"  - Agent type: {wifi_config.get('agent_type')}")
    else:
        print("  ❌ WiFi agent configuration NOT found")
        sys.exit(1)
    
    # Test 4: Try to create WiFiAgent
    print("\n4. Testing WiFiAgent creation...")
    try:
        model_config = ModelConfig()
        data_service = DataService(model_config)
        model_manager = ModelManager.get_instance(model_config)
        
        agent = WiFiAgent(wifi_config, data_service, model_manager)
        print("  ✅ WiFiAgent created successfully")
        print(f"  - Agent type: {type(agent).__name__}")
        print(f"  - Model: {type(agent.model) if agent.model else None}")
        print(f"  - Model valid: {agent._is_valid_model(agent.model) if agent.model else False}")
        print(f"  - Status: {agent.status}")
        print(f"  - Is running: {agent.is_running}")
        
    except Exception as e:
        print(f"  ❌ Error creating WiFiAgent: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 5: Check agent registry creation
    print("\n5. Testing agent registry creation...")
    try:
        agent = agent_registry.create_agent('wifi_agent', data_service, model_manager)
        if agent:
            print("  ✅ Agent registry created WiFiAgent successfully")
        else:
            print("  ❌ Agent registry failed to create WiFiAgent")
    except Exception as e:
        print(f"  ❌ Error in agent registry creation: {e}")
        import traceback
        traceback.print_exc()
    
except Exception as e:
    print(f"❌ Error in test: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===") 