import os
import json
import zipfile
import shutil
import logging
import hashlib
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import joblib

logger = logging.getLogger(__name__)

class ModelLoader:
    """Service for loading and validating model packages."""
    
    def __init__(self, models_directory: str = "backend/models"):
        self.models_directory = Path(models_directory)
        self.models_directory.mkdir(parents=True, exist_ok=True)
    
    async def process_model_package(self, zip_path: str, validate: bool = True) -> Dict[str, Any]:
        """Process uploaded model package ZIP file."""
        try:
            # Extract version from filename
            filename = Path(zip_path).name
            version = filename.replace('model_', '').replace('_deployment.zip', '')
            
            # Create model directory
            model_dir = self.models_directory / f"model_{version}"
            model_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract ZIP contents
            if not await self.extract_model_package(zip_path, model_dir):
                raise ValueError("Failed to extract model package")
            
            # Validate contents
            if validate:
                validation_result = await self.validate_model_contents(model_dir)
                if not validation_result['is_valid']:
                    shutil.rmtree(model_dir)
                    raise ValueError(f"Model validation failed: {validation_result['errors']}")
            
            # Register model
            await self.register_model(model_dir, version)
            
            return {
                "version": version,
                "status": "imported",
                "path": str(model_dir),
                "imported_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing model package: {e}")
            raise
    
    async def extract_model_package(self, zip_path: str, target_dir: Path) -> bool:
        """Extract model package ZIP to target directory."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Validate ZIP contents before extraction
                required_files = [
                    'model.joblib',
                    'metadata.json', 
                    'deployment_manifest.json',
                    'validate_model.py',
                    'inference_example.py',
                    'requirements.txt',
                    'README.md'
                ]
                
                zip_files = zip_ref.namelist()
                missing_files = [f for f in required_files if f not in zip_files]
                
                if missing_files:
                    raise ValueError(f"Missing required files: {missing_files}")
                
                # Extract to target directory
                zip_ref.extractall(target_dir)
                
                return True
                
        except zipfile.BadZipFile:
            raise ValueError("Invalid ZIP file format")
        except Exception as e:
            logger.error(f"Error extracting ZIP: {e}")
            raise
    
    async def validate_model_contents(self, model_dir: Path) -> Dict[str, Any]:
        """Validate model package contents."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'metadata': {}
        }
        
        try:
            # Check required files
            required_files = [
                'model.joblib',
                'metadata.json',
                'deployment_manifest.json',
                'validate_model.py',
                'inference_example.py',
                'requirements.txt',
                'README.md'
            ]
            
            for file in required_files:
                if not (model_dir / file).exists():
                    validation_result['is_valid'] = False
                    validation_result['errors'].append(f"Missing required file: {file}")
            
            # Validate metadata.json
            if (model_dir / 'metadata.json').exists():
                try:
                    with open(model_dir / 'metadata.json', 'r') as f:
                        metadata = json.load(f)
                    
                    # Check required metadata fields
                    required_fields = ['model_type', 'version', 'created_at', 'training_info']
                    for field in required_fields:
                        if field not in metadata:
                            validation_result['warnings'].append(f"Missing metadata field: {field}")
                    
                    validation_result['metadata'] = metadata
                    
                except json.JSONDecodeError:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append("Invalid metadata.json format")
            
            # Validate deployment_manifest.json
            if (model_dir / 'deployment_manifest.json').exists():
                try:
                    with open(model_dir / 'deployment_manifest.json', 'r') as f:
                        manifest = json.load(f)
                    
                    # Verify SHA256 hashes
                    if 'file_hashes' in manifest:
                        for filename, expected_hash in manifest['file_hashes'].items():
                            file_path = model_dir / filename
                            if file_path.exists():
                                actual_hash = self._calculate_file_hash(file_path)
                                if actual_hash != expected_hash:
                                    validation_result['is_valid'] = False
                                    validation_result['errors'].append(f"Hash mismatch for {filename}")
                    
                except json.JSONDecodeError:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append("Invalid deployment_manifest.json format")
            
            # Test model loading
            try:
                model_file = model_dir / 'model.joblib'
                if model_file.exists():
                    model = joblib.load(str(model_file))
                    validation_result['metadata']['model_type'] = type(model).__name__
            except Exception as e:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"Failed to load model: {str(e)}")
            
        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    async def register_model(self, model_dir: Path, version: str):
        """Register model in the registry."""
        try:
            registry_file = self.models_directory / "model_registry.json"
            registry = {}
            
            if registry_file.exists():
                with open(registry_file, 'r') as f:
                    registry = json.load(f)
            
            # Add new model to registry
            registry[version] = {
                'path': str(model_dir),
                'created_at': datetime.now().isoformat(),
                'status': 'imported',
                'last_updated': datetime.now().isoformat(),
                'import_method': 'zip_upload'
            }
            
            # Save updated registry
            with open(registry_file, 'w') as f:
                json.dump(registry, f, indent=2)
                
            logger.info(f"Model {version} registered successfully")
            
        except Exception as e:
            logger.error(f"Error registering model: {e}")
            raise
    
    def validate_uploaded_file(self, filename: str, file_size: int) -> bool:
        """Validate uploaded file for security."""
        # Check file extension
        if not filename.lower().endswith('.zip'):
            return False
        
        # Check file size (100MB limit)
        if file_size > 100 * 1024 * 1024:
            return False
        
        # Check for path traversal in filename
        if '..' in filename or '/' in filename:
            return False
        
        # Check naming convention
        if not filename.startswith('model_') or not filename.endswith('_deployment.zip'):
            return False
        
        return True 