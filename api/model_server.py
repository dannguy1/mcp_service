from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import asyncio
from datetime import datetime
import json
import os
import shutil
from prometheus_client import Counter, Histogram, Gauge
import numpy as np

from models.model_loader import ModelLoader
from models.training import ModelTrainer
from models.monitoring import ModelMonitor
from models.config import ModelConfig
from data_service import data_service
from components.data_service import DataService
from components.resource_monitor import ResourceMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="WiFi Anomaly Detection API",
    description="API for WiFi anomaly detection model serving and management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize model loader
model_loader = ModelLoader()

# Pydantic models for request/response
class PredictionRequest(BaseModel):
    logs: List[Dict]
    model_version: Optional[str] = None

class PredictionResponse(BaseModel):
    predictions: List[int]
    scores: List[float]
    model_version: str
    timestamp: str

class ModelInfo(BaseModel):
    version: str
    timestamp: str
    config: Dict
    feature_names: List[str]

class TrainingRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    config_path: Optional[str] = None

class TrainingResponse(BaseModel):
    model_path: str
    version: str
    timestamp: str

class ModelVersion(BaseModel):
    version: str
    created_at: datetime
    metrics: Dict[str, float]
    features: List[str]
    status: str

class ModelRollback(BaseModel):
    version: str
    reason: str

# Background task for model training
async def train_model_task(start_date: Optional[str], end_date: Optional[str], config_path: Optional[str]):
    try:
        # Load configuration
        if config_path:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        else:
            config = {}  # Use default config
        
        # Initialize trainer
        trainer = ModelTrainer(config)
        
        # Convert dates if provided
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        
        # Train model
        model_path = await trainer.train_and_save(start, end)
        logger.info(f"Model training completed: {model_path}")
        
    except Exception as e:
        logger.error(f"Error in model training: {e}")

@app.on_event("startup")
async def startup_event():
    """Load the latest model on startup."""
    try:
        model_loader.load_model()
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Error loading model: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "model_loaded": model_loader.model is not None}

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Make predictions on new data."""
    try:
        # Load specified model version if provided
        if request.model_version:
            model_loader.load_model(request.model_version)
        
        # Make predictions
        predictions, scores = await model_loader.predict(request.logs)
        
        return PredictionResponse(
            predictions=predictions.tolist(),
            scores=scores.tolist(),
            model_version=model_loader.metadata['version'],
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models", response_model=List[str])
async def list_models():
    """List available model versions."""
    return model_loader.list_models()

@app.get("/models/{version}", response_model=ModelInfo)
async def get_model_info(version: str):
    """Get information about a specific model version."""
    try:
        model_loader.load_model(version)
        return model_loader.get_model_info()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/train", response_model=TrainingResponse)
async def train_model(request: TrainingRequest, background_tasks: BackgroundTasks):
    """Start model training in background."""
    try:
        # Start training in background
        background_tasks.add_task(
            train_model_task,
            request.start_date,
            request.end_date,
            request.config_path
        )
        
        return TrainingResponse(
            model_path="Training started in background",
            version="pending",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Get model performance metrics."""
    try:
        # Get metrics from Prometheus
        metrics = {
            "predictions_total": data_service.metrics['predictions_total']._value.get(),
            "anomalies_detected": data_service.metrics['anomalies_detected']._value.get(),
            "prediction_latency": data_service.metrics['prediction_latency']._value.get(),
            "model_load_time": data_service.metrics['model_load_time']._value.get()
        }
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/versions", response_model=List[ModelVersion])
async def list_model_versions():
    """List all available model versions with their metadata."""
    try:
        versions = []
        model_dir = os.path.join(config.model_dir, "versions")
        if not os.path.exists(model_dir):
            return []
            
        for version in os.listdir(model_dir):
            version_path = os.path.join(model_dir, version)
            if os.path.isdir(version_path):
                metadata_path = os.path.join(version_path, "metadata.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        versions.append(ModelVersion(
                            version=version,
                            created_at=datetime.fromisoformat(metadata['created_at']),
                            metrics=metadata['metrics'],
                            features=metadata['features'],
                            status=metadata['status']
                        ))
        return sorted(versions, key=lambda x: x.created_at, reverse=True)
    except Exception as e:
        logger.error(f"Error listing model versions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/versions/{version}", response_model=ModelVersion)
