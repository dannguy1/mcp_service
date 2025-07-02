#!/usr/bin/env python3

import os

print("=== Path Resolution Test ===")

# Test the WiFiAgent model path
wifi_path = "/home/dannguyen/WNC/mcp_service/backend/models/model_tmpo3jl9ugx.zip"
print(f"\nWiFiAgent model path: {wifi_path}")
print(f"Path exists: {os.path.exists(wifi_path)}")
print(f"Is directory: {os.path.isdir(wifi_path)}")
print(f"Is file: {os.path.isfile(wifi_path)}")

if os.path.exists(wifi_path) and os.path.isdir(wifi_path):
    model_file = os.path.join(wifi_path, 'model.joblib')
    print(f"Model file path: {model_file}")
    print(f"Model file exists: {os.path.exists(model_file)}")
    
    if os.path.exists(model_file):
        print("✅ Model file found!")
    else:
        print("❌ Model file not found")
        # List contents of the directory
        print("Directory contents:")
        for item in os.listdir(wifi_path):
            print(f"  - {item}")

# Test the SystemAgent model path for comparison
system_path = "/home/dannguyen/WNC/mcp_service/backend/models/model_tmpebpfo3a3.zip"
print(f"\nSystemAgent model path: {system_path}")
print(f"Path exists: {os.path.exists(system_path)}")
print(f"Is directory: {os.path.isdir(system_path)}")
print(f"Is file: {os.path.isfile(system_path)}")

if os.path.exists(system_path) and os.path.isdir(system_path):
    model_file = os.path.join(system_path, 'model.joblib')
    print(f"Model file path: {model_file}")
    print(f"Model file exists: {os.path.exists(model_file)}")

print("\n=== Test Complete ===") 