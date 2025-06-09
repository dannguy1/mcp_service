import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# Prometheus metrics
CLASSIFICATION_TIME = Histogram(
    'anomaly_classification_seconds',
    'Time spent classifying anomalies'
)
ANOMALY_CLASSIFICATIONS = Counter(
    'anomaly_classifications_total',
    'Number of anomalies classified',
    ['severity', 'type']
)

class AnomalyClassifier:
    """Component for classifying detected anomalies."""
    
    def __init__(self):
        self._severity_thresholds = {
            'critical': 0.95,  # 95% confidence
            'high': 0.85,      # 85% confidence
            'medium': 0.75,    # 75% confidence
            'low': 0.65        # 65% confidence
        }
        
        self._type_patterns = {
            'connection': ['connection', 'connect', 'disconnect', 'link'],
            'authentication': ['auth', 'login', 'password', 'credential'],
            'performance': ['slow', 'latency', 'timeout', 'performance'],
            'security': ['security', 'attack', 'breach', 'unauthorized'],
            'system': ['system', 'service', 'process', 'daemon']
        }
    
    def classify(
        self,
        features: Dict[str, float],
        confidence: float,
        description: str
    ) -> Tuple[str, int, str]:
        """Classify an anomaly based on its features and confidence."""
        with CLASSIFICATION_TIME.time():
            # Determine severity
            severity = self._determine_severity(confidence)
            
            # Determine type
            anomaly_type = self._determine_type(description)
            
            # Generate detailed description
            detailed_description = self._generate_description(
                features, severity, anomaly_type, description
            )
            
            # Record metrics
            ANOMALY_CLASSIFICATIONS.labels(
                severity=severity,
                type=anomaly_type
            ).inc()
            
            return severity, self._severity_to_int(severity), detailed_description
    
    def _determine_severity(self, confidence: float) -> str:
        """Determine the severity level based on confidence score."""
        if confidence >= self._severity_thresholds['critical']:
            return 'critical'
        elif confidence >= self._severity_thresholds['high']:
            return 'high'
        elif confidence >= self._severity_thresholds['medium']:
            return 'medium'
        else:
            return 'low'
    
    def _determine_type(self, description: str) -> str:
        """Determine the anomaly type based on description."""
        description_lower = description.lower()
        
        for anomaly_type, patterns in self._type_patterns.items():
            if any(pattern in description_lower for pattern in patterns):
                return anomaly_type
        
        return 'unknown'
    
    def _generate_description(
        self,
        features: Dict[str, float],
        severity: str,
        anomaly_type: str,
        original_description: str
    ) -> str:
        """Generate a detailed description of the anomaly."""
        # Extract relevant features
        error_ratio = features.get('error_ratio', 0.0)
        avg_severity = features.get('avg_severity', 0.0)
        
        # Build description
        description_parts = [
            f"[{severity.upper()}] {anomaly_type.title()} Anomaly Detected",
            f"Original: {original_description}",
            f"Error Ratio: {error_ratio:.1%}",
            f"Average Severity: {avg_severity:.1f}"
        ]
        
        return " | ".join(description_parts)
    
    def _severity_to_int(self, severity: str) -> int:
        """Convert severity string to integer value."""
        severity_map = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }
        return severity_map.get(severity, 0)
    
    def get_severity_thresholds(self) -> Dict[str, float]:
        """Get the current severity thresholds."""
        return self._severity_thresholds.copy()
    
    def set_severity_thresholds(self, thresholds: Dict[str, float]) -> None:
        """Update the severity thresholds."""
        for severity, threshold in thresholds.items():
            if 0 <= threshold <= 1:
                self._severity_thresholds[severity] = threshold
            else:
                logger.warning(f"Invalid threshold for {severity}: {threshold}")
    
    def get_type_patterns(self) -> Dict[str, List[str]]:
        """Get the current type patterns."""
        return {k: v.copy() for k, v in self._type_patterns.items()}
    
    def add_type_pattern(self, anomaly_type: str, pattern: str) -> None:
        """Add a new pattern for an anomaly type."""
        if anomaly_type not in self._type_patterns:
            self._type_patterns[anomaly_type] = []
        self._type_patterns[anomaly_type].append(pattern.lower())
