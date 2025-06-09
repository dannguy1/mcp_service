import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
import numpy as np
import asyncio

from agents.wifi_agent import WiFiAgent

@pytest.fixture
def agent_config():
    """Create test configuration for WiFi agent."""
    return {
        'processing_interval': 60,
        'batch_size': 1000,
        'lookback_window': 30,
        'model_path': 'test_model.joblib'
    }

@pytest.fixture
def wifi_agent(agent_config, test_registry):
    """Create a WiFiAgent instance for testing."""
    return WiFiAgent(agent_config)

@pytest.fixture
def sample_logs():
    """Create sample WiFi logs for testing."""
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
            'device_id': 'device2',
            'signal_strength': -60,
            'channel': 6,
            'data_rate': 36,
            'packets_sent': 90,
            'packets_received': 80,
            'retry_count': 5
        }
    ]

@pytest.fixture
def sample_features():
    """Create sample features for testing."""
    return {
        'device_ids': ['device1', 'device2'],
        'signal_strength': [-50, -60],
        'channel': [1, 6],
        'data_rate': [54, 36],
        'packet_loss_rate': [0.05, 0.11],
        'retry_rate': [0.02, 0.06]
    }

@pytest.fixture
def sample_anomalies():
    """Create sample anomalies for testing."""
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
        }
    ]

def test_wifi_agent_initialization(wifi_agent, agent_config):
    """Test WiFi agent initialization."""
    assert wifi_agent.processing_interval == agent_config['processing_interval']
    assert wifi_agent.batch_size == agent_config['batch_size']
    assert wifi_agent.lookback_window == agent_config['lookback_window']
    assert wifi_agent.last_processed_timestamp is None
    assert isinstance(wifi_agent.active_devices, dict)
    assert len(wifi_agent.active_devices) == 0

