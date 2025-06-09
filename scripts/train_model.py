#!/usr/bin/env python3
import os
import sys
import yaml
import asyncio
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from models.training import ModelTrainer

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
    parser = argparse.ArgumentParser(description='Train WiFi anomaly detection model')
    parser.add_argument(
        '--config',
        type=str,
        default='config/model_config.yaml',
        help='Path to model configuration file'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days of historical data to use for training'
    )
    parser.add_argument(
        '--model-dir',
        type=str,
        default='models',
        help='Directory to save trained models'
    )
    return parser.parse_args()

async def main():
    """Main training function."""
    # Parse arguments
    args = parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Update model directory in config
    config['model_dir'] = args.model_dir
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    
    logger.info(f"Training model on data from {start_date} to {end_date}")
    
    try:
        # Initialize trainer
        trainer = ModelTrainer(config)
        
        # Train and save model
        model_path = await trainer.train_and_save(start_date, end_date)
        
        logger.info(f"Model training completed successfully")
        logger.info(f"Model saved to: {model_path}")
        
    except Exception as e:
        logger.error(f"Error during model training: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main()) 