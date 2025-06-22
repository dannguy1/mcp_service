#!/usr/bin/env python3
import os
import sys
import asyncio
import logging
import argparse
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.agents.wifi_agent import WiFiAgent
from data_service import data_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    try:
        config = {
            'processing_interval': int(os.getenv('AGENT_PROCESSING_INTERVAL', '60')),
            'batch_size': int(os.getenv('AGENT_BATCH_SIZE', '1000')),
            'lookback_window': int(os.getenv('AGENT_LOOKBACK_WINDOW', '30')),
            'model_path': os.getenv('MODEL_PATH', 'models/wifi_anomaly_detector.joblib'),
            'database': {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', '5432')),
                'name': os.getenv('DB_NAME', 'mcp_service'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', '')
            },
            'redis': {
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', '6379')),
                'db': int(os.getenv('REDIS_DB', '0')),
                'password': os.getenv('REDIS_PASSWORD', '')
            },
            'prometheus': {
                'host': os.getenv('PROMETHEUS_HOST', 'localhost'),
                'port': int(os.getenv('PROMETHEUS_PORT', '9090')),
                'path': os.getenv('PROMETHEUS_PATH', '/metrics')
            },
            'logging': {
                'level': os.getenv('LOG_LEVEL', 'INFO'),
                'format': os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
                'file': os.getenv('LOG_FILE', 'logs/wifi_agent.log')
            },
            'thresholds': {
                'signal_strength': int(os.getenv('THRESHOLD_SIGNAL_STRENGTH', '-70')),
                'packet_loss_rate': float(os.getenv('THRESHOLD_PACKET_LOSS_RATE', '0.1')),
                'retry_rate': float(os.getenv('THRESHOLD_RETRY_RATE', '0.2')),
                'data_rate': int(os.getenv('THRESHOLD_DATA_RATE', '24'))
            },
            'resource_monitoring': {
                'enabled': os.getenv('RESOURCE_MONITORING_ENABLED', 'true').lower() == 'true',
                'check_interval': int(os.getenv('RESOURCE_CHECK_INTERVAL', '60')),
                'thresholds': {
                    'cpu': int(os.getenv('RESOURCE_THRESHOLD_CPU', '80')),
                    'memory': int(os.getenv('RESOURCE_THRESHOLD_MEMORY', '85')),
                    'disk': int(os.getenv('RESOURCE_THRESHOLD_DISK', '90')),
                    'network': int(os.getenv('RESOURCE_THRESHOLD_NETWORK', '1000000'))
                }
            }
        }
        return config
    except Exception as e:
        logger.error(f"Error loading config from environment variables: {str(e)}")
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
    config = load_config()
    
    # Start the agent
    asyncio.run(start_agent(config))

if __name__ == '__main__':
    main() 