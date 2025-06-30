#!/usr/bin/env python3
"""
Model Validation Script for 20250630_114348
Validates model integrity and basic functionality.
"""

import sys
import json
import hashlib
import joblib
import numpy as np
from pathlib import Path

def calculate_file_hash(filepath):
    """Calculate SHA256 hash of a file."""
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def validate_model():
    """Validate the deployed model."""
    print("🔍 Validating model deployment...")
    
    # Load deployment manifest
    try:
        with open('deployment_manifest.json', 'r') as f:
            manifest = json.load(f)
    except FileNotFoundError:
        print("❌ deployment_manifest.json not found")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid deployment_manifest.json: {e}")
        return False
    
    # Validate file integrity
    print("📁 Checking file integrity...")
    for filename, expected_hash in manifest['file_integrity'].items():
        if Path(filename).exists():
            actual_hash = calculate_file_hash(filename)
            if actual_hash == expected_hash:
                print(f"✅ {filename}: OK")
            else:
                print(f"❌ {filename}: Hash mismatch!")
                print(f"   Expected: {expected_hash}")
                print(f"   Actual:   {actual_hash}")
                return False
        else:
            print(f"⚠️  {filename}: File not found")
            # Don't fail for optional files like scaler.joblib
            if filename != 'scaler.joblib':
                return False
    
    # Load and validate model
    print("🤖 Loading model...")
    try:
        model = joblib.load('model.joblib')
        print("✅ Model loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return False
    
    # Load scaler if available
    scaler = None
    if Path('scaler.joblib').exists():
        try:
            scaler = joblib.load('scaler.joblib')
            print("✅ Scaler loaded successfully")
        except Exception as e:
            print(f"⚠️  Failed to load scaler: {e}")
    
    # Test with sample data
    print("🧪 Testing model inference...")
    try:
        feature_names = manifest['training_info']['feature_names']
        n_features = len(feature_names)
        
        # Create sample data
        sample_data = np.random.randn(10, n_features)
        
        # Scale if scaler is available
        if scaler:
            sample_data = scaler.transform(sample_data)
        
        # Make predictions
        scores = -model.score_samples(sample_data)
        predictions = (scores > manifest['inference_config']['threshold']).astype(int)
        
        print(f"✅ Inference test successful")
        print(f"   Sample predictions: {predictions[:5].tolist()}")
        print(f"   Score range: {scores.min():.3f} to {scores.max():.3f}")
        
    except Exception as e:
        print(f"❌ Inference test failed: {e}")
        return False
    
    print("🎉 Model validation completed successfully!")
    return True

if __name__ == "__main__":
    success = validate_model()
    sys.exit(0 if success else 1)
