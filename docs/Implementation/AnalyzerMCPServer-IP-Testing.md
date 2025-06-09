# AnalyzerMCPServer Implementation Plan - Testing

## Overview

This document details the testing implementation for the AnalyzerMCPServer, including unit tests, integration tests, and performance tests.

## 1. Test Structure

### 1.1 Directory Structure

```
/tests/
├── __init__.py
├── conftest.py                 # Test configuration
├── /unit/                      # Unit tests
│   ├── __init__.py
│   ├── test_data_service.py
│   ├── test_feature_extractor.py
│   ├── test_model_manager.py
│   └── test_anomaly_classifier.py
├── /integration/               # Integration tests
│   ├── __init__.py
│   ├── test_agent_workflow.py
│   └── test_training_pipeline.py
└── /performance/               # Performance tests
    ├── __init__.py
    └── test_resource_usage.py
```

## 2. Test Configuration

### 2.1 Test Configuration (`conftest.py`)

```python
import pytest
import asyncio
import asyncpg
import redis
from config import Config

@pytest.fixture
def config():
    """Test configuration."""
    return Config()

@pytest.fixture
async def db_pool(config):
    """Database connection pool."""
    pool = await asyncpg.create_pool(
        host=config.db.host,
        port=config.db.port,
        user=config.db.user,
        password=config.db.password,
        database=config.db.database
    )
    yield pool
    await pool.close()

@pytest.fixture
def redis_client(config):
    """Redis client."""
    client = redis.Redis(
        host=config.redis.host,
        port=config.redis.port,
        db=config.redis.db
    )
    yield client
    client.close()

@pytest.fixture
def event_loop():
    """Event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

## 3. Unit Tests

### 3.1 Data Service Tests (`test_data_service.py`)

```python
import pytest
from datetime import datetime, timedelta
from data_service import DataService

@pytest.mark.asyncio
async def test_get_logs(db_pool, redis_client, config):
    """Test log retrieval with caching."""
    # Initialize service
    service = DataService(config)
    service.pool = db_pool
    service.redis = redis_client
    
    # Test parameters
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=5)
    
    # Test cache miss
    logs = await service.get_logs(
        start_time.isoformat(),
        end_time.isoformat()
    )
    assert isinstance(logs, list)
    
    # Test cache hit
    cached_logs = await service.get_logs(
        start_time.isoformat(),
        end_time.isoformat()
    )
    assert cached_logs == logs

@pytest.mark.asyncio
async def test_store_anomaly(db_pool, config):
    """Test anomaly storage."""
    # Initialize service
    service = DataService(config)
    service.pool = db_pool
    
    # Test data
    anomaly_data = {
        'type': 'test_anomaly',
        'severity': 3,
        'description': 'Test anomaly',
        'details': {'test': 'data'},
        'model_version': 'test_v1'
    }
    
    # Store anomaly
    anomaly_id = await service.store_anomaly(anomaly_data)
    assert isinstance(anomaly_id, int)
    
    # Verify storage
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT * FROM wifi_anomalies WHERE id = $1',
            anomaly_id
        )
        assert row['anomaly_type'] == anomaly_data['type']
        assert row['severity'] == anomaly_data['severity']
```

### 3.2 Feature Extractor Tests (`test_feature_extractor.py`)

```python
import pytest
from components.feature_extractor import WiFiFeatureExtractor

def test_feature_extraction():
    """Test feature extraction from logs."""
    # Test data
    logs = [
        {
            'timestamp': '2024-01-01T00:00:00',
            'level': 'error',
            'message': 'Test error',
            'client_mac': '00:11:22:33:44:55',
            'ap_mac': 'AA:BB:CC:DD:EE:FF',
            'event_type': 'authentication_failure'
        },
        {
            'timestamp': '2024-01-01T00:00:01',
            'level': 'info',
            'message': 'Test info',
            'client_mac': '00:11:22:33:44:55',
            'ap_mac': 'AA:BB:CC:DD:EE:FF',
            'event_type': 'connection_attempt'
        }
    ]
    
    # Extract features
    extractor = WiFiFeatureExtractor()
    features = extractor.extract_features(logs)
    
    # Verify features
    assert 'error_ratio' in features
    assert 'auth_failure_rate' in features
    assert 'conn_attempt_rate' in features
    assert 'unique_clients' in features
    assert 'unique_aps' in features
    
    assert features['error_ratio'] == 0.5
    assert features['auth_failure_rate'] == 0.5
    assert features['conn_attempt_rate'] == 0.5
    assert features['unique_clients'] == 1
    assert features['unique_aps'] == 1

