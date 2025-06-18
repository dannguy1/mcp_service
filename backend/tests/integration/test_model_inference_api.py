import pytest
import numpy as np
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
import joblib
from fastapi.testclient import TestClient

from app.main import app
from app.components.model_manager import ModelManager
from app.models.config import ModelConfig

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def model_config():
    """Create a test ModelConfig."""
    config = ModelConfig()
    config.storage.directory = "/tmp/test_models"
    return config

@pytest.fixture
def sample_model():
    """Create a sample model for testing."""
    from sklearn.ensemble import IsolationForest
    return IsolationForest(n_estimators=100, random_state=42)

@pytest.fixture
def temp_model_dir():
    """Create a temporary directory for model files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

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
                "recall": 0.82,
                "accuracy": 0.90
            }
        }
    }

@pytest.fixture
def sample_logs():
    """Create sample log entries for testing."""
    return [
        {
            "id": 1,
            "timestamp": "2024-01-01T10:00:00Z",
            "level": "INFO",
            "program": "test_program",
            "message": "Test log message 1",
            "device_id": "device1",
            "device_ip": "192.168.1.1",
            "process": "test_process",
            "raw_message": "Raw test message 1",
            "structured_data": {"key1": "value1"}
        },
        {
            "id": 2,
            "timestamp": "2024-01-01T10:01:00Z",
            "level": "WARNING",
            "program": "test_program",
            "message": "Test log message 2",
            "device_id": "device2",
            "device_ip": "192.168.1.2",
            "process": "test_process",
            "raw_message": "Raw test message 2",
            "structured_data": {"key2": "value2"}
        }
    ]

class TestModelInferenceAPI:
    """Integration tests for model inference API endpoints."""

    def test_get_models(self, client):
        """Test getting list of models."""
        response = client.get("/api/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "total" in data

    def test_get_model_info(self, client):
        """Test getting model information."""
        # First get models to find an existing model ID
        models_response = client.get("/api/v1/models")
        models_data = models_response.json()
        
        if models_data["models"]:
            model_id = models_data["models"][0]["id"]
            response = client.get(f"/api/v1/models/{model_id}/info")
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "version" in data
        else:
            # Test with non-existent model
            response = client.get("/api/v1/models/nonexistent/info")
            assert response.status_code == 404

    def test_get_current_model(self, client):
        """Test getting current model information."""
        response = client.get("/api/v1/models/current")
        assert response.status_code == 200
        data = response.json()
        # Should return either model info or message about no model loaded
        assert "message" in data or "version" in data

    @pytest.mark.asyncio
    async def test_load_model_version(self, client, temp_model_dir, sample_model, sample_metadata):
        """Test loading a specific model version."""
        # Create a test model
        model_path = Path(temp_model_dir) / "test_version"
        model_path.mkdir()
        
        joblib.dump(sample_model, model_path / "model.joblib")
        with open(model_path / "metadata.json", 'w') as f:
            json.dump(sample_metadata, f)
        
        # Mock the ModelManager to return our test model
        with patch('app.components.model_manager.ModelManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.list_models.return_value = [
                {
                    'version': 'test_version',
                    'path': str(model_path)
                }
            ]
            mock_manager.load_model_version.return_value = True
            mock_manager.get_model_info.return_value = {
                'version': 'test_version',
                'model_type': 'IsolationForest',
                'feature_names': ['feature1', 'feature2', 'feature3']
            }
            
            response = client.post("/api/v1/models/test_version/load")
            assert response.status_code == 200
            data = response.json()
            assert data["version"] == "test_version"
            assert data["status"] == "loaded"

    def test_load_model_version_not_found(self, client):
        """Test loading non-existent model version."""
        with patch('app.components.model_manager.ModelManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.list_models.return_value = []
            
            response = client.post("/api/v1/models/nonexistent/load")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_analyze_logs(self, client, sample_logs):
        """Test analyzing logs with current model."""
        # Mock the ModelManager and FeatureExtractor
        with patch('app.components.model_manager.ModelManager') as mock_manager_class, \
             patch('app.components.feature_extractor.FeatureExtractor') as mock_extractor_class:
            
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.is_model_loaded.return_value = True
            mock_manager.current_model_version = "1.0.0"
            mock_manager.predict.return_value = np.array([1, 0])
            mock_manager.predict_proba.return_value = np.array([[0.2, 0.8], [0.9, 0.1]])
            
            mock_extractor = MagicMock()
            mock_extractor_class.return_value = mock_extractor
            mock_extractor.extract_features.return_value = [1, 2, 3]
            
            response = client.post("/api/v1/models/analyze", json=sample_logs)
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 2
            assert "log_entry" in data[0]
            assert "analysis_result" in data[0]
            assert "is_anomaly" in data[0]["analysis_result"]

    def test_analyze_logs_no_model_loaded(self, client, sample_logs):
        """Test analyzing logs without loaded model."""
        with patch('app.components.model_manager.ModelManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.is_model_loaded.return_value = False
            
            response = client.post("/api/v1/models/analyze", json=sample_logs)
            assert response.status_code == 400
            assert "No model loaded" in response.json()["detail"]

    def test_analyze_logs_empty_input(self, client):
        """Test analyzing empty log list."""
        with patch('app.components.model_manager.ModelManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.is_model_loaded.return_value = True
            
            response = client.post("/api/v1/models/analyze", json=[])
            assert response.status_code == 400
            assert "No valid features extracted" in response.json()["detail"]

    def test_activate_model(self, client):
        """Test activating a model."""
        # Mock the model manager
        with patch('app.mcp_service.components.model_manager.model_manager') as mock_manager:
            mock_manager.activate_model.return_value = True
            
            response = client.post("/api/v1/models/test_model/activate")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_deactivate_model(self, client):
        """Test deactivating a model."""
        # Mock the model manager
        with patch('app.mcp_service.components.model_manager.model_manager') as mock_manager:
            mock_manager.deactivate_model.return_value = True
            
            response = client.post("/api/v1/models/test_model/deactivate")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_deploy_model(self, client):
        """Test deploying a model."""
        response = client.post("/api/v1/models/test_model/deploy")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

class TestModelManagementAPI:
    """Integration tests for enhanced model management API endpoints."""

    def test_list_enhanced_models(self, client):
        """Test listing enhanced models."""
        with patch('app.components.model_manager.ModelManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.list_models.return_value = [
                {
                    'version': '1.0.0',
                    'path': '/tmp/models/1.0.0',
                    'status': 'available',
                    'created_at': '2024-01-01T00:00:00',
                    'model_type': 'IsolationForest'
                }
            ]
            
            response = client.get("/api/v1/model-management/models")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]['version'] == '1.0.0'

    def test_get_enhanced_model_info(self, client):
        """Test getting enhanced model information."""
        with patch('app.components.model_manager.ModelManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.list_models.return_value = [
                {
                    'version': '1.0.0',
                    'path': '/tmp/models/1.0.0',
                    'status': 'available'
                }
            ]
            
            response = client.get("/api/v1/model-management/models/1.0.0")
            assert response.status_code == 200
            data = response.json()
            assert data['version'] == '1.0.0'

    def test_deploy_model_version(self, client):
        """Test deploying a model version."""
        with patch('app.components.model_manager.ModelManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.deploy_model.return_value = True
            
            response = client.post("/api/v1/model-management/1.0.0/deploy")
            assert response.status_code == 200
            data = response.json()
            assert data['version'] == '1.0.0'
            assert data['status'] == 'deployed'

    def test_rollback_model(self, client):
        """Test rolling back to a model version."""
        with patch('app.components.model_manager.ModelManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.rollback_model.return_value = True
            
            response = client.post("/api/v1/model-management/1.0.0/rollback")
            assert response.status_code == 200
            data = response.json()
            assert data['version'] == '1.0.0'
            assert data['status'] == 'rolled_back'

    def test_validate_model(self, client):
        """Test model validation."""
        with patch('app.services.model_validator.ModelValidator') as mock_validator_class, \
             patch('app.components.model_manager.ModelManager') as mock_manager_class:
            
            mock_validator = MagicMock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_model_quality.return_value = {
                'is_valid': True,
                'score': 0.9,
                'errors': [],
                'warnings': [],
                'recommendations': []
            }
            
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.list_models.return_value = [
                {
                    'version': '1.0.0',
                    'path': '/tmp/models/1.0.0'
                }
            ]
            
            response = client.post("/api/v1/model-management/1.0.0/validate")
            assert response.status_code == 200
            data = response.json()
            assert data['is_valid'] is True

    def test_get_model_performance(self, client):
        """Test getting model performance metrics."""
        with patch('app.services.model_performance_monitor.ModelPerformanceMonitor') as mock_monitor_class:
            mock_monitor = MagicMock()
            mock_monitor_class.return_value = mock_monitor
            mock_monitor.get_performance_summary.return_value = {
                'model_version': '1.0.0',
                'total_inferences': 1000,
                'performance_metrics': {
                    'avg_inference_time': 0.1,
                    'anomaly_rate': 0.05
                }
            }
            
            response = client.get("/api/v1/model-management/performance/1.0.0")
            assert response.status_code == 200
            data = response.json()
            assert data['model_version'] == '1.0.0'
            assert data['total_inferences'] == 1000

    def test_check_model_drift(self, client):
        """Test checking model drift."""
        with patch('app.services.model_performance_monitor.ModelPerformanceMonitor') as mock_monitor_class:
            mock_monitor = MagicMock()
            mock_monitor_class.return_value = mock_monitor
            mock_monitor.check_model_drift.return_value = {
                'drift_detected': False,
                'drift_score': 0.05,
                'confidence': 0.8
            }
            
            response = client.post("/api/v1/model-management/performance/1.0.0/check-drift")
            assert response.status_code == 200
            data = response.json()
            assert data['drift_detected'] is False

    def test_get_transfer_history(self, client):
        """Test getting model transfer history."""
        with patch('app.services.model_transfer_service.ModelTransferService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.get_transfer_history.return_value = [
                {
                    'transfer_id': 'transfer_1',
                    'original_path': '/tmp/original',
                    'local_path': '/tmp/local',
                    'transferred_at': '2024-01-01T00:00:00',
                    'status': 'completed'
                }
            ]
            
            response = client.get("/api/v1/model-management/transfer-history")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]['transfer_id'] == 'transfer_1'

    def test_cleanup_transfer_history(self, client):
        """Test cleaning up transfer history."""
        with patch('app.services.model_transfer_service.ModelTransferService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            response = client.delete("/api/v1/model-management/transfer-history?days_to_keep=30")
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'

    def test_cleanup_performance_metrics(self, client):
        """Test cleaning up performance metrics."""
        with patch('app.services.model_performance_monitor.ModelPerformanceMonitor') as mock_monitor_class:
            mock_monitor = MagicMock()
            mock_monitor_class.return_value = mock_monitor
            
            response = client.delete("/api/v1/model-management/performance/cleanup?days_to_keep=30")
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'

    def test_validate_training_service_connection(self, client):
        """Test validating training service connection."""
        with patch('app.services.model_transfer_service.ModelTransferService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.validate_training_service_connection.return_value = {
                'connected': True,
                'path_exists': True,
                'models_found': 5
            }
            
            response = client.get("/api/v1/model-management/training-service/connection")
            assert response.status_code == 200
            data = response.json()
            assert data['connected'] is True

    def test_import_latest_model(self, client):
        """Test importing latest model from training service."""
        with patch('app.services.model_transfer_service.ModelTransferService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.import_latest_model.return_value = {
                'imported_version': 'import_20240101_120000',
                'local_path': '/tmp/models/import_20240101_120000',
                'status': 'imported'
            }
            
            response = client.post("/api/v1/model-management/import-latest")
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'imported'
            assert 'imported_version' in data

    def test_generate_performance_report(self, client):
        """Test generating performance report."""
        with patch('app.services.model_performance_monitor.ModelPerformanceMonitor') as mock_monitor_class:
            mock_monitor = MagicMock()
            mock_monitor_class.return_value = mock_monitor
            mock_monitor.generate_performance_report.return_value = {
                'model_version': '1.0.0',
                'report_timestamp': '2024-01-01T00:00:00',
                'performance_summary': {},
                'drift_analysis': {},
                'recommendations': []
            }
            
            response = client.get("/api/v1/model-management/performance/1.0.0/report")
            assert response.status_code == 200
            data = response.json()
            assert data['model_version'] == '1.0.0'

    def test_generate_validation_report(self, client):
        """Test generating validation report."""
        with patch('app.services.model_validator.ModelValidator') as mock_validator_class, \
             patch('app.components.model_manager.ModelManager') as mock_manager_class:
            
            mock_validator = MagicMock()
            mock_validator_class.return_value = mock_validator
            mock_validator.generate_validation_report.return_value = {
                'report_id': 'validation_20240101_120000',
                'generated_at': '2024-01-01T12:00:00',
                'model_path': '/tmp/models/1.0.0',
                'validation_summary': {
                    'is_valid': True,
                    'score': 0.9
                }
            }
            
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.list_models.return_value = [
                {
                    'version': '1.0.0',
                    'path': '/tmp/models/1.0.0'
                }
            ]
            
            response = client.get("/api/v1/model-management/1.0.0/validation-report")
            assert response.status_code == 200
            data = response.json()
            assert data['validation_summary']['is_valid'] is True

    def test_validate_model_compatibility(self, client):
        """Test validating model compatibility."""
        with patch('app.services.model_validator.ModelValidator') as mock_validator_class, \
             patch('app.components.model_manager.ModelManager') as mock_manager_class:
            
            mock_validator = MagicMock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_model_compatibility.return_value = {
                'is_compatible': True,
                'compatibility_score': 0.95,
                'missing_features': [],
                'extra_features': [],
                'feature_mapping': {'feature1': 0, 'feature2': 1}
            }
            
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            mock_manager.list_models.return_value = [
                {
                    'version': '1.0.0',
                    'path': '/tmp/models/1.0.0'
                }
            ]
            
            target_features = ['feature1', 'feature2']
            response = client.post("/api/v1/model-management/1.0.0/validate-compatibility", json=target_features)
            assert response.status_code == 200
            data = response.json()
            assert data['is_compatible'] is True 