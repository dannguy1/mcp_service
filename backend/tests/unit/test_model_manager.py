import pytest
import numpy as np
from datetime import datetime
from unittest.mock import patch, MagicMock
import joblib
import os
import tempfile

from app.components.model_manager import ModelManager

@pytest.fixture
def model_manager(test_registry):
    """Create a ModelManager instance for testing."""
    return ModelManager(registry=test_registry)

@pytest.fixture
def sample_model():
    """Create a sample model for testing."""
    model = MagicMock()
    model.predict.return_value = np.array([0, 1, 0])
    model.predict_proba.return_value = np.array([[0.8, 0.2], [0.3, 0.7], [0.9, 0.1]])
    return model

@pytest.fixture
def temp_model_dir():
    """Create a temporary directory for model storage."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

def test_model_manager_initialization(model_manager):
    """Test ModelManager initialization."""
    assert model_manager is not None
    assert model_manager.registry is not None
    assert model_manager.current_model is None
    assert model_manager.model_version is None

def test_load_model(model_manager, sample_model, temp_model_dir):
    """Test model loading functionality."""
    # Save a sample model
    model_path = os.path.join(temp_model_dir, 'test_model.joblib')
    joblib.dump(sample_model, model_path)
    
    # Load the model
    model_manager.load_model(model_path)
    
    assert model_manager.current_model is not None
    assert model_manager.model_version is not None
    assert model_manager.model_version['path'] == model_path
    assert model_manager.model_version['loaded_at'] is not None

def test_save_model(model_manager, sample_model, temp_model_dir):
    """Test model saving functionality."""
    # Set up model manager with a model
    model_manager.current_model = sample_model
    model_manager.model_version = {
        'version': '1.0.0',
        'created_at': datetime.now(),
        'metrics': {'accuracy': 0.95}
    }
    
    # Save the model
    model_path = os.path.join(temp_model_dir, 'saved_model.joblib')
    model_manager.save_model(model_path)
    
    # Verify the model was saved
    assert os.path.exists(model_path)
    loaded_model = joblib.load(model_path)
    assert loaded_model is not None

def test_predict(model_manager, sample_model):
    """Test model prediction functionality."""
    # Set up model manager with a model
    model_manager.current_model = sample_model
    
    # Test prediction
    features = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    predictions = model_manager.predict(features)
    
    assert len(predictions) == 3
    assert all(pred in [0, 1] for pred in predictions)
    sample_model.predict.assert_called_once_with(features)

def test_predict_proba(model_manager, sample_model):
    """Test model probability prediction functionality."""
    # Set up model manager with a model
    model_manager.current_model = sample_model
    
    # Test probability prediction
    features = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    probabilities = model_manager.predict_proba(features)
    
    assert probabilities.shape == (3, 2)
    assert all(np.all(prob >= 0) and np.all(prob <= 1) for prob in probabilities)
    sample_model.predict_proba.assert_called_once_with(features)

def test_get_model_info(model_manager, sample_model):
    """Test model information retrieval."""
    # Set up model manager with a model
    model_manager.current_model = sample_model
    model_manager.model_version = {
        'version': '1.0.0',
        'created_at': datetime.now(),
        'metrics': {'accuracy': 0.95}
    }
    
    # Get model info
    info = model_manager.get_model_info()
    
    assert info['version'] == '1.0.0'
    assert 'created_at' in info
    assert info['metrics']['accuracy'] == 0.95
    assert 'loaded_at' in info

def test_handle_no_model(model_manager):
    """Test handling of operations when no model is loaded."""
    features = np.array([[1, 2, 3]])
    
    with pytest.raises(RuntimeError):
        model_manager.predict(features)
    
    with pytest.raises(RuntimeError):
        model_manager.predict_proba(features)
    
    with pytest.raises(RuntimeError):
        model_manager.get_model_info()

def test_metrics_recording(model_manager, sample_model, test_registry):
    """Test Prometheus metrics recording."""
    # Set up model manager with a model
    model_manager.current_model = sample_model
    
    # Perform operations to trigger metrics recording
    features = np.array([[1, 2, 3]])
    model_manager.predict(features)
    model_manager.predict_proba(features)
    
    # Verify metrics were recorded
    metrics = {m.name: m for m in test_registry.collect()}
    assert 'model_prediction_duration_seconds' in metrics
    assert 'model_prediction_count' in metrics
    assert 'model_probability_duration_seconds' in metrics
    assert 'model_probability_count' in metrics

def test_model_versioning(model_manager, sample_model, temp_model_dir):
    """Test model versioning functionality."""
    # Save multiple versions of the model
    versions = ['1.0.0', '1.0.1', '1.1.0']
    for version in versions:
        model_manager.current_model = sample_model
        model_manager.model_version = {
            'version': version,
            'created_at': datetime.now(),
            'metrics': {'accuracy': 0.95}
        }
        model_path = os.path.join(temp_model_dir, f'model_v{version}.joblib')
        model_manager.save_model(model_path)
    
    # Verify all versions were saved
    for version in versions:
        model_path = os.path.join(temp_model_dir, f'model_v{version}.joblib')
        assert os.path.exists(model_path) 