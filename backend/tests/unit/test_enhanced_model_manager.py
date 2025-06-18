import pytest
import numpy as np
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

from app.components.model_manager import ModelManager
from app.models.config import ModelConfig, StorageConfig, IntegrationConfig

@pytest.fixture
def model_config():
    """Create a test ModelConfig."""
    return ModelConfig(
        storage=StorageConfig(directory="test_models"),
        integration=IntegrationConfig(training_service_path="/tmp/test_training")
    )

@pytest.fixture
def model_manager(model_config):
    """Create a ModelManager instance for testing."""
    return ModelManager(config=model_config)

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