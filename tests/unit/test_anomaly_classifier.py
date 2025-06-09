import pytest
from datetime import datetime
import numpy as np

from components.anomaly_classifier import AnomalyClassifier

@pytest.fixture
def anomaly_classifier(test_registry):
    """Create an AnomalyClassifier instance for testing."""
    return AnomalyClassifier(registry=test_registry)

@pytest.fixture
def sample_anomalies():
    """Create sample anomaly data for testing."""
    return [
        {
            'timestamp': datetime.now(),
            'device_id': 'device1',
            'anomaly_score': 0.95,
            'features': {
                'signal_strength': -80,
                'packet_loss_rate': 0.3,
                'retry_rate': 0.4
            }
        },
        {
            'timestamp': datetime.now(),
            'device_id': 'device2',
            'anomaly_score': 0.75,
            'features': {
                'signal_strength': -65,
                'packet_loss_rate': 0.1,
                'retry_rate': 0.2
            }
        },
        {
            'timestamp': datetime.now(),
            'device_id': 'device3',
            'anomaly_score': 0.45,
            'features': {
                'signal_strength': -50,
                'packet_loss_rate': 0.05,
                'retry_rate': 0.1
            }
        }
    ]

def test_anomaly_classifier_initialization(anomaly_classifier):
    """Test AnomalyClassifier initialization."""
    assert anomaly_classifier is not None
    assert anomaly_classifier.registry is not None
    assert anomaly_classifier.severity_thresholds['high'] == 0.8
    assert anomaly_classifier.severity_thresholds['medium'] == 0.6
    assert anomaly_classifier.severity_thresholds['low'] == 0.4

def test_classify_severity(anomaly_classifier, sample_anomalies):
    """Test anomaly severity classification."""
    # Test high severity
    high_severity = anomaly_classifier.classify_severity(sample_anomalies[0])
    assert high_severity == 'high'
    
    # Test medium severity
    medium_severity = anomaly_classifier.classify_severity(sample_anomalies[1])
    assert medium_severity == 'medium'
    
    # Test low severity
    low_severity = anomaly_classifier.classify_severity(sample_anomalies[2])
    assert low_severity == 'low'

def test_classify_type(anomaly_classifier, sample_anomalies):
    """Test anomaly type classification."""
    # Test signal strength anomaly
    signal_anomaly = anomaly_classifier.classify_type(sample_anomalies[0])
    assert signal_anomaly == 'signal_strength'
    
    # Test packet loss anomaly
    packet_loss_anomaly = anomaly_classifier.classify_type(sample_anomalies[1])
    assert packet_loss_anomaly == 'packet_loss'
    
    # Test retry rate anomaly
    retry_anomaly = anomaly_classifier.classify_type(sample_anomalies[2])
    assert retry_anomaly == 'retry_rate'

def test_classify_anomalies(anomaly_classifier, sample_anomalies):
    """Test complete anomaly classification."""
    classified_anomalies = anomaly_classifier.classify_anomalies(sample_anomalies)
    
    assert len(classified_anomalies) == 3
    
    # Verify classification results
    assert classified_anomalies[0]['severity'] == 'high'
    assert classified_anomalies[0]['type'] == 'signal_strength'
    
    assert classified_anomalies[1]['severity'] == 'medium'
    assert classified_anomalies[1]['type'] == 'packet_loss'
    
    assert classified_anomalies[2]['severity'] == 'low'
    assert classified_anomalies[2]['type'] == 'retry_rate'

def test_get_classification_rules(anomaly_classifier):
    """Test retrieval of classification rules."""
    rules = anomaly_classifier.get_classification_rules()
    
    assert 'severity_thresholds' in rules
    assert 'type_thresholds' in rules
    
    assert rules['severity_thresholds']['high'] == 0.8
    assert rules['severity_thresholds']['medium'] == 0.6
    assert rules['severity_thresholds']['low'] == 0.4

def test_set_classification_rules(anomaly_classifier):
    """Test setting of classification rules."""
    new_rules = {
        'severity_thresholds': {
            'high': 0.9,
            'medium': 0.7,
            'low': 0.5
        },
        'type_thresholds': {
            'signal_strength': -70,
            'packet_loss_rate': 0.2,
            'retry_rate': 0.3
        }
    }
    
    anomaly_classifier.set_classification_rules(new_rules)
    
    # Verify new rules were set
    assert anomaly_classifier.severity_thresholds['high'] == 0.9
    assert anomaly_classifier.severity_thresholds['medium'] == 0.7
    assert anomaly_classifier.severity_thresholds['low'] == 0.5

def test_handle_invalid_anomaly(anomaly_classifier):
    """Test handling of invalid anomaly data."""
    invalid_anomaly = {
        'timestamp': datetime.now(),
        'device_id': 'device1'
        # Missing required fields
    }
    
    with pytest.raises(KeyError):
        anomaly_classifier.classify_anomalies([invalid_anomaly])

def test_metrics_recording(anomaly_classifier, sample_anomalies, test_registry):
    """Test Prometheus metrics recording."""
    # Classify anomalies to trigger metrics recording
    anomaly_classifier.classify_anomalies(sample_anomalies)
    
    # Verify metrics were recorded
    metrics = {m.name: m for m in test_registry.collect()}
    assert 'anomaly_classification_duration_seconds' in metrics
    assert 'anomaly_classification_count' in metrics
    assert 'anomaly_severity_count' in metrics
    assert 'anomaly_type_count' in metrics

def test_classification_consistency(anomaly_classifier, sample_anomalies):
    """Test consistency of classification results."""
    # Classify anomalies multiple times
    results1 = anomaly_classifier.classify_anomalies(sample_anomalies)
    results2 = anomaly_classifier.classify_anomalies(sample_anomalies)
    
    # Verify consistent results
    assert results1 == results2 