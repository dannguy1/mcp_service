#!/usr/bin/env python3
"""
Inference Example for Model 20250624_205530
Demonstrates how to use the deployed model for predictions.
"""

import joblib
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Any

class ModelInference:
    def __init__(self, model_dir: str = "."):
        """Initialize model inference."""
        self.model_dir = Path(model_dir)
        
        # Load deployment manifest
        with open(self.model_dir / 'deployment_manifest.json', 'r') as f:
            self.manifest = json.load(f)
        
        # Load model and scaler
        self.model = joblib.load(self.model_dir / 'model.joblib')
        self.scaler = None
        if (self.model_dir / 'scaler.joblib').exists():
            self.scaler = joblib.load(self.model_dir / 'scaler.joblib')
        
        # Get configuration
        self.threshold = self.manifest['inference_config']['threshold']
        self.feature_names = self.manifest['training_info']['feature_names']
    
    @property
    def manifest(self) -> Dict[str, Any]:
        """Deployment manifest data."""
        return self._manifest
    
    @manifest.setter
    def manifest(self, value: Dict[str, Any]):
        self._manifest = value
    
    @property
    def model(self) -> Any:
        """Loaded scikit-learn model."""
        return self._model
    
    @model.setter
    def model(self, value: Any):
        self._model = value
    
    @property
    def scaler(self) -> Any:
        """Feature scaler (if available)."""
        return self._scaler
    
    @scaler.setter
    def scaler(self, value: Any):
        self._scaler = value
    
    @property
    def threshold(self) -> float:
        """Detection threshold."""
        return self._threshold
    
    @threshold.setter
    def threshold(self, value: float):
        self._threshold = value
    
    @property
    def feature_names(self) -> List[str]:
        """List of expected feature names."""
        return self._feature_names
    
    @feature_names.setter
    def feature_names(self, value: List[str]):
        self._feature_names = value
    
    def preprocess_features(self, features: List[Dict[str, Any]]) -> np.ndarray:
        """Preprocess input features.
        
        Args:
            features: List of feature dictionaries
            
        Returns:
            Numpy array of features
            
        Raises:
            ValueError: If required features are missing
        """
        # Convert to numpy array
        feature_array = []
        for feature_dict in features:
            feature_vector = []
            for feature_name in self.feature_names:
                if feature_name not in feature_dict:
                    raise ValueError(f"Feature '{feature_name}' not found in input")
                feature_vector.append(feature_dict[feature_name])
            feature_array.append(feature_vector)
        
        return np.array(feature_array)
    
    def predict(self, features: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Make predictions on input features.
        
        Args:
            features: List of feature dictionaries
            
        Returns:
            Dictionary with predictions, scores, and statistics
            
        Raises:
            ValueError: If features are invalid
            RuntimeError: If prediction fails
        """
        try:
            # Preprocess features
            X = self.preprocess_features(features)
            
            # Scale features if scaler is available
            if self.scaler:
                X = self.scaler.transform(X)
            
            # Make predictions
            scores = -self.model.score_samples(X)
            predictions = (scores > self.threshold).astype(int)
            
            return {
                'predictions': predictions.tolist(),
                'scores': scores.tolist(),
                'threshold': self.threshold,
                'anomaly_count': int(predictions.sum()),
                'total_samples': len(predictions)
            }
        except Exception as e:
            raise RuntimeError(f"Prediction failed: {e}")

def main():
    """Example usage."""
    # Initialize inference
    inference = ModelInference()
    
    # Example features (replace with your actual data)
    sample_features = [
        {
            'auth_failure_ratio': 0.1,
            'deauth_ratio': 0.05,
            'beacon_ratio': 0.3,
            'unique_mac_count': 15,
            'unique_ssid_count': 8,
            'mean_signal_strength': -45.0,
            'std_signal_strength': 5.0,
            'mean_data_rate': 54.0,
            'mean_packet_loss': 0.02,
            'error_ratio': 0.01,
            'warning_ratio': 0.03,
            'mean_hour_of_day': 14.0,
            'mean_day_of_week': 3.0,
            'mean_time_between_events': 120.0,
            'total_devices': 25,
            'max_device_activity': 0.8,
            'mean_device_activity': 0.4
        }
    ]
    
    # Make prediction
    result = inference.predict(sample_features)
    
    print("🔍 Model Inference Example")
    print(f"Model Version: {inference.manifest['model_version']}")
    print(f"Threshold: {result['threshold']}")
    print(f"Predictions: {result['predictions']}")
    print(f"Scores: {result['scores']}")
    print(f"Anomalies detected: {result['anomaly_count']}/{result['total_samples']}")

if __name__ == "__main__":
    main()
