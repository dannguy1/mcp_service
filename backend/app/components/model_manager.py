import os
import pickle
import logging
from typing import Any, Optional, Dict, List, Tuple
import asyncio
from datetime import datetime, timedelta
import joblib
import json
import shutil
from pathlib import Path
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
        
        # Ensure models directory exists
        self.models_directory.mkdir(parents=True, exist_ok=True)
        
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
            if 'deployment_info' not in metadata:
                metadata['deployment_info'] = {}
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
    
    async def load_model_version(self, version: str) -> bool:
        """Load a specific model version."""
        try:
            # Find the model in the registry
            models = await self.list_models()
            model_info = next((m for m in models if m['version'] == version), None)
            
            if not model_info:
                logger.error(f"Model version not found in registry: {version}")
                return False
            
            model_path = Path(model_info['path'])
            if not model_path.exists():
                logger.error(f"Model directory not found: {model_path}")
                return False
            
            model_file = model_path / "model.joblib"
            scaler_file = model_path / "scaler.joblib"
            
            return await self.load_model(str(model_file), str(scaler_file) if scaler_file.exists() else None)
            
        except Exception as e:
            logger.error(f"Error loading model version {version}: {e}")
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
    
    async def _update_deployment_status(self, version: str, status: str):
        """Update deployment status in model metadata."""
        try:
            model_dir = self.models_directory / version
            metadata_path = model_dir / "metadata.json"
            
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                if 'deployment_info' not in metadata:
                    metadata['deployment_info'] = {}
                
                metadata['deployment_info']['status'] = status
                metadata['deployment_info']['deployed_at'] = datetime.now().isoformat()
                
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2, default=str)
                    
        except Exception as e:
            logger.error(f"Error updating deployment status: {e}")
    
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
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List all available models."""
        try:
            models = []
            
            logger.info(f"Listing models from directory: {self.models_directory}")
            logger.info(f"Registry file path: {self.model_registry_file}")
            
            # Load registry
            registry = {}
            if self.model_registry_file.exists():
                logger.info("Registry file exists, loading...")
                with open(self.model_registry_file, 'r') as f:
                    registry = json.load(f)
                logger.info(f"Loaded registry: {registry}")
            else:
                logger.warning("Registry file does not exist")
            
            # Handle different registry formats
            if 'models' in registry:
                # New format with models array
                model_list = registry['models']
                logger.info(f"Using new format, found {len(model_list)} models")
            else:
                # Old format with version keys
                model_list = [{'version': version, **info} for version, info in registry.items()]
                logger.info(f"Using old format, found {len(model_list)} models")
            
            # Get model information
            for model_info in model_list:
                version = model_info['version']
                model_path = model_info['path']
                model_dir = Path(model_path)
                metadata_path = model_dir / "metadata.json"
                
                logger.info(f"Processing model: {version} at {model_path}")
                
                model_data = {
                    'version': version,
                    'path': model_path,
                    'status': model_info.get('status', 'available'),
                    'created_at': model_info.get('created_at', ''),
                    'last_updated': model_info.get('last_updated', ''),
                    'model_type': model_info.get('model_type', 'Unknown')
                }
                
                # Load additional metadata if available
                if metadata_path.exists():
                    logger.info(f"Loading metadata from: {metadata_path}")
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    model_data.update({
                        'model_type': metadata.get('model_info', {}).get('model_type', 'Unknown'),
                        'training_samples': metadata.get('training_info', {}).get('n_samples', 0),
                        'evaluation_metrics': metadata.get('evaluation_info', {}).get('basic_metrics', {}),
                        'feature_count': len(metadata.get('training_info', {}).get('feature_names', []))
                    })
                else:
                    logger.warning(f"Metadata file not found: {metadata_path}")
                
                models.append(model_data)
            
            # Sort by creation date (newest first)
            models.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            logger.info(f"Returning {len(models)} models")
            return models
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    async def predict(self, features: np.ndarray) -> np.ndarray:
        """Make predictions using the loaded model."""
        if not self.model_loaded or self.current_model is None:
            raise RuntimeError("No model loaded")
        
        try:
            # Scale features if scaler is available
            if self.current_scaler is not None:
                features = self.current_scaler.transform(features)
            
            # Make prediction
            predictions = self.current_model.predict(features)
            return predictions
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            raise
    
    async def predict_proba(self, features: np.ndarray) -> np.ndarray:
        """Get prediction probabilities if available."""
        if not self.model_loaded or self.current_model is None:
            raise RuntimeError("No model loaded")
        
        try:
            # Scale features if scaler is available
            if self.current_scaler is not None:
                features = self.current_scaler.transform(features)
            
            # Get prediction probabilities if available
            if hasattr(self.current_model, 'predict_proba'):
                probabilities = self.current_model.predict_proba(features)
                return probabilities
            elif hasattr(self.current_model, 'score_samples'):
                # For anomaly detection models, use score_samples
                scores = self.current_model.score_samples(features)
                # Convert scores to probabilities (simple normalization)
                probabilities = np.exp(scores)
                return probabilities.reshape(-1, 1)
            else:
                raise RuntimeError("Model does not support probability predictions")
            
        except Exception as e:
            logger.error(f"Error getting prediction probabilities: {e}")
            raise
    
    def get_model_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently loaded model."""
        if not self.model_loaded:
            return None
        
        return {
            'version': self.current_model_version,
            'model_type': type(self.current_model).__name__,
            'feature_names': self.feature_names,
            'metadata': self.current_model_metadata,
            'loaded_at': datetime.now().isoformat()
        }
    
    def is_model_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        return self.model_loaded 