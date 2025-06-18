# Model Management and Integration Enhancement Plan

## Overview

This document outlines the implementation plan to enhance the model management and integration system for the MCP service, addressing the integration between the standalone training service and the main MCP service. The goal is to create a robust, production-ready model management pipeline that seamlessly integrates trained models from the standalone training service into the main MCP service for inference.

## Current Architecture

### ✅ Standalone Training Service (Independent)
- **Location**: `/home/dannguyen/WNC/mcp_training`
- **Purpose**: Train anomaly detection models from exported data
- **Output**: Trained models with metadata in joblib format
- **Interface**: CLI and REST API for training operations

### ✅ Main MCP Service (Inference)
- **Location**: `/home/dannguyen/WNC/mcp_service`
- **Purpose**: Load trained models and perform real-time inference
- **Input**: Trained models from standalone training service
- **Interface**: ModelManager, agents, and UI for model management

### 🔄 Integration Points
- **Model Transfer**: Trained models moved from training service to main service
- **Model Validation**: Validation of model compatibility and quality
- **Model Deployment**: Deployment of validated models for inference
- **Model Management**: UI and API for model lifecycle management

## Current State Analysis

### ✅ Implemented Components
1. **Basic Model Loading**: `ModelLoader` class for loading saved models
2. **Model Manager**: Basic model management with current model tracking
3. **Feature Extraction**: Basic WiFi feature extraction for inference
4. **Agent Integration**: Basic integration with WiFi agent
5. **Model Configuration**: Basic model configuration support
6. **Export System**: Data export functionality for training service consumption

### ❌ Missing or Incomplete Components
1. **Enhanced Model Management**: Advanced model loading, validation, and deployment
2. **Model Transfer Integration**: Seamless integration with standalone training service
3. **Model Quality Validation**: Comprehensive model validation and quality checks
4. **Advanced Model Versioning**: Robust versioning with metadata management
5. **UI Model Management**: Enhanced frontend interface for model management
6. **Model Performance Tracking**: Comprehensive performance monitoring
7. **Model Fallback Mechanisms**: Fallback for model failures
8. **Model Hot-Swapping**: Dynamic model switching without restart

## Implementation Phases

### Phase 1: Enhanced Model Management (Priority: Critical)

