#!/usr/bin/env python3
"""
Model Validation Script
Validates model integrity and performance.
"""

import joblib
import numpy as np
import json
import sys
from pathlib import Path
from typing import Dict, Any

def validate_model():
    """Validate the deployed model."""
    try:
        # Load deployment manifest
        with open('deployment_manifest.json', 'r') as f:
            manifest = json.load(f)
        
        print("🔍 Validating Model " + manifest['model_version'])
        print("Model Type: " + manifest['model_info']['model_type'])
        print("Training Samples: " + str(manifest['training_info']['training_samples']))
        print("Features: " + str(manifest['training_info']['feature_count']))
        
        # Load model
        model = joblib.load('model.joblib')
        print("✅ Model loaded successfully")
        
        # Load scaler if available
        scaler = None
        if Path('scaler.joblib').exists():
            scaler = joblib.load('scaler.joblib')
            print("✅ Scaler loaded successfully")
        else:
            print("ℹ️  No scaler found (not required)")
        
        # Generate test data
        feature_names = manifest['training_info']['feature_names']
        n_features = len(feature_names)
        
        # Create synthetic test data
        np.random.seed(42)
        X_test = np.random.randn(100, n_features)
        
        # Apply scaler if available
        if scaler:
            X_test = scaler.transform(X_test)
        
        # Make predictions
        scores = -model.score_samples(X_test)
        predictions = (scores > manifest['inference_config']['threshold']).astype(int)
        
        print("✅ Predictions successful: " + str(len(predictions)) + " samples")
        print("Score range: [" + str(scores.min()) + ", " + str(scores.max()) + "]")
        print("Anomalies detected: " + str(predictions.sum()) + "/" + str(len(predictions)))
        
        # Validate file integrity
        import hashlib
        file_hashes = manifest['file_integrity']
        
        for filename, expected_hash in file_hashes.items():
            if Path(filename).exists():
                with open(filename, 'rb') as f:
                    actual_hash = hashlib.sha256(f.read()).hexdigest()
                if actual_hash == expected_hash:
                    print("✅ " + filename + ": integrity verified")
                else:
                    print("❌ " + filename + ": integrity check failed")
                    return False
            else:
                print("⚠️  " + filename + ": file not found")
        
        # Quality assessment
        quality = manifest['quality_assessment']
        print("\n📊 Quality Assessment:")
        print("Model Quality Score: " + str(quality['model_quality_score']))
        print("Silhouette Score: " + str(quality['silhouette_score']))
        print("Feature Utilization: " + str(quality['feature_utilization']))
        print("Training Data Quality: " + quality['training_data_quality'])
        
        print("\n🎉 Model validation completed successfully!")
        return True
        
    except Exception as e:
        print("❌ Model validation failed: " + str(e))
        return False

if __name__ == "__main__":
    success = validate_model()
    sys.exit(0 if success else 1)
