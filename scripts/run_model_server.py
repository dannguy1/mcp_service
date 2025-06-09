#!/usr/bin/env python3
import os
import sys
import yaml
import uvicorn
import logging
import argparse
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        sys.exit(1)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run WiFi anomaly detection model server')
    parser.add_argument(
        '--config',
        type=str,
        default='config/server_config.yaml',
        help='Path to server configuration file'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host to bind the server to'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port to bind the server to'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Number of worker processes'
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Enable auto-reload on code changes'
    )
    return parser.parse_args()

def main():
    """Main function to run the model server."""
    # Parse arguments
    args = parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Update configuration with command line arguments
    config['server'] = {
        'host': args.host,
        'port': args.port,
        'workers': args.workers,
        'reload': args.reload
    }
    
    logger.info(f"Starting model server on {args.host}:{args.port}")
    logger.info(f"Number of workers: {args.workers}")
    logger.info(f"Auto-reload: {args.reload}")
    
    # Run server
    uvicorn.run(
        "api.model_server:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload
    )

if __name__ == '__main__':
    main() 