#### 1.1 Enhanced Model Manager
```python
# backend/app/components/model_manager.py - Enhanced model management
import logging
import joblib
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import numpy as np
from sklearn.preprocessing import StandardScaler

from ..models.config import ModelConfig
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ModelManager:
    """Enhanced model manager for loading and managing trained models."""
    
    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()
        self.current_model = None
        self.current_scaler = None
        self.current_model_version = None
        self.current_model_metadata = None
        self.feature_names = []
        self.model_loaded = False
        self.models_directory = Path(self.config.storage.directory)
        self.model_registry_file = self.models_directory / "model_registry.json"
        
    async def import_model_from_training_service(self, model_path: str, 
                                               validate: bool = True) -> Dict[str, Any]:
        """Import a model from the standalone training service."""
        try:
            logger.info(f"Importing model from training service: {model_path}")
            
            # Validate model structure
            if validate:
                validation_result = await self._validate_imported_model(model_path)
                if not validation_result['is_valid']:
                    raise ValueError(f"Model validation failed: {validation_result['errors']}")
            
            # Copy model to local storage
            model_dir = Path(model_path)
            if not model_dir.exists():
                raise ValueError(f"Model directory not found: {model_path}")
            
            # Generate import version
            import_version = datetime.now().strftime('%Y%m%d_%H%M%S')
            local_model_dir = self.models_directory / f"imported_{import_version}"
            
            # Copy model files
            shutil.copytree(model_dir, local_model_dir)
            
            # Update metadata with import information
            await self._update_import_metadata(local_model_dir, model_path)
            
            # Update model registry
            await self._update_model_registry(local_model_dir, 'imported')
            
            logger.info(f"Model imported successfully: {local_model_dir}")
            return {
                'imported_version': import_version,
                'local_path': str(local_model_dir),
                'original_path': model_path,
                'status': 'imported'
            }
            
        except Exception as e:
            logger.error(f"Error importing model: {e}")
            raise
    
    async def _validate_imported_model(self, model_path: str) -> Dict[str, Any]:
        """Validate an imported model for compatibility."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'metadata': {}
        }
        
        try:
            model_dir = Path(model_path)
            
            # Check required files
            required_files = ['model.joblib', 'metadata.json']
            for file in required_files:
                if not (model_dir / file).exists():
                    validation_result['is_valid'] = False
                    validation_result['errors'].append(f"Missing required file: {file}")
            
            # Load and validate metadata
            if (model_dir / 'metadata.json').exists():
                with open(model_dir / 'metadata.json', 'r') as f:
                    metadata = json.load(f)
                
                validation_result['metadata'] = metadata
                
                # Check metadata structure
                required_metadata_fields = ['model_info', 'training_info', 'evaluation_info']
                for field in required_metadata_fields:
                    if field not in metadata:
                        validation_result['errors'].append(f"Missing metadata field: {field}")
                
                # Check model type compatibility
                model_type = metadata.get('model_info', {}).get('model_type', '')
                if model_type not in ['IsolationForest', 'LocalOutlierFactor']:
                    validation_result['warnings'].append(f"Unknown model type: {model_type}")
                
                # Check evaluation metrics
                evaluation_metrics = metadata.get('evaluation_info', {}).get('basic_metrics', {})
                if evaluation_metrics:
                    # Check if metrics meet minimum thresholds
                    if evaluation_metrics.get('f1_score', 0) < 0.5:
                        validation_result['warnings'].append("Low F1 score detected")
                    
                    if evaluation_metrics.get('roc_auc', 0) < 0.6:
                        validation_result['warnings'].append("Low ROC AUC detected")
            
            # Test model loading
            if (model_dir / 'model.joblib').exists():
                try:
                    test_model = joblib.load(model_dir / 'model.joblib')
                    if not hasattr(test_model, 'predict'):
                        validation_result['is_valid'] = False
                        validation_result['errors'].append("Model does not have predict method")
                except Exception as e:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append(f"Model loading failed: {str(e)}")
            
            # Check feature compatibility
            if 'training_info' in metadata:
                feature_names = metadata['training_info'].get('feature_names', [])
                if not feature_names:
                    validation_result['warnings'].append("No feature names found in metadata")
                else:
                    validation_result['metadata']['feature_count'] = len(feature_names)
            
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    async def _update_import_metadata(self, model_dir: Path, original_path: str):
        """Update metadata with import information."""
        metadata_path = model_dir / 'metadata.json'
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Add import information
            metadata['import_info'] = {
                'imported_at': datetime.now().isoformat(),
                'original_path': original_path,
                'imported_by': 'system'
            }
            
            # Update deployment status
            metadata['deployment_info']['status'] = 'available'
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
    
    async def load_model(self, model_path: str, scaler_path: Optional[str] = None) -> bool:
        """Load a trained model from file paths."""
        try:
            logger.info(f"Loading model from: {model_path}")
            
            # Validate model file
            if not Path(model_path).exists():
                logger.error(f"Model file not found: {model_path}")
                return False
            
            # Load model
            self.current_model = joblib.load(model_path)
            logger.info(f"Model loaded successfully: {type(self.current_model).__name__}")
            
            # Load scaler if provided
            if scaler_path and Path(scaler_path).exists():
                self.current_scaler = joblib.load(scaler_path)
                logger.info("Scaler loaded successfully")
            else:
                logger.warning("No scaler provided, using unscaled features")
                self.current_scaler = None
            
            # Load metadata
            metadata_path = Path(model_path).parent / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    self.current_model_metadata = json.load(f)
                self.current_model_version = self.current_model_metadata['model_info']['version']
                logger.info(f"Model metadata loaded: {self.current_model_version}")
            
            # Load feature names
            if self.current_model_metadata and 'training_info' in self.current_model_metadata:
                self.feature_names = self.current_model_metadata['training_info'].get('feature_names', [])
            
            self.model_loaded = True
            logger.info("Model loading completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.model_loaded = False
            return False
    
    async def deploy_model(self, version: str) -> bool:
        """Deploy a specific model version."""
        try:
            # Load the model to validate it
            if not await self.load_model_version(version):
                return False
            
            # Update deployment status in metadata
            await self._update_deployment_status(version, 'deployed')
            
            # Update model registry
            await self._update_model_registry(Path(self.models_directory) / version, 'deployed')
            
            logger.info(f"Model version {version} deployed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deploying model version {version}: {e}")
            return False
    
    async def rollback_model(self, version: str) -> bool:
        """Rollback to a previous model version."""
        try:
            # Check if version exists
            model_dir = self.models_directory / version
            if not model_dir.exists():
                logger.error(f"Model version not found: {version}")
                return False
            
            # Load the rollback model
            if not await self.load_model_version(version):
                return False
            
            # Update deployment status
            await self._update_deployment_status(version, 'deployed')
            
            # Update current model status to available
            if self.current_model_version:
                await self._update_deployment_status(self.current_model_version, 'available')
            
            logger.info(f"Rolled back to model version {version}")
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back to version {version}: {e}")
            return False
    
    async def _update_model_registry(self, model_dir: Path, status: str):
        """Update model registry with new model."""
        registry = {}
        if self.model_registry_file.exists():
            with open(self.model_registry_file, 'r') as f:
                registry = json.load(f)
        
        # Add new model to registry
        model_version = model_dir.name
        registry[model_version] = {
            'path': str(model_dir),
            'created_at': datetime.now().isoformat(),
            'status': status,
            'last_updated': datetime.now().isoformat()
        }
        
        # Save updated registry
        with open(self.model_registry_file, 'w') as f:
            json.dump(registry, f, indent=2)
```

