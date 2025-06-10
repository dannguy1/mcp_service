import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
from prometheus_client import Histogram
import pandas as pd

logger = logging.getLogger(__name__)

# Prometheus metrics
FEATURE_EXTRACTION_TIME = Histogram(
    'feature_extraction_seconds',
    'Time spent extracting features',
    ['feature_type']
)

class FeatureExtractor:
    """Extracts features from WiFi logs for model input."""
    
    def __init__(self):
        """Initialize the feature extractor."""
        self.feature_columns = [
            "signal_strength",
            "connection_duration",
            "bytes_transferred",
            "packet_loss_rate"
        ]
    
    async def extract(self, logs: List[Dict]) -> Dict:
        """Extract features from logs.
        
        Args:
            logs: List of log entries
            
        Returns:
            Dictionary of extracted features
        """
        try:
            # Convert logs to DataFrame
            df = pd.DataFrame(logs)
            
            # Extract features
            features = {}
            
            # Signal strength
            features['signal_strength'] = df['signal_strength'].values
            
            # Connection duration
            features['connection_duration'] = (
                pd.to_datetime(df['disconnect_time']) - 
                pd.to_datetime(df['connect_time'])
            ).dt.total_seconds().values
            
            # Bytes transferred
            features['bytes_transferred'] = df['bytes_up'].fillna(0).values + df['bytes_down'].fillna(0).values
            
            # Packet loss rate
            features['packet_loss_rate'] = (
                df['packets_lost'].fillna(0).values / 
                (df['packets_sent'].fillna(0).values + 1e-6)
            )
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            raise
