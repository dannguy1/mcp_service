import pytest
import numpy as np
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock, mock_open
import joblib
import os

from app.components.model_manager import ModelManager
from app.models.config import ModelConfig, StorageConfig, IntegrationConfig

@pytest.fixture
def model_config():
    """Create a test ModelConfig."""
    config = ModelConfig()
    config.storage.directory = "/tmp/test_models"
    return config

@pytest.fixture
def model_manager(model_config):
    """Create a ModelManager instance for testing."""
    return ModelManager(config=model_config)

@pytest.fixture
def mock_model():
    """Create a mock model for testing."""
    model = MagicMock()
    model.predict.return_value = np.array([1, 0, 1])
    model.predict_proba.return_value = np.array([[0.2, 0.8], [0.9, 0.1], [0.3, 0.7]])
    model.score_samples.return_value = np.array([-0.5, -1.2, -0.8])
    return model

@pytest.fixture
def mock_metadata():
    """Create mock model metadata."""
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
                "accuracy": 0.95,
                "precision": 0.92,
                "recall": 0.88,
                "f1_score": 0.90,
                "roc_auc": 0.94
            }
        }
    }

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
                "recall": 0.82
            }
        }
    }

class TestEnhancedModelManager:
    """Test cases for the enhanced ModelManager."""
    
    def test_initialization(self, model_manager):
        """Test ModelManager initialization."""
        assert model_manager is not None
        assert model_manager.config is not None
        assert model_manager.current_model is None
        assert model_manager.model_loaded is False
        assert model_manager.models_directory.exists()
    
    @pytest.mark.asyncio
    async def test_import_model_from_training_service(self, model_manager, temp_model_dir, sample_model, sample_metadata):
        """Test importing a model from training service."""
        # Create a mock training service model
        model_path = Path(temp_model_dir) / "test_model"
        model_path.mkdir()
        
        # Save model and metadata
        import joblib
        joblib.dump(sample_model, model_path / "model.joblib")
        with open(model_path / "metadata.json", 'w') as f:
            json.dump(sample_metadata, f)
        
        # Test import
        result = await model_manager.import_model_from_training_service(str(model_path))
        
        assert result['status'] == 'imported'
        assert 'imported_version' in result
        assert 'local_path' in result
        assert result['original_path'] == str(model_path)
    
    @pytest.mark.asyncio
    async def test_validate_imported_model(self, model_manager, temp_model_dir, sample_model, sample_metadata):
        """Test model validation."""
        # Create a valid model
        model_path = Path(temp_model_dir) / "valid_model"
        model_path.mkdir()
        
        import joblib
        joblib.dump(sample_model, model_path / "model.joblib")
        with open(model_path / "metadata.json", 'w') as f:
            json.dump(sample_metadata, f)
        
        # Test validation
        result = await model_manager._validate_imported_model(str(model_path))
        
        assert result['is_valid'] is True
        assert len(result['errors']) == 0
        assert 'metadata' in result
    
    @pytest.mark.asyncio
    async def test_validate_imported_model_missing_files(self, model_manager, temp_model_dir):
        """Test model validation with missing files."""
        # Create an invalid model (missing files)
        model_path = Path(temp_model_dir) / "invalid_model"
        model_path.mkdir()
        
        # Test validation
        result = await model_manager._validate_imported_model(str(model_path))
        
        assert result['is_valid'] is False
        assert len(result['errors']) > 0
    
    @pytest.mark.asyncio
    async def test_load_model(self, model_manager, temp_model_dir, sample_model, sample_metadata):
        """Test model loading."""
        # Create model files
        model_path = Path(temp_model_dir) / "test_model"
        model_path.mkdir()
        
        import joblib
        joblib.dump(sample_model, model_path / "model.joblib")
        with open(model_path / "metadata.json", 'w') as f:
            json.dump(sample_metadata, f)
        
        # Test loading
        success = await model_manager.load_model(str(model_path / "model.joblib"))
        
        assert success is True
        assert model_manager.model_loaded is True
        assert model_manager.current_model is not None
        assert model_manager.current_model_version == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_load_model_version(self, model_manager, temp_model_dir, sample_model, sample_metadata):
        """Test loading a specific model version."""
        # Create model version directory
        version_dir = model_manager.models_directory / "test_version"
        version_dir.mkdir(parents=True, exist_ok=True)
        
        import joblib
        joblib.dump(sample_model, version_dir / "model.joblib")
        with open(version_dir / "metadata.json", 'w') as f:
            json.dump(sample_metadata, f)
        
        # Test loading version
        success = await model_manager.load_model_version("test_version")
        
        assert success is True
        assert model_manager.model_loaded is True
    
    @pytest.mark.asyncio
    async def test_deploy_model(self, model_manager, temp_model_dir, sample_model, sample_metadata):
        """Test model deployment."""
        # Create model version directory
        version_dir = model_manager.models_directory / "test_version"
        version_dir.mkdir(parents=True, exist_ok=True)
        
        import joblib
        joblib.dump(sample_model, version_dir / "model.joblib")
        with open(version_dir / "metadata.json", 'w') as f:
            json.dump(sample_metadata, f)
        
        # Test deployment
        success = await model_manager.deploy_model("test_version")
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_rollback_model(self, model_manager, temp_model_dir, sample_model, sample_metadata):
        """Test model rollback."""
        # Create two model versions
        for version in ["old_version", "new_version"]:
            version_dir = model_manager.models_directory / version
            version_dir.mkdir(parents=True, exist_ok=True)
            
            import joblib
            joblib.dump(sample_model, version_dir / "model.joblib")
            with open(version_dir / "metadata.json", 'w') as f:
                json.dump(sample_metadata, f)
        
        # Load new version first
        await model_manager.load_model_version("new_version")
        
        # Test rollback
        success = await model_manager.rollback_model("old_version")
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_list_models(self, model_manager, temp_model_dir, sample_model, sample_metadata):
        """Test listing models."""
        # Create a model
        version_dir = model_manager.models_directory / "test_version"
        version_dir.mkdir(parents=True, exist_ok=True)
        
        import joblib
        joblib.dump(sample_model, version_dir / "model.joblib")
        with open(version_dir / "metadata.json", 'w') as f:
            json.dump(sample_metadata, f)
        
        # Update registry
        await model_manager._update_model_registry(version_dir, 'available')
        
        # Test listing
        models = await model_manager.list_models()
        
        assert len(models) > 0
        assert any(m['version'] == 'test_version' for m in models)
    
    @pytest.mark.asyncio
    async def test_predict(self, model_manager, temp_model_dir, sample_model, sample_metadata):
        """Test model prediction."""
        # Create and load model
        model_path = Path(temp_model_dir) / "test_model"
        model_path.mkdir()
        
        import joblib
        joblib.dump(sample_model, model_path / "model.joblib")
        with open(model_path / "metadata.json", 'w') as f:
            json.dump(sample_metadata, f)
        
        await model_manager.load_model(str(model_path / "model.joblib"))
        
        # Test prediction
        features = np.array([[1.0, 2.0, 3.0]])
        predictions = await model_manager.predict(features)
        
        assert predictions is not None
        assert len(predictions) == 1
    
    @pytest.mark.asyncio
    async def test_predict_proba(self, model_manager, temp_model_dir, sample_model, sample_metadata):
        """Test model probability prediction."""
        # Create and load model
        model_path = Path(temp_model_dir) / "test_model"
        model_path.mkdir()
        
        import joblib
        joblib.dump(sample_model, model_path / "model.joblib")
        with open(model_path / "metadata.json", 'w') as f:
            json.dump(sample_metadata, f)
        
        await model_manager.load_model(str(model_path / "model.joblib"))
        
        # Test probability prediction
        features = np.array([[1.0, 2.0, 3.0]])
        probabilities = await model_manager.predict_proba(features)
        
        assert probabilities is not None
        assert len(probabilities) == 1
    
    def test_get_model_info(self, model_manager):
        """Test getting model information."""
        # Test when no model is loaded
        info = model_manager.get_model_info()
        assert info is None
        
        # Test when model is loaded
        model_manager.model_loaded = True
        model_manager.current_model_version = "1.0.0"
        model_manager.current_model_metadata = {"test": "data"}
        
        info = model_manager.get_model_info()
        assert info is not None
        assert info['version'] == "1.0.0"
    
    def test_is_model_loaded(self, model_manager):
        """Test model loaded status check."""
        assert model_manager.is_model_loaded() is False
        
        model_manager.model_loaded = True
        assert model_manager.is_model_loaded() is True

    @pytest.mark.asyncio
    async def test_load_model_success(self, model_manager, mock_model, mock_metadata):
        """Test successful model loading."""
        with patch('joblib.load') as mock_load, \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_metadata))), \
             patch('pathlib.Path.exists', return_value=True):
            
            mock_load.return_value = mock_model
            
            # Test loading model
            result = await model_manager.load_model("/tmp/test_model.joblib")
            
            assert result is True
            assert model_manager.model_loaded is True
            assert model_manager.current_model is mock_model
            assert model_manager.current_model_version == "1.0.0"
            assert model_manager.feature_names == ["feature1", "feature2", "feature3"]

    @pytest.mark.asyncio
    async def test_load_model_file_not_found(self, model_manager):
        """Test model loading with non-existent file."""
        with patch('pathlib.Path.exists', return_value=False):
            result = await model_manager.load_model("/tmp/nonexistent.joblib")
            assert result is False
            assert model_manager.model_loaded is False

    @pytest.mark.asyncio
    async def test_load_model_version_success(self, model_manager, mock_model, mock_metadata):
        """Test loading model by version."""
        with patch('joblib.load') as mock_load, \
             patch('builtins.open', mock_open(read_data=json.dumps(mock_metadata))), \
             patch('pathlib.Path.exists', return_value=True), \
             patch.object(model_manager, 'list_models') as mock_list_models:
            
            mock_load.return_value = mock_model
            mock_list_models.return_value = [
                {
                    'version': '1.0.0',
                    'path': '/tmp/models/1.0.0'
                }
            ]
            
            result = await model_manager.load_model_version('1.0.0')
            assert result is True
            assert model_manager.model_loaded is True

    @pytest.mark.asyncio
    async def test_load_model_version_not_found(self, model_manager):
        """Test loading non-existent model version."""
        with patch.object(model_manager, 'list_models') as mock_list_models:
            mock_list_models.return_value = []
            
            result = await model_manager.load_model_version('nonexistent')
            assert result is False

    @pytest.mark.asyncio
    async def test_predict_success(self, model_manager, mock_model):
        """Test successful prediction."""
        model_manager.current_model = mock_model
        model_manager.model_loaded = True
        
        features = np.array([[1, 2, 3], [4, 5, 6]])
        result = await model_manager.predict(features)
        
        assert result is not None
        mock_model.predict.assert_called_once()

    @pytest.mark.asyncio
    async def test_predict_no_model_loaded(self, model_manager):
        """Test prediction without loaded model."""
        features = np.array([[1, 2, 3]])
        
        with pytest.raises(RuntimeError, match="No model loaded"):
            await model_manager.predict(features)

    @pytest.mark.asyncio
    async def test_predict_proba_success(self, model_manager, mock_model):
        """Test successful probability prediction."""
        model_manager.current_model = mock_model
        model_manager.model_loaded = True
        
        features = np.array([[1, 2, 3]])
        result = await model_manager.predict_proba(features)
        
        assert result is not None
        mock_model.predict_proba.assert_called_once()

    @pytest.mark.asyncio
    async def test_predict_proba_with_score_samples(self, model_manager):
        """Test probability prediction with score_samples method."""
        model = MagicMock()
        model.predict_proba = None
        model.score_samples.return_value = np.array([-0.5, -1.2])
        
        model_manager.current_model = model
        model_manager.model_loaded = True
        
        features = np.array([[1, 2, 3], [4, 5, 6]])
        result = await model_manager.predict_proba(features)
        
        assert result is not None
        assert result.shape == (2, 1)

    @pytest.mark.asyncio
    async def test_predict_proba_no_support(self, model_manager):
        """Test probability prediction with unsupported model."""
        model = MagicMock()
        model.predict_proba = None
        model.score_samples = None
        
        model_manager.current_model = model
        model_manager.model_loaded = True
        
        features = np.array([[1, 2, 3]])
        
        with pytest.raises(RuntimeError, match="Model does not support probability predictions"):
            await model_manager.predict_proba(features)

    @pytest.mark.asyncio
    async def test_list_models_empty(self, model_manager):
        """Test listing models when none exist."""
        with patch('pathlib.Path.exists', return_value=False):
            result = await model_manager.list_models()
            assert result == []

    @pytest.mark.asyncio
    async def test_list_models_with_data(self, model_manager, mock_metadata):
        """Test listing models with existing data."""
        registry_data = {
            "1.0.0": {
                "path": "/tmp/models/1.0.0",
                "created_at": "2024-01-01T00:00:00",
                "status": "available",
                "last_updated": "2024-01-01T00:00:00"
            }
        }
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(registry_data))), \
             patch('pathlib.Path.exists', side_effect=lambda x: str(x).endswith('metadata.json')):
            
            result = await model_manager.list_models()
            assert len(result) == 1
            assert result[0]['version'] == '1.0.0'

    def test_get_model_info_no_model(self, model_manager):
        """Test getting model info when no model is loaded."""
        result = model_manager.get_model_info()
        assert result is None

    def test_get_model_info_with_model(self, model_manager, mock_model):
        """Test getting model info when model is loaded."""
        model_manager.current_model = mock_model
        model_manager.model_loaded = True
        model_manager.current_model_version = "1.0.0"
        model_manager.feature_names = ["feature1", "feature2"]
        model_manager.current_model_metadata = {"test": "data"}
        
        result = model_manager.get_model_info()
        
        assert result is not None
        assert result['version'] == "1.0.0"
        assert result['model_type'] == "MagicMock"
        assert result['feature_names'] == ["feature1", "feature2"]

    @pytest.mark.asyncio
    async def test_deploy_model_success(self, model_manager):
        """Test successful model deployment."""
        with patch.object(model_manager, 'load_model_version', return_value=True), \
             patch.object(model_manager, '_update_deployment_status'), \
             patch.object(model_manager, '_update_model_registry'):
            
            result = await model_manager.deploy_model("1.0.0")
            assert result is True

    @pytest.mark.asyncio
    async def test_deploy_model_failure(self, model_manager):
        """Test model deployment failure."""
        with patch.object(model_manager, 'load_model_version', return_value=False):
            result = await model_manager.deploy_model("1.0.0")
            assert result is False

    @pytest.mark.asyncio
    async def test_rollback_model_success(self, model_manager):
        """Test successful model rollback."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch.object(model_manager, 'load_model_version', return_value=True), \
             patch.object(model_manager, '_update_deployment_status'):
            
            result = await model_manager.rollback_model("1.0.0")
            assert result is True

    @pytest.mark.asyncio
    async def test_rollback_model_not_found(self, model_manager):
        """Test rollback with non-existent model."""
        with patch('pathlib.Path.exists', return_value=False):
            result = await model_manager.rollback_model("nonexistent")
            assert result is False

    @pytest.mark.asyncio
    async def test_import_model_from_training_service(self, model_manager):
        """Test importing model from training service."""
        with patch.object(model_manager, '_validate_imported_model', return_value={'is_valid': True}), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('shutil.copytree'), \
             patch.object(model_manager, '_update_import_metadata'), \
             patch.object(model_manager, '_update_model_registry'):
            
            result = await model_manager.import_model_from_training_service("/tmp/training_model")
            
            assert result is not None
            assert 'imported_version' in result
            assert 'local_path' in result
            assert result['status'] == 'imported'

    @pytest.mark.asyncio
    async def test_import_model_validation_failure(self, model_manager):
        """Test model import with validation failure."""
        with patch.object(model_manager, '_validate_imported_model', return_value={'is_valid': False, 'errors': ['test error']}):
            
            with pytest.raises(ValueError, match="Model validation failed"):
                await model_manager.import_model_from_training_service("/tmp/training_model")

    @pytest.mark.asyncio
    async def test_scaler_integration(self, model_manager, mock_model):
        """Test model prediction with scaler."""
        scaler = MagicMock()
        scaler.transform.return_value = np.array([[1, 2, 3]])
        
        model_manager.current_model = mock_model
        model_manager.current_scaler = scaler
        model_manager.model_loaded = True
        
        features = np.array([[1, 2, 3]])
        
        # Test that scaler is used in prediction
        result = await model_manager.predict(features)
        
        scaler.transform.assert_called_once()
        mock_model.predict.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_in_predict(self, model_manager, mock_model):
        """Test error handling in prediction."""
        model_manager.current_model = mock_model
        model_manager.model_loaded = True
        
        mock_model.predict.side_effect = Exception("Prediction error")
        
        features = np.array([[1, 2, 3]])
        
        with pytest.raises(Exception, match="Prediction error"):
            await model_manager.predict(features)

    @pytest.mark.asyncio
    async def test_error_handling_in_predict_proba(self, model_manager, mock_model):
        """Test error handling in probability prediction."""
        model_manager.current_model = mock_model
        model_manager.model_loaded = True
        
        mock_model.predict_proba.side_effect = Exception("Probability error")
        
        features = np.array([[1, 2, 3]])
        
        with pytest.raises(Exception, match="Probability error"):
            await model_manager.predict_proba(features) 