#### 1.2 Model Transfer Service
```python
# backend/app/services/model_transfer_service.py - New service for model transfer
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import shutil

from ..components.model_manager import ModelManager
from ..models.config import ModelConfig

logger = logging.getLogger(__name__)

class ModelTransferService:
    """Service for transferring models from training service to main service."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.model_manager = ModelManager(config)
        self.training_service_path = Path(config.integration.training_service_path)
        self.transfer_history_file = Path(config.storage.directory) / "transfer_history.json"
    
    async def scan_training_service_models(self) -> List[Dict[str, Any]]:
        """Scan for available models in the training service."""
        try:
            models = []
            training_models_dir = self.training_service_path / "models"
            
            if not training_models_dir.exists():
                logger.warning("Training service models directory not found")
                return models
            
            for model_dir in training_models_dir.iterdir():
                if model_dir.is_dir():
                    metadata_path = model_dir / "metadata.json"
                    if metadata_path.exists():
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        
                        models.append({
                            'version': metadata['model_info']['version'],
                            'path': str(model_dir),
                            'created_at': metadata['model_info']['created_at'],
                            'model_type': metadata['model_info']['model_type'],
                            'training_samples': metadata['training_info']['training_samples'],
                            'evaluation_metrics': metadata['evaluation_info']['basic_metrics'],
                            'imported': await self._is_model_imported(metadata['model_info']['version'])
                        })
            
            # Sort by creation date (newest first)
            models.sort(key=lambda x: x['created_at'], reverse=True)
            return models
            
        except Exception as e:
            logger.error(f"Error scanning training service models: {e}")
            return []
    
    async def import_latest_model(self, validate: bool = True) -> Dict[str, Any]:
        """Import the latest model from training service."""
        try:
            models = await self.scan_training_service_models()
            if not models:
                raise ValueError("No models found in training service")
            
            # Find the latest non-imported model
            for model in models:
                if not model['imported']:
                    return await self.import_model(model['path'], validate)
            
            raise ValueError("No new models to import")
            
        except Exception as e:
            logger.error(f"Error importing latest model: {e}")
            raise
    
    async def import_model(self, model_path: str, validate: bool = True) -> Dict[str, Any]:
        """Import a specific model from training service."""
        try:
            logger.info(f"Importing model: {model_path}")
            
            # Import model using model manager
            result = await self.model_manager.import_model_from_training_service(
                model_path, validate
            )
            
            # Record transfer history
            await self._record_transfer_history(result)
            
            logger.info(f"Model imported successfully: {result['imported_version']}")
            return result
            
        except Exception as e:
            logger.error(f"Error importing model: {e}")
            raise
    
    async def _is_model_imported(self, version: str) -> bool:
        """Check if a model version has already been imported."""
        models = await self.model_manager.list_models()
        return any(model['version'] == version for model in models)
    
    async def _record_transfer_history(self, transfer_result: Dict[str, Any]):
        """Record model transfer history."""
        history = []
        if self.transfer_history_file.exists():
            with open(self.transfer_history_file, 'r') as f:
                history = json.load(f)
        
        history.append({
            'transfer_id': transfer_result['imported_version'],
            'original_path': transfer_result['original_path'],
            'local_path': transfer_result['local_path'],
            'transferred_at': datetime.now().isoformat(),
            'status': transfer_result['status']
        })
        
        with open(self.transfer_history_file, 'w') as f:
            json.dump(history, f, indent=2)
```

