#!/usr/bin/env python3
import os
import sys
import yaml
import uvicorn
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()

# Configure logging
def setup_logging(debug: bool = False):
    """Set up logging configuration."""
    # Create logs directory in user's home directory
    log_dir = Path.home() / '.mcp_service' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'model_server.log'),
            logging.StreamHandler()
        ]
    )

def setup_environment():
    """Set up environment variables and directories."""
    # Create models directory if it doesn't exist
    models_dir = project_root / 'models' / 'saved'
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Create versions and backups directories
    (models_dir / 'versions').mkdir(exist_ok=True)
    (models_dir / 'backups').mkdir(exist_ok=True)
    
    # Set environment variables if not already set
    os.environ.setdefault('MODEL_DIR', str(models_dir))
    os.environ.setdefault('HOST', '0.0.0.0')
    os.environ.setdefault('PORT', '8000')
    os.environ.setdefault('WORKERS', '4')

def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    try:
        config_file = project_root / config_path
        if not config_file.exists():
            logger.warning(f"Config file {config_path} not found, using defaults")
            return {}
            
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        return {}

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
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    return parser.parse_args()

def main():
    """Run the model server."""
    parser = argparse.ArgumentParser(description='Run the model server')
    parser.add_argument('--config', type=str, default='config/server_config.yaml',
                      help='Path to server configuration file')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                      help='Host to bind the server to')
    parser.add_argument('--port', type=int, default=8000,
                      help='Port to bind the server to')
    parser.add_argument('--workers', type=int, default=4,
                      help='Number of worker processes')
    parser.add_argument('--reload', action='store_true',
                      help='Enable auto-reload on code changes')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    # Set up environment
    setup_environment()
    
    # Log startup information
    logger.info(f"Starting model server on {args.host}:{args.port}")
    logger.info(f"Number of workers: {args.workers}")
    logger.info(f"Auto-reload: {args.reload}")
    logger.info(f"Debug mode: {args.debug}")
    
    # Run the server
    uvicorn.run(
        "api.model_server:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level="debug" if args.debug else "info"
    )

if __name__ == "__main__":
    main() 