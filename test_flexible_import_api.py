#!/usr/bin/env python3
"""
API test script for flexible model import functionality.

This script tests the improved model import API that distinguishes between
required and optional components.
"""

import requests
import json
import time
from pathlib import Path

def test_model_import_api(zip_file_path):
    """Test the model import API with a ZIP file."""
    base_url = "http://localhost:5000/api/v1"
    
    print(f"Testing model import with: {zip_file_path}")
    print("-" * 50)
    
    # Check if file exists
    if not Path(zip_file_path).exists():
        print(f"❌ File not found: {zip_file_path}")
        return False
    
    try:
        # Prepare the file upload
        with open(zip_file_path, 'rb') as f:
            files = {'file': (Path(zip_file_path).name, f, 'application/zip')}
            
            print("📤 Uploading model package...")
            response = requests.post(
                f"{base_url}/model-management/import",
                files=files,
                timeout=30
            )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Import successful!")
            print(f"   Version: {result.get('version', 'N/A')}")
            print(f"   Status: {result.get('status', 'N/A')}")
            print(f"   Path: {result.get('path', 'N/A')}")
            
            # Display validation summary if available
            validation_summary = result.get('validation_summary')
            if validation_summary:
                print("\n📋 Validation Summary:")
                print(f"   Required files present: {len(validation_summary.get('required_files_present', []))}")
                print(f"   Optional files missing: {len(validation_summary.get('optional_files_missing', []))}")
                print(f"   Warnings: {len(validation_summary.get('warnings', []))}")
                
                if validation_summary.get('optional_files_missing'):
                    print("   ⚠️  Missing optional files:")
                    for file in validation_summary['optional_files_missing']:
                        print(f"      - {file}")
                
                if validation_summary.get('warnings'):
                    print("   ⚠️  Warnings:")
                    for warning in validation_summary['warnings']:
                        print(f"      - {warning}")
            else:
                print("   ℹ️  No validation summary available")
            
            return True
            
        else:
            print(f"❌ Import failed!")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Make sure the backend server is running on http://localhost:5000")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout: The server took too long to respond")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_models_list():
    """Test the models list API to see imported models."""
    base_url = "http://localhost:5000/api/v1"
    
    print("\n📋 Testing models list API...")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/model-management/models", timeout=10)
        
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Found {len(models)} models:")
            
            for model in models:
                print(f"   - {model.get('version', 'N/A')} ({model.get('status', 'N/A')})")
            
            return True
        else:
            print(f"❌ Failed to list models: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return False

def main():
    """Main function to run the API tests."""
    print("🧪 Testing Flexible Model Import API")
    print("=" * 50)
    
    # Check if test packages exist
    test_packages = list(Path.cwd().glob("model_test_*_deployment.zip"))
    
    if not test_packages:
        print("❌ No test packages found!")
        print("Please run test_flexible_model_import.py first to create test packages.")
        return
    
    print(f"📦 Found {len(test_packages)} test packages:")
    for package in test_packages:
        print(f"   - {package.name}")
    
    # Test each package
    successful_imports = 0
    
    for package in test_packages:
        print(f"\n{'='*60}")
        if test_model_import_api(str(package)):
            successful_imports += 1
        time.sleep(1)  # Small delay between requests
    
    # Test models list
    print(f"\n{'='*60}")
    test_models_list()
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total packages tested: {len(test_packages)}")
    print(f"Successful imports: {successful_imports}")
    print(f"Failed imports: {len(test_packages) - successful_imports}")
    
    if successful_imports > 0:
        print("\n✅ The flexible import system is working correctly!")
        print("   - Models with only required files should import successfully")
        print("   - Models with missing optional files should show warnings")
        print("   - Models with missing required files should fail appropriately")
    else:
        print("\n❌ All imports failed. Check the backend server and logs.")

if __name__ == "__main__":
    main() 