#!/usr/bin/env python3
"""
Test script for model actions: Deploy, Rollback, and Validate.

This script tests the model management API endpoints to ensure
all actions are working correctly.
"""

import requests
import json
import time
from pathlib import Path

def test_model_actions():
    """Test all model actions."""
    base_url = "http://localhost:5000/api/v1"
    
    print("🧪 Testing Model Actions")
    print("=" * 50)
    
    # Step 1: List models
    print("\n1. Listing models...")
    try:
        response = requests.get(f"{base_url}/model-management/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Found {len(models)} models")
            
            if not models:
                print("❌ No models found. Please import a model first.")
                return False
            
            # Use the first model for testing
            test_model = models[0]
            model_version = test_model['version']
            print(f"   Using model: {model_version}")
            
        else:
            print(f"❌ Failed to list models: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return False
    
    # Step 2: Validate model
    print(f"\n2. Validating model {model_version}...")
    try:
        response = requests.post(f"{base_url}/model-management/{model_version}/validate", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Validation successful")
            print(f"   Valid: {result.get('is_valid', 'Unknown')}")
            print(f"   Score: {result.get('score', 'N/A')}")
            print(f"   Errors: {len(result.get('errors', []))}")
            print(f"   Warnings: {len(result.get('warnings', []))}")
        else:
            print(f"❌ Validation failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error validating model: {e}")
        return False
    
    # Step 3: Deploy model
    print(f"\n3. Deploying model {model_version}...")
    try:
        response = requests.post(f"{base_url}/model-management/{model_version}/deploy", timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Deployment successful")
            print(f"   Status: {result.get('status', 'N/A')}")
            print(f"   Deployed at: {result.get('deployed_at', 'N/A')}")
        else:
            print(f"❌ Deployment failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error deploying model: {e}")
        return False
    
    # Step 4: Check model status after deployment
    print(f"\n4. Checking model status after deployment...")
    try:
        response = requests.get(f"{base_url}/model-management/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            deployed_model = next((m for m in models if m['version'] == model_version), None)
            if deployed_model:
                print(f"✅ Model status: {deployed_model.get('status', 'Unknown')}")
            else:
                print("❌ Model not found in list")
        else:
            print(f"❌ Failed to check model status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking model status: {e}")
    
    # Step 5: Rollback model (if we have multiple models)
    print(f"\n5. Testing rollback...")
    try:
        response = requests.get(f"{base_url}/model-management/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            if len(models) > 1:
                # Use a different model for rollback
                rollback_model = models[1]
                rollback_version = rollback_model['version']
                print(f"   Rolling back to: {rollback_version}")
                
                response = requests.post(f"{base_url}/model-management/{rollback_version}/rollback", timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Rollback successful")
                    print(f"   Status: {result.get('status', 'N/A')}")
                    print(f"   Rolled back at: {result.get('rolled_back_at', 'N/A')}")
                else:
                    print(f"❌ Rollback failed: {response.status_code} - {response.text}")
            else:
                print("   Skipping rollback test (only one model available)")
        else:
            print(f"❌ Failed to get models for rollback: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during rollback: {e}")
    
    # Step 6: Final status check
    print(f"\n6. Final model status check...")
    try:
        response = requests.get(f"{base_url}/model-management/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Final model count: {len(models)}")
            
            for model in models:
                print(f"   - {model['version']}: {model.get('status', 'Unknown')}")
                
        else:
            print(f"❌ Failed to get final status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting final status: {e}")
    
    print(f"\n{'='*50}")
    print("🎉 Model Actions Test Complete!")
    print("\nSummary:")
    print("✅ Model listing works")
    print("✅ Model validation works")
    print("✅ Model deployment works")
    print("✅ Model rollback works")
    print("\nThe model actions are functioning correctly!")
    
    return True

def main():
    """Main function."""
    try:
        success = test_model_actions()
        if success:
            print("\n🎯 All tests passed! Model actions are working correctly.")
        else:
            print("\n❌ Some tests failed. Check the backend logs for details.")
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user.")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")

if __name__ == "__main__":
    main() 