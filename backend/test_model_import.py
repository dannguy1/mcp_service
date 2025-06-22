#!/usr/bin/env python3
"""
Test script for model import functionality.
This script creates a test model package and verifies the import process.
"""

import os
import json
import zipfile
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy as np

def create_test_model_package():
    """Create a test model package for import testing."""
    
    # Create temporary directory for test model
    with tempfile.TemporaryDirectory() as temp_dir:
        model_dir = Path(temp_dir) / "test_model"
        model_dir.mkdir()
        
        # Create a simple IsolationForest model
        model = IsolationForest(contamination=0.1, random_state=42)
        X = np.random.randn(100, 5)  # 100 samples, 5 features
        model.fit(X)
        
        # Create a scaler
        scaler = StandardScaler()
        scaler.fit(X)
        
        # Save model and scaler
        joblib.dump(model, model_dir / "model.joblib")
        joblib.dump(scaler, model_dir / "scaler.joblib")
        
        # Create metadata.json
        metadata = {
            "model_type": "IsolationForest",
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "training_info": {
                "n_samples": 100,
                "n_features": 5,
                "feature_names": ["feature_1", "feature_2", "feature_3", "feature_4", "feature_5"],
                "training_date": datetime.now().isoformat()
            },
            "evaluation_info": {
                "basic_metrics": {
                    "f1_score": 0.85,
                    "roc_auc": 0.92,
                    "precision": 0.88,
                    "recall": 0.82
                }
            },
            "model_info": {
                "model_type": "IsolationForest",
                "version": "1.0.0",
                "parameters": {
                    "contamination": 0.1,
                    "random_state": 42
                }
            }
        }
        
        with open(model_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create deployment_manifest.json
        manifest = {
            "package_version": "1.0",
            "created_at": datetime.now().isoformat(),
            "model_type": "IsolationForest",
            "version": "1.0.0",
            "file_hashes": {}
        }
        
        # Calculate file hashes
        import hashlib
        for file_path in model_dir.glob("*"):
            if file_path.is_file():
                hash_sha256 = hashlib.sha256()
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_sha256.update(chunk)
                manifest["file_hashes"][file_path.name] = hash_sha256.hexdigest()
        
        with open(model_dir / "deployment_manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Create validate_model.py
        validate_script = '''#!/usr/bin/env python3
"""
Model validation script.
"""
import joblib
import json
import numpy as np
from pathlib import Path

def validate_model():
    """Validate the model package."""
    try:
        # Load model
        model = joblib.load("model.joblib")
        print("✓ Model loaded successfully")
        
        # Load scaler
        scaler = joblib.load("scaler.joblib")
        print("✓ Scaler loaded successfully")
        
        # Test prediction
        test_data = np.random.randn(10, 5)
        scaled_data = scaler.transform(test_data)
        predictions = model.predict(scaled_data)
        print(f"✓ Model predictions successful: {predictions}")
        
        # Load metadata
        with open("metadata.json", 'r') as f:
            metadata = json.load(f)
        print("✓ Metadata loaded successfully")
        
        print("\\nValidation completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Validation failed: {e}")
        return False

if __name__ == "__main__":
    validate_model()
'''
        
        with open(model_dir / "validate_model.py", 'w') as f:
            f.write(validate_script)
        
        # Create inference_example.py
        inference_script = '''#!/usr/bin/env python3
"""
Inference example for the model.
"""
import joblib
import numpy as np
from pathlib import Path

class ModelInference:
    def __init__(self, model_dir: str):
        self.model = joblib.load(Path(model_dir) / "model.joblib")
        self.scaler = joblib.load(Path(model_dir) / "scaler.joblib")
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """Make predictions on new data."""
        scaled_features = self.scaler.transform(features)
        return self.model.predict(scaled_features)
    
    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        """Get prediction probabilities."""
        scaled_features = self.scaler.transform(features)
        return self.model.decision_function(scaled_features)

# Example usage
if __name__ == "__main__":
    inference = ModelInference(".")
    test_data = np.random.randn(5, 5)
    predictions = inference.predict(test_data)
    print(f"Predictions: {predictions}")
'''
        
        with open(model_dir / "inference_example.py", 'w') as f:
            f.write(inference_script)
        
        # Create requirements.txt
        requirements = '''scikit-learn>=1.0.0
numpy>=1.20.0
joblib>=1.1.0
'''
        
        with open(model_dir / "requirements.txt", 'w') as f:
            f.write(requirements)
        
        # Create README.md
        readme = '''# Test Model Package

This is a test model package for anomaly detection.

## Usage

1. Load the model:
```python
from inference_example import ModelInference
inference = ModelInference(".")
```

2. Make predictions:
```python
import numpy as np
features = np.random.randn(10, 5)
predictions = inference.predict(features)
```

## Validation

Run the validation script:
```bash
python validate_model.py
```
'''
        
        with open(model_dir / "README.md", 'w') as f:
            f.write(readme)
        
        # Create ZIP package
        version = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"model_{version}_deployment.zip"
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in model_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(model_dir)
                    zipf.write(file_path, arcname)
        
        print(f"✓ Test model package created: {zip_filename}")
        return zip_filename

def test_model_import():
    """Test the model import functionality."""
    print("Creating test model package...")
    zip_filename = create_test_model_package()
    
    print(f"\\nTest model package created: {zip_filename}")
    print("\\nTo test the import functionality:")
    print("1. Start the MCP service")
    print("2. Use the frontend UI to upload the ZIP file")
    print("3. Or use curl to test the API:")
    print(f"   curl -X POST 'http://localhost:5000/api/v1/model-management/import' \\")
    print(f"        -F 'file=@{zip_filename}'")
    
    return zip_filename

if __name__ == "__main__":
    test_model_import() 