### Phase 2: Enhanced Model Configuration (Priority: High)

#### 2.1 Update ModelConfig Structure
```python
# backend/app/models/config.py - Enhanced configuration
class ModelConfig(BaseModel):
    """Enhanced configuration for model management and inference."""
    version: str = Field(default="2.0.0", description="Configuration version")
    
    # Model parameters
    model: ModelParameters = Field(default_factory=ModelParameters)
    
    # Storage configuration
    storage: StorageConfig = Field(default_factory=StorageConfig)
    
    # Integration configuration
    integration: IntegrationConfig = Field(default_factory=IntegrationConfig)
    
    # Monitoring configuration
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    
    # Logging configuration
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

class IntegrationConfig(BaseModel):
    """Integration configuration for training service."""
    training_service_path: str = Field(default="/home/dannguyen/WNC/mcp_training", 
                                      description="Path to training service")
    auto_import: bool = Field(default=False, description="Auto-import new models")
    import_interval: int = Field(default=3600, description="Import check interval (seconds)")
    validate_imports: bool = Field(default=True, description="Validate imported models")

class MonitoringConfig(BaseModel):
    """Monitoring configuration for model inference."""
    enable_drift_detection: bool = Field(default=True, description="Enable drift detection")
    drift_threshold: float = Field(default=0.1, description="Drift detection threshold")
    performance_tracking: bool = Field(default=True, description="Enable performance tracking")
    resource_monitoring: bool = Field(default=True, description="Enable resource monitoring")
    model_health_checks: bool = Field(default=True, description="Enable model health checks")
```

#### 2.2 Enhanced Configuration YAML
```yaml
# backend/app/config/model_config.yaml - Updated structure
version: '2.0.0'

model:
  type: isolation_forest
  anomaly_threshold: 0.5
  confidence_threshold: 0.8
  max_features: 1.0

storage:
  directory: models
  backup_enabled: true
  compression: true
  retention_days: 30

integration:
  training_service_path: /home/dannguyen/WNC/mcp_training
  auto_import: false
  import_interval: 3600
  validate_imports: true

monitoring:
  enable_drift_detection: true
  drift_threshold: 0.1
  performance_tracking: true
  resource_monitoring: true
  model_health_checks: true
  alerting:
    enabled: true
    email_notifications: false
    slack_notifications: false

logging:
  level: INFO
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  file: logs/model_inference.log
  rotation:
    max_size: 100MB
    backup_count: 10
```

