import asyncio
import pytest
from datetime import datetime, timedelta
import numpy as np
from unittest.mock import patch, MagicMock

from agents.wifi_agent import WiFiAgent
from data_service import data_service
from components.resource_monitor import ResourceMonitor
from models.feature_extractor import FeatureExtractor
from models.model_manager import ModelManager
from models.anomaly_classifier import AnomalyClassifier

@pytest.fixture(scope="module")
def event_loop():
    """Create an instance of the default event loop for the test module."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def test_db():
    """Set up test database and clean up after tests."""
    # Initialize database
    await data_service.initialize()
    
    # Create test tables
    await data_service.execute("""
        CREATE TABLE IF NOT EXISTS wifi_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            device_id VARCHAR(50) NOT NULL,
            signal_strength INTEGER NOT NULL,
            channel INTEGER NOT NULL,
            data_rate INTEGER NOT NULL,
            packets_sent INTEGER NOT NULL,
            packets_received INTEGER NOT NULL,
            retry_count INTEGER NOT NULL
        )
    """)
    
    await data_service.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            device_id VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            type VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            status VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    yield data_service
    
    # Clean up
    await data_service.execute("DROP TABLE IF EXISTS wifi_logs")
    await data_service.execute("DROP TABLE IF EXISTS alerts")
    await data_service.close()

@pytest.fixture
async def sample_logs(test_db):
    """Insert sample logs into the database."""
    base_time = datetime.now()
    logs = [
        (base_time, 'device1', -50, 1, 54, 100, 95, 2),
        (base_time + timedelta(minutes=1), 'device1', -55, 1, 48, 120, 110, 3),
        (base_time + timedelta(minutes=2), 'device2', -60, 6, 36, 90, 80, 5)
    ]
    
    for log in logs:
        await test_db.execute("""
            INSERT INTO wifi_logs 
            (timestamp, device_id, signal_strength, channel, data_rate, 
             packets_sent, packets_received, retry_count)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, *log)
    
    return logs

@pytest.fixture
def agent_config():
    """Create test configuration for WiFi agent."""
    return {
        'processing_interval': 1,  # Short interval for testing
        'batch_size': 1000,
        'lookback_window': 30,
        'model_path': 'test_model.joblib',
        'resource_monitoring': {
            'enabled': True,
            'check_interval': 1,
            'thresholds': {
                'cpu': 80,
                'memory': 85,
                'disk': 90,
                'network': 1_000_000
            }
        }
    }

@pytest.fixture
async def wifi_agent(agent_config, test_db):
    """Create and initialize a WiFi agent for testing."""
    agent = WiFiAgent(agent_config)
    await agent.start()
    yield agent
    await agent.stop()

@pytest.mark.asyncio
async def test_end_to_end_log_processing(wifi_agent, sample_logs, test_db):
    """Test complete log processing workflow from database to alerts."""
    # Mock model predictions
    with patch.object(wifi_agent.model_manager, 'predict') as mock_predict, \
         patch.object(wifi_agent.model_manager, 'predict_proba') as mock_predict_proba:
        
        # Set up mock returns
        mock_predict.return_value = np.array([1, 0, 1])  # Two anomalies
        mock_predict_proba.return_value = np.array([
            [0.2, 0.8],  # High confidence anomaly
            [0.7, 0.3],  # Normal
            [0.1, 0.9]   # High confidence anomaly
        ])
        
        # Process logs
        await wifi_agent.process_logs()
        
        # Verify alerts were created
        alerts = await test_db.fetch_all("SELECT * FROM alerts ORDER BY timestamp DESC")
        assert len(alerts) == 2  # Two anomalies should generate alerts
        
        # Verify alert content
        for alert in alerts:
            assert alert['device_id'] in ['device1', 'device2']
            assert alert['severity'] in ['high', 'medium', 'low']
            assert alert['type'] in ['signal_strength', 'performance', 'channel']
            assert alert['status'] == 'new'

