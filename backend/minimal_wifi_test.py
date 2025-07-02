#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("=== Minimal WiFiAgent Test ===")

try:
    # Test 1: Check if we can import the agent registry
    print("\n1. Testing imports...")
    from app.mcp_service.components.agent_registry import agent_registry
    print("  ✅ Agent registry imported successfully")
    
    # Test 2: Check agent configurations
    print("\n2. Checking agent configurations...")
    configs = agent_registry.list_agent_configs()
    print(f"  Found {len(configs)} agent configurations:")
    for config_info in configs:
        print(f"    - {config_info['agent_id']}: {config_info['name']} ({config_info['agent_type']})")
    
    # Test 3: Check WiFi agent config specifically
    print("\n3. Checking WiFi agent configuration...")
    wifi_config = agent_registry.get_agent_config('wifi_agent')
    if wifi_config:
        print("  ✅ WiFi agent configuration found:")
        print(f"    - Model path: {wifi_config.get('model_path')}")
        print(f"    - Agent type: {wifi_config.get('agent_type')}")
        print(f"    - Process filters: {wifi_config.get('process_filters')}")
        
        # Test 4: Check if model file exists
        model_path = wifi_config.get('model_path')
        if model_path:
            print(f"\n4. Checking model file...")
            if os.path.exists(model_path):
                print(f"  ✅ Model file exists: {model_path}")
                if os.path.isdir(model_path):
                    print(f"    - It's a directory")
                    # Check for model.joblib inside
                    model_file = os.path.join(model_path, 'model.joblib')
                    if os.path.exists(model_file):
                        print(f"    - model.joblib found inside directory")
                    else:
                        print(f"    - model.joblib NOT found inside directory")
                else:
                    print(f"    - It's a file")
            else:
                print(f"  ❌ Model file does NOT exist: {model_path}")
        else:
            print("  ❌ No model path in configuration")
    else:
        print("  ❌ WiFi agent configuration NOT found!")
    
    # Test 5: Check registered agents
    print("\n5. Checking registered agents...")
    agents = agent_registry.list_agents()
    print(f"  Found {len(agents)} registered agents:")
    for agent_info in agents:
        print(f"    - {agent_info['id']}: {agent_info['name']} - Status: {agent_info['status']} - Running: {agent_info['is_running']}")
    
    # Test 6: Try to create WiFi agent (without starting)
    print("\n6. Testing WiFi agent creation...")
    try:
        from app.mcp_service.data_service import DataService
        from app.components.model_manager import ModelManager
        from app.models.config import ModelConfig
        
        config = ModelConfig()
        data_service = DataService(config)
        model_manager = ModelManager.get_instance(config)
        
        agent = agent_registry.create_agent('wifi_agent', data_service, model_manager)
        if agent:
            print("  ✅ WiFi agent created successfully")
            print(f"    - Agent type: {type(agent).__name__}")
            print(f"    - Model: {type(agent.model) if agent.model else None}")
            print(f"    - Status: {agent.status}")
            print(f"    - Is running: {agent.is_running}")
        else:
            print("  ❌ Failed to create WiFi agent")
    except Exception as e:
        print(f"  ❌ Error creating WiFi agent: {e}")
        import traceback
        traceback.print_exc()
    
except Exception as e:
    print(f"❌ Error in minimal test: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===") 