import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.config import ModelConfig

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def sample_model():
    """Create a sample model for testing."""
    from sklearn.ensemble import IsolationForest
    return IsolationForest(n_estimators=100, random_state=42)

@pytest.fixture
def sample_metadata():
    """Create sample model metadata."""
    return {
        "model_info": {
            "version": "1.0.0",
            "model_type": "IsolationForest",
            "created_at": datetime.now().isoformat()
        },
        "training_info": {
            "training_samples": 1000,
            "feature_names": ["feature1", "feature2", "feature3"]
        },
        "evaluation_info": {
            "basic_metrics": {
                "f1_score": 0.85,
                "roc_auc": 0.92,
                "precision": 0.88,
                "recall": 0.82
            }
        }
    }

@pytest.fixture
def mock_training_service():
    """Mock training service directory."""
    temp_dir = tempfile.mkdtemp()
    models_dir = Path(temp_dir) / "models"
    models_dir.mkdir()
    
    # Create a sample model in training service
    model_dir = models_dir / "test_model_v1"
    model_dir.mkdir()
    
    from sklearn.ensemble import IsolationForest
    import joblib
    
    model = IsolationForest(n_estimators=100, random_state=42)
    joblib.dump(model, model_dir / "model.joblib")
    
    metadata = {
        "model_info": {
            "version": "1.0.0",
            "model_type": "IsolationForest",
            "created_at": datetime.now().isoformat()
        },
        "training_info": {
            "training_samples": 1000,
            "feature_names": ["feature1", "feature2", "feature3"]
        },
        "evaluation_info": {
            "basic_metrics": {
                "f1_score": 0.85,
                "roc_auc": 0.92,
                "precision": 0.88,
                "recall": 0.82
            }
        }
    }
    
    with open(model_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f)
    
    yield temp_dir
    shutil.rmtree(temp_dir)

