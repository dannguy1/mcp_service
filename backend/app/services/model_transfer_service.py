import asyncio
import logging
import json
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
        
        # Ensure transfer history directory exists
        self.transfer_history_file.parent.mkdir(parents=True, exist_ok=True)
    
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
    
    async def get_transfer_history(self) -> List[Dict[str, Any]]:
        """Get model transfer history."""
        try:
            if self.transfer_history_file.exists():
                with open(self.transfer_history_file, 'r') as f:
                    history = json.load(f)
                return history
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting transfer history: {e}")
            return []
    
    async def cleanup_old_transfers(self, days_to_keep: int = 30):
        """Clean up old transfer records."""
        try:
            history = await self.get_transfer_history()
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
            
            # Filter out old records
            filtered_history = []
            for record in history:
                record_date = datetime.fromisoformat(record['transferred_at']).timestamp()
                if record_date > cutoff_date:
                    filtered_history.append(record)
            
            # Save filtered history
            with open(self.transfer_history_file, 'w') as f:
                json.dump(filtered_history, f, indent=2)
            
            logger.info(f"Cleaned up transfer history, kept {len(filtered_history)} records")
            
        except Exception as e:
            logger.error(f"Error cleaning up transfer history: {e}")
    
    async def validate_training_service_connection(self) -> Dict[str, Any]:
        """Validate connection to training service."""
        try:
            result = {
                'connected': False,
                'path_exists': False,
                'models_found': 0,
                'error': None
            }
            
            # Check if training service path exists
            if self.training_service_path.exists():
                result['path_exists'] = True
                
                # Check for models directory
                models_dir = self.training_service_path / "models"
                if models_dir.exists():
                    # Count available models
                    model_count = len([d for d in models_dir.iterdir() if d.is_dir()])
                    result['models_found'] = model_count
                    result['connected'] = True
                else:
                    result['error'] = "Models directory not found in training service"
            else:
                result['error'] = f"Training service path not found: {self.training_service_path}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating training service connection: {e}")
            return {
                'connected': False,
                'path_exists': False,
                'models_found': 0,
                'error': str(e)
            } 