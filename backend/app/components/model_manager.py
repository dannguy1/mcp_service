import os
import pickle
import logging
import warnings
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
        self.models: Dict[str, Dict[str, Any]] = {}  # agent registration
        self.redis_client: Optional[Any] = None
        
        # Resolve models directory path relative to project root
        models_dir = self.config.storage.directory
        if not Path(models_dir).is_absolute():
            # Get the project root more reliably
            # Start from current file location and navigate to backend root
            current_file = Path(__file__)
            
            # Navigate from backend/app/components/ to backend/
            project_root = current_file.parent.parent.parent  # backend/
            
            # Validate we're in the correct location by checking for expected directories
            if not (project_root / "app").exists() or not (project_root / "config").exists():
                # Fallback: try to find backend directory from current working directory
                cwd = Path.cwd()
                
                # Check if we're already in the backend directory
                if (cwd / "app").exists() and (cwd / "config").exists():
                    project_root = cwd
                # Check if we're in the project root and need to go to backend/
                elif (cwd / "backend" / "app").exists() and (cwd / "backend" / "config").exists():
                    project_root = cwd / "backend"
                else:
                    # Last resort: use current working directory
                    project_root = cwd
                    logger.warning(f"Could not reliably determine project root, using current directory: {project_root}")
            
            # Final validation to prevent nested directories
            if "backend/backend" in str(project_root):
                logger.error(f"Detected nested backend path: {project_root}")
                # Try to find the correct backend directory
                path_parts = project_root.parts
                backend_indices = [i for i, part in enumerate(path_parts) if part == "backend"]
                if len(backend_indices) > 1:
                    # Use the first backend directory found
                    correct_backend_index = backend_indices[0]
                    project_root = Path(*path_parts[:correct_backend_index + 1])
                    logger.info(f"Corrected project root to: {project_root}")
            
            self.models_directory = project_root / models_dir
        else:
            self.models_directory = Path(models_dir)
            
        self.model_registry_file = self.models_directory / "model_registry.json"
        
        # Ensure models directory exists with better error handling
        try:
            self.models_directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Models directory initialized at: {self.models_directory}")
            
            # Validate directory structure to prevent nested issues
            self._validate_directory_structure()
        except Exception as e:
            logger.error(f"Failed to create models directory {self.models_directory}: {e}")
            raise
        
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
        """Validate an imported model for compatibility with flexible requirements."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'metadata': {},
            'required_files_present': [],
            'optional_files_missing': [],
            'optional_files_present': []
        }
        
        try:
            model_dir = Path(model_path)
            
            # Define required and optional files
            required_files = ['model.joblib', 'metadata.json']
            optional_files = ['deployment_manifest.json', 'validate_model.py', 'inference_example.py', 'requirements.txt', 'README.md']
            
            # Check required files (import fails if any are missing)
            for file in required_files:
                if (model_dir / file).exists():
                    validation_result['required_files_present'].append(file)
                else:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append(f"Missing required file: {file}")
            
            # Check optional files (import succeeds but reports missing ones)
            for file in optional_files:
                if (model_dir / file).exists():
                    validation_result['optional_files_present'].append(file)
                else:
                    validation_result['optional_files_missing'].append(file)
                    validation_result['warnings'].append(f"Missing optional file: {file}")
            
            # Load and validate metadata
            if (model_dir / 'metadata.json').exists():
                try:
                    with open(model_dir / 'metadata.json', 'r') as f:
                        metadata = json.load(f)
                    
                    validation_result['metadata'] = metadata
                    
                    # Check metadata structure (warnings for missing fields, not errors)
                    required_metadata_fields = ['model_info', 'training_info', 'evaluation_info']
                    for field in required_metadata_fields:
                        if field not in metadata:
                            validation_result['warnings'].append(f"Missing metadata field: {field}")
                    
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
                
                except json.JSONDecodeError:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append("Invalid metadata.json format")
            
            # Test model loading with scikit-learn version compatibility handling
            if (model_dir / 'model.joblib').exists():
                try:
                    # Suppress scikit-learn version warnings during loading
                    with warnings.catch_warnings(record=True) as w:
                        warnings.simplefilter("ignore", category=UserWarning)
                        warnings.simplefilter("ignore", category=FutureWarning)
                        
                        # Try to load the model
                        test_model = joblib.load(model_dir / 'model.joblib')
                        
                        # Handle version warnings based on configuration
                        version_warnings = self._handle_version_warnings(w)
                        validation_result['warnings'].extend(version_warnings)
                        
                        if not hasattr(test_model, 'predict'):
                            validation_result['is_valid'] = False
                            validation_result['errors'].append("Model does not have predict method")
                
                except Exception as e:
                    # Check if it's a scikit-learn version compatibility issue
                    error_str = str(e).lower()
                    if "inconsistentversionwarning" in error_str or "version" in error_str:
                        if self.config.compatibility.allow_version_mismatch:
                            validation_result['warnings'].append(f"Version compatibility issue: {str(e)}")
                            if self.config.compatibility.log_version_warnings:
                                logger.warning(f"Model loading encountered version compatibility issue: {e}")
                            # Don't fail the import for version warnings if allowed
                        else:
                            validation_result['is_valid'] = False
                            validation_result['errors'].append(f"Version compatibility error: {str(e)}")
                    else:
                        validation_result['is_valid'] = False
                        validation_result['errors'].append(f"Model loading failed: {str(e)}")
            
            # Check feature compatibility
            if 'training_info' in metadata:
                feature_names = metadata['training_info'].get('feature_names', [])
                if not feature_names:
                    validation_result['warnings'].append("No feature names found in metadata")
                else:
                    validation_result['metadata']['feature_count'] = len(feature_names)
            
            # Add summary information
            if validation_result['optional_files_missing']:
                validation_result['warnings'].append(
                    f"Model validation successful but missing {len(validation_result['optional_files_missing'])} optional files: "
                    f"{', '.join(validation_result['optional_files_missing'])}"
                )
            
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
    
    def _handle_version_warnings(self, warnings_list: List[warnings.WarningMessage]) -> List[str]:
        """Handle scikit-learn version warnings based on configuration."""
        version_warnings = []
        
        for warning in warnings_list:
            if "InconsistentVersionWarning" in str(warning.message) or "version" in str(warning.message).lower():
                if self.config.compatibility.log_version_warnings:
                    logger.warning(f"Version compatibility warning: {warning.message}")
                
                if not self.config.compatibility.suppress_version_warnings:
                    version_warnings.append(f"Version compatibility warning: {warning.message}")
        
        return version_warnings
    
    async def load_model(self, model_path: str, scaler_path: Optional[str] = None) -> bool:
        """Load a trained model from file paths."""
        try:
            logger.info(f"Loading model from: {model_path}")
            
            # Validate model file
            if not Path(model_path).exists():
                logger.error(f"Model file not found: {model_path}")
                return False
            
            # Load model with scikit-learn version compatibility handling
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("ignore", category=UserWarning)
                warnings.simplefilter("ignore", category=FutureWarning)
                
                # Load the model
                self.current_model = joblib.load(model_path)
                
                # Handle version warnings based on configuration
                version_warnings = self._handle_version_warnings(w)
                for warning in version_warnings:
                    logger.warning(f"Model loaded with version compatibility warning: {warning}")
            
            logger.info(f"Model loaded successfully: {type(self.current_model).__name__}")
            
            # Load scaler if provided
            if scaler_path and Path(scaler_path).exists():
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("ignore", category=UserWarning)
                    warnings.simplefilter("ignore", category=FutureWarning)
                    
                    self.current_scaler = joblib.load(scaler_path)
                    
                    # Handle version warnings based on configuration
                    version_warnings = self._handle_version_warnings(w)
                    for warning in version_warnings:
                        logger.warning(f"Scaler loaded with version compatibility warning: {warning}")
                
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
    
    async def delete_model(self, version: str) -> bool:
        """Delete a model version from the registry and filesystem."""
        try:
            # Check if version exists
            models = await self.list_models()
            model_info = next((m for m in models if m['version'] == version), None)
            
            if not model_info:
                logger.error(f"Model version not found in registry: {version}")
                return False
            
            model_path = Path(model_info['path'])
            
            # Remove from registry first
            await self._remove_from_registry(version)
            
            # Delete model files
            if model_path.exists():
                try:
                    shutil.rmtree(model_path)
                    logger.info(f"Deleted model directory: {model_path}")
                except Exception as e:
                    logger.error(f"Error deleting model directory {model_path}: {e}")
                    # Continue even if file deletion fails, as registry is already updated
            
            logger.info(f"Model version {version} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting model version {version}: {e}")
            return False

    async def _remove_from_registry(self, version: str):
        """Remove a model from the registry."""
        try:
            if not self.model_registry_file.exists():
                return
            
            with open(self.model_registry_file, 'r') as f:
                registry_data = json.load(f)
            
            # Handle both old and new registry formats
            if isinstance(registry_data, dict) and 'models' in registry_data:
                # Old format: {"models": [...], "last_updated": "..."}
                models_list = registry_data.get('models', [])
                # Remove the model from the list
                registry_data['models'] = [m for m in models_list if m.get('version') != version]
                registry_data['last_updated'] = datetime.now().isoformat()
                
            elif isinstance(registry_data, dict):
                # New format: {"version": {...}, "version2": {...}}
                if version in registry_data:
                    del registry_data[version]
            
            # Save updated registry
            with open(self.model_registry_file, 'w') as f:
                json.dump(registry_data, f, indent=2)
                
            logger.info(f"Model {version} removed from registry")
            
        except Exception as e:
            logger.error(f"Error removing model from registry: {e}")
            raise
    
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
        try:
            registry_data = {}
            if self.model_registry_file.exists():
                with open(self.model_registry_file, 'r') as f:
                    registry_data = json.load(f)
            
            # Handle both old and new registry formats
            if isinstance(registry_data, dict) and 'models' in registry_data:
                # Old format: {"models": [...], "last_updated": "..."}
                models_list = registry_data.get('models', [])
                
                # Check if model already exists
                existing_model = next((m for m in models_list if m.get('version') == model_dir.name), None)
                if existing_model:
                    # Update existing model
                    existing_model.update({
                        'path': f"models/{model_dir.name}",
                        'status': status,
                        'last_updated': datetime.now().isoformat()
                    })
                else:
                    # Add new model
                    models_list.append({
                        'version': model_dir.name,
                        'path': f"models/{model_dir.name}",
                        'status': status,
                        'created_at': datetime.now().isoformat(),
                        'last_updated': datetime.now().isoformat(),
                        'model_type': 'IsolationForest'  # Default type
                    })
                
                registry_data['models'] = models_list
                registry_data['last_updated'] = datetime.now().isoformat()
                
            else:
                # New format: {"version": {...}, "version2": {...}}
                model_version = model_dir.name
                registry_data[model_version] = {
                    'path': str(model_dir),
                    'created_at': datetime.now().isoformat(),
                    'status': status,
                    'last_updated': datetime.now().isoformat(),
                    'import_method': 'zip_upload'
                }
            
            # Save updated registry
            with open(self.model_registry_file, 'w') as f:
                json.dump(registry_data, f, indent=2)
                
            logger.info(f"Model {model_dir.name} registered successfully")
            
        except Exception as e:
            logger.error(f"Error registering model: {e}")
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List all available models."""
        try:
            models = []
            
            # Load registry if it exists
            if self.model_registry_file.exists():
                with open(self.model_registry_file, 'r') as f:
                    registry_data = json.load(f)
                
                # Handle both old format (with models array) and new format (flat dict)
                if isinstance(registry_data, dict) and 'models' in registry_data:
                    # Old format: {"models": [...], "last_updated": "..."}
                    registry_items = registry_data['models']
                elif isinstance(registry_data, dict):
                    # New format: {"version": {...}, "version2": {...}}
                    registry_items = registry_data.items()
                else:
                    registry_items = []
                
                for item in registry_items:
                    if isinstance(item, tuple):
                        # New format: (version, model_info)
                        version, model_info = item
                    else:
                        # Old format: model_info dict with version field
                        model_info = item
                        version = model_info.get('version', 'unknown')
                    
                    # Handle different path formats
                    model_path_str = model_info.get('path', '')
                    if model_path_str.startswith('models/'):
                        # Relative path from registry
                        model_path = self.models_directory / model_path_str.replace('models/', '')
                    else:
                        # Absolute or relative path
                        model_path = Path(model_path_str)
                    
                    if model_path.exists():
                        # Load metadata if available
                        metadata_path = model_path / 'metadata.json'
                        metadata = {}
                        if metadata_path.exists():
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                        
                        models.append({
                            'version': version,
                            'path': str(model_path),
                            'status': model_info.get('status', 'unknown'),
                            'created_at': model_info.get('created_at', ''),
                            'last_updated': model_info.get('last_updated', ''),
                            'import_method': model_info.get('import_method', 'unknown'),
                            'metadata': metadata
                        })
            
            return models
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def scan_model_directory(self) -> List[Dict[str, Any]]:
        """Scan models directory for new models."""
        models = []
        
        if not self.models_directory.exists():
            return models
        
        for model_dir in self.models_directory.iterdir():
            if model_dir.is_dir() and (model_dir.name.startswith('model_') or model_dir.name.startswith('test_model_')):
                try:
                    # Check if already registered
                    if not await self._is_model_registered(model_dir.name):
                        # Validate and register new model
                        validation_result = await self._validate_imported_model(str(model_dir))
                        if validation_result['is_valid']:
                            await self._update_model_registry(model_dir, 'available')
                            models.append({
                                'version': model_dir.name,
                                'path': str(model_dir),
                                'status': 'available',
                                'created_at': datetime.now().isoformat()
                            })
                            logger.info(f"Discovered and registered new model: {model_dir.name}")
                        else:
                            logger.warning(f"Model {model_dir.name} failed validation: {validation_result['errors']}")
                except Exception as e:
                    logger.warning(f"Error processing model directory {model_dir}: {e}")
        
        return models
    
    async def _is_model_registered(self, version: str) -> bool:
        """Check if a model version is already registered."""
        try:
            if not self.model_registry_file.exists():
                return False
            
            with open(self.model_registry_file, 'r') as f:
                registry_data = json.load(f)
            
            # Handle both old and new registry formats
            if isinstance(registry_data, dict) and 'models' in registry_data:
                # Old format: check in models array
                return any(model.get('version') == version for model in registry_data['models'])
            elif isinstance(registry_data, dict):
                # New format: check in flat dictionary
                return version in registry_data
            
            return False
        except Exception as e:
            logger.error(f"Error checking model registration: {e}")
            return False
    
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

    def _validate_directory_structure(self):
        """Validate directory structure to prevent nested directory issues."""
        try:
            # Check if we're in a nested backend directory
            current_path = self.models_directory
            path_parts = current_path.parts
            
            # Look for repeated 'backend' in path
            backend_count = path_parts.count('backend')
            if backend_count > 1:
                logger.error(f"CRITICAL: Detected nested backend directory structure: {current_path}")
                logger.error(f"Found {backend_count} 'backend' directories in path")
                
                # Check if there are nested models directories
                models_count = path_parts.count('models')
                if models_count > 1:
                    logger.error(f"CRITICAL: Detected nested models directories: {current_path}")
                    logger.error("This indicates a serious path resolution issue")
                
                # Log the expected correct path
                expected_path = Path(__file__).parent.parent.parent / "models"
                logger.error(f"Expected models directory should be: {expected_path}")
                
                # Try to fix the path automatically
                backend_indices = [i for i, part in enumerate(path_parts) if part == "backend"]
                if len(backend_indices) > 1:
                    # Use the first backend directory found
                    correct_backend_index = backend_indices[0]
                    corrected_path = Path(*path_parts[:correct_backend_index + 1]) / "models"
                    logger.error(f"CRITICAL: Path should be corrected to: {corrected_path}")
                    
                    # Attempt to fix the path
                    try:
                        # Remove the incorrect directory
                        if current_path.exists():
                            import shutil
                            shutil.rmtree(current_path)
                            logger.info(f"Removed incorrect nested directory: {current_path}")
                        
                        # Set the correct path
                        self.models_directory = corrected_path
                        self.model_registry_file = self.models_directory / "model_registry.json"
                        
                        # Create the correct directory
                        self.models_directory.mkdir(parents=True, exist_ok=True)
                        logger.info(f"Created correct models directory at: {self.models_directory}")
                        
                    except Exception as e:
                        logger.error(f"Failed to fix nested directory: {e}")
                        raise RuntimeError(f"Cannot continue with nested backend directory: {current_path}")
            
            # Check if models directory is in the expected location
            expected_models_dir = Path(__file__).parent.parent.parent / "models"
            if self.models_directory != expected_models_dir:
                logger.warning(f"Models directory location: {self.models_directory}")
                logger.warning(f"Expected location: {expected_models_dir}")
                
        except Exception as e:
            logger.error(f"Error during directory structure validation: {e}")
            raise

    def set_redis_client(self, redis_client):
        self.redis_client = redis_client

    def _update_model_status(self, model_id: str, model_entry: Dict[str, Any]):
        try:
            if not self.redis_client:
                logger.warning("Redis client not available, skipping status update")
                return
            # Clean up old keys with variations of the model ID
            old_keys = [
                f"mcp:model:wi_fi_agent:status",
                f"mcp:model:WiFiAgent:status",
                f"mcp:model:wifiagent:status",
                f"mcp:model:wifi_agent:status"
            ]
            for key in old_keys:
                self.redis_client.delete(key)
            key = f"mcp:model:{model_id}:status"
            # Map agent status to frontend status
            if model_entry['status'] in ['active', 'analyzing', 'initialized']:
                frontend_status = 'active'
            elif model_entry['status'] == 'error':
                frontend_status = 'error'
            else:
                frontend_status = 'inactive'
            model_entry['status'] = frontend_status
            self.redis_client.set(key, json.dumps(model_entry))
            logger.info(f"Setting Redis key: {key}")
            logger.info(f"Setting Redis value: {json.dumps(model_entry)}")
        except Exception as e:
            logger.error(f"Error updating model status in Redis: {e}")

    def register_model(self, agent, model_id: str) -> bool:
        try:
            if model_id in self.models:
                logger.warning(f"Model {model_id} already registered")
                return False
            agent_name = getattr(agent, 'agent_name', None) or getattr(agent, 'name', None) or agent.__class__.__name__
            model_entry = {
                'id': model_id,
                'name': agent_name,
                'status': 'initialized',
                'is_running': False,
                'last_run': None,
                'capabilities': getattr(agent, 'capabilities', []),
                'description': getattr(agent, 'description', '')
            }
            self.models[model_id] = {
                'agent': agent,
                'entry': model_entry
            }
            self._update_model_status(model_id, model_entry)
            logger.info(f"Successfully registered model: {model_id} with name: {agent_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register model {model_id}: {e}")
            return False

    def unregister_model(self, model_id: str) -> bool:
        try:
            if model_id not in self.models:
                logger.warning(f"Model {model_id} not registered")
                return False
            model_entry = self.models[model_id]['entry']
            model_entry['status'] = 'inactive'
            model_entry['is_running'] = False
            model_entry['last_run'] = datetime.now().isoformat()
            self._update_model_status(model_id, model_entry)
            del self.models[model_id]
            logger.info(f"Successfully unregistered model: {model_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unregister model {model_id}: {e}")
            return False

    def activate_model(self, model_id: str) -> bool:
        try:
            if model_id not in self.models:
                logger.warning(f"Model {model_id} not found in registry")
                return False
            model_entry = self.models[model_id]['entry']
            model_entry['status'] = 'active'
            model_entry['is_running'] = True
            model_entry['last_run'] = datetime.now().isoformat()
            self._update_model_status(model_id, model_entry)
            logger.info(f"Model {model_id} activated successfully")
            return True
        except Exception as e:
            logger.error(f"Error activating model {model_id}: {e}")
            return False

    def deactivate_model(self, model_id: str) -> bool:
        try:
            if model_id not in self.models:
                logger.warning(f"Model {model_id} not found in registry")
                return False
            model_entry = self.models[model_id]['entry']
            model_entry['status'] = 'inactive'
            model_entry['is_running'] = False
            model_entry['last_run'] = datetime.now().isoformat()
            self._update_model_status(model_id, model_entry)
            logger.info(f"Model {model_id} deactivated successfully")
            return True
        except Exception as e:
            logger.error(f"Error deactivating model {model_id}: {e}")
            return False

    def get_all_models(self) -> List[Dict[str, Any]]:
        models = []
        for model_id, model_data in self.models.items():
            entry = model_data['entry']
            status = entry.get('status', 'inactive')
            if self.redis_client:
                try:
                    key = f"mcp:model:{model_id}:status"
                    status_data = self.redis_client.get(key)
                    if status_data:
                        agent_status = json.loads(status_data)
                        status = agent_status.get('status', status)
                except Exception as e:
                    logger.error(f"Error getting Redis status for {model_id}: {e}")
            entry['status'] = status
            models.append(entry)
        return models

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        if model_id not in self.models:
            logger.warning(f"Model {model_id} not found in registry")
            return None
        entry = self.models[model_id]['entry']
        status = entry.get('status', 'inactive')
        if self.redis_client:
            try:
                key = f"mcp:model:{model_id}:status"
                status_data = self.redis_client.get(key)
                if status_data:
                    agent_status = json.loads(status_data)
                    status = agent_status.get('status', status)
            except Exception as e:
                logger.error(f"Error getting Redis status for {model_id}: {e}")
        entry['status'] = status
        return entry 