import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_recall_curve, average_precision_score
import joblib

from components.feature_extractor import FeatureExtractor
from data_service import data_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelTrainer:
    """Handles model training, evaluation, and persistence."""
    
    def __init__(self, config: Dict):
        """Initialize the model trainer.
        
        Args:
            config: Configuration dictionary containing training parameters
        """
        self.config = config
        self.model_dir = config.get('model_dir', 'models')
        self.feature_extractor = FeatureExtractor()
        self.scaler = StandardScaler()
        
        # Create model directory if it doesn't exist
        os.makedirs(self.model_dir, exist_ok=True)
    
    async def prepare_training_data(self, start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from database.
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            
        Returns:
            Tuple of (features, labels) for training
        """
        # Fetch logs from database
        query = """
            SELECT * FROM wifi_logs 
            WHERE timestamp BETWEEN $1 AND $2
            ORDER BY timestamp
        """
        logs = await data_service.fetch_all(query, start_date, end_date)
        
        if not logs:
            raise ValueError("No training data available for the specified period")
        
        # Extract features
        features = await self.feature_extractor.extract(logs)
        
        # Prepare feature matrix
        X = self._prepare_feature_matrix(features)
        
        # For unsupervised learning, we don't have true labels
        # We'll use the model's predictions on a validation set as pseudo-labels
        y = np.zeros(len(X))
        
        return X, y
    
    def _prepare_feature_matrix(self, features: Dict) -> np.ndarray:
        """Prepare feature matrix for training.
        
        Args:
            features: Dictionary of extracted features
            
        Returns:
            Feature matrix as numpy array
        """
        # Convert features to DataFrame
        df = pd.DataFrame(features)
        
        # Select numeric features
        numeric_features = [
            'signal_strength',
            'channel',
            'data_rate',
            'packet_loss_rate',
            'retry_rate'
        ]
        
        # Extract numeric features
        X = df[numeric_features].values
        
        # Scale features
        X = self.scaler.fit_transform(X)
        
        return X
    
    def train_model(self, X: np.ndarray, y: np.ndarray) -> IsolationForest:
        """Train the anomaly detection model.
        
        Args:
            X: Feature matrix
            y: Labels (not used in unsupervised learning)
            
        Returns:
            Trained model
        """
        # Split data into train and validation sets
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Initialize model
        model = IsolationForest(
            n_estimators=self.config.get('n_estimators', 100),
            max_samples=self.config.get('max_samples', 'auto'),
            contamination=self.config.get('contamination', 0.1),
            random_state=42
        )
        
        # Train model
        model.fit(X_train)
        
        # Evaluate model
        metrics = self._evaluate_model(model, X_val)
        logger.info(f"Model evaluation metrics: {metrics}")
        
        return model
    
    def _evaluate_model(self, model: IsolationForest, X: np.ndarray) -> Dict:
        """Evaluate model performance.
        
        Args:
            model: Trained model
            X: Feature matrix
            
        Returns:
            Dictionary of evaluation metrics
        """
        # Get anomaly scores
        scores = -model.score_samples(X)
        
        # Calculate precision-recall curve
        # For unsupervised learning, we use the model's predictions as pseudo-labels
        y_pred = model.predict(X)
        y_pred = (y_pred == -1).astype(int)  # Convert to binary labels
        
        precision, recall, thresholds = precision_recall_curve(y_pred, scores)
        avg_precision = average_precision_score(y_pred, scores)
        
        return {
            'average_precision': avg_precision,
            'precision': precision.tolist(),
            'recall': recall.tolist(),
            'thresholds': thresholds.tolist()
        }
    
    def save_model(self, model: IsolationForest, version: str) -> str:
        """Save model and metadata.
        
        Args:
            model: Trained model
            version: Model version
            
        Returns:
            Path to saved model
        """
        # Create version directory
        version_dir = os.path.join(self.model_dir, version)
        os.makedirs(version_dir, exist_ok=True)
        
        # Save model
        model_path = os.path.join(version_dir, 'model.joblib')
        joblib.dump(model, model_path)
        
        # Save scaler
        scaler_path = os.path.join(version_dir, 'scaler.joblib')
        joblib.dump(self.scaler, scaler_path)
        
        # Save metadata
        metadata = {
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'feature_names': [
                'signal_strength',
                'channel',
                'data_rate',
                'packet_loss_rate',
                'retry_rate'
            ]
        }
        
        metadata_path = os.path.join(version_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Model saved to {version_dir}")
        return version_dir
    
    async def train_and_save(self, start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> str:
        """Train model and save to disk.
        
        Args:
            start_date: Start date for data collection
            end_date: End date for data collection
            
        Returns:
            Path to saved model
        """
        # Prepare data
        X, y = await self.prepare_training_data(start_date, end_date)
        
        # Train model
        model = self.train_model(X, y)
        
        # Generate version
        version = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save model
        model_path = self.save_model(model, version)
        
        return model_path 