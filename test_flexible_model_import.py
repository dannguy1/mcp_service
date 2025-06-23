#!/usr/bin/env python3
"""
Test script for flexible model import functionality.

This script demonstrates the improved model import system that distinguishes
between required and optional components. It creates test model packages with
varying levels of completeness to show how the system handles different scenarios.
"""

import os
import json
import zipfile
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

def create_test_model():
    """Create a simple test model for demonstration."""
    # Create synthetic data
    np.random.seed(42)
    X = np.random.randn(1000, 5)
    
    # Create and train model
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(X)
    
    return model

def create_metadata():
    """Create sample metadata for the model."""
    return {
        "model_info": {
            "model_type": "IsolationForest",
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "description": "Test model for flexible import validation"
        },
        "training_info": {
            "feature_names": ["feature_1", "feature_2", "feature_3", "feature_4", "feature_5"],
            "training_samples": 1000,
            "contamination": 0.1
        },
        "evaluation_info": {
            "basic_metrics": {
                "f1_score": 0.85,
                "roc_auc": 0.92,
                "precision": 0.88,
                "recall": 0.82
            }
        }
    }

def create_deployment_manifest(files):
    """Create deployment manifest with file hashes."""
    import hashlib
    
    file_hashes = {}
    for file_path in files:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
                file_hashes[os.path.basename(file_path)] = file_hash
    
    return {
        "version": "1.0.0",
        "created_at": datetime.now().isoformat(),
        "file_hashes": file_hashes,
        "total_files": len(file_hashes)
    }

def create_optional_files():
    """Create optional files for the model package."""
    files = {}
    
    # requirements.txt
    files["requirements.txt"] = """scikit-learn>=1.0.0
numpy>=1.20.0
joblib>=1.1.0
pandas>=1.3.0
"""
    
    # README.md
    files["README.md"] = """# Test Model Package

This is a test model package for demonstrating flexible import validation.

## Usage

```python
import joblib
model = joblib.load('model.joblib')
predictions = model.predict(data)
```

## Model Information

- Type: IsolationForest
- Features: 5
- Training samples: 1000
- Contamination: 0.1
"""
    
    # validate_model.py
    files["validate_model.py"] = """#!/usr/bin/env python3
\"\"\"
Model validation script.
\"\"\"

import joblib
import numpy as np
from sklearn.metrics import roc_auc_score

def validate_model(model_path, test_data_path=None):
    \"\"\"Validate the loaded model.\"\"\"
    try:
        model = joblib.load(model_path)
        
        # Basic validation
        if not hasattr(model, 'predict'):
            return False, "Model missing predict method"
        
        # Test prediction
        test_data = np.random.randn(10, 5)
        predictions = model.predict(test_data)
        
        if len(predictions) != 10:
            return False, "Prediction output size mismatch"
        
        return True, "Model validation passed"
        
    except Exception as e:
        return False, f"Validation failed: {str(e)}"

if __name__ == "__main__":
    success, message = validate_model("model.joblib")
    print(f"Validation result: {message}")
"""
    
    # inference_example.py
    files["inference_example.py"] = """#!/usr/bin/env python3
\"\"\"
Inference example for the model.
\"\"\"

import joblib
import numpy as np
import json

def load_model(model_path):
    \"\"\"Load the trained model.\"\"\"
    return joblib.load(model_path)

def predict_anomaly(model, data):
    \"\"\"Predict anomalies using the model.\"\"\"
    predictions = model.predict(data)
    scores = model.score_samples(data)
    return predictions, scores

def main():
    \"\"\"Example usage.\"\"\"
    # Load model
    model = load_model("model.joblib")
    
    # Create sample data
    sample_data = np.random.randn(5, 5)
    
    # Make predictions
    predictions, scores = predict_anomaly(model, sample_data)
    
    print("Predictions:", predictions)
    print("Scores:", scores)

if __name__ == "__main__":
    main()
"""
    
    return files