async def get_model_version(version: str):
    """Get detailed information about a specific model version."""
    try:
        version_path = os.path.join(config.model_dir, "versions", version)
        if not os.path.exists(version_path):
            raise HTTPException(status_code=404, detail="Model version not found")
            
        metadata_path = os.path.join(version_path, "metadata.json")
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail="Model metadata not found")
            
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            return ModelVersion(
                version=version,
                created_at=datetime.fromisoformat(metadata['created_at']),
                metrics=metadata['metrics'],
                features=metadata['features'],
                status=metadata['status']
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model version: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/rollback")
async def rollback_model(rollback: ModelRollback, background_tasks: BackgroundTasks):
    """Rollback to a previous model version."""
    try:
        version_path = os.path.join(config.model_dir, "versions", rollback.version)
        if not os.path.exists(version_path):
            raise HTTPException(status_code=404, detail="Model version not found")
            
        # Create backup of current model
        current_model_path = os.path.join(config.model_dir, "current")
        backup_path = os.path.join(config.model_dir, "backups", f"backup_{datetime.now().isoformat()}")
        if os.path.exists(current_model_path):
            shutil.copytree(current_model_path, backup_path)
            
        # Copy selected version to current
        shutil.copytree(version_path, current_model_path, dirs_exist_ok=True)
        
        # Update metadata
        metadata_path = os.path.join(current_model_path, "metadata.json")
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        metadata['rollback_info'] = {
            'from_version': config.current_version,
            'to_version': rollback.version,
            'reason': rollback.reason,
            'timestamp': datetime.now().isoformat()
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        # Reload model in background
        background_tasks.add_task(reload_model)
        
        return {"message": f"Successfully rolled back to version {rollback.version}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rolling back model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/compare/{version1}/{version2}")
async def compare_models(version1: str, version2: str):
    """Compare two model versions."""
    try:
        v1_path = os.path.join(config.model_dir, "versions", version1)
        v2_path = os.path.join(config.model_dir, "versions", version2)
        
        if not os.path.exists(v1_path) or not os.path.exists(v2_path):
            raise HTTPException(status_code=404, detail="One or both model versions not found")
            
        # Load metadata for both versions
        with open(os.path.join(v1_path, "metadata.json"), 'r') as f:
            v1_metadata = json.load(f)
        with open(os.path.join(v2_path, "metadata.json"), 'r') as f:
            v2_metadata = json.load(f)
            
        # Compare metrics
        metrics_diff = {}
        for metric in set(v1_metadata['metrics'].keys()) | set(v2_metadata['metrics'].keys()):
            v1_value = v1_metadata['metrics'].get(metric, 0)
            v2_value = v2_metadata['metrics'].get(metric, 0)
            metrics_diff[metric] = {
                'version1': v1_value,
                'version2': v2_value,
                'difference': v2_value - v1_value
            }
            
        # Compare features
        features_diff = {
            'common': list(set(v1_metadata['features']) & set(v2_metadata['features'])),
            'only_in_v1': list(set(v1_metadata['features']) - set(v2_metadata['features'])),
            'only_in_v2': list(set(v2_metadata['features']) - set(v1_metadata['features']))
        }
        
        return {
            "version1": version1,
            "version2": version2,
            "metrics_comparison": metrics_diff,
            "features_comparison": features_diff,
            "created_at_diff": {
                "version1": v1_metadata['created_at'],
                "version2": v2_metadata['created_at']
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 