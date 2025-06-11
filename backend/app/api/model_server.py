from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import logging
import asyncio
from datetime import datetime
import json
import os
import shutil
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client.openmetrics.exposition import generate_latest as generate_latest_openmetrics
import numpy as np
import yaml
from pathlib import Path

from app.models.model_loader import ModelLoader
from app.models.training import ModelTrainer
from app.models.monitoring import ModelMonitor
from app.models.config import ModelConfig
from app.components.data_service import DataService
from app.components.resource_monitor import ResourceMonitor
from app.components.feature_extractor import FeatureExtractor
from app.config import config

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

# Load configuration
config = ModelConfig.from_yaml("app/config/model_config.yaml")

# Initialize components
model_loader = ModelLoader(config)
model_monitor = ModelMonitor()

# Pydantic models for request/response
class PredictionRequest(BaseModel):
    """Request model for prediction endpoint."""
    data: List[Dict]

class PredictionResponse(BaseModel):
    """Response model for prediction endpoint."""
    predictions: List[float]
    anomalies: List[bool]
    confidence: List[float]

class TrainingRequest(BaseModel):
    """Request model for training endpoint."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class TrainingResponse(BaseModel):
    """Response model for training endpoint."""
    status: str
    message: str
    model_version: Optional[str] = None

class ModelVersion(BaseModel):
    """Model for model version information."""
    version: str
    created_at: str
    metrics: Dict[str, float]

class ModelRollback(BaseModel):
    """Request model for rollback endpoint."""
    version: str

class ModelCompare(BaseModel):
    """Request model for model comparison."""
    version1: str
    version2: str

# Background task for model training
async def train_model_task(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Background task for model training."""
    try:
        # Load configuration
        model_config = ModelConfig()
        
        # Initialize trainer
        trainer = ModelTrainer(model_config)
        
        # Train model
        model, metrics = await trainer.train(start_date, end_date)
        
        # Save model
        if model_loader.save_model(model, model_config, {
            "version": model_config.model_version,
            "type": model_config.model_type,
            "created_at": datetime.now().isoformat(),
            "metrics": metrics
        }):
            logger.info(f"Model training completed successfully. Version: {model_config.model_version}")
        else:
            logger.error("Failed to save trained model")
            
    except Exception as e:
        logger.error(f"Error in model training task: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup."""
    try:
        # Load latest model
        if not model_loader.load_latest_model():
            logger.warning("No model loaded. Please train a model first.")
            
        # Initialize monitoring
        await model_monitor.initialize()
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": model_loader.model is not None,
        "monitoring_active": model_monitor.is_initialized()
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Make predictions using the loaded model."""
    try:
        if model_loader.model is None:
            raise HTTPException(
                status_code=503,
                detail="No model loaded. Please train a model first."
            )
            
        # Extract features
        features = await model_loader.predict_new_data(request.data)
        
        # Make predictions
        predictions = model_loader.predict(features)
        
        # Convert predictions to anomaly scores and labels
        anomaly_scores = 1 - predictions  # Convert to anomaly scores
        anomalies = anomaly_scores > 0.5  # Threshold for anomaly detection
        
        # Update monitoring metrics
        await model_monitor.update_metrics(predictions)
        
        return PredictionResponse(
            predictions=anomaly_scores.tolist(),
            anomalies=anomalies.tolist(),
            confidence=[1.0 - abs(score - 0.5) * 2 for score in anomaly_scores]  # Confidence based on distance from threshold
        )
        
    except Exception as e:
        logger.error(f"Error making predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/train")
async def train_model(
    request: Request,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Train a new model version."""
    try:
        # Initialize trainer
        trainer = ModelTrainer(config)
        
        # Train model in background
        background_tasks.add_task(train_model_async, trainer, config)
        
        return {
            "status": "training_started",
            "message": "Model training started in background",
            "config": config.model_dump()
        }
        
    except Exception as e:
        logger.error(f"Error starting model training: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error starting model training: {str(e)}"
        )

async def train_model_async(trainer: ModelTrainer, config: ModelConfig):
    """Background task for model training."""
    try:
        # Train model
        model = await trainer.train()
        
        # Save model
        if model_loader.save_model(model):
            logger.info("Model training completed successfully")
        else:
            logger.error("Failed to save trained model")
            
    except Exception as e:
        logger.error(f"Error in model training: {e}")

@app.get("/models", response_model=List[ModelVersion])
async def list_models():
    """List available model versions."""
    try:
        versions = []
        model_dir = os.path.join(config.MODEL_DIR, "versions")
        if not os.path.exists(model_dir):
            return []
            
        for version in os.listdir(model_dir):
            if version.endswith('.joblib'):
                metadata_path = os.path.join(model_dir, f"{version[:-7]}_metadata.yaml")
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = yaml.safe_load(f)
                        versions.append(ModelVersion(
                            version=metadata['version'],
                            created_at=metadata['created_at'],
                            metrics=metadata['metrics']
                        ))
        
        return sorted(versions, key=lambda x: x.created_at, reverse=True)
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/{version}", response_model=ModelVersion)
async def get_model_info(version: str):
    """Get detailed information about a specific model version."""
    try:
        version_path = os.path.join(config.MODEL_DIR, "versions", version)
        if not os.path.exists(version_path):
            raise HTTPException(status_code=404, detail="Model version not found")
            
        metadata_path = os.path.join(config.MODEL_DIR, "versions", f"{version}_metadata.yaml")
        if not os.path.exists(metadata_path):
            raise HTTPException(status_code=404, detail="Model metadata not found")
            
        with open(metadata_path, 'r') as f:
            metadata = yaml.safe_load(f)
            return ModelVersion(
                version=metadata['version'],
                created_at=metadata['created_at'],
                metrics=metadata['metrics']
            )
            
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/rollback", response_model=TrainingResponse)
async def rollback_model(rollback: ModelRollback):
    """Rollback to a previous model version."""
    try:
        version_path = os.path.join(config.MODEL_DIR, "versions", rollback.version)
        if not os.path.exists(version_path):
            raise HTTPException(status_code=404, detail="Model version not found")
            
        # Create backup of current model
        current_model_path = os.path.join(config.MODEL_DIR, "current")
        backup_path = os.path.join(config.MODEL_DIR, "backups", f"backup_{datetime.now().isoformat()}")
        if os.path.exists(current_model_path):
            shutil.copytree(current_model_path, backup_path)
            
        # Copy selected version to current
        shutil.copytree(version_path, current_model_path)
        
        # Reload model
        if not model_loader.load_model(Path(version_path)):
            raise HTTPException(status_code=500, detail="Failed to load rolled back model")
            
        return TrainingResponse(
            status="success",
            message=f"Successfully rolled back to version {rollback.version}",
            model_version=rollback.version
        )
        
    except Exception as e:
        logger.error(f"Error rolling back model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/models/compare")
async def compare_models(compare: ModelCompare):
    """Compare two model versions."""
    try:
        v1_path = os.path.join(config.MODEL_DIR, "versions", compare.version1)
        v2_path = os.path.join(config.MODEL_DIR, "versions", compare.version2)
        
        if not os.path.exists(v1_path) or not os.path.exists(v2_path):
            raise HTTPException(status_code=404, detail="One or both model versions not found")
            
        # Load metadata for both versions
        v1_metadata = {}
        v2_metadata = {}
        
        v1_metadata_path = os.path.join(config.MODEL_DIR, "versions", f"{compare.version1}_metadata.yaml")
        v2_metadata_path = os.path.join(config.MODEL_DIR, "versions", f"{compare.version2}_metadata.yaml")
        
        if os.path.exists(v1_metadata_path):
            with open(v1_metadata_path, 'r') as f:
                v1_metadata = yaml.safe_load(f)
                
        if os.path.exists(v2_metadata_path):
            with open(v2_metadata_path, 'r') as f:
                v2_metadata = yaml.safe_load(f)
                
        # Compare metrics
        comparison = {
            "version1": {
                "version": compare.version1,
                "created_at": v1_metadata.get("created_at", "unknown"),
                "metrics": v1_metadata.get("metrics", {})
            },
            "version2": {
                "version": compare.version2,
                "created_at": v2_metadata.get("created_at", "unknown"),
                "metrics": v2_metadata.get("metrics", {})
            },
            "differences": {}
        }
        
        # Calculate metric differences
        for metric in set(v1_metadata.get("metrics", {}).keys()) | set(v2_metadata.get("metrics", {}).keys()):
            v1_value = v1_metadata.get("metrics", {}).get(metric, 0)
            v2_value = v2_metadata.get("metrics", {}).get(metric, 0)
            comparison["differences"][metric] = v2_value - v1_value
            
        return comparison
        
    except Exception as e:
        logger.error(f"Error comparing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Get current monitoring metrics."""
    try:
        return await model_monitor.get_metrics()
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting metrics: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 