### Phase 3: Enhanced Model Validation and Quality Assurance (Priority: High)

#### 3.1 Model Quality Validator
```python
# backend/app/services/model_validator.py - New model validation service
import logging
import numpy as np
from typing import Dict, Any, List, Optional
from pathlib import Path
import joblib

from ..models.config import ModelConfig

logger = logging.getLogger(__name__)

class ModelValidator:
    """Comprehensive model validation and quality assurance."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
    
    async def validate_model_quality(self, model_path: str) -> Dict[str, Any]:
        """Validate model quality and performance."""
        try:
            validation_result = {
                'is_valid': True,
                'score': 0.0,
                'errors': [],
                'warnings': [],
                'recommendations': []
            }
            
            # Load model and metadata
            model_dir = Path(model_path)
            model = joblib.load(model_dir / 'model.joblib')
            
            with open(model_dir / 'metadata.json', 'r') as f:
                metadata = json.load(f)
            
            # Check model structure
            structure_check = self._validate_model_structure(model)
            validation_result.update(structure_check)
            
            # Check performance metrics
            performance_check = self._validate_performance_metrics(metadata)
            validation_result.update(performance_check)
            
            # Check feature compatibility
            feature_check = self._validate_feature_compatibility(metadata)
            validation_result.update(feature_check)
            
            # Check model age
            age_check = self._validate_model_age(metadata)
            validation_result.update(age_check)
            
            # Calculate overall score
            validation_result['score'] = self._calculate_quality_score(validation_result)
            
            # Determine validity
            if validation_result['score'] < 0.6:
                validation_result['is_valid'] = False
                validation_result['errors'].append("Model quality score below threshold")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating model quality: {e}")
            return {
                'is_valid': False,
                'score': 0.0,
                'errors': [f"Validation failed: {str(e)}"],
                'warnings': [],
                'recommendations': []
            }
    
    def _validate_model_structure(self, model: Any) -> Dict[str, Any]:
        """Validate model structure and methods."""
        errors = []
        warnings = []
        
        # Check required methods
        required_methods = ['predict', 'score_samples']
        for method in required_methods:
            if not hasattr(model, method):
                errors.append(f"Model missing required method: {method}")
        
        # Check model parameters
        if hasattr(model, 'n_estimators'):
            if model.n_estimators < 50:
                warnings.append("Low number of estimators may affect performance")
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_performance_metrics(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate model performance metrics."""
        errors = []
        warnings = []
        recommendations = []
        
        evaluation_metrics = metadata.get('evaluation_info', {}).get('basic_metrics', {})
        
        # Check F1 score
        f1_score = evaluation_metrics.get('f1_score', 0)
        if f1_score < 0.5:
            errors.append("F1 score below acceptable threshold (0.5)")
        elif f1_score < 0.7:
            warnings.append("F1 score below recommended threshold (0.7)")
            recommendations.append("Consider retraining with more data or different parameters")
        
        # Check ROC AUC
        roc_auc = evaluation_metrics.get('roc_auc', 0)
        if roc_auc < 0.6:
            errors.append("ROC AUC below acceptable threshold (0.6)")
        elif roc_auc < 0.8:
            warnings.append("ROC AUC below recommended threshold (0.8)")
            recommendations.append("Consider feature engineering or model tuning")
        
        # Check precision and recall
        precision = evaluation_metrics.get('precision', 0)
        recall = evaluation_metrics.get('recall', 0)
        
        if precision < 0.5:
            warnings.append("Low precision may result in many false positives")
        if recall < 0.5:
            warnings.append("Low recall may miss many anomalies")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'recommendations': recommendations
        }
    
    def _validate_feature_compatibility(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate feature compatibility with current system."""
        warnings = []
        
        training_info = metadata.get('training_info', {})
        feature_names = training_info.get('feature_names', [])
        
        # Check feature count
        if len(feature_names) < 5:
            warnings.append("Low feature count may limit model performance")
        
        # Check for expected features
        expected_features = ['hour_of_day', 'day_of_week', 'message_length']
        missing_features = [f for f in expected_features if f not in feature_names]
        if missing_features:
            warnings.append(f"Missing expected features: {missing_features}")
        
        return {
            'warnings': warnings
        }
    
    def _validate_model_age(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate model age and freshness."""
        warnings = []
        
        created_at = metadata.get('model_info', {}).get('created_at')
        if created_at:
            from datetime import datetime, timezone
            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            age_days = (datetime.now(timezone.utc) - created_date).days
            
            if age_days > 30:
                warnings.append(f"Model is {age_days} days old, consider retraining")
            elif age_days > 7:
                warnings.append(f"Model is {age_days} days old, monitor for drift")
        
        return {
            'warnings': warnings
        }
    
    def _calculate_quality_score(self, validation_result: Dict[str, Any]) -> float:
        """Calculate overall model quality score."""
        score = 1.0
        
        # Deduct for errors
        score -= len(validation_result['errors']) * 0.2
        
        # Deduct for warnings
        score -= len(validation_result['warnings']) * 0.05
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
```

