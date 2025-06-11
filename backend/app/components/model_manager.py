import os
import pickle
import logging
from typing import Any, Optional
import asyncio
from datetime import datetime, timedelta

class ModelManager:
    def __init__(self):
        """Initialize the model manager."""
        self.logger = logging.getLogger("ModelManager")
        self.models = {}
        self.last_modified = {}
        self.check_interval = 300  # 5 minutes

    async def load_model(self, model_path: str) -> Any:
        """
        Load a model from disk.
        
        Args:
            model_path: Path to the model file
            
        Returns:
            The loaded model
        """
        try:
            # Check if model exists
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            # Get file modification time
            mod_time = os.path.getmtime(model_path)
            
            # Check if model is already loaded and up to date
            if (
                model_path in self.models
                and model_path in self.last_modified
                and self.last_modified[model_path] == mod_time
            ):
                self.logger.debug(f"Using cached model: {model_path}")
                return self.models[model_path]
            
            # Load model in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(
                None,
                self._load_model_file,
                model_path
            )
            
            # Cache the model
            self.models[model_path] = model
            self.last_modified[model_path] = mod_time
            
            self.logger.info(f"Loaded model: {model_path}")
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to load model {model_path}: {e}")
            raise

    def _load_model_file(self, model_path: str) -> Any:
        """
        Load a model file from disk (synchronous).
        
        Args:
            model_path: Path to the model file
            
        Returns:
            The loaded model
        """
        try:
            with open(model_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            self.logger.error(f"Error loading model file {model_path}: {e}")
            raise

    async def start_model_checker(self):
        """Start the model checker task."""
        while True:
            try:
                await self._check_models()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error in model checker: {e}")
                await asyncio.sleep(60)

    async def _check_models(self):
        """Check for model updates."""
        for model_path in list(self.models.keys()):
            try:
                if not os.path.exists(model_path):
                    self.logger.warning(f"Model file removed: {model_path}")
                    del self.models[model_path]
                    del self.last_modified[model_path]
                    continue
                
                mod_time = os.path.getmtime(model_path)
                if mod_time != self.last_modified.get(model_path):
                    self.logger.info(f"Model file updated: {model_path}")
                    await self.load_model(model_path)
                    
            except Exception as e:
                self.logger.error(f"Error checking model {model_path}: {e}")

    def get_model_info(self, model_path: str) -> Optional[dict]:
        """
        Get information about a loaded model.
        
        Args:
            model_path: Path to the model file
            
        Returns:
            Dictionary containing model information, or None if not loaded
        """
        if model_path not in self.models:
            return None
            
        return {
            "path": model_path,
            "last_modified": datetime.fromtimestamp(
                self.last_modified[model_path]
            ).isoformat(),
            "type": type(self.models[model_path]).__name__
        }

    def get_all_model_info(self) -> dict:
        """
        Get information about all loaded models.
        
        Returns:
            Dictionary containing information about all loaded models
        """
        return {
            path: self.get_model_info(path)
            for path in self.models.keys()
        } 