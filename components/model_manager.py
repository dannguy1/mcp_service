import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
from prometheus_client import Counter, Gauge, Histogram
from sklearn.ensemble import IsolationForest

from config import settings

logger = logging.getLogger(__name__)

# Prometheus metrics
MODEL_LOAD_TIME = Histogram(
    'model_load_seconds',
    'Time spent loading models'
)
MODEL_PREDICTION_TIME = Histogram(
    'model_prediction_seconds',
    'Time spent making predictions'
)
MODEL_VERSION = Gauge(
    'model_version',
    'Current model version',
    ['model_type']
)
MODEL_PREDICTIONS = Counter(
    'model_predictions_total',
    'Number of predictions made',
    ['model_type', 'result']
)

class ModelManager:
    """Component for managing ML models."""
    
    def __init__(self):
        self._models: Dict[str, IsolationForest] = {}
        self._model_versions: Dict[str, str] = {}
        self._model_dir = Path(settings.MODEL_DIR)
        self._model_dir.mkdir(parents=True, exist_ok=True)
    
    def load_model(self, model_type: str, version: str) -> bool:
        """Load a model from disk."""
        try:
            with MODEL_LOAD_TIME.time():
                model_path = self._model_dir / f"{model_type}_{version}.joblib"
                if not model_path.exists():
                    logger.error(f"Model file not found: {model_path}")
                    return False
                
                model = joblib.load(model_path)
                self._models[model_type] = model
                self._model_versions[model_type] = version
                MODEL_VERSION.labels(model_type).set(float(version))
                logger.info(f"Loaded {model_type} model version {version}")
                return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def save_model(self, model_type: str, model: IsolationForest, version: str) -> bool:
        """Save a model to disk."""
        try:
            model_path = self._model_dir / f"{model_type}_{version}.joblib"
            joblib.dump(model, model_path)
            
            # Update database
            self._update_model_version(model_type, version)
            
            logger.info(f"Saved {model_type} model version {version}")
            return True
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False
    
    def predict(self, model_type: str, features: np.ndarray) -> Tuple[bool, float]:
        """Make a prediction using the specified model."""
        if model_type not in self._models:
            raise ValueError(f"Model {model_type} not loaded")
        
        try:
            with MODEL_PREDICTION_TIME.time():
                model = self._models[model_type]
                prediction = model.predict(features.reshape(1, -1))
                score = model.score_samples(features.reshape(1, -1))
                
                is_anomaly = prediction[0] == -1
                confidence = float(score[0])
                
                MODEL_PREDICTIONS.labels(
                    model_type=model_type,
                    result='anomaly' if is_anomaly else 'normal'
                ).inc()
                
                return is_anomaly, confidence
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            raise
    
    def train_model(
        self,
        model_type: str,
        features: np.ndarray,
        contamination: float = 0.1
    ) -> Optional[IsolationForest]:
        """Train a new model."""
        try:
            model = IsolationForest(
                n_estimators=100,
                contamination=contamination,
                random_state=42
            )
            model.fit(features)
            return model
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return None
    
    async def _update_model_version(self, model_type: str, version: str) -> None:
        """Update model version in the database."""
        try:
            query = """
                INSERT INTO model_versions (version, is_active, performance_metrics)
                VALUES ($1, true, $2)
                ON CONFLICT (version) DO UPDATE
                SET is_active = true,
                    performance_metrics = $2
            """
            metrics = {
                'version': version,
                'created_at': datetime.utcnow().isoformat(),
                'model_type': model_type
            }
            await data_service.execute_query(query, version, json.dumps(metrics))
        except Exception as e:
            logger.error(f"Error updating model version: {e}")
            raise
    
    def get_active_version(self, model_type: str) -> Optional[str]:
        """Get the currently active model version."""
        return self._model_versions.get(model_type)
    
    def list_available_models(self) -> List[str]:
        """List all available model types."""
        return list(self._models.keys())
    
    def list_available_versions(self, model_type: str) -> List[str]:
        """List all available versions for a model type."""
        versions = []
        for file in self._model_dir.glob(f"{model_type}_*.joblib"):
            version = file.stem.split('_')[1]
            versions.append(version)
        return sorted(versions)
