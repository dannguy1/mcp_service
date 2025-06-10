#!/usr/bin/env python3
import os
import sys
import yaml
import logging
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from models.training import ModelTrainer
from models.config import ModelConfig

# Configure logging
def setup_logging(debug: bool = False):
    """Set up logging configuration."""
    # Create logs directory in user's home directory
    log_dir = Path.home() / '.mcp_service' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / 'training.log'
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def setup_environment():
    """Set up the environment for training."""
    # Load environment variables from .env file
    env_path = Path(project_root) / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        logger.warning("No .env file found, using default environment variables")
    
    # Create necessary directories
    os.makedirs('models', exist_ok=True)
    
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
    parser = argparse.ArgumentParser(description='Train WiFi anomaly detection model')
    parser.add_argument(
        '--config',
        type=str,
        default='config/model_config.yaml',
        help='Path to model configuration file'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date for training data (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date for training data (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    return parser.parse_args()

def main():
    """Main function to train the model."""
    try:
        # Parse arguments
        args = parse_args()
        
        # Set up environment
        setup_environment()
        
        # Set log level
        if args.debug:
            logger.setLevel(logging.DEBUG)
        
        # Load configuration
        model_config = load_config(args.config)
        
        # Parse dates if provided
        start_date = datetime.fromisoformat(args.start_date) if args.start_date else None
        end_date = datetime.fromisoformat(args.end_date) if args.end_date else None
        
        logger.info("Starting model training")
        logger.info(f"Configuration: {model_config.dict()}")
        if start_date and end_date:
            logger.info(f"Training period: {start_date} to {end_date}")
        
        # Initialize trainer
        trainer = ModelTrainer(model_config)
        
        # Train model
        model_path = trainer.train_and_save(start_date, end_date)
        
        logger.info(f"Model training completed successfully")
        logger.info(f"Model saved to: {model_path}")
        
    except Exception as e:
        logger.error(f"Failed to train model: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 