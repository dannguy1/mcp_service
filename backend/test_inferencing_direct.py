#!/usr/bin/env python3
"""
Direct Test Script for Inferencing Functionality

This script tests the inferencing functionality directly without going through the API.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.components.model_manager import ModelManager
from app.models.config import ModelConfig
import asyncio
import numpy as np

async def test_inferencing():
    """Test the inferencing functionality directly."""
    
    print("Testing Inferencing Functionality Directly")
    print("=" * 50)
    
    # Initialize model manager
    config = ModelConfig()
    model_manager = ModelManager(config)
    
    print(f"Models directory: {model_manager.models_directory}")
    print(f"Registry file: {model_manager.model_registry_file}")
    
    # List models
    print("\n1. Listing models...")
    models = await model_manager.list_models()
    print(f"Found {len(models)} models:")
    for model in models:
        print(f"  - {model['version']}: {model['status']}")
    
    if not models:
        print("No models found!")
        return False
    
    # Load the first model
    test_model = models[0]
    version = test_model['version']
    
    print(f"\n2. Loading model version: {version}")
    success = await model_manager.load_model_version(version)
    if success:
        print("✓ Model loaded successfully")
    else:
        print("✗ Failed to load model")
        return False
    
    # Check if model is loaded
    print(f"\n3. Checking model status...")
    is_loaded = model_manager.is_model_loaded()
    print(f"Model loaded: {is_loaded}")
    
    if is_loaded:
        model_info = model_manager.get_model_info()
        print(f"Model info: {model_info}")
    
    # Test prediction
    print(f"\n4. Testing prediction...")
    if is_loaded:
        # Create sample test data
        test_data = np.array([
            [-65, 25, 0.1, 3600, 15, 2],  # Normal data
            [-70, 30, 0.2, 3600, 18, 5],  # Normal data
            [10, 100, 0.8, 100, 50, 20],  # Anomalous data
        ])
        
        try:
            predictions = await model_manager.predict(test_data)
            probabilities = await model_manager.predict_proba(test_data)
            
            print("✓ Prediction successful")
            print("Results:")
            for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
                status = "ANOMALY" if pred == -1 else "NORMAL"
                print(f"  Sample {i+1}: {status} (score: {prob[0]:.4f})")
            
            return True
            
        except Exception as e:
            print(f"✗ Prediction failed: {e}")
            return False
    else:
        print("✗ No model loaded for prediction")
        return False

def main():
    """Main test function."""
    try:
        result = asyncio.run(test_inferencing())
        if result:
            print("\n✅ Inferencing functionality test PASSED!")
        else:
            print("\n❌ Inferencing functionality test FAILED!")
            return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 