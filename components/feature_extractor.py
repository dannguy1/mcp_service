import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
from prometheus_client import Histogram

logger = logging.getLogger(__name__)

# Prometheus metrics
FEATURE_EXTRACTION_TIME = Histogram(
    'feature_extraction_seconds',
    'Time spent extracting features',
    ['feature_type']
)

class FeatureExtractor:
    """Component for extracting features from log data."""
    
    def __init__(self):
        self._window_size = 300  # 5 minutes
        self._min_samples = 10  # Minimum samples for reliable features
    
    def extract_features(self, logs: List[Dict]) -> Dict[str, float]:
        """Extract features from a list of logs."""
        with FEATURE_EXTRACTION_TIME.labels('all').time():
            if len(logs) < self._min_samples:
                return self._get_default_features()
            
            return {
                'temporal': self._extract_temporal_features(logs),
                'statistical': self._extract_statistical_features(logs),
                'pattern': self._extract_pattern_features(logs)
            }
    
    def _get_default_features(self) -> Dict[str, Dict[str, float]]:
        """Get default feature values when insufficient data."""
        return {
            'temporal': {
                'log_frequency': 0.0,
                'time_span': 0.0,
                'hour_of_day': 0.0
            },
            'statistical': {
                'error_ratio': 0.0,
                'avg_severity': 0.0,
                'severity_std': 0.0
            },
            'pattern': {
                'unique_types': 0.0,
                'type_entropy': 0.0,
                'connection_ratio': 0.0
            }
        }
    
    def _extract_temporal_features(self, logs: List[Dict]) -> Dict[str, float]:
        """Extract temporal features from logs."""
        with FEATURE_EXTRACTION_TIME.labels('temporal').time():
            timestamps = [log['timestamp'] for log in logs]
            time_diffs = np.diff([ts.timestamp() for ts in timestamps])
            
            return {
                'log_frequency': len(logs) / self._window_size,
                'time_span': (timestamps[-1] - timestamps[0]).total_seconds(),
                'hour_of_day': timestamps[-1].hour / 24.0
            }
    
    def _extract_statistical_features(self, logs: List[Dict]) -> Dict[str, float]:
        """Extract statistical features from logs."""
        with FEATURE_EXTRACTION_TIME.labels('statistical').time():
            severities = [log['severity'] for log in logs]
            error_count = sum(1 for s in severities if s >= 3)
            
            return {
                'error_ratio': error_count / len(logs),
                'avg_severity': np.mean(severities),
                'severity_std': np.std(severities)
            }
    
    def _extract_pattern_features(self, logs: List[Dict]) -> Dict[str, float]:
        """Extract pattern-based features from logs."""
        with FEATURE_EXTRACTION_TIME.labels('pattern').time():
            log_types = [log['log_type'] for log in logs]
            unique_types = set(log_types)
            type_counts = {t: log_types.count(t) for t in unique_types}
            
            # Calculate entropy
            total = len(logs)
            entropy = -sum((count/total) * np.log2(count/total) 
                         for count in type_counts.values())
            
            # Calculate connection ratio
            connection_count = sum(1 for t in log_types 
                                if 'connection' in t.lower())
            
            return {
                'unique_types': len(unique_types),
                'type_entropy': entropy,
                'connection_ratio': connection_count / total
            }
    
    def normalize_features(self, features: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """Normalize feature values to [0, 1] range."""
        normalized = {}
        
        # Temporal features
        normalized['temporal'] = {
            'log_frequency': min(features['temporal']['log_frequency'] / 10.0, 1.0),
            'time_span': min(features['temporal']['time_span'] / self._window_size, 1.0),
            'hour_of_day': features['temporal']['hour_of_day']
        }
        
        # Statistical features
        normalized['statistical'] = {
            'error_ratio': features['statistical']['error_ratio'],
            'avg_severity': features['statistical']['avg_severity'] / 5.0,
            'severity_std': min(features['statistical']['severity_std'] / 2.0, 1.0)
        }
        
        # Pattern features
        normalized['pattern'] = {
            'unique_types': min(features['pattern']['unique_types'] / 10.0, 1.0),
            'type_entropy': min(features['pattern']['type_entropy'] / 3.0, 1.0),
            'connection_ratio': features['pattern']['connection_ratio']
        }
        
        return normalized