### Phase 4: Enhanced UI Model Management (Priority: Medium)

#### 4.1 Model Management API
```python
# backend/app/api/endpoints/model_management.py - Enhanced model management API
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
import logging

from ...services.model_transfer_service import ModelTransferService
from ...services.model_validator import ModelValidator
from ...components.model_manager import ModelManager
from ...models.config import ModelConfig

router = APIRouter(prefix="/api/v1/model-management", tags=["model-management"])
logger = logging.getLogger(__name__)

@router.get("/training-service/models")
async def get_training_service_models() -> List[Dict[str, Any]]:
    """Get available models from training service."""
    try:
        config = ModelConfig()
        transfer_service = ModelTransferService(config)
        models = await transfer_service.scan_training_service_models()
        return models
    except Exception as e:
        logger.error(f"Error getting training service models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/{model_path:path}")
async def import_model_from_training_service(model_path: str, 
                                           validate: bool = True) -> Dict[str, Any]:
    """Import a model from training service."""
    try:
        config = ModelConfig()
        transfer_service = ModelTransferService(config)
        result = await transfer_service.import_model(model_path, validate)
        return result
    except Exception as e:
        logger.error(f"Error importing model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import-latest")
async def import_latest_model(validate: bool = True) -> Dict[str, Any]:
    """Import the latest model from training service."""
    try:
        config = ModelConfig()
        transfer_service = ModelTransferService(config)
        result = await transfer_service.import_latest_model(validate)
        return result
    except Exception as e:
        logger.error(f"Error importing latest model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{version}/validate")
async def validate_model(version: str) -> Dict[str, Any]:
    """Validate a specific model version."""
    try:
        config = ModelConfig()
        validator = ModelValidator(config)
        model_manager = ModelManager(config)
        
        # Find model path
        models = await model_manager.list_models()
        model_info = next((m for m in models if m['version'] == version), None)
        
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        validation_result = await validator.validate_model_quality(model_info['model_path'])
        return validation_result
        
    except Exception as e:
        logger.error(f"Error validating model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{version}/deploy")
async def deploy_model(version: str) -> Dict[str, Any]:
    """Deploy a specific model version."""
    try:
        model_manager = ModelManager()
        success = await model_manager.deploy_model(version)
        
        if success:
            return {
                "version": version,
                "status": "deployed",
                "deployed_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to deploy model")
            
    except Exception as e:
        logger.error(f"Error deploying model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{version}/rollback")
async def rollback_model(version: str) -> Dict[str, Any]:
    """Rollback to a specific model version."""
    try:
        model_manager = ModelManager()
        success = await model_manager.rollback_model(version)
        
        if success:
            return {
                "version": version,
                "status": "rolled_back",
                "rolled_back_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to rollback model")
            
    except Exception as e:
        logger.error(f"Error rolling back model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transfer-history")
async def get_transfer_history() -> List[Dict[str, Any]]:
    """Get model transfer history."""
    try:
        config = ModelConfig()
        transfer_service = ModelTransferService(config)
        
        if transfer_service.transfer_history_file.exists():
            with open(transfer_service.transfer_history_file, 'r') as f:
                history = json.load(f)
            return history
        else:
            return []
            
    except Exception as e:
        logger.error(f"Error getting transfer history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Phase 5: Model Performance Monitoring (Priority: Medium)

#### 5.1 Model Performance Monitor
```python
# backend/app/services/model_performance_monitor.py - New performance monitoring
import logging
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

