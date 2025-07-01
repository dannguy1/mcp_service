import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

class AnomalyClassifier:
    """Classifies anomalies in extracted features using both ML model and rule-based detection."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model = None
        self.threshold = 0.95  # Confidence threshold for ML model predictions
        
        # Rule-based thresholds for different anomaly types
        self.thresholds = {
            'auth_failures': 5,  # More than 5 auth failures in 5 minutes
            'deauth_count': 10,  # More than 10 deauth frames in 5 minutes
            'beacon_count': 100,  # More than 100 beacon frames in 5 minutes
            'unique_mac_count': 20  # More than 20 unique MACs in 5 minutes
        }
    
    def set_model(self, model: Any):
        """Set the anomaly detection model."""
        self.model = model
        self.logger.info("Anomaly detection model set")
    
    def detect_anomalies(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect anomalies using both ML model and rule-based detection.
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            List of detected anomalies
        """
        try:
            anomalies = []
            
            # Rule-based detection
            rule_based_anomalies = self._detect_rule_based_anomalies(features)
            anomalies.extend(rule_based_anomalies)
            
            # ML model-based detection if model is available
            if self.model:
                try:
                    ml_anomalies = self._detect_ml_anomalies(features)
                    anomalies.extend(ml_anomalies)
                except Exception as e:
                    self.logger.warning(f"ML model detection failed: {e}")
            
            self.logger.info(f"Detected {len(anomalies)} anomalies")
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            raise
    
    def _detect_rule_based_anomalies(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies using rule-based thresholds."""
        anomalies = []
        
        # Check authentication failures
        if features['auth_failures'] > self.thresholds['auth_failures']:
            anomalies.append({
                'type': 'auth_failure',
                'severity': min(5, features['auth_failures'] // 2),
                'confidence': 0.8,
                'description': (
                    f"Multiple authentication failures detected "
                    f"({features['auth_failures']} failures in 5 minutes)"
                ),
                'features': {
                    'auth_failures': features['auth_failures'],
                    'failed_auth_mac_count': features.get('failed_auth_mac_count', 0)
                }
            })
        
        # Check deauthentication flood
        if features['deauth_count'] > self.thresholds['deauth_count']:
            anomalies.append({
                'type': 'deauth_flood',
                'severity': min(5, features['deauth_count'] // 5),
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
                'severity': min(5, features['beacon_count'] // 50),
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
        
        return anomalies
    
    def _detect_ml_anomalies(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies using the ML model."""
        if not self.model:
            return []
            
        try:
            # Handle dictionary-based models (rule-based fallback)
            if isinstance(self.model, dict):
                self.logger.info("Using dictionary-based model for rule-based detection")
                return self._detect_rule_based_anomalies(features)
            
            # Handle sklearn models
            if hasattr(self.model, 'predict_proba'):
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
            elif hasattr(self.model, 'predict'):
                # Handle models that only have predict method (like IsolationForest)
                X = self._prepare_features(features)
                predictions = self.model.predict(X)
                
                # For IsolationForest, -1 means anomaly, 1 means normal
                anomalies = []
                for i, pred in enumerate(predictions):
                    if pred == -1:  # Anomaly detected
                        # Get anomaly score if available
                        if hasattr(self.model, 'score_samples'):
                            scores = self.model.score_samples(X)
                            confidence = 1.0 - np.exp(scores[i])  # Convert to confidence
                        else:
                            confidence = 0.8  # Default confidence
                        
                        anomaly = self._create_anomaly(
                            features,
                            confidence,
                            i
                        )
                        anomalies.append(anomaly)
                
                return anomalies
            else:
                self.logger.warning("Model does not have predict or predict_proba method")
                return []
            
        except Exception as e:
            self.logger.error(f"Error in ML model detection: {e}")
            return []
    
    def _prepare_features(self, features: Dict[str, Any]) -> np.ndarray:
        """Prepare features for ML model input."""
        # Extract relevant features in the correct order
        feature_vector = [
            features['auth_failures'],
            features['deauth_count'],
            features['beacon_count'],
            features['unique_mac_count'],
            features.get('unique_ssid_count', 0)
        ]
        
        # Add reason code counts
        for code in range(1, 18):  # Common WiFi reason codes
            feature_vector.append(
                features.get('reason_codes', {}).get(str(code), 0)
            )
        
        # Add status code counts
        for code in range(1, 18):  # Common WiFi status codes
            feature_vector.append(
                features.get('status_codes', {}).get(str(code), 0)
            )
        
        # Convert to numpy array and reshape for model input
        return np.array(feature_vector).reshape(1, -1)
    
    def _create_anomaly(
        self,
        features: Dict[str, Any],
        confidence: float,
        index: int
    ) -> Dict[str, Any]:
        """Create an anomaly dictionary from ML model prediction."""
        # Determine anomaly type based on feature values
        if features['auth_failures'] > self.thresholds['auth_failures']:
            anomaly_type = 'auth_failure'
            severity = min(5, features['auth_failures'] // 2)
        elif features['deauth_count'] > self.thresholds['deauth_count']:
            anomaly_type = 'deauth_flood'
            severity = min(5, features['deauth_count'] // 5)
        elif features['beacon_count'] > self.thresholds['beacon_count']:
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
        """Generate a human-readable description for an anomaly."""
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