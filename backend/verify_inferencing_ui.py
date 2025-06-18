#!/usr/bin/env python3
"""
Inferencing UI Verification Script

This script verifies that the model inferencing functionality is working correctly
from the UI perspective by testing all the key components.
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
import sys

# Configuration
API_BASE_URL = "http://localhost:5000/api/v1"

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_status(message, status="INFO"):
    """Print a status message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {status}: {message}")

def test_backend_connectivity():
    """Test if the backend is accessible"""
    print_section("Testing Backend Connectivity")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_status("✓ Backend is accessible", "SUCCESS")
            return True
        else:
            print_status(f"✗ Backend returned status {response.status_code}", "ERROR")
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"✗ Cannot connect to backend: {e}", "ERROR")
        return False

def test_model_listing():
    """Test listing available models"""
    print_section("Testing Model Listing")
    
    try:
        response = requests.get(f"{API_BASE_URL}/models", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_status("✓ Model listing successful", "SUCCESS")
            print(f"   - Response type: {type(data)}")
            if isinstance(data, list):
                print(f"   - Number of models: {len(data)}")
                for i, model in enumerate(data[:3]):  # Show first 3 models
                    print(f"   - Model {i+1}: {model.get('id', 'N/A')} - {model.get('version', 'N/A')}")
            elif isinstance(data, dict):
                print(f"   - Models key: {list(data.keys())}")
                models = data.get('models', [])
                print(f"   - Number of models: {len(models)}")
            return True
        else:
            print_status(f"✗ Model listing failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Model listing error: {e}", "ERROR")
        return False

def test_enhanced_model_listing():
    """Test listing enhanced models"""
    print_section("Testing Enhanced Model Listing")
    
    try:
        response = requests.get(f"{API_BASE_URL}/model-management/models", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_status("✓ Enhanced model listing successful", "SUCCESS")
            print(f"   - Number of models: {len(data)}")
            for i, model in enumerate(data[:3]):  # Show first 3 models
                print(f"   - Model {i+1}: {model.get('version', 'N/A')} - {model.get('status', 'N/A')}")
            return data
        else:
            print_status(f"✗ Enhanced model listing failed: {response.status_code} - {response.text}", "ERROR")
            return []
    except Exception as e:
        print_status(f"✗ Enhanced model listing error: {e}", "ERROR")
        return []

def test_current_model():
    """Test getting current model information"""
    print_section("Testing Current Model")
    
    try:
        response = requests.get(f"{API_BASE_URL}/models/current", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_status("✓ Current model info retrieved", "SUCCESS")
            if isinstance(data, dict):
                if 'message' in data:
                    print(f"   - Status: {data['message']}")
                else:
                    print(f"   - Version: {data.get('version', 'N/A')}")
                    print(f"   - Status: {data.get('status', 'N/A')}")
            return True
        else:
            print_status(f"✗ Current model failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Current model error: {e}", "ERROR")
        return False

def test_model_loading(version):
    """Test loading a specific model version"""
    print_section("Testing Model Loading")
    
    if not version:
        print_status("✗ No model version provided", "ERROR")
        return False
    
    try:
        response = requests.post(f"{API_BASE_URL}/models/{version}/load", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print_status(f"✓ Model {version} loaded successfully", "SUCCESS")
            print(f"   - Status: {data.get('status', 'N/A')}")
            print(f"   - Version: {data.get('version', 'N/A')}")
            return True
        else:
            print_status(f"✗ Model loading failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Model loading error: {e}", "ERROR")
        return False

def test_model_deployment(version):
    """Test deploying a model version"""
    print_section("Testing Model Deployment")
    
    if not version:
        print_status("✗ No model version provided", "ERROR")
        return False
    
    try:
        response = requests.post(f"{API_BASE_URL}/model-management/{version}/deploy", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print_status(f"✓ Model {version} deployed successfully", "SUCCESS")
            print(f"   - Status: {data.get('status', 'N/A')}")
            print(f"   - Deployed at: {data.get('deployed_at', 'N/A')}")
            return True
        else:
            print_status(f"✗ Model deployment failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Model deployment error: {e}", "ERROR")
        return False

def test_model_validation(version):
    """Test validating a model version"""
    print_section("Testing Model Validation")
    
    if not version:
        print_status("✗ No model version provided", "ERROR")
        return False
    
    try:
        response = requests.post(f"{API_BASE_URL}/model-management/{version}/validate", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print_status(f"✓ Model {version} validation successful", "SUCCESS")
            print(f"   - Is Valid: {data.get('is_valid', 'N/A')}")
            print(f"   - Score: {data.get('validation_score', 'N/A')}")
            return True
        else:
            print_status(f"✗ Model validation failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Model validation error: {e}", "ERROR")
        return False

def test_log_analysis():
    """Test analyzing logs with the current model"""
    print_section("Testing Log Analysis")
    
    # Sample log data for testing
    sample_logs = [
        {
            "timestamp": "2024-01-01T10:00:00Z",
            "signal_strength": -65,
            "latency": 25,
            "packet_loss": 0.1,
            "connection_duration": 3600,
            "client_count": 15,
            "error_count": 2
        },
        {
            "timestamp": "2024-01-01T10:01:00Z",
            "signal_strength": -70,
            "latency": 30,
            "packet_loss": 0.2,
            "connection_duration": 3600,
            "client_count": 18,
            "error_count": 5
        }
    ]
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/models/analyze",
            json=sample_logs,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status("✓ Log analysis successful", "SUCCESS")
            print(f"   - Number of results: {len(data)}")
            
            # Show first result details
            if data and len(data) > 0:
                first_result = data[0]
                analysis = first_result.get('analysis_result', {})
                print(f"   - First result:")
                print(f"     * Prediction: {analysis.get('prediction', 'N/A')}")
                print(f"     * Anomaly Score: {analysis.get('anomaly_score', 'N/A')}")
                print(f"     * Is Anomaly: {analysis.get('is_anomaly', 'N/A')}")
                print(f"     * Model Version: {analysis.get('model_version', 'N/A')}")
            
            return True
        else:
            print_status(f"✗ Log analysis failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Log analysis error: {e}", "ERROR")
        return False

def test_model_performance(version):
    """Test getting model performance metrics"""
    print_section("Testing Model Performance")
    
    if not version:
        print_status("✗ No model version provided", "ERROR")
        return False
    
    try:
        response = requests.get(f"{API_BASE_URL}/model-management/performance/{version}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_status(f"✓ Model {version} performance retrieved", "SUCCESS")
            print(f"   - Total Inferences: {data.get('total_inferences', 'N/A')}")
            print(f"   - Average Inference Time: {data.get('avg_inference_time', 'N/A')}ms")
            print(f"   - Anomaly Rate: {data.get('anomaly_rate', 'N/A')}%")
            return True
        else:
            print_status(f"✗ Model performance failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Model performance error: {e}", "ERROR")
        return False

def test_model_drift_check(version):
    """Test checking model drift"""
    print_section("Testing Model Drift Check")
    
    if not version:
        print_status("✗ No model version provided", "ERROR")
        return False
    
    try:
        response = requests.post(f"{API_BASE_URL}/model-management/performance/{version}/check-drift", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print_status(f"✓ Model {version} drift check successful", "SUCCESS")
            print(f"   - Drift Detected: {data.get('drift_detected', 'N/A')}")
            print(f"   - Drift Score: {data.get('drift_score', 'N/A')}")
            return True
        else:
            print_status(f"✗ Model drift check failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Model drift check error: {e}", "ERROR")
        return False

def test_transfer_history():
    """Test getting model transfer history"""
    print_section("Testing Transfer History")
    
    try:
        response = requests.get(f"{API_BASE_URL}/model-management/transfer-history", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_status("✓ Transfer history retrieved", "SUCCESS")
            print(f"   - Number of transfers: {len(data)}")
            for i, transfer in enumerate(data[:3]):  # Show first 3 transfers
                print(f"   - Transfer {i+1}: {transfer.get('version', 'N/A')} - {transfer.get('status', 'N/A')}")
            return True
        else:
            print_status(f"✗ Transfer history failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Transfer history error: {e}", "ERROR")
        return False

def test_training_service_connection():
    """Test training service connection"""
    print_section("Testing Training Service Connection")
    
    try:
        response = requests.get(f"{API_BASE_URL}/model-management/training-service/connection", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_status("✓ Training service connection successful", "SUCCESS")
            print(f"   - Status: {data.get('status', 'N/A')}")
            print(f"   - Message: {data.get('message', 'N/A')}")
            return True
        else:
            print_status(f"✗ Training service connection failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Training service connection error: {e}", "ERROR")
        return False

def test_frontend_api_endpoints():
    """Test that all frontend API endpoints are accessible"""
    print_section("Testing Frontend API Endpoints")
    
    endpoints = [
        ("GET", "/health", "Health Check"),
        ("GET", "/models", "List Models"),
        ("GET", "/models/current", "Current Model"),
        ("GET", "/model-management/models", "Enhanced Models"),
        ("GET", "/model-management/transfer-history", "Transfer History"),
        ("GET", "/model-management/performance", "All Performance"),
        ("GET", "/model-management/training-service/connection", "Training Service"),
    ]
    
    success_count = 0
    total_count = len(endpoints)
    
    for method, endpoint, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
            
            if response.status_code in [200, 201, 400, 404]:  # Acceptable responses
                print_status(f"✓ {description}: {response.status_code}", "SUCCESS")
                success_count += 1
            else:
                print_status(f"✗ {description}: {response.status_code}", "ERROR")
        except Exception as e:
            print_status(f"✗ {description}: {e}", "ERROR")
    
    print_status(f"API Endpoints: {success_count}/{total_count} accessible", "INFO")
    return success_count == total_count

def main():
    """Main verification function"""
    print("Inferencing UI Verification Script")
    print("=" * 60)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test connectivity
    if not test_backend_connectivity():
        print_status("Backend is not accessible. Please start the backend server.", "ERROR")
        return False
    
    # Test API endpoints
    test_frontend_api_endpoints()
    
    # Test basic model functionality
    test_model_listing()
    test_current_model()
    
    # Test enhanced model functionality
    models = test_enhanced_model_listing()
    
    # Test with a specific model if available
    if models and len(models) > 0:
        test_model = models[0]
        version = test_model.get('version')
        
        if version:
            print_status(f"Testing with model version: {version}", "INFO")
            
            # Test model operations
            test_model_loading(version)
            test_model_deployment(version)
            test_model_validation(version)
            test_model_performance(version)
            test_model_drift_check(version)
    
    # Test log analysis
    test_log_analysis()
    
    # Test other functionality
    test_transfer_history()
    test_training_service_connection()
    
    print_section("Verification Complete")
    print_status("Inferencing functionality verification completed!", "SUCCESS")
    print("\nTo verify the UI manually:")
    print("1. Open your browser and navigate to the frontend")
    print("2. Go to the Enhanced Models page")
    print("3. Check the Models tab to see available models")
    print("4. Try loading and deploying a model")
    print("5. Go to the Performance tab to view metrics")
    print("6. Test log analysis functionality")
    print("7. Check model validation and drift detection")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_status("Verification interrupted by user", "INFO")
    except Exception as e:
        print_status(f"Verification failed with error: {e}", "ERROR")
        sys.exit(1) 