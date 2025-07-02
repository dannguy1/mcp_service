#!/usr/bin/env python3
"""
Script to fix model registry version numbers to match metadata.
"""

import json
import os
from pathlib import Path
from datetime import datetime

def fix_model_registry():
    """Fix model registry to use correct version numbers from metadata."""
    
    # Paths
    models_dir = Path("models")
    registry_file = models_dir / "model_registry.json"
    
    if not registry_file.exists():
        print("Model registry file not found!")
        return
    
    # Load current registry
    with open(registry_file, 'r') as f:
        registry_data = json.load(f)
    
    print("Current registry structure:")
    print(f"Has 'models' array: {'models' in registry_data}")
    print(f"Number of models in array: {len(registry_data.get('models', []))}")
    print(f"Number of flat entries: {len([k for k in registry_data.keys() if k != 'models' and k != 'last_updated'])}")
    
    # Deduplicate entries: keep only the entry whose path matches the version
    if 'models' in registry_data:
        models_list = registry_data['models']
        deduped = {}
        for model_info in models_list:
            version = model_info.get('version', '')
            path = model_info.get('path', '')
            # The correct path for a version is models/<version>
            correct_path = f"models/{version}"
            if version not in deduped:
                deduped[version] = model_info
            else:
                # If this entry has the correct path, prefer it
                if path == correct_path:
                    # If either is deployed, keep deployed status
                    if deduped[version]['status'] == 'deployed' or model_info['status'] == 'deployed':
                        model_info['status'] = 'deployed'
                    deduped[version] = model_info
                else:
                    # If the existing one is not correct path but this is, replace
                    if deduped[version]['path'] != correct_path and path == correct_path:
                        deduped[version] = model_info
                    # If both are not correct, keep the first
                    # If either is deployed, keep deployed status
                    if deduped[version]['status'] == 'deployed' or model_info['status'] == 'deployed':
                        deduped[version]['status'] = 'deployed'
        # Only keep entries whose path matches the version
        cleaned_models = [m for v, m in deduped.items() if m['path'] == f"models/{v}"]
        registry_data['models'] = cleaned_models
        registry_data['last_updated'] = datetime.now().isoformat()
    
    # Save updated registry
    with open(registry_file, 'w') as f:
        json.dump(registry_data, f, indent=2)
    
    print("\nRegistry updated successfully!")
    
    # Show updated registry
    print("\nUpdated registry structure:")
    with open(registry_file, 'r') as f:
        updated_registry = json.load(f)
    
    if 'models' in updated_registry:
        print("Models in array:")
        for model in updated_registry['models']:
            print(f"  {model['version']} -> {model['status']}")

if __name__ == "__main__":
    fix_model_registry() 