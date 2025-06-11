import pytest
import asyncio
import numpy as np
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.api.model_server import app
from app.models.model_loader import ModelLoader
from app.models.training import ModelTrainer
from app.data_service import data_service

# Initialize test client
client = TestClient(app)

@pytest.fixture
async def test_db():
    """Set up test database and clean up after tests."""
    # Create test tables
    await data_service.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            prediction INTEGER NOT NULL,
            score FLOAT NOT NULL,
            is_anomaly BOOLEAN,
            features JSONB
        )
    """)
    
    yield
    
    # Clean up
    await data_service.execute("DROP TABLE IF EXISTS predictions")

@pytest.fixture
async def sample_model():
    """Create a sample model for testing."""
    # Initialize trainer with test config
    config = {
        'model_dir': 'models/test',
        'n_estimators': 10,
        'contamination': 0.1
    }
    trainer = ModelTrainer(config)
    
    # Create sample data
    X = np.random.randn(100, 5)  # 100 samples, 5 features
    y = np.zeros(100)  # Dummy labels
    
    # Train model
    model = trainer.train_model(X, y)
    
    # Save model
    version = datetime.now().strftime('%Y%m%d_%H%M%S')
    model_path = trainer.save_model(model, version)
    
    return model_path

@pytest.fixture
def sample_logs():
    """Create sample log data for testing."""
    return [
        {
            'timestamp': datetime.now().isoformat(),
            'device_id': 'test_device_1',
            'signal_strength': -65,
            'channel': 1,
            'data_rate': 54.0,
            'packet_loss_rate': 0.01,
            'retry_rate': 0.05
        },
        {
            'timestamp': datetime.now().isoformat(),
            'device_id': 'test_device_2',
            'signal_strength': -75,
            'channel': 6,
            'data_rate': 36.0,
            'packet_loss_rate': 0.05,
            'retry_rate': 0.1
        }
    ]

@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model_loaded" in data

@pytest.mark.asyncio
async def test_predict_endpoint(sample_model, sample_logs):
    """Test prediction endpoint."""
    # Load model
    model_loader = ModelLoader()
    model_loader.load_model(sample_model)
    
    # Make prediction request
    response = client.post("/predict", json={
        "logs": sample_logs,
        "model_version": None
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert "scores" in data
    assert "model_version" in data
    assert "timestamp" in data
    assert len(data["predictions"]) == len(sample_logs)

@pytest.mark.asyncio
async def test_list_models(sample_model):
    """Test listing available models."""
    response = client.get("/models")
    assert response.status_code == 200
    models = response.json()
    assert isinstance(models, list)
    assert len(models) > 0

@pytest.mark.asyncio
async def test_get_model_info(sample_model):
    """Test getting model information."""
    # Get model version from path
    version = sample_model.split('/')[-1]
    
    response = client.get(f"/models/{version}")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "timestamp" in data
    assert "config" in data
    assert "feature_names" in data

@pytest.mark.asyncio
async def test_train_model():
    """Test model training endpoint."""
    response = client.post("/train", json={
        "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
        "end_date": datetime.now().isoformat(),
        "config_path": "config/model_config.yaml"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "model_path" in data
    assert "version" in data
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_metrics_endpoint(test_db):
    """Test metrics endpoint."""
    # Insert some test predictions
    await data_service.execute("""
        INSERT INTO predictions (timestamp, prediction, score, is_anomaly)
        VALUES ($1, $2, $3, $4)
    """, datetime.now(), -1, 0.8, True)
    
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "predictions_total" in data
    assert "anomalies_detected" in data
    assert "prediction_latency" in data
    assert "model_load_time" in data

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in API endpoints."""
    # Test with invalid model version
    response = client.get("/models/invalid_version")
    assert response.status_code == 404
    
    # Test with invalid prediction data
    response = client.post("/predict", json={
        "logs": [{"invalid": "data"}],
        "model_version": None
    })
    assert response.status_code == 500

@pytest.mark.asyncio
async def test_concurrent_requests(sample_model, sample_logs):
    """Test handling of concurrent requests."""
    # Load model
    model_loader = ModelLoader()
    model_loader.load_model(sample_model)
    
    # Create multiple concurrent requests
    async def make_request():
        return client.post("/predict", json={
            "logs": sample_logs,
            "model_version": None
        })
    
    # Make 10 concurrent requests
    tasks = [make_request() for _ in range(10)]
    responses = await asyncio.gather(*tasks)
    
    # Check all requests succeeded
    assert all(r.status_code == 200 for r in responses)
    
    # Verify response consistency
    first_data = responses[0].json()
    for response in responses[1:]:
        data = response.json()
        assert len(data["predictions"]) == len(first_data["predictions"])
        assert len(data["scores"]) == len(first_data["scores"]) 