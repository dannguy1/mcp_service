#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
from app.mcp_service.components.agent_registry import agent_registry
from app.mcp_service.data_service import DataService
from app.components.model_manager import ModelManager
from app.models.config import ModelConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_wifi_status():
    """Debug the WiFiAgent status."""
    
    print("=== WiFiAgent Status Debug ===")
    
    # Initialize components
    config = ModelConfig()
    data_service = DataService(config)
    model_manager = ModelManager.get_instance(config)
    
    try:
        # Start data service
        await data_service.start()
        
        # Check agent configurations
        print("\n1. Checking agent configurations...")
        configs = agent_registry.list_agent_configs()
        print(f"Found {len(configs)} agent configurations:")
        for config_info in configs:
            print(f"  - {config_info['agent_id']}: {config_info['name']} ({config_info['agent_type']})")
        
        # Check if WiFi agent config exists
        wifi_config = agent_registry.get_agent_config('wifi_agent')
        if wifi_config:
            print(f"\n2. WiFi agent configuration found:")
            print(f"  - Model path: {wifi_config.get('model_path')}")
            print(f"  - Agent type: {wifi_config.get('agent_type')}")
            print(f"  - Process filters: {wifi_config.get('process_filters')}")
        else:
            print("\n2. ❌ WiFi agent configuration NOT found!")
            return
        
        # Try to create WiFi agent
        print("\n3. Creating WiFi agent...")
        agent = agent_registry.create_agent('wifi_agent', data_service, model_manager)
        if agent:
            print(f"  ✅ Agent created successfully")
            print(f"  - Agent type: {type(agent).__name__}")
            print(f"  - Model: {type(agent.model) if agent.model else None}")
            print(f"  - Model valid: {agent._is_valid_model(agent.model) if agent.model else False}")
            print(f"  - Status: {agent.status}")
            print(f"  - Is running: {agent.is_running}")
            
            # Try to start the agent
            print("\n4. Starting WiFi agent...")
            try:
                await agent.start()
                print(f"  ✅ Agent started successfully")
                print(f"  - Status: {agent.status}")
                print(f"  - Is running: {agent.is_running}")
                
                # Check if agent is registered
                print("\n5. Checking agent registration...")
                registered_agents = agent_registry.list_agents()
                print(f"Registered agents: {len(registered_agents)}")
                for agent_info in registered_agents:
                    print(f"  - {agent_info['id']}: {agent_info['name']} - {agent_info['status']}")
                
                # Stop the agent
                print("\n6. Stopping WiFi agent...")
                await agent.stop()
                print(f"  ✅ Agent stopped successfully")
                
            except Exception as e:
                print(f"  ❌ Error starting agent: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("  ❌ Failed to create WiFi agent")
        
        # Check Redis status
        print("\n7. Checking Redis status...")
        try:
            if agent_registry.redis_client:
                agent_registry.redis_client.ping()
                print("  ✅ Redis connection successful")
                
                # Check for agent status in Redis
                agent_key = "mcp:agent:wifi_agent:status"
                status_data = agent_registry.redis_client.get(agent_key)
                if status_data:
                    print(f"  - Agent status in Redis: {status_data}")
                else:
                    print("  - No agent status found in Redis")
            else:
                print("  ❌ Redis client not available")
        except Exception as e:
            print(f"  ❌ Redis error: {e}")
        
    except Exception as e:
        print(f"Error in debug: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await data_service.stop()

if __name__ == "__main__":
    asyncio.run(debug_wifi_status()) 