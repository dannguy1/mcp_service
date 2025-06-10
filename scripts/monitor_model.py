#!/usr/bin/env python3
import os
import sys
import yaml
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from models.monitoring import ModelMonitor
from models.model_loader import ModelLoader
from models.config import ModelConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/monitoring.log')
    ]
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Set up the environment for monitoring."""
    # Load environment variables from .env file
    env_path = Path(project_root) / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        logger.warning("No .env file found, using default environment variables")
    
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    
    # Set PYTHONPATH
    os.environ['PYTHONPATH'] = project_root

def load_config(config_path: str) -> ModelConfig:
    """Load model configuration from YAML file."""
    try:
        config_file = Path(project_root) / config_path
        if not config_file.exists():
            logger.warning(f"Config file {config_path} not found, using defaults")
            return ModelConfig()
            
        with open(config_file, 'r') as f:
            config_dict = yaml.safe_load(f)
            return ModelConfig(**config_dict)
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        return ModelConfig()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Monitor WiFi anomaly detection model')
    parser.add_argument(
        '--config',
        type=str,
        default='config/model_config.yaml',
        help='Path to model configuration file'
    )
    parser.add_argument(
        '--model-version',
        type=str,
        default='latest',
        help='Model version to monitor'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Monitoring interval in seconds'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    return parser.parse_args()

def main():
    """Main function to monitor the model."""
    try:
        # Parse arguments
        args = parse_args()
        
        # Set up environment
        setup_environment()
        
        # Set log level
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Load configuration
        model_config = load_config(args.config)
        
        logger.info("Starting model monitoring")
        logger.info(f"Configuration: {model_config.dict()}")
        logger.info(f"Model version: {args.model_version}")
        logger.info(f"Monitoring interval: {args.interval} seconds")
        
        # Initialize monitor and model loader
        monitor = ModelMonitor()
        model_loader = ModelLoader(model_config.model_dir)
        
        # Load model
        model_loader.load_model(args.model_version)
        
        while True:
            try:
                # Check for drift
                drift_flags = monitor.check_drift()
                
                # Log drift status
                for metric, has_drift in drift_flags.items():
                    if has_drift:
                        logger.warning(f"Drift detected in {metric}")
                    else:
                        logger.debug(f"No drift in {metric}")
                
                # Get performance metrics
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=1)
                metrics = monitor.get_performance_metrics(start_time, end_time)
                
                # Log performance metrics
                logger.info("Performance metrics:")
                for metric, value in metrics.items():
                    logger.info(f"  {metric}: {value}")
                
                # Sleep until next check
                time.sleep(args.interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error during monitoring: {e}", exc_info=True)
                time.sleep(args.interval)  # Continue monitoring after error
        
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 