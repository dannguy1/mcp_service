#!/usr/bin/env python3
"""
Simple test script to verify the model import API endpoints.
"""

import requests
import json
import time

def test_model_import_api():
    """Test the model import API endpoints."""
    
    base_url = "http://localhost:5000/api/v1"
    
    print("Testing Model Import API Endpoints")
    print("=" * 40)
    
    # Test 1: List models
    print("\n1. Testing list models endpoint...")
    try:
        response = requests.get(f"{base_url}/model-management/models")
        if response.status_code == 200:
            models = response.json()
            print(f"✓ Successfully listed {len(models)} models")
            for model in models:
                print(f"   - {model.get('version', 'Unknown')}: {model.get('status', 'Unknown')}")
        else:
            print(f"✗ Failed to list models: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ Error listing models: {e}")
    
    # Test 2: Get model info (if models exist)
    print("\n2. Testing get model info endpoint...")
    try:
        response = requests.get(f"{base_url}/model-management/models")
        if response.status_code == 200:
            models = response.json()
            if models:
                model_version = models[0]['version']
                response = requests.get(f"{base_url}/model-management/models/{model_version}")
                if response.status_code == 200:
                    model_info = response.json()
                    print(f"✓ Successfully got info for model {model_version}")
                else:
                    print(f"✗ Failed to get model info: {response.status_code} - {response.text}")
            else:
                print("   No models available to test")
        else:
            print(f"✗ Failed to list models for testing: {response.status_code}")
    except Exception as e:
        print(f"✗ Error getting model info: {e}")
    
    # Test 3: Validate model (if models exist)
    print("\n3. Testing validate model endpoint...")
    try:
        response = requests.get(f"{base_url}/model-management/models")
        if response.status_code == 200:
            models = response.json()
            if models:
                model_version = models[0]['version']
                response = requests.post(f"{base_url}/model-management/{model_version}/validate")
                if response.status_code == 200:
                    validation_result = response.json()
                    print(f"✓ Successfully validated model {model_version}")
                    print(f"   Valid: {validation_result.get('is_valid', 'Unknown')}")
                else:
                    print(f"✗ Failed to validate model: {response.status_code} - {response.text}")
            else:
                print("   No models available to test")
        else:
            print(f"✗ Failed to list models for testing: {response.status_code}")
    except Exception as e:
        print(f"✗ Error validating model: {e}")
    
    print("\n" + "=" * 40)
    print("API Testing Complete!")
    print("\nTo test ZIP upload:")
    print("1. Create a test model package using: python test_model_import.py")
    print("2. Use the frontend UI or curl to upload the ZIP file")
    print("3. Check the models list again to see the imported model")

if __name__ == "__main__":
    test_model_import_api() 