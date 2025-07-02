#!/usr/bin/env python3
"""
Script to fix model registry paths to match actual directory names.
"""

import json
import os
from pathlib import Path
from datetime import datetime

def fix_registry_paths():
    """Fix model registry paths to match actual directory names."""
    
    # Paths
    models_dir = Path("models")
    registry_file = models_dir / "model_registry.json"
    
    if not registry_file.exists():
        print("Model registry file not found!")
        return
    
    # Load current registry
    with open(registry_file, 'r') as f:
        registry_data = json.load(f)
    
    print("Fixing registry paths...")
    
    # Fix paths in models array
    if 'models' in registry_data:
        models_list = registry_data['models']
        
        for model_info in models_list:
            version = model_info.get('version', '')
            current_path = model_info.get('path', '')
            
            # Find the actual directory that contains this version
            actual_dir = None
            for model_dir in models_dir.iterdir():
                if model_dir.is_dir() and model_dir.name.startswith('model_'):
                    metadata_file = model_dir / 'metadata.json'
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                            dir_version = metadata.get('model_info', {}).get('version', '')
                            if dir_version == version:
                                actual_dir = model_dir.name
                                break
                        except Exception as e:
                            print(f"Error reading metadata for {model_dir.name}: {e}")
            
            if actual_dir:
                correct_path = f"models/{actual_dir}"
                if current_path != correct_path:
                    print(f"Fixing path for {version}: {current_path} -> {correct_path}")
                    model_info['path'] = correct_path
                    model_info['last_updated'] = datetime.now().isoformat()
            else:
                print(f"Warning: Could not find actual directory for version {version}")
        
        registry_data['models'] = models_list
        registry_data['last_updated'] = datetime.now().isoformat()
    
    # Save updated registry
    with open(registry_file, 'w') as f:
        json.dump(registry_data, f, indent=2)
    
    print("\nRegistry paths fixed!")
    
    # Show final registry
    print("\nFinal registry structure:")
    with open(registry_file, 'r') as f:
        final_registry = json.load(f)
    
    if 'models' in final_registry:
        print("Models in array:")
        for model in final_registry['models']:
            print(f"  {model['version']} -> {model['status']} (path: {model['path']})")

if __name__ == "__main__":
    fix_registry_paths() 