@pytest.mark.asyncio
async def test_end_to_end_resource_monitoring(wifi_agent):
    """Test resource monitoring integration with agent."""
    # Mock system metrics
    with patch('psutil.cpu_percent', return_value=90.0), \
         patch('psutil.virtual_memory', return_value=MagicMock(percent=90.0)), \
         patch('psutil.disk_usage', return_value=MagicMock(percent=95.0)), \
         patch('psutil.net_io_counters', return_value=MagicMock(
             bytes_sent=2_000_000,
             bytes_recv=2_000_000
         )):
        
        # Check resources
        resources = wifi_agent.resource_monitor.check_resources()
        assert resources['cpu'] == 90.0
        assert resources['memory'] == 90.0
        assert resources['disk'] == 95.0
        
        # Check alerts
        alerts = wifi_agent.resource_monitor.check_alerts()
        assert len(alerts) == 4  # All resources above threshold
        
        # Verify metrics
        metrics = {m.name: m for m in wifi_agent.resource_monitor.registry.collect()}
        assert 'cpu_usage_percent' in metrics
        assert 'memory_usage_percent' in metrics
        assert 'disk_usage_percent' in metrics
        assert 'network_io_bytes' in metrics

@pytest.mark.asyncio
async def test_end_to_end_alert_workflow(wifi_agent, test_db):
    """Test complete alert workflow from detection to storage."""
    # Create a test anomaly
    anomaly = {
        'timestamp': datetime.now(),
        'device_id': 'test_device',
        'anomaly_score': 0.95,
        'features': {
            'signal_strength': -80,
            'packet_loss_rate': 0.3,
            'retry_rate': 0.4
        }
    }
    
    # Generate alert
    await wifi_agent._create_alert(anomaly, 'signal_strength')
    
    # Verify alert in database
    alert = await test_db.fetch_one(
        "SELECT * FROM alerts WHERE device_id = $1",
        'test_device'
    )
    
    assert alert is not None
    assert alert['severity'] == 'high'
    assert alert['type'] == 'signal_strength'
    assert 'Signal Strength' in alert['description']
    assert alert['status'] == 'new'

@pytest.mark.asyncio
async def test_end_to_end_cache_workflow(wifi_agent, test_db):
    """Test cache workflow for frequently accessed data."""
    # Set cache
    await wifi_agent._set_cached('test_key', 'test_value', ttl=300)
    
    # Get cache
    value = await wifi_agent._get_cached('test_key')
    assert value == 'test_value'
    
    # Verify cache miss
    value = await wifi_agent._get_cached('nonexistent_key')
    assert value is None

@pytest.mark.asyncio
async def test_end_to_end_error_handling(wifi_agent, test_db):
    """Test error handling in the complete workflow."""
    # Simulate database error
    with patch.object(test_db, 'fetch_all', side_effect=Exception('Database error')):
        # Process should continue despite error
        await wifi_agent.process_logs()
        assert wifi_agent.is_running
    
    # Simulate model error
    with patch.object(wifi_agent.model_manager, 'predict', side_effect=Exception('Model error')):
        # Process should continue despite error
        await wifi_agent.process_logs()
        assert wifi_agent.is_running
    
    # Simulate resource monitor error
    with patch.object(wifi_agent.resource_monitor, 'check_resources', 
                     side_effect=Exception('Resource monitor error')):
        # Process should continue despite error
        await wifi_agent.process_logs()
        assert wifi_agent.is_running

@pytest.mark.asyncio
async def test_end_to_end_health_check(wifi_agent):
    """Test health check endpoint integration."""
    # Mock database check
    with patch.object(data_service, 'fetch_one', return_value={'1': 1}):
        # Check health
        response = await wifi_agent.health_check(None)
        assert response.status == 200
        data = await response.json()
        assert data['status'] == 'healthy'
    
    # Test unhealthy state
    with patch.object(data_service, 'fetch_one', side_effect=Exception('Database error')):
        response = await wifi_agent.health_check(None)
        assert response.status == 500
        data = await response.json()
        assert data['status'] == 'error' 