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
            'unique_mac_count': 20,  # More than 20 unique MACs in 5 minutes
            'query_flood_threshold': 1000,  # More than 1000 queries in 5 minutes
            'response_time_threshold': 5000  # More than 5000ms response time
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
        """Detect anomalies using rule-based logic."""
        anomalies = []
        
        # Determine feature type based on available features
        if 'auth_failures' in features:
            # WiFi features
            return self._detect_wifi_anomalies(features)
        elif 'query_count' in features:
            # DNS features
            return self._detect_dns_anomalies(features)
        elif 'blocked_connections' in features:
            # Firewall features
            return self._detect_firewall_anomalies(features)
        else:
            # Generic features
            return self._detect_generic_anomalies(features)
    
    def _detect_wifi_anomalies(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect WiFi-specific anomalies."""
        anomalies = []
        
        # Check authentication failures
        if features['auth_failures'] > self.thresholds.get('auth_failures', 5):
            anomalies.append({
                'type': 'auth_failure',
                'severity': min(5, features['auth_failures'] // 2),
                'confidence': 0.9,
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
        if features['deauth_count'] > self.thresholds.get('deauth_count', 10):
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
        if features['beacon_count'] > self.thresholds.get('beacon_count', 100):
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
        if features['unique_mac_count'] > self.thresholds.get('unique_mac_count', 50):
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
    
    def _detect_dns_anomalies(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect DNS-specific anomalies."""
        anomalies = []
        
        # Check query flood
        if features['query_count'] > self.thresholds.get('query_flood_threshold', 1000):
            anomalies.append({
                'type': 'dns_query_flood',
                'severity': min(5, features['query_count'] // 200),
                'confidence': 0.8,
                'description': (
                    f"DNS query flood detected "
                    f"({features['query_count']} queries in 5 minutes)"
                ),
                'features': {
                    'query_count': features['query_count'],
                    'unique_domain_count': features.get('unique_domain_count', 0)
                }
            })
        
        # Check response time anomalies
        if features.get('avg_response_time', 0) > self.thresholds.get('response_time_threshold', 5000):
            anomalies.append({
                'type': 'dns_slow_response',
                'severity': 3,
                'confidence': 0.7,
                'description': (
                    f"Slow DNS response detected "
                    f"(avg {features.get('avg_response_time', 0):.2f}ms)"
                ),
                'features': {
                    'avg_response_time': features.get('avg_response_time', 0),
                    'query_count': features['query_count']
                }
            })
        
        # Check error rate
        if features['error_count'] > 0 and features['query_count'] > 0:
            error_rate = features['error_count'] / features['query_count']
            if error_rate > 0.1:  # 10% error rate
                anomalies.append({
                    'type': 'dns_high_error_rate',
                    'severity': 4,
                    'confidence': 0.8,
                    'description': (
                        f"High DNS error rate detected "
                        f"({error_rate:.1%} error rate)"
                    ),
                    'features': {
                        'error_count': features['error_count'],
                        'query_count': features['query_count'],
                        'error_rate': error_rate
                    }
                })
        
        return anomalies
    
    def _detect_firewall_anomalies(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect firewall-specific anomalies."""
        anomalies = []
        
        # Check blocked connections
        if features['blocked_connections'] > self.thresholds.get('blocked_connections', 100):
            anomalies.append({
                'type': 'firewall_high_blocked',
                'severity': min(5, features['blocked_connections'] // 20),
                'confidence': 0.8,
                'description': (
                    f"High number of blocked connections "
                    f"({features['blocked_connections']} blocked in 5 minutes)"
                ),
                'features': {
                    'blocked_connections': features['blocked_connections'],
                    'unique_ip_count': features.get('unique_ip_count', 0)
                }
            })
        
        return anomalies
    
    def _detect_generic_anomalies(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect generic anomalies for any log type."""
        anomalies = []
        
        # Check error rate
        if features.get('error_count', 0) > 0:
            anomalies.append({
                'type': 'high_error_rate',
                'severity': min(5, features['error_count'] // 5),
                'confidence': 0.7,
                'description': (
                    f"High error rate detected "
                    f"({features['error_count']} errors in 5 minutes)"
                ),
                'features': {
                    'error_count': features['error_count'],
                    'log_count': features.get('log_count', 0)
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
        # Determine feature type and prepare accordingly
        if 'auth_failures' in features:
            # WiFi features
            return self._prepare_wifi_features(features)
        elif 'query_count' in features:
            # DNS features
            return self._prepare_dns_features(features)
        elif 'blocked_connections' in features:
            # Firewall features
            return self._prepare_firewall_features(features)
        else:
            # Generic features
            return self._prepare_generic_features(features)
    
    def _prepare_wifi_features(self, features: Dict[str, Any]) -> np.ndarray:
        """Prepare WiFi features for ML model input."""
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
    
    def _prepare_dns_features(self, features: Dict[str, Any]) -> np.ndarray:
        """Prepare DNS features for ML model input."""
        feature_vector = [
            features['query_count'],
            features.get('response_count', 0),
            features.get('error_count', 0),
            features.get('unique_domain_count', 0),
            features.get('avg_response_time', 0)
        ]
        
        # Add query type counts
        query_types = ['A', 'AAAA', 'MX', 'CNAME', 'TXT', 'NS', 'PTR', 'SOA']
        for qtype in query_types:
            feature_vector.append(
                features.get('query_types', {}).get(qtype, 0)
            )
        
        # Convert to numpy array and reshape for model input
        return np.array(feature_vector).reshape(1, -1)
    
    def _prepare_firewall_features(self, features: Dict[str, Any]) -> np.ndarray:
        """Prepare firewall features for ML model input."""
        feature_vector = [
            features['blocked_connections'],
            features.get('allowed_connections', 0),
            features.get('unique_ip_count', 0),
            features.get('unique_port_count', 0)
        ]
        
        # Add protocol counts
        protocols = ['TCP', 'UDP', 'ICMP', 'HTTP', 'HTTPS', 'FTP', 'SSH']
        for protocol in protocols:
            feature_vector.append(
                features.get('protocols', {}).get(protocol, 0)
            )
        
        # Convert to numpy array and reshape for model input
        return np.array(feature_vector).reshape(1, -1)
    
    def _prepare_generic_features(self, features: Dict[str, Any]) -> np.ndarray:
        """Prepare generic features for ML model input."""
        feature_vector = [
            features.get('log_count', 0),
            features.get('error_count', 0),
            features.get('warning_count', 0),
            features.get('unique_program_count', 0),
            features.get('unique_host_count', 0)
        ]
        
        # Convert to numpy array and reshape for model input
        return np.array(feature_vector).reshape(1, -1)
    
    def _create_anomaly(
        self,
        features: Dict[str, Any],
        confidence: float,
        index: int
    ) -> Dict[str, Any]:
        """Create an anomaly dictionary from ML model prediction."""
        # Determine anomaly type based on feature values and type
        if 'auth_failures' in features:
            # WiFi features
            if features['auth_failures'] > self.thresholds.get('auth_failures', 5):
                anomaly_type = 'auth_failure'
                severity = min(5, features['auth_failures'] // 2)
            elif features['deauth_count'] > self.thresholds.get('deauth_count', 10):
                anomaly_type = 'deauth_flood'
                severity = min(5, features['deauth_count'] // 5)
            elif features['beacon_count'] > self.thresholds.get('beacon_count', 100):
                anomaly_type = 'beacon_flood'
                severity = min(5, features['beacon_count'] // 50)
            else:
                anomaly_type = 'wifi_unknown'
                severity = 3
        elif 'query_count' in features:
            # DNS features
            if features['query_count'] > self.thresholds.get('query_flood_threshold', 1000):
                anomaly_type = 'dns_query_flood'
                severity = min(5, features['query_count'] // 200)
            elif features.get('avg_response_time', 0) > self.thresholds.get('response_time_threshold', 5000):
                anomaly_type = 'dns_slow_response'
                severity = 3
            else:
                anomaly_type = 'dns_unknown'
                severity = 3
        elif 'blocked_connections' in features:
            # Firewall features
            if features['blocked_connections'] > self.thresholds.get('blocked_connections', 100):
                anomaly_type = 'firewall_high_blocked'
                severity = min(5, features['blocked_connections'] // 20)
            else:
                anomaly_type = 'firewall_unknown'
                severity = 3
        else:
            # Generic features
            anomaly_type = 'generic_unknown'
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