@pytest.mark.asyncio
async def test_fetch_logs(wifi_agent, sample_logs):
    """Test log fetching functionality."""
    # Mock data service
    with patch('agents.wifi_agent.data_service.fetch_all', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = sample_logs
        
        # Test fetching logs
        logs = await wifi_agent._fetch_logs()
        
        assert len(logs) == len(sample_logs)
        assert all(log in sample_logs for log in logs)
        mock_fetch.assert_called_once()

def test_update_active_devices(wifi_agent, sample_logs):
    """Test active devices tracking."""
    # Update active devices
    wifi_agent._update_active_devices(sample_logs)
    
    # Verify active devices
    assert len(wifi_agent.active_devices) == 2
    assert 'device1' in wifi_agent.active_devices
    assert 'device2' in wifi_agent.active_devices
    
    # Test device timeout
    old_time = datetime.now() - timedelta(minutes=wifi_agent.lookback_window + 1)
    wifi_agent.active_devices['device1'] = old_time
    wifi_agent._update_active_devices([])  # Update with empty logs
    
    assert 'device1' not in wifi_agent.active_devices
    assert 'device2' in wifi_agent.active_devices

@pytest.mark.asyncio
async def test_detect_anomalies(wifi_agent, sample_features):
    """Test anomaly detection."""
    # Mock model manager
    wifi_agent.model_manager.predict = MagicMock(return_value=np.array([1, 0]))
    wifi_agent.model_manager.predict_proba = MagicMock(
        return_value=np.array([[0.2, 0.8], [0.7, 0.3]])
    )
    
    # Detect anomalies
    anomalies = await wifi_agent._detect_anomalies(sample_features)
    
    assert len(anomalies) == 1  # Only one anomaly detected
    assert anomalies[0]['device_id'] == 'device1'
    assert anomalies[0]['anomaly_score'] == 0.8

def test_prepare_feature_matrix(wifi_agent, sample_features):
    """Test feature matrix preparation."""
    matrix = wifi_agent._prepare_feature_matrix(sample_features)
    
    assert len(matrix) == 2  # Two devices
    assert len(matrix[0]) == 5  # Five numeric features
    assert matrix[0][0] == -50  # First device's signal strength
    assert matrix[1][0] == -60  # Second device's signal strength

@pytest.mark.asyncio
async def test_generate_alerts(wifi_agent, sample_anomalies):
    """Test alert generation."""
    # Mock data service
    with patch('agents.wifi_agent.data_service.execute', new_callable=AsyncMock) as mock_execute:
        # Generate alerts
        await wifi_agent._generate_alerts(sample_anomalies)
        
        # Verify database calls
        assert mock_execute.call_count == len(sample_anomalies)
        
        # Verify alert content
        first_call = mock_execute.call_args_list[0][0]
        assert first_call[1] == sample_anomalies[0]['device_id']
        assert first_call[2] == 'high'  # Severity
        assert first_call[3] == 'signal_strength'  # Type

def test_generate_alert_description(wifi_agent, sample_anomalies):
    """Test alert description generation."""
    description = wifi_agent._generate_alert_description(sample_anomalies[0])
    
    assert 'HIGH' in description
    assert 'Signal Strength' in description
    assert 'device1' in description
    assert '0.95' in description

@pytest.mark.asyncio
async def test_process_logs(wifi_agent, sample_logs, sample_features, sample_anomalies):
    """Test complete log processing workflow."""
    # Mock all necessary components
    with patch('agents.wifi_agent.data_service.fetch_all', new_callable=AsyncMock) as mock_fetch, \
         patch.object(wifi_agent.feature_extractor, 'extract_features') as mock_extract, \
         patch.object(wifi_agent.model_manager, 'predict') as mock_predict, \
         patch.object(wifi_agent.model_manager, 'predict_proba') as mock_predict_proba, \
         patch.object(wifi_agent.anomaly_classifier, 'classify_anomalies') as mock_classify, \
         patch.object(wifi_agent, '_generate_alerts', new_callable=AsyncMock) as mock_generate:
        
        # Set up mock returns
        mock_fetch.return_value = sample_logs
        mock_extract.return_value = sample_features
        mock_predict.return_value = np.array([1, 0])
        mock_predict_proba.return_value = np.array([[0.2, 0.8], [0.7, 0.3]])
        mock_classify.return_value = sample_anomalies
        
        # Process logs
        await wifi_agent.process_logs()
        
        # Verify component calls
        mock_fetch.assert_called_once()
        mock_extract.assert_called_once_with(sample_logs)
        mock_predict.assert_called_once()
        mock_predict_proba.assert_called_once()
        mock_classify.assert_called_once()
        mock_generate.assert_called_once_with(sample_anomalies)

@pytest.mark.asyncio
async def test_start_stop(wifi_agent):
    """Test agent start and stop functionality."""
    # Mock resource monitor
    wifi_agent.resource_monitor.start = MagicMock()
    wifi_agent.resource_monitor.stop = MagicMock()
    
    # Start agent
    await wifi_agent.start()
    wifi_agent.resource_monitor.start.assert_called_once()
    
    # Stop agent
    await wifi_agent.stop()
    wifi_agent.resource_monitor.stop.assert_called_once()

def test_metrics_recording(wifi_agent, sample_logs, sample_anomalies, test_registry):
    """Test Prometheus metrics recording."""
    # Mock necessary components
    wifi_agent.feature_extractor.extract_features = MagicMock(return_value={})
    wifi_agent.model_manager.predict = MagicMock(return_value=np.array([1]))
    wifi_agent.model_manager.predict_proba = MagicMock(return_value=np.array([[0.2, 0.8]]))
    wifi_agent.anomaly_classifier.classify_anomalies = MagicMock(return_value=sample_anomalies)
    
    # Process logs
    asyncio.run(wifi_agent.process_logs())
    
    # Verify metrics
    metrics = {m.name: m for m in test_registry.collect()}
    assert 'wifi_agent_logs_processed_total' in metrics
    assert 'wifi_agent_anomalies_detected_total' in metrics
    assert 'wifi_agent_alerts_generated_total' in metrics
    assert 'wifi_agent_processing_duration_seconds' in metrics
    assert 'wifi_agent_active_devices' in metrics 