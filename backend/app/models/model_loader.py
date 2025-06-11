import os
import json
import logging
import numpy as np
import pandas as pd
import joblib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
import yaml
from .config import ModelConfig

from app.components.feature_extractor import FeatureExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelLoader:
    """Handles model loading and inference."""
    
    def __init__(self, config: ModelConfig):
        """Initialize the model loader with configuration."""
        self.config = config
        self.model = None
        self.metadata = {}
        
        # Create necessary directories
        self.model_dir = Path(self.config.storage.directory)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        (self.model_dir / "versions").mkdir(exist_ok=True)
        (self.model_dir / "backups").mkdir(exist_ok=True)
        
        # Try to load the latest model
        self.load_latest_model()
    
    def load_latest_model(self) -> bool:
        """Load the latest model version.
        
        Returns:
            bool: True if model was loaded successfully, False otherwise
        """
        try:
            # Get the latest model version
            versions_dir = self.model_dir / "versions"
            if not versions_dir.exists():
                logger.warning("No versions directory found")
                return False
                
            model_files = list(versions_dir.glob("model_*.joblib"))
            if not model_files:
                logger.warning("No model files found")
                return False
                
            latest_model = max(model_files, key=lambda x: x.stat().st_mtime)
            return self.load_model(latest_model)
            
        except Exception as e:
            logger.error(f"Error loading latest model: {e}")
            return False
    
    def load_model(self, model_path: Path) -> bool:
        """Load a specific model version.
        
        Args:
            model_path: Path to the model file
            
        Returns:
            bool: True if model was loaded successfully, False otherwise
        """
        try:
            if not model_path.exists():
                logger.warning(f"Model file not found: {model_path}")
                return False
                
            # Load the model
            self.model = joblib.load(model_path)
            
            # Load metadata if available
            metadata_path = model_path.with_suffix('.yaml')
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    self.metadata = yaml.safe_load(f)
            
            logger.info(f"Loaded model from {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def save_model(self, model: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Save model and metadata."""
        try:
            # Create versions directory if it doesn't exist
            versions_dir = self.model_dir / "versions"
            versions_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate version string
            version = datetime.now().strftime(self.config.storage.version_format)
            
            # Save model
            model_path = versions_dir / f"model_{version}.joblib"
            joblib.dump(model, model_path)
            
            # Save metadata
            if metadata:
                metadata_path = model_path.with_suffix('.yaml')
                with open(metadata_path, 'w') as f:
                    yaml.dump(metadata, f)
            
            logger.info(f"Saved model to {model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def predict(self, data: Any) -> Any:
        """Make predictions using the loaded model.
        
        Args:
            data: Input data
            
        Returns:
            Any: Model predictions
            
        Raises:
            RuntimeError: If no model is loaded
        """
        if self.model is None:
            raise RuntimeError("No model loaded")
        return self.model.predict(data)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model.
        
        Returns:
            Dict[str, Any]: Model information including version and metadata
        """
        return {
            "version": self.metadata.get("version", "unknown"),
            "type": self.metadata.get("type", "unknown"),
            "created_at": self.metadata.get("created_at", "unknown"),
            "metrics": self.metadata.get("metrics", {}),
            "config": self.metadata.get("config", {})
        }
    
    def list_models(self) -> List[str]:
        """List available model versions.
        
        Returns:
            List of model version directories
        """
        if not self.model_dir.exists():
            return []
        
        return [d.name for d in self.model_dir.glob("*") if d.is_dir()]
    
    def get_latest_model(self) -> Optional[str]:
        """Get the latest model version.
        
        Returns:
            Path to latest model version directory
        """
        versions = self.list_models()
        if not versions:
            return None
        
        # Sort versions by timestamp (they are named with timestamps)
        versions.sort(reverse=True)
        return self.model_dir / versions[0]
    
    async def predict_new_data(self, logs: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Make predictions on new data.
        
        Args:
            logs: List of log entries to predict on
            
        Returns:
            Tuple of (predictions, scores)
            predictions: -1 for anomalies, 1 for normal
            scores: Anomaly scores (higher means more anomalous)
        """
        if self.model is None:
            raise ValueError("No model loaded. Call load_model() first.")
        
        # Extract features
        features = await self.feature_extractor.extract(logs)
        
        # Prepare feature matrix
        X = self._prepare_feature_matrix(features)
        
        # Make predictions
        predictions = self.model.predict(X)
        scores = -self.model.score_samples(X)
        
        return predictions, scores
    
    def _prepare_feature_matrix(self, features: Dict) -> np.ndarray:
        """Prepare feature matrix for prediction.
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            Feature matrix as numpy array
        """
        # Convert features to DataFrame
        df = pd.DataFrame(features)
        
        # Select numeric features
        numeric_features = self.metadata['feature_names']
        
        # Extract numeric features
        X = df[numeric_features].values
        
        # Scale features
        X = self.scaler.transform(X)
        
        return X 