import pytest
from datetime import datetime, timedelta
import numpy as np

from components.feature_extractor import FeatureExtractor

@pytest.fixture
def feature_extractor(test_registry):
    """Create a FeatureExtractor instance for testing."""
    return FeatureExtractor(registry=test_registry)

@pytest.fixture
def sample_logs():
    """Create sample log data for testing."""
    base_time = datetime.now()
    return [
        {
            'timestamp': base_time,
            'device_id': 'device1',
            'signal_strength': -50,
            'channel': 1,
            'data_rate': 54,
            'packets_sent': 100,
            'packets_received': 95,
            'retry_count': 2
        },
        {
            'timestamp': base_time + timedelta(minutes=1),
            'device_id': 'device1',
            'signal_strength': -55,
            'channel': 1,
            'data_rate': 48,
            'packets_sent': 120,
            'packets_received': 110,
            'retry_count': 3
        },
        {
            'timestamp': base_time + timedelta(minutes=2),
            'device_id': 'device1',
            'signal_strength': -60,
            'channel': 1,
            'data_rate': 36,
            'packets_sent': 90,
            'packets_received': 80,
            'retry_count': 5
        }
    ]

def test_feature_extractor_initialization(feature_extractor):
    """Test FeatureExtractor initialization."""
    assert feature_extractor is not None
    assert feature_extractor.registry is not None

def test_extract_signal_features(feature_extractor, sample_logs):
    """Test signal strength feature extraction."""
    features = feature_extractor.extract_signal_features(sample_logs)
    
    assert 'mean_signal_strength' in features
    assert 'std_signal_strength' in features
    assert 'min_signal_strength' in features
    assert 'max_signal_strength' in features
    assert 'signal_strength_trend' in features
    
    assert features['mean_signal_strength'] == -55.0
    assert features['min_signal_strength'] == -60
    assert features['max_signal_strength'] == -50
    assert features['signal_strength_trend'] < 0  # Negative trend

def test_extract_channel_features(feature_extractor, sample_logs):
    """Test channel feature extraction."""
    features = feature_extractor.extract_channel_features(sample_logs)
    
    assert 'channel_utilization' in features
    assert 'channel_changes' in features
    assert 'channel_stability' in features
    
    assert features['channel_changes'] == 0  # No channel changes in sample
    assert features['channel_stability'] == 1.0  # Perfect stability

def test_extract_performance_features(feature_extractor, sample_logs):
    """Test performance feature extraction."""
    features = feature_extractor.extract_performance_features(sample_logs)
    
    assert 'mean_data_rate' in features
    assert 'packet_loss_rate' in features
    assert 'retry_rate' in features
    assert 'throughput' in features
    
    assert features['mean_data_rate'] == 46.0
    assert 0 < features['packet_loss_rate'] < 1
    assert 0 < features['retry_rate'] < 1
    assert features['throughput'] > 0

def test_extract_temporal_features(feature_extractor, sample_logs):
    """Test temporal feature extraction."""
    features = feature_extractor.extract_temporal_features(sample_logs)
    
    assert 'time_span' in features
    assert 'log_frequency' in features
    assert 'time_between_logs' in features
    
    assert features['time_span'] == 120  # 2 minutes in seconds
    assert features['log_frequency'] == 3  # 3 logs
    assert len(features['time_between_logs']) == 2  # 2 intervals

def test_extract_all_features(feature_extractor, sample_logs):
    """Test extraction of all features."""
    features = feature_extractor.extract_features(sample_logs)
    
    # Check that all feature categories are present
    assert 'signal' in features
    assert 'channel' in features
    assert 'performance' in features
    assert 'temporal' in features
    
    # Check that each category has its expected features
    assert len(feature_extractor.extract_signal_features(sample_logs)) == len(features['signal'])
    assert len(feature_extractor.extract_channel_features(sample_logs)) == len(features['channel'])
    assert len(feature_extractor.extract_performance_features(sample_logs)) == len(features['performance'])
    assert len(feature_extractor.extract_temporal_features(sample_logs)) == len(features['temporal'])

def test_handle_empty_logs(feature_extractor):
    """Test feature extraction with empty log list."""
    empty_logs = []
    
    with pytest.raises(ValueError):
        feature_extractor.extract_features(empty_logs)

def test_handle_invalid_logs(feature_extractor):
    """Test feature extraction with invalid log data."""
    invalid_logs = [
        {'timestamp': datetime.now(), 'device_id': 'device1'}  # Missing required fields
    ]
    
    with pytest.raises(KeyError):
        feature_extractor.extract_features(invalid_logs)

def test_metrics_recording(feature_extractor, sample_logs, test_registry):
    """Test Prometheus metrics recording during feature extraction."""
    # Extract features to trigger metrics recording
    feature_extractor.extract_features(sample_logs)
    
    # Verify metrics were recorded
    metrics = {m.name: m for m in test_registry.collect()}
    assert 'feature_extraction_duration_seconds' in metrics
    assert 'feature_extraction_count' in metrics 