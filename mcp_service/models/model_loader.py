from typing import Optional, Dict, Any
import os
import logging
import joblib
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    model_config = {
        'protected_namespaces': ()
    }
    model_version: str = Field(default="1.0.0")
    model_type: str
    model_path: str
    model_params: Dict[str, Any] = Field(default_factory=dict)

class ModelLoader:
    def __init__(self, model_dir: str = "/app/models"):
        self.logger = logging.getLogger(__name__)
        self.model_dir = model_dir
        self.model = None
        self.config = None
        self._load_model()

    def _load_model(self):
        """Load the latest model from the model directory."""
        try:
            # Find all model files
            model_files = [f for f in os.listdir(self.model_dir) 
                         if f.endswith('.joblib')]
            
            if not model_files:
                self.logger.warning("No model files found")
                return
            
            # Get the latest model file
            latest_model = max(model_files, key=lambda x: os.path.getctime(
                os.path.join(self.model_dir, x)))
            
            model_path = os.path.join(self.model_dir, latest_model)
            self.model = joblib.load(model_path)
            
            # Load config if exists
            config_path = os.path.join(self.model_dir, 'model_config.json')
            if os.path.exists(config_path):
                self.config = ModelConfig.model_validate_json(
                    open(config_path).read())
            
            self.logger.info(f"Loaded model from {model_path}")
            
        except Exception as e:
            self.logger.error(f"Error loading model: {e}")
            self.model = None

    def predict(self, features: Dict[str, Any]) -> Optional[float]:
        """Make a prediction using the loaded model."""
        if self.model is None:
            self.logger.warning("No model loaded")
            return None
        
        try:
            # Convert features to model input format
            X = self._prepare_features(features)
            prediction = self.model.predict_proba(X)[0][1]
            return float(prediction)
        except Exception as e:
            self.logger.error(f"Error making prediction: {e}")
            return None

    def _prepare_features(self, features: Dict[str, Any]) -> Any:
        """Prepare features for model input."""
        # Extract features in the correct order
        feature_vector = [
            features['auth_failures'],
            features['deauth_count'],
            features['beacon_count'],
            features['unique_mac_count'],
            features['unique_ssid_count']
        ]
        
        # Add reason code counts
        for code in range(1, 18):  # Common WiFi reason codes
            feature_vector.append(
                features['reason_codes'].get(str(code), 0)
            )
        
        # Add status code counts
        for code in range(1, 18):  # Common WiFi status codes
            feature_vector.append(
                features['status_codes'].get(str(code), 0)
            )
        
        return [feature_vector]  # Return as 2D array for sklearn 