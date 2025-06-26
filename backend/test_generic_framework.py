#!/usr/bin/env python3
"""
Test script for the Generic Agent Framework.
This script tests the new agent classes and configuration system.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.mcp_service.data_service import DataService
from app.mcp_service.components.agent_registry import agent_registry
from app.mcp_service.components.model_manager import model_manager
from app.config.config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent_creation():
    """Test creating agents from configuration."""
    logger.info("Testing agent creation from configuration...")
    
    # Initialize data service
    data_service = DataService(config=config)
    await data_service.start()
    
    try:
        # Test creating WiFi agent
        logger.info("Creating WiFi agent...")
        wifi_agent = agent_registry.create_agent("wifi_agent", data_service, model_manager)
        if wifi_agent:
            logger.info(f"✓ WiFi agent created successfully: {wifi_agent.__class__.__name__}")
            logger.info(f"  Agent ID: {wifi_agent.agent_id}")
            logger.info(f"  Agent Type: {wifi_agent.agent_type}")
            logger.info(f"  Capabilities: {wifi_agent.capabilities}")
        else:
            logger.error("✗ Failed to create WiFi agent")
            return False
        
        # Test creating Log Level agent
        logger.info("Creating Log Level agent...")
        log_level_agent = agent_registry.create_agent("log_level_agent", data_service, model_manager)
        if log_level_agent:
            logger.info(f"✓ Log Level agent created successfully: {log_level_agent.__class__.__name__}")
            logger.info(f"  Agent ID: {log_level_agent.agent_id}")
            logger.info(f"  Agent Type: {log_level_agent.agent_type}")
            logger.info(f"  Capabilities: {log_level_agent.capabilities}")
        else:
            logger.error("✗ Failed to create Log Level agent")
            return False
        
        # Test creating DNS agent
        logger.info("Creating DNS agent...")
        dns_agent = agent_registry.create_agent("dns_agent", data_service, model_manager)
        if dns_agent:
            logger.info(f"✓ DNS agent created successfully: {dns_agent.__class__.__name__}")
            logger.info(f"  Agent ID: {dns_agent.agent_id}")
            logger.info(f"  Agent Type: {dns_agent.agent_type}")
            logger.info(f"  Capabilities: {dns_agent.capabilities}")
        else:
            logger.error("✗ Failed to create DNS agent")
            return False
        
        return True
        
    finally:
        await data_service.stop()

async def test_agent_lifecycle():
    """Test agent lifecycle (start, stop, analysis)."""
    logger.info("Testing agent lifecycle...")
    
    # Initialize data service
    data_service = DataService(config=config)
    await data_service.start()
    
    try:
        # Create and start WiFi agent
        logger.info("Creating and starting WiFi agent...")
        wifi_agent = agent_registry.create_agent("wifi_agent", data_service, model_manager)
        if wifi_agent:
            # Register agent first
            agent_registry.register_agent(wifi_agent, "wifi_agent")
            
            await wifi_agent.start()
            logger.info("✓ WiFi agent started successfully")
            
            # Check status
            status = wifi_agent.get_status()
            logger.info(f"  Status: {status['status']}")
            logger.info(f"  Is Running: {status['is_running']}")
            
            # Run analysis cycle
            logger.info("Running analysis cycle...")
            await wifi_agent.run_analysis_cycle()
            logger.info("✓ Analysis cycle completed")
            
            # Stop agent
            await wifi_agent.stop()
            logger.info("✓ WiFi agent stopped successfully")
            
            # Unregister agent
            agent_registry.unregister_agent("wifi_agent")
        else:
            logger.error("✗ Failed to create WiFi agent")
            return False
        
        return True
        
    finally:
        await data_service.stop()

async def test_configuration_management():
    """Test configuration management features."""
    logger.info("Testing configuration management...")
    
    # Test listing configurations
    configs = agent_registry.list_agent_configs()
    logger.info(f"Found {len(configs)} agent configurations:")
    for config_info in configs:
        logger.info(f"  - {config_info['agent_id']}: {config_info['name']} ({config_info['agent_type']})")
    
    # Test getting specific configuration
    wifi_config = agent_registry.get_agent_config("wifi_agent")
    if wifi_config:
        logger.info("✓ WiFi agent configuration retrieved")
        logger.info(f"  Name: {wifi_config.get('name')}")
        logger.info(f"  Type: {wifi_config.get('agent_type')}")
    else:
        logger.error("✗ Failed to get WiFi agent configuration")
        return False
    
    return True

async def test_agent_registry():
    """Test agent registry functionality."""
    logger.info("Testing agent registry...")
    
    # Initialize data service
    data_service = DataService(config=config)
    await data_service.start()
    
    try:
        # Create and register agents
        wifi_agent = agent_registry.create_agent("wifi_agent", data_service, model_manager)
        log_level_agent = agent_registry.create_agent("log_level_agent", data_service, model_manager)
        
        if wifi_agent and log_level_agent:
            # Register agents
            agent_registry.register_agent(wifi_agent, "wifi_agent")
            agent_registry.register_agent(log_level_agent, "log_level_agent")
            
            # List registered agents
            agents = agent_registry.list_agents()
            logger.info(f"Registered {len(agents)} agents:")
            for agent_info in agents:
                logger.info(f"  - {agent_info['id']}: {agent_info['name']}")
            
            # Test getting agent
            retrieved_agent = agent_registry.get_agent("wifi_agent")
            if retrieved_agent:
                logger.info("✓ Agent retrieval successful")
            else:
                logger.error("✗ Agent retrieval failed")
                return False
            
            # Unregister agents
            agent_registry.unregister_agent("wifi_agent")
            agent_registry.unregister_agent("log_level_agent")
            
            logger.info("✓ Agent registry tests completed")
            return True
        else:
            logger.error("✗ Failed to create agents for registry test")
            return False
            
    finally:
        await data_service.stop()

async def main():
    """Run all tests."""
    logger.info("Starting Generic Agent Framework tests...")
    
    tests = [
        ("Configuration Management", test_configuration_management),
        ("Agent Creation", test_agent_creation),
        ("Agent Registry", test_agent_registry),
        ("Agent Lifecycle", test_agent_lifecycle),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✓ {test_name} PASSED")
            else:
                logger.error(f"✗ {test_name} FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} FAILED with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Generic Agent Framework is working correctly.")
        return 0
    else:
        logger.error("❌ Some tests failed. Please check the logs above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 