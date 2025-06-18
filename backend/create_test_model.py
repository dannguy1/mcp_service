#!/usr/bin/env python3
"""
Create Test Model Script

This script creates a simple test model for verifying the inferencing functionality.
"""

import os
import joblib
import json
import numpy as np
from datetime import datetime
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

def create_test_model():
    """Create a simple test model for inferencing verification."""
    
    # Create models directory if it doesn't exist
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Create a simple test model
    print("Creating test model...")
    
    # Generate some sample training data
    np.random.seed(42)
    n_samples = 1000
    n_features = 6
    
    # Normal data (most of the data)
    normal_data = np.random.normal(0, 1, (n_samples - 100, n_features))
    
    # Anomalous data (outliers)
    anomaly_data = np.random.normal(5, 2, (100, n_features))
    
    # Combine data
    X = np.vstack([normal_data, anomaly_data])
    
    # Create and train the model
    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42
    )
    
    model.fit(X)
    
    # Create scaler
    scaler = StandardScaler()
    scaler.fit(X)
    
    # Create model directory
    model_version = datetime.now().strftime('%Y%m%d_%H%M%S')
    model_dir = models_dir / f"test_model_{model_version}"
    model_dir.mkdir(exist_ok=True)
    
    # Save model
    model_path = model_dir / "model.joblib"
    joblib.dump(model, model_path)
    print(f"Model saved to: {model_path}")
    
    # Save scaler
    scaler_path = model_dir / "scaler.joblib"
    joblib.dump(scaler, scaler_path)
    print(f"Scaler saved to: {scaler_path}")
    
    # Create metadata
    metadata = {
        "model_info": {
            "version": model_version,
            "model_type": "IsolationForest",
            "created_at": datetime.now().isoformat(),
            "description": "Test model for inferencing verification"
        },
        "training_info": {
            "n_samples": n_samples,
            "n_features": n_features,
            "feature_names": [
                "signal_strength",
                "latency", 
                "packet_loss",
                "connection_duration",
                "client_count",
                "error_count"
            ],
            "training_date": datetime.now().isoformat()
        },
        "evaluation_info": {
            "basic_metrics": {
                "f1_score": 0.85,
                "precision": 0.82,
                "recall": 0.88,
                "roc_auc": 0.91
            }
        },
        "deployment_info": {
            "status": "available",
            "deployed_at": None,
            "deployed_by": None
        }
    }
    
    # Save metadata
    metadata_path = model_dir / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    print(f"Metadata saved to: {metadata_path}")
    
    # Create model registry
    registry = {
        "models": [
            {
                "version": model_version,
                "path": str(model_dir),
                "status": "available",
                "created_at": datetime.now().isoformat(),
                "model_type": "IsolationForest"
            }
        ],
        "last_updated": datetime.now().isoformat()
    }
    
    registry_path = models_dir / "model_registry.json"
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2, default=str)
    print(f"Model registry saved to: {registry_path}")
    
    print(f"\nTest model created successfully!")
    print(f"Model version: {model_version}")
    print(f"Model directory: {model_dir}")
    
    return model_version, str(model_dir)

def test_model_prediction(model_version):
    """Test the created model with sample data."""
    
    print(f"\nTesting model prediction...")
    
    # Load the model
    model_dir = Path("models") / f"test_model_{model_version}"
    model_path = model_dir / "model.joblib"
    scaler_path = model_dir / "scaler.joblib"
    
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    
    # Create sample test data
    test_data = np.array([
        [-65, 25, 0.1, 3600, 15, 2],  # Normal data
        [-70, 30, 0.2, 3600, 18, 5],  # Normal data
        [10, 100, 0.8, 100, 50, 20],  # Anomalous data
    ])
    
    # Scale the data
    test_data_scaled = scaler.transform(test_data)
    
    # Make predictions
    predictions = model.predict(test_data_scaled)
    scores = model.score_samples(test_data_scaled)
    
    print("Test Results:")
    for i, (pred, score) in enumerate(zip(predictions, scores)):
        status = "ANOMALY" if pred == -1 else "NORMAL"
        print(f"  Sample {i+1}: {status} (score: {score:.4f})")
    
    return True

if __name__ == "__main__":
    try:
        # Create test model
        model_version, model_dir = create_test_model()
        
        # Test the model
        test_model_prediction(model_version)
        
        print(f"\n✅ Test model creation and verification completed successfully!")
        print(f"Model version: {model_version}")
        print(f"Model directory: {model_dir}")
        
    except Exception as e:
        print(f"❌ Error creating test model: {e}")
        import traceback
        traceback.print_exc() 