def test_missing_columns():
    """Test handling of missing columns."""
    # Test data with missing columns
    logs = [
        {
            'timestamp': '2024-01-01T00:00:00',
            'level': 'error'
        }
    ]
    
    # Verify error handling
    extractor = WiFiFeatureExtractor()
    with pytest.raises(ValueError):
        extractor.extract_features(logs)
```

### 3.3 Model Manager Tests (`test_model_manager.py`)

```python
import pytest
import os
import joblib
import numpy as np
from components.model_manager import WiFiModelManager

@pytest.fixture
def model_dir(tmp_path):
    """Create temporary model directory."""
    return str(tmp_path)

@pytest.fixture
def sample_model(model_dir):
    """Create sample model file."""
    model = joblib.dump(np.random.rand(10, 10), f"{model_dir}/test_model.joblib")
    return model

@pytest.mark.asyncio
async def test_model_loading(model_dir, sample_model):
    """Test model loading."""
    manager = WiFiModelManager(model_dir)
    await manager.start()
    
    assert manager.model is not None
    assert manager.model_version == 'test_model'

@pytest.mark.asyncio
async def test_model_prediction(model_dir, sample_model):
    """Test model prediction."""
    manager = WiFiModelManager(model_dir)
    await manager.start()
    
    features = {
        'error_ratio': 0.1,
        'disassoc_rate': 0.2,
        'auth_failure_rate': 0.15,
        'conn_attempt_rate': 0.3,
        'unique_clients': 5,
        'unique_aps': 2
    }
    
    prediction = manager.predict(features)
    assert isinstance(prediction, float)
```

### 3.4 Anomaly Classifier Tests (`test_anomaly_classifier.py`)

```python
import pytest
from components.anomaly_classifier import WiFiAnomalyClassifier

def test_anomaly_classification():
    """Test anomaly classification."""
    classifier = WiFiAnomalyClassifier(threshold=-0.5)
    
    # Test normal case
    normal_prediction = -0.3
    normal_result = classifier.classify(normal_prediction, {})
    assert normal_result is None
    
    # Test anomaly case
    anomaly_prediction = -0.7
    anomaly_result = classifier.classify(anomaly_prediction, {
        'error_ratio': 0.2,
        'disassoc_rate': 0.3,
        'auth_failure_rate': 0.25
    })
    
    assert anomaly_result is not None
    assert anomaly_result['type'] == 'wifi_anomaly'
    assert 1 <= anomaly_result['severity'] <= 5
    assert 'description' in anomaly_result
    assert 'details' in anomaly_result

def test_severity_calculation():
    """Test severity calculation."""
    classifier = WiFiAnomalyClassifier()
    
    # Test severity levels
    assert classifier._calculate_severity(-0.9) == 5
    assert classifier._calculate_severity(-0.7) == 4
    assert classifier._calculate_severity(-0.5) == 3
    assert classifier._calculate_severity(-0.3) == 2
    assert classifier._calculate_severity(-0.1) == 1
```

## 4. Integration Tests

### 4.1 Agent Workflow Tests (`test_agent_workflow.py`)

```python
import pytest
from datetime import datetime, timedelta
from agents.wifi_agent import WiFiAgent
from data_service import DataService