def create_model_package(include_optional=True, missing_files=None):
    """Create a model package with specified components."""
    if missing_files is None:
        missing_files = []
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create required files
        print("Creating required files...")
        
        # 1. model.joblib
        if "model.joblib" not in missing_files:
            model = create_test_model()
            joblib.dump(model, temp_path / "model.joblib")
            print("✓ Created model.joblib")
        else:
            print("✗ Skipping model.joblib (missing)")
        
        # 2. metadata.json
        if "metadata.json" not in missing_files:
            metadata = create_metadata()
            with open(temp_path / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            print("✓ Created metadata.json")
        else:
            print("✗ Skipping metadata.json (missing)")
        
        # 3. deployment_manifest.json
        if "deployment_manifest.json" not in missing_files:
            existing_files = [str(temp_path / f) for f in os.listdir(temp_path)]
            manifest = create_deployment_manifest(existing_files)
            with open(temp_path / "deployment_manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)
            print("✓ Created deployment_manifest.json")
        else:
            print("✗ Skipping deployment_manifest.json (missing)")
        
        # Create optional files
        if include_optional:
            print("\nCreating optional files...")
            optional_files = create_optional_files()
            
            for filename, content in optional_files.items():
                if filename not in missing_files:
                    with open(temp_path / filename, 'w') as f:
                        f.write(content)
                    print(f"✓ Created {filename}")
                else:
                    print(f"✗ Skipping {filename} (missing)")
        
        # Create ZIP file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"model_test_{timestamp}_deployment.zip"
        zip_path = Path.cwd() / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in temp_path.rglob('*'):
                if file_path.is_file():
                    zipf.write(file_path, file_path.name)
        
        print(f"\n✓ Created model package: {zip_filename}")
        return zip_path

def test_import_scenarios():
    """Test different import scenarios."""
    print("=" * 60)
    print("FLEXIBLE MODEL IMPORT TESTING")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "Complete Package",
            "description": "All required and optional files present",
            "include_optional": True,
            "missing_files": []
        },
        {
            "name": "Minimal Package",
            "description": "Only required files present",
            "include_optional": False,
            "missing_files": []
        },
        {
            "name": "Missing Optional Files",
            "description": "Required files + some optional files missing",
            "include_optional": True,
            "missing_files": ["README.md", "validate_model.py"]
        },
        {
            "name": "Missing Required File",
            "description": "Missing deployment_manifest.json (should fail)",
            "include_optional": True,
            "missing_files": ["deployment_manifest.json"]
        }
    ]
    
    created_packages = []
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   {scenario['description']}")
        print("-" * 40)
        
        try:
            package_path = create_model_package(
                include_optional=scenario["include_optional"],
                missing_files=scenario["missing_files"]
            )
            created_packages.append((scenario["name"], package_path))
            print(f"   ✓ Package created successfully")
        except Exception as e:
            print(f"   ✗ Failed to create package: {e}")
    
    return created_packages

def main():
    """Main function to run the tests."""
    print("Testing Flexible Model Import System")
    print("This script demonstrates the improved model import functionality")
    print("that distinguishes between required and optional components.\n")
    
    # Create test packages
    packages = test_import_scenarios()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, package_path in packages:
        print(f"✓ {name}: {package_path.name}")
    
    print(f"\nCreated {len(packages)} test packages.")
    print("\nTo test the import functionality:")
    print("1. Use the frontend UI to upload one of these ZIP files")
    print("2. Or use curl to test the API directly:")
    print("   curl -X POST -F 'file=@<package_name>' http://localhost:5000/api/v1/model-management/import")
    print("\nExpected behavior:")
    print("- Complete Package: Should import successfully with no warnings")
    print("- Minimal Package: Should import successfully with warnings about missing optional files")
    print("- Missing Optional Files: Should import successfully with warnings about specific missing files")
    print("- Missing Required File: Should fail import with error about missing required file")

if __name__ == "__main__":
    main() 