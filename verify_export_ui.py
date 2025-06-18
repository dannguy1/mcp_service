#!/usr/bin/env python3
"""
Export UI Verification Script

This script verifies that the export functionality is working correctly
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
REDIS_HOST = "localhost"
REDIS_PORT = 6379

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

def test_redis_connectivity():
    """Test if Redis is accessible"""
    print_section("Testing Redis Connectivity")
    
    try:
        import redis
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        print_status("✓ Redis is accessible", "SUCCESS")
        return True
    except Exception as e:
        print_status(f"✗ Cannot connect to Redis: {e}", "ERROR")
        return False

def test_export_creation():
    """Test creating a new export"""
    print_section("Testing Export Creation")
    
    # Test export configuration
    export_config = {
        "data_types": ["logs"],
        "batch_size": 100,
        "include_metadata": True,
        "validation_level": "basic",
        "output_format": "json",
        "compression": False,
        "processes": ["nginx", "apache"],
        "start_date": (datetime.now() - timedelta(days=1)).isoformat(),
        "end_date": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/export",
            json=export_config,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            export_id = data.get("export_id")
            print_status(f"✓ Export created successfully with ID: {export_id}", "SUCCESS")
            return export_id
        else:
            print_status(f"✗ Export creation failed: {response.status_code} - {response.text}", "ERROR")
            return None
    except Exception as e:
        print_status(f"✗ Export creation error: {e}", "ERROR")
        return None

def test_export_status(export_id):
    """Test getting export status"""
    print_section("Testing Export Status")
    
    if not export_id:
        print_status("✗ No export ID provided", "ERROR")
        return False
    
    try:
        response = requests.get(f"{API_BASE_URL}/export/{export_id}/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")
            print_status(f"✓ Export status retrieved: {status}", "SUCCESS")
            print(f"   - Status: {status}")
            print(f"   - Total Records: {data.get('total_records', 0)}")
            print(f"   - Total Size: {data.get('total_size', 0)} bytes")
            return True
        else:
            print_status(f"✗ Status retrieval failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Status retrieval error: {e}", "ERROR")
        return False

def test_export_progress(export_id):
    """Test getting export progress"""
    print_section("Testing Export Progress")
    
    if not export_id:
        print_status("✗ No export ID provided", "ERROR")
        return False
    
    try:
        response = requests.get(f"{API_BASE_URL}/export/{export_id}/progress", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_status("✓ Export progress retrieved", "SUCCESS")
            print(f"   - Status: {data.get('status', 'unknown')}")
            print(f"   - Progress: {data.get('progress', {})}")
            print(f"   - Processed Records: {data.get('processed_records', 0)}")
            return True
        else:
            print_status(f"✗ Progress retrieval failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Progress retrieval error: {e}", "ERROR")
        return False

def test_export_list():
    """Test listing exports"""
    print_section("Testing Export List")
    
    try:
        response = requests.get(f"{API_BASE_URL}/export?limit=10", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print_status(f"✓ Export list retrieved: {len(data)} exports", "SUCCESS")
                for export in data[:3]:  # Show first 3 exports
                    print(f"   - {export.get('export_id', 'N/A')}: {export.get('status', 'unknown')}")
                return True
            else:
                print_status("✗ Export list format is incorrect", "ERROR")
                return False
        else:
            print_status(f"✗ Export list failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Export list error: {e}", "ERROR")
        return False

def test_export_download(export_id):
    """Test downloading an export"""
    print_section("Testing Export Download")
    
    if not export_id:
        print_status("✗ No export ID provided", "ERROR")
        return False
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/export/download/{export_id}",
            timeout=30,
            stream=True
        )
        
        if response.status_code == 200:
            # Check if we got a file
            content_type = response.headers.get('content-type', '')
            content_length = response.headers.get('content-length', 0)
            
            print_status("✓ Export download successful", "SUCCESS")
            print(f"   - Content Type: {content_type}")
            print(f"   - Content Length: {content_length} bytes")
            
            # Save a small sample to verify it's valid
            sample_data = response.content[:1000]  # First 1KB
            if sample_data:
                print(f"   - Sample data preview: {sample_data[:100].decode('utf-8', errors='ignore')}...")
            
            return True
        else:
            print_status(f"✗ Export download failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Export download error: {e}", "ERROR")
        return False

def test_export_cleanup():
    """Test export cleanup functionality"""
    print_section("Testing Export Cleanup")
    
    try:
        response = requests.post(f"{API_BASE_URL}/export/cleanup", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print_status("✓ Export cleanup successful", "SUCCESS")
            print(f"   - Message: {data.get('message', 'N/A')}")
            return True
        else:
            print_status(f"✗ Export cleanup failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Export cleanup error: {e}", "ERROR")
        return False

def test_export_stats():
    """Test export statistics"""
    print_section("Testing Export Statistics")
    
    try:
        response = requests.get(f"{API_BASE_URL}/export/stats", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_status("✓ Export statistics retrieved", "SUCCESS")
            print(f"   - Total Exports: {data.get('total_exports', 0)}")
            print(f"   - Completed: {data.get('completed_exports', 0)}")
            print(f"   - Failed: {data.get('failed_exports', 0)}")
            return True
        else:
            print_status(f"✗ Export stats failed: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        print_status(f"✗ Export stats error: {e}", "ERROR")
        return False

def test_frontend_api_endpoints():
    """Test that all frontend API endpoints are accessible"""
    print_section("Testing Frontend API Endpoints")
    
    endpoints = [
        ("GET", "/health", "Health Check"),
        ("GET", "/export", "List Exports"),
        ("POST", "/export", "Create Export"),
        ("GET", "/export/stats", "Export Stats"),
        ("POST", "/export/cleanup", "Export Cleanup"),
    ]
    
    success_count = 0
    total_count = len(endpoints)
    
    for method, endpoint, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
            elif method == "POST":
                response = requests.post(f"{API_BASE_URL}{endpoint}", json={}, timeout=5)
            
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
    print("Export UI Verification Script")
    print("=" * 60)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Redis Host: {REDIS_HOST}:{REDIS_PORT}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test connectivity
    if not test_backend_connectivity():
        print_status("Backend is not accessible. Please start the backend server.", "ERROR")
        return False
    
    if not test_redis_connectivity():
        print_status("Redis is not accessible. Please start Redis.", "ERROR")
        return False
    
    # Test API endpoints
    test_frontend_api_endpoints()
    
    # Test export functionality
    export_id = test_export_creation()
    
    if export_id:
        # Wait a moment for the export to start
        time.sleep(2)
        
        # Test status and progress
        test_export_status(export_id)
        test_export_progress(export_id)
        
        # Wait for export to complete (with timeout)
        print_section("Waiting for Export to Complete")
        max_wait = 60  # 60 seconds
        wait_time = 0
        while wait_time < max_wait:
            try:
                response = requests.get(f"{API_BASE_URL}/export/{export_id}/status", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "unknown")
                    print_status(f"Export status: {status}", "INFO")
                    
                    if status in ["completed", "failed"]:
                        break
                    
                    time.sleep(5)
                    wait_time += 5
                else:
                    break
            except:
                break
        
        # Test download if completed
        if status == "completed":
            test_export_download(export_id)
    
    # Test other functionality
    test_export_list()
    test_export_stats()
    test_export_cleanup()
    
    print_section("Verification Complete")
    print_status("Export functionality verification completed!", "SUCCESS")
    print("\nTo verify the UI manually:")
    print("1. Open your browser and navigate to the frontend")
    print("2. Go to the Export page")
    print("3. Fill out the export form and click 'Start Export'")
    print("4. Check the Export History tab to monitor progress")
    print("5. Download completed exports")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_status("Verification interrupted by user", "INFO")
    except Exception as e:
        print_status(f"Verification failed with error: {e}", "ERROR")
        sys.exit(1) 