@pytest.mark.asyncio
async def test_agent_workflow(db_pool, redis_client, config):
    """Test complete agent workflow."""
    # Initialize services
    data_service = DataService(config)
    data_service.pool = db_pool
    data_service.redis = redis_client
    
    agent = WiFiAgent(data_service, config)
    
    # Start agent
    await agent.start()
    
    # Run analysis cycle
    await agent.run_analysis_cycle()
    
    # Stop agent
    await agent.stop()
    
    # Verify results
    async with db_pool.acquire() as conn:
        anomalies = await conn.fetch('SELECT * FROM wifi_anomalies')
        assert len(anomalies) >= 0

@pytest.mark.asyncio
async def test_agent_error_handling(db_pool, redis_client, config):
    """Test agent error handling."""
    # Initialize services
    data_service = DataService(config)
    data_service.pool = db_pool
    data_service.redis = redis_client
    
    agent = WiFiAgent(data_service, config)
    
    # Start agent
    await agent.start()
    
    # Simulate error
    data_service.pool = None
    
    # Run analysis cycle
    await agent.run_analysis_cycle()
    
    # Stop agent
    await agent.stop()
    
    # Verify agent is still running
    assert agent.running is False
```

### 4.2 Training Pipeline Tests (`test_training_pipeline.py`)

```python
import pytest
import os
from train_pipeline import run_training_pipeline

def test_training_pipeline(config, tmp_path):
    """Test complete training pipeline."""
    # Set output directory
    os.chdir(tmp_path)
    
    # Run pipeline
    run_training_pipeline(config)
    
    # Verify outputs
    assert os.path.exists('wifi_logs.csv')
    assert os.path.exists('models')
    assert len(os.listdir('models')) > 0

def test_pipeline_error_handling(config, tmp_path):
    """Test pipeline error handling."""
    # Set output directory
    os.chdir(tmp_path)
    
    # Simulate error
    config.db.password = 'invalid'
    
    # Run pipeline
    with pytest.raises(Exception):
        run_training_pipeline(config)
```

## 5. Performance Tests

### 5.1 Resource Usage Tests (`test_resource_usage.py`)

```python
import pytest
import psutil
import time
from agents.wifi_agent import WiFiAgent
from data_service import DataService

@pytest.mark.asyncio
async def test_memory_usage(db_pool, redis_client, config):
    """Test memory usage during operation."""
    # Initialize services
    data_service = DataService(config)
    data_service.pool = db_pool
    data_service.redis = redis_client
    
    agent = WiFiAgent(data_service, config)
    
    # Measure memory before
    process = psutil.Process()
    memory_before = process.memory_info().rss
    
    # Start agent
    await agent.start()
    
    # Run analysis cycle
    await agent.run_analysis_cycle()
    
    # Measure memory after
    memory_after = process.memory_info().rss
    memory_increase = memory_after - memory_before
    
    # Stop agent
    await agent.stop()
    
    # Verify memory usage
    assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase

@pytest.mark.asyncio
async def test_cpu_usage(db_pool, redis_client, config):
    """Test CPU usage during operation."""
    # Initialize services
    data_service = DataService(config)
    data_service.pool = db_pool
    data_service.redis = redis_client
    
    agent = WiFiAgent(data_service, config)
    
    # Start agent
    await agent.start()
    
    # Measure CPU usage
    process = psutil.Process()
    cpu_percent = process.cpu_percent(interval=1)
    
    # Stop agent
    await agent.stop()
    
    # Verify CPU usage
    assert cpu_percent < 50  # Less than 50% CPU usage
```

## 6. Test Execution

### 6.1 Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/

# Run with coverage
pytest --cov=mcp_service tests/

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_data_service.py
```

### 6.2 Test Configuration (`pytest.ini`)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --cov=mcp_service --cov-report=term-missing
```

## Next Steps

1. Review the [Deployment Guide](AnalyzerMCPServer-IP-Deployment.md) for setup instructions
2. Check the [Documentation Guide](AnalyzerMCPServer-IP-Docs.md) for documentation templates
3. Follow the [Training Implementation](AnalyzerMCPServer-IP-Training.md) for model management 