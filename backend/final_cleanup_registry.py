#!/usr/bin/env python3
"""
Final cleanup script to fix model registry completely.
"""

import json
import os
from pathlib import Path
from datetime import datetime

def final_cleanup_registry():
    """Final cleanup of model registry."""
    
    # Paths
    models_dir = Path("models")
    registry_file = models_dir / "model_registry.json"
    
    if not registry_file.exists():
        print("Model registry file not found!")
        return
    
    # Load current registry
    with open(registry_file, 'r') as f:
        registry_data = json.load(f)
    
    print("Starting final cleanup...")
    
    # Remove all directory-based entries from models array
    if 'models' in registry_data:
        models_list = registry_data['models']
        cleaned_models = []
        
        for model_info in models_list:
            version = model_info.get('version', '')
            # Keep only entries that don't start with 'model_' and end with '.zip'
            if not (version.startswith('model_') and version.endswith('.zip')):
                cleaned_models.append(model_info)
            else:
                print(f"Removing directory-based entry: {version}")
        
        registry_data['models'] = cleaned_models
    
    # Scan all model directories and add correct entries
    if models_dir.exists():
        for model_dir in models_dir.iterdir():
            if model_dir.is_dir() and model_dir.name.startswith('model_'):
                metadata_file = model_dir / 'metadata.json'
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        correct_version = metadata.get('model_info', {}).get('version', '')
                        if correct_version:
                            # Check if this version already exists
                            existing_models = registry_data.get('models', [])
                            existing_version = next((m for m in existing_models if m.get('version') == correct_version), None)
                            
                            if not existing_version:
                                # Add new entry
                                new_entry = {
                                    'version': correct_version,
                                    'path': f"models/{correct_version}",
                                    'status': 'available',  # Default to available
                                    'created_at': metadata.get('model_info', {}).get('created_at', datetime.now().isoformat()),
                                    'last_updated': datetime.now().isoformat(),
                                    'model_type': 'IsolationForest'
                                }
                                registry_data['models'].append(new_entry)
                                print(f"Added missing entry: {correct_version}")
                            else:
                                # Update existing entry if needed
                                if existing_version['path'] != f"models/{correct_version}":
                                    existing_version['path'] = f"models/{correct_version}"
                                    existing_version['last_updated'] = datetime.now().isoformat()
                                    print(f"Updated path for {correct_version}")
                        
                    except Exception as e:
                        print(f"Error processing {model_dir.name}: {e}")
    
    # Save updated registry
    registry_data['last_updated'] = datetime.now().isoformat()
    with open(registry_file, 'w') as f:
        json.dump(registry_data, f, indent=2)
    
    print("\nFinal cleanup completed!")
    
    # Show final registry
    print("\nFinal registry structure:")
    with open(registry_file, 'r') as f:
        final_registry = json.load(f)
    
    if 'models' in final_registry:
        print("Models in array:")
        for model in final_registry['models']:
            print(f"  {model['version']} -> {model['status']} (path: {model['path']})")

if __name__ == "__main__":
    final_cleanup_registry() 