import os
import json
import logging
import numpy as np
import joblib
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from components.feature_extractor import FeatureExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelLoader:
    """Handles model loading and inference."""
    
    def __init__(self, model_dir: str = 'models'):
        """Initialize the model loader.
        
        Args:
            model_dir: Directory containing model versions
        """
        self.model_dir = model_dir
        self.feature_extractor = FeatureExtractor()
        self.model = None
        self.scaler = None
        self.metadata = None
        
        # Create model directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)
    
    def list_models(self) -> List[str]:
        """List available model versions.
        
        Returns:
            List of model version directories
        """
        if not os.path.exists(self.model_dir):
            return []
        
        return [d for d in os.listdir(self.model_dir)
                if os.path.isdir(os.path.join(self.model_dir, d))]
    
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
        return os.path.join(self.model_dir, versions[0])
    
    def load_model(self, version: Optional[str] = None) -> None:
        """Load a specific model version or the latest one.
        
        Args:
            version: Model version to load (if None, loads latest)
        """
        if version is None:
            model_path = self.get_latest_model()
        else:
            model_path = os.path.join(self.model_dir, version)
        
        if not model_path or not os.path.exists(model_path):
            raise ValueError(f"No model found at {model_path}")
        
        # Load model
        model_file = os.path.join(model_path, 'model.joblib')
        self.model = joblib.load(model_file)
        
        # Load scaler
        scaler_file = os.path.join(model_path, 'scaler.joblib')
        self.scaler = joblib.load(scaler_file)
        
        # Load metadata
        metadata_file = os.path.join(model_path, 'metadata.json')
        with open(metadata_file, 'r') as f:
            self.metadata = json.load(f)
        
        logger.info(f"Loaded model version {self.metadata['version']}")
    
    async def predict(self, logs: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
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
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model.
        
        Returns:
            Dictionary containing model information
        """
        if self.metadata is None:
            raise ValueError("No model loaded. Call load_model() first.")
        
        return {
            'version': self.metadata['version'],
            'timestamp': self.metadata['timestamp'],
            'config': self.metadata['config'],
            'feature_names': self.metadata['feature_names']
        } 