class TestModelManagementAPI:
    """Integration tests for model management API endpoints."""
    
    def test_get_training_service_models(self, client, mock_training_service):
        """Test getting models from training service."""
        with patch('app.models.config.ModelConfig') as mock_config:
            mock_config.return_value.integration.training_service_path = mock_training_service
            
            response = client.get("/api/v1/model-management/training-service/models")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            assert data[0]['version'] == '1.0.0'
    
    def test_import_model_from_training_service(self, client, mock_training_service):
        """Test importing a model from training service."""
        with patch('app.models.config.ModelConfig') as mock_config:
            mock_config.return_value.integration.training_service_path = mock_training_service
            mock_config.return_value.storage.directory = tempfile.mkdtemp()
            
            model_path = f"{mock_training_service}/models/test_model_v1"
            response = client.post(f"/api/v1/model-management/import/{model_path}")
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'imported'
            assert 'imported_version' in data
    
    def test_import_latest_model(self, client, mock_training_service):
        """Test importing the latest model."""
        with patch('app.models.config.ModelConfig') as mock_config:
            mock_config.return_value.integration.training_service_path = mock_training_service
            mock_config.return_value.storage.directory = tempfile.mkdtemp()
            
            response = client.post("/api/v1/model-management/import-latest")
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'imported'
    
    def test_list_models(self, client):
        """Test listing all models."""
        response = client.get("/api/v1/model-management/models")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_model_info(self, client):
        """Test getting model information."""
        # First list models to get a version
        list_response = client.get("/api/v1/model-management/models")
        if list_response.status_code == 200 and list_response.json():
            version = list_response.json()[0]['version']
            
            response = client.get(f"/api/v1/model-management/models/{version}")
            assert response.status_code == 200
            data = response.json()
            assert data['version'] == version
        else:
            # If no models exist, should return 404
            response = client.get("/api/v1/model-management/models/nonexistent")
            assert response.status_code == 404
    
    def test_validate_model(self, client):
        """Test model validation."""
        # First list models to get a version
        list_response = client.get("/api/v1/model-management/models")
        if list_response.status_code == 200 and list_response.json():
            version = list_response.json()[0]['version']
            
            response = client.post(f"/api/v1/model-management/{version}/validate")
            assert response.status_code == 200
            data = response.json()
            assert 'is_valid' in data
            assert 'score' in data
        else:
            # If no models exist, should return 404
            response = client.post("/api/v1/model-management/nonexistent/validate")
            assert response.status_code == 404
    
    def test_deploy_model(self, client):
        """Test model deployment."""
        # First list models to get a version
        list_response = client.get("/api/v1/model-management/models")
        if list_response.status_code == 200 and list_response.json():
            version = list_response.json()[0]['version']
            
            response = client.post(f"/api/v1/model-management/{version}/deploy")
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'deployed'
            assert data['version'] == version
        else:
            # If no models exist, should return 400
            response = client.post("/api/v1/model-management/nonexistent/deploy")
            assert response.status_code == 400
    
    def test_rollback_model(self, client):
        """Test model rollback."""
        # First list models to get a version
        list_response = client.get("/api/v1/model-management/models")
        if list_response.status_code == 200 and len(list_response.json()) > 1:
            version = list_response.json()[1]['version']  # Use second model for rollback
            
            response = client.post(f"/api/v1/model-management/{version}/rollback")
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'rolled_back'
            assert data['version'] == version
        else:
            # If insufficient models exist, should return 400
            response = client.post("/api/v1/model-management/nonexistent/rollback")
            assert response.status_code == 400
    
    def test_get_transfer_history(self, client):
        """Test getting transfer history."""
        response = client.get("/api/v1/model-management/transfer-history")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_model_performance(self, client):
        """Test getting model performance."""
        # First list models to get a version
        list_response = client.get("/api/v1/model-management/models")
        if list_response.status_code == 200 and list_response.json():
            version = list_response.json()[0]['version']
            
            response = client.get(f"/api/v1/model-management/performance/{version}")
            assert response.status_code == 200
            data = response.json()
            assert 'model_version' in data
            assert 'total_inferences' in data
        else:
            # If no models exist, should return 200 with empty data
            response = client.get("/api/v1/model-management/performance/nonexistent")
            assert response.status_code == 200
    
    def test_get_all_model_performance(self, client):
        """Test getting all model performance."""
        response = client.get("/api/v1/model-management/performance")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_check_model_drift(self, client):
        """Test checking model drift."""
        # First list models to get a version
        list_response = client.get("/api/v1/model-management/models")
        if list_response.status_code == 200 and list_response.json():
            version = list_response.json()[0]['version']
            
            response = client.post(f"/api/v1/model-management/performance/{version}/check-drift")
            assert response.status_code == 200
            data = response.json()
            assert 'drift_detected' in data
            assert 'drift_score' in data
        else:
            # If no models exist, should return 200 with no drift
            response = client.post("/api/v1/model-management/performance/nonexistent/check-drift")
            assert response.status_code == 200
    
    def test_generate_performance_report(self, client):
        """Test generating performance report."""
        # First list models to get a version
        list_response = client.get("/api/v1/model-management/models")
        if list_response.status_code == 200 and list_response.json():
            version = list_response.json()[0]['version']
            
            response = client.get(f"/api/v1/model-management/performance/{version}/report")
            assert response.status_code == 200
            data = response.json()
            assert 'model_version' in data
            assert 'report_timestamp' in data
        else:
            # If no models exist, should return 200 with error
            response = client.get("/api/v1/model-management/performance/nonexistent/report")
            assert response.status_code == 200
    
    def test_validate_model_compatibility(self, client):
        """Test model compatibility validation."""
        # First list models to get a version
        list_response = client.get("/api/v1/model-management/models")
        if list_response.status_code == 200 and list_response.json():
            version = list_response.json()[0]['version']
            
            target_features = ["feature1", "feature2", "feature3"]
            response = client.post(
                f"/api/v1/model-management/{version}/validate-compatibility",
                json=target_features
            )
            assert response.status_code == 200
            data = response.json()
            assert 'compatible' in data
            assert 'missing_features' in data
        else:
            # If no models exist, should return 404
            response = client.post(
                "/api/v1/model-management/nonexistent/validate-compatibility",
                json=["feature1", "feature2"]
            )
            assert response.status_code == 404
    
    def test_generate_validation_report(self, client):
        """Test generating validation report."""
        # First list models to get a version
        list_response = client.get("/api/v1/model-management/models")
        if list_response.status_code == 200 and list_response.json():
            version = list_response.json()[0]['version']
            
            response = client.get(f"/api/v1/model-management/{version}/validation-report")
            assert response.status_code == 200
            data = response.json()
            assert 'model_path' in data
            assert 'validation_timestamp' in data
        else:
            # If no models exist, should return 404
            response = client.get("/api/v1/model-management/nonexistent/validation-report")
            assert response.status_code == 404
    
    def test_validate_training_service_connection(self, client, mock_training_service):
        """Test validating training service connection."""
        with patch('app.models.config.ModelConfig') as mock_config:
            mock_config.return_value.integration.training_service_path = mock_training_service
            
            response = client.get("/api/v1/model-management/training-service/connection")
            
            assert response.status_code == 200
            data = response.json()
            assert 'connected' in data
            assert 'path_exists' in data
            assert 'models_found' in data
    
    def test_cleanup_transfer_history(self, client):
        """Test cleaning up transfer history."""
        response = client.delete("/api/v1/model-management/transfer-history?days_to_keep=30")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
    
    def test_cleanup_performance_metrics(self, client):
        """Test cleaning up performance metrics."""
        response = client.delete("/api/v1/model-management/performance/cleanup?days_to_keep=30")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success' 