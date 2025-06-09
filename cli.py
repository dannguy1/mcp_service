#!/usr/bin/env python3
import os
import sys
import asyncio
import logging
import argparse
import yaml
from typing import Dict, Any

from agents.wifi_agent import WiFiAgent
from data_service import data_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {str(e)}")
        sys.exit(1)

async def start_agent(config: Dict[str, Any]) -> None:
    """Start the WiFi agent with the given configuration."""
    try:
        # Initialize data service
        await data_service.initialize()
        
        # Create and start agent
        agent = WiFiAgent(config)
        await agent.start()
        
        # Keep the agent running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down agent...")
            await agent.stop()
            await data_service.close()
            
    except Exception as e:
        logger.error(f"Error running agent: {str(e)}")
        await data_service.close()
        sys.exit(1)

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description='WiFi Agent CLI')
    parser.add_argument(
        '--config',
        type=str,
        default='config/agent_config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Set log level
    logging.getLogger().setLevel(args.log_level)
    
    # Load configuration
    config = load_config(args.config)
    
    # Start the agent
    asyncio.run(start_agent(config))

if __name__ == '__main__':
    main() 