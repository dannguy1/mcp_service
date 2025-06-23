#!/usr/bin/env python3
"""
Test script for model upload functionality
"""
import requests
import os
import tempfile
import zipfile
import json
import joblib
from sklearn.ensemble import RandomForestClassifier
import numpy as np

def create_test_model_package():
    """Create a test model package ZIP file"""
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
        with zipfile.ZipFile(tmp_file.name, 'w') as zip_ref:
            # Create a proper test model
            model = RandomForestClassifier(n_estimators=10, random_state=42)
            # Train on dummy data
            X = np.random.rand(100, 5)
            y = np.random.randint(0, 2, 100)
            model.fit(X, y)
            
            # Save model to temporary file
            with tempfile.NamedTemporaryFile(suffix='.joblib', delete=False) as model_file:
                joblib.dump(model, model_file.name)
                with open(model_file.name, 'rb') as f:
                    model_data = f.read()
                os.unlink(model_file.name)
            
            # Create test files
            test_files = {
                'model.joblib': model_data,
                'metadata.json': json.dumps({
                    'model_type': 'RandomForestClassifier',
                    'version': '1.0.0',
                    'created_at': '2024-01-01T00:00:00Z',
                    'training_info': {'accuracy': 0.95}
                }).encode(),
                'deployment_manifest.json': json.dumps({
                    'version': '1.0.0',
                    'file_hashes': {}
                }).encode(),
                'validate_model.py': b'def validate(): pass',
                'inference_example.py': b'def predict(): pass',
                'requirements.txt': b'scikit-learn==1.0.0\njoblib==1.0.0',
                'README.md': b'Test model package'
            }
            
            for filename, content in test_files.items():
                zip_ref.writestr(filename, content)
        
        return tmp_file.name

def test_model_upload():
    """Test the model upload endpoint"""
    # Create test model package
    zip_path = create_test_model_package()
    
    try:
        # Test the upload endpoint
        url = "http://localhost:5000/api/v1/model-management/import"
        
        with open(zip_path, 'rb') as f:
            files = {'file': ('model_1.0.0_deployment.zip', f, 'application/zip')}
            data = {'validate': 'true'}
            
            print(f"Uploading to: {url}")
            response = requests.post(url, files=files, data=data)
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response body: {response.text}")
            
            if response.status_code == 200:
                print("✅ Upload successful!")
            else:
                print("❌ Upload failed!")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Cleanup
        if os.path.exists(zip_path):
            os.unlink(zip_path)

if __name__ == "__main__":
    test_model_upload() 