from ..models.config import ModelConfig

logger = logging.getLogger(__name__)

class ModelPerformanceMonitor:
    """Monitor model performance and detect drift."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.performance_file = Path(config.storage.directory) / "performance_metrics.json"
        self.drift_threshold = config.monitoring.drift_threshold
    
    async def record_inference_metrics(self, model_version: str, 
                                     inference_time: float,
                                     anomaly_score: float,
                                     is_anomaly: bool) -> None:
        """Record inference performance metrics."""
        try:
            metrics = self._load_performance_metrics()
            
            timestamp = datetime.now().isoformat()
            
            if model_version not in metrics:
                metrics[model_version] = {
                    'inference_times': [],
                    'anomaly_scores': [],
                    'anomaly_counts': [],
                    'total_inferences': 0,
                    'last_updated': timestamp
                }
            
            # Record metrics
            metrics[model_version]['inference_times'].append(inference_time)
            metrics[model_version]['anomaly_scores'].append(anomaly_score)
            metrics[model_version]['anomaly_counts'].append(1 if is_anomaly else 0)
            metrics[model_version]['total_inferences'] += 1
            metrics[model_version]['last_updated'] = timestamp
            
            # Keep only recent metrics (last 1000 inferences)
            max_metrics = 1000
            for key in ['inference_times', 'anomaly_scores', 'anomaly_counts']:
                if len(metrics[model_version][key]) > max_metrics:
                    metrics[model_version][key] = metrics[model_version][key][-max_metrics:]
            
            self._save_performance_metrics(metrics)
            
        except Exception as e:
            logger.error(f"Error recording inference metrics: {e}")
    
    async def check_model_drift(self, model_version: str) -> Dict[str, Any]:
        """Check for model drift."""
        try:
            metrics = self._load_performance_metrics()
            
            if model_version not in metrics:
                return {
                    'drift_detected': False,
                    'confidence': 0.0,
                    'metrics': {}
                }
            
            model_metrics = metrics[model_version]
            
            # Calculate drift indicators
            drift_indicators = {
                'anomaly_rate_change': self._calculate_anomaly_rate_change(model_metrics),
                'score_distribution_change': self._calculate_score_distribution_change(model_metrics),
                'inference_time_change': self._calculate_inference_time_change(model_metrics)
            }
            
            # Determine overall drift
            drift_score = np.mean(list(drift_indicators.values()))
            drift_detected = drift_score > self.drift_threshold
            
            return {
                'drift_detected': drift_detected,
                'drift_score': drift_score,
                'confidence': min(drift_score, 1.0),
                'indicators': drift_indicators,
                'threshold': self.drift_threshold
            }
            
        except Exception as e:
            logger.error(f"Error checking model drift: {e}")
            return {
                'drift_detected': False,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _calculate_anomaly_rate_change(self, metrics: Dict[str, Any]) -> float:
        """Calculate change in anomaly rate."""
        anomaly_counts = metrics.get('anomaly_counts', [])
        if len(anomaly_counts) < 20:
            return 0.0
        
        # Compare recent vs older anomaly rates
        recent_rate = np.mean(anomaly_counts[-10:])
        older_rate = np.mean(anomaly_counts[-20:-10])
        
        if older_rate == 0:
            return 0.0
        
        return abs(recent_rate - older_rate) / older_rate
    
    def _calculate_score_distribution_change(self, metrics: Dict[str, Any]) -> float:
        """Calculate change in anomaly score distribution."""
        scores = metrics.get('anomaly_scores', [])
        if len(scores) < 20:
            return 0.0
        
        # Compare recent vs older score distributions
        recent_scores = scores[-10:]
        older_scores = scores[-20:-10]
        
        recent_mean = np.mean(recent_scores)
        older_mean = np.mean(older_scores)
        
        if older_mean == 0:
            return 0.0
        
        return abs(recent_mean - older_mean) / older_mean
    
    def _calculate_inference_time_change(self, metrics: Dict[str, Any]) -> float:
        """Calculate change in inference time."""
        times = metrics.get('inference_times', [])
        if len(times) < 20:
            return 0.0
        
        # Compare recent vs older inference times
        recent_times = times[-10:]
        older_times = times[-20:-10]
        
        recent_mean = np.mean(recent_times)
        older_mean = np.mean(older_times)
        
        if older_mean == 0:
            return 0.0
        
        return abs(recent_mean - older_mean) / older_mean
    
    def _load_performance_metrics(self) -> Dict[str, Any]:
        """Load performance metrics from file."""
        if self.performance_file.exists():
            with open(self.performance_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_performance_metrics(self, metrics: Dict[str, Any]) -> None:
        """Save performance metrics to file."""
        with open(self.performance_file, 'w') as f:
            json.dump(metrics, f, indent=2)
```

## Implementation Timeline

### Week 1-2: Enhanced Model Management
- [ ] Implement enhanced ModelManager with import capabilities
- [ ] Create ModelTransferService for training service integration
- [ ] Add model validation and quality checks
- [ ] Test model import and validation

### Week 3-4: Model Configuration and API
- [ ] Update ModelConfig structure for integration
- [ ] Implement model management API endpoints
- [ ] Add model transfer and deployment endpoints
- [ ] Test API integration

### Week 5-6: Model Quality Assurance
- [ ] Implement comprehensive model validation
- [ ] Add quality scoring and recommendations
- [ ] Create model health checks
- [ ] Test validation system

### Week 7-8: Performance Monitoring
- [ ] Implement model performance monitoring
- [ ] Add drift detection capabilities
- [ ] Create performance metrics tracking
- [ ] Test monitoring system

### Week 9-10: UI Integration and Testing
- [ ] Update frontend for enhanced model management
- [ ] Add model transfer and validation UI
- [ ] Implement performance monitoring dashboard
- [ ] Comprehensive testing and documentation

## Success Criteria

1. **Functional Requirements**:
   - Seamless integration with standalone training service
   - Comprehensive model validation and quality assurance
   - Enhanced model management and deployment
   - Performance monitoring and drift detection

2. **Integration Requirements**:
   - Automated model import from training service
   - Model quality validation before deployment
   - Seamless model switching and rollback
   - Performance tracking and alerting

3. **Quality Requirements**:
   - All tests passing
   - Documentation complete and accurate
   - Error handling robust
   - Logging comprehensive

## Next Steps

1. **Review and Approve**: Review this plan with stakeholders
2. **Resource Allocation**: Assign developers to implementation phases
3. **Environment Setup**: Prepare development and testing environments
4. **Implementation**: Begin Phase 1 implementation
5. **Regular Reviews**: Weekly progress reviews and adjustments

This enhancement plan will transform the current basic model management system into a production-ready, comprehensive model management pipeline that seamlessly integrates with the standalone training service and provides robust model validation, deployment, and monitoring capabilities. 