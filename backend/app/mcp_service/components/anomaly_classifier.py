import logging
from typing import List, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class AnomalyClassifier:
    """Classifies anomalies in extracted features."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model = None
        self.thresholds = {
            'auth_failures': 5,  # More than 5 auth failures in 5 minutes
            'deauth_count': 10,  # More than 10 deauth frames in 5 minutes
            'beacon_count': 100,  # More than 100 beacon frames in 5 minutes
            'unique_mac_count': 20  # More than 20 unique MACs in 5 minutes
        }
    
    def set_model(self, model):
        """Set the anomaly detection model."""
        self.model = model
        self.logger.info("Anomaly detection model set")
    
    def detect_anomalies(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect anomalies in the extracted features.
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            List of detected anomalies
        """
        try:
            anomalies = []
            
            # Check authentication failures
            if features['auth_failures'] > self.thresholds['auth_failures']:
                anomalies.append({
                    'type': 'auth_failure',
                    'severity': 3,
                    'confidence': 0.8,
                    'description': (
                        f"Multiple authentication failures detected "
                        f"({features['auth_failures']} failures in 5 minutes)"
                    ),
                    'features': {
                        'auth_failures': features['auth_failures'],
                        'failed_auth_mac_count': features['failed_auth_mac_count']
                    }
                })
            
            # Check deauthentication flood
            if features['deauth_count'] > self.thresholds['deauth_count']:
                anomalies.append({
                    'type': 'deauth_flood',
                    'severity': 4,
                    'confidence': 0.9,
                    'description': (
                        f"Deauthentication flood detected "
                        f"({features['deauth_count']} deauth frames in 5 minutes)"
                    ),
                    'features': {
                        'deauth_count': features['deauth_count']
                    }
                })
            
            # Check beacon flood
            if features['beacon_count'] > self.thresholds['beacon_count']:
                anomalies.append({
                    'type': 'beacon_flood',
                    'severity': 2,
                    'confidence': 0.7,
                    'description': (
                        f"Beacon frame flood detected "
                        f"({features['beacon_count']} beacon frames in 5 minutes)"
                    ),
                    'features': {
                        'beacon_count': features['beacon_count']
                    }
                })
            
            # Check for potential MAC spoofing
            if features['unique_mac_count'] > self.thresholds['unique_mac_count']:
                anomalies.append({
                    'type': 'mac_spoofing',
                    'severity': 4,
                    'confidence': 0.6,
                    'description': (
                        f"Potential MAC spoofing detected "
                        f"({features['unique_mac_count']} unique MACs in 5 minutes)"
                    ),
                    'features': {
                        'unique_mac_count': features['unique_mac_count']
                    }
                })
            
            self.logger.info(f"Detected {len(anomalies)} anomalies")
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            raise 