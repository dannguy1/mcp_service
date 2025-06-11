import logging
from typing import List, Dict, Any, Optional
import numpy as np

class AnomalyClassifier:
    def __init__(self):
        """Initialize the anomaly classifier."""
        self.logger = logging.getLogger("AnomalyClassifier")
        self.model = None
        self.threshold = 0.95  # Confidence threshold for anomaly detection

    def set_model(self, model: Any):
        """
        Set the model to use for classification.
        
        Args:
            model: The ML model to use
        """
        self.model = model
        self.logger.info("Set anomaly detection model")

    def detect_anomalies(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect anomalies in the given features.
        
        Args:
            features: Dictionary of features
            
        Returns:
            List of detected anomalies
        """
        if not self.model:
            raise ValueError("Model not set")
            
        try:
            # Convert features to model input format
            X = self._prepare_features(features)
            
            # Get model predictions
            predictions = self.model.predict_proba(X)
            
            # Find anomalies
            anomalies = []
            for i, pred in enumerate(predictions):
                if pred[1] > self.threshold:  # Assuming binary classification
                    anomaly = self._create_anomaly(
                        features,
                        pred[1],
                        i
                    )
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            raise

    def _prepare_features(self, features: Dict[str, Any]) -> np.ndarray:
        """
        Prepare features for model input.
        
        Args:
            features: Dictionary of features
            
        Returns:
            numpy array of prepared features
        """
        # Extract relevant features in the correct order
        feature_vector = [
            features['auth_failures'],
            features['deauth_count'],
            features['beacon_count'],
            features['unique_mac_count'],
            features['unique_ssid_count']
        ]
        
        # Add reason code counts
        for code in range(1, 18):  # Common WiFi reason codes
            feature_vector.append(
                features['reason_codes'].get(str(code), 0)
            )
        
        # Add status code counts
        for code in range(1, 18):  # Common WiFi status codes
            feature_vector.append(
                features['status_codes'].get(str(code), 0)
            )
        
        # Convert to numpy array and reshape for model input
        return np.array(feature_vector).reshape(1, -1)

    def _create_anomaly(
        self,
        features: Dict[str, Any],
        confidence: float,
        index: int
    ) -> Dict[str, Any]:
        """
        Create an anomaly dictionary from features and prediction.
        
        Args:
            features: Dictionary of features
            confidence: Model prediction confidence
            index: Index of the prediction
            
        Returns:
            Dictionary containing anomaly information
        """
        # Determine anomaly type based on feature values
        if features['auth_failures'] > 5:
            anomaly_type = 'auth_failure'
            severity = min(5, features['auth_failures'] // 2)
        elif features['deauth_count'] > 10:
            anomaly_type = 'deauth_flood'
            severity = min(5, features['deauth_count'] // 5)
        elif features['beacon_count'] > 100:
            anomaly_type = 'beacon_flood'
            severity = min(5, features['beacon_count'] // 50)
        else:
            anomaly_type = 'unknown'
            severity = 3
        
        return {
            'type': anomaly_type,
            'severity': severity,
            'confidence': float(confidence),
            'description': self._get_anomaly_description(
                anomaly_type,
                features
            ),
            'features': features
        }

    def _get_anomaly_description(
        self,
        anomaly_type: str,
        features: Dict[str, Any]
    ) -> str:
        """
        Generate a human-readable description for an anomaly.
        
        Args:
            anomaly_type: Type of anomaly
            features: Dictionary of features
            
        Returns:
            Human-readable description
        """
        if anomaly_type == 'auth_failure':
            return (
                f"Multiple authentication failures detected "
                f"({features['auth_failures']} failures in 5 minutes)"
            )
        elif anomaly_type == 'deauth_flood':
            return (
                f"Deauthentication flood detected "
                f"({features['deauth_count']} deauth frames in 5 minutes)"
            )
        elif anomaly_type == 'beacon_flood':
            return (
                f"Beacon frame flood detected "
                f"({features['beacon_count']} beacon frames in 5 minutes)"
            )
        else:
            return f"Unknown anomaly type: {anomaly_type}" 