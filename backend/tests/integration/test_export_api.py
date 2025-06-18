import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestExportAPI:
    def test_create_export(self):
        """Test creating an export job."""
        response = client.post("/api/v1/export/", json={
            "data_types": ["logs"],
            "batch_size": 100,
            "include_metadata": True,
            "output_format": "json",
            "compression": False
        })
        assert response.status_code == 200
        data = response.json()
        assert "export_id" in data
        assert data["status"] == "pending"
    
    def test_create_export_with_date_range(self):
        """Test creating an export job with date range."""
        response = client.post("/api/v1/export/", json={
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-01-31T23:59:59Z",
            "data_types": ["logs"],
            "batch_size": 100
        })
        assert response.status_code == 200
        data = response.json()
        assert "export_id" in data
    
    def test_create_export_with_process_filter(self):
        """Test creating an export job with process filter."""
        response = client.post("/api/v1/export/", json={
            "data_types": ["logs"],
            "processes": ["nginx", "apache"],
            "batch_size": 100
        })
        assert response.status_code == 200
        data = response.json()
        assert "export_id" in data
    
    def test_get_export_status(self):
        """Test getting export status."""
        # First create an export
        create_response = client.post("/api/v1/export/", json={
            "data_types": ["logs"],
            "batch_size": 100
        })
        export_id = create_response.json()["export_id"]
        
        # Then get status
        status_response = client.get(f"/api/v1/export/{export_id}/status")
        assert status_response.status_code == 200
        data = status_response.json()
        assert data["export_id"] == export_id
    
    def test_get_export_progress(self):
        """Test getting export progress."""
        # First create an export
        create_response = client.post("/api/v1/export/", json={
            "data_types": ["logs"],
            "batch_size": 100
        })
        export_id = create_response.json()["export_id"]
        
        # Then get progress
        progress_response = client.get(f"/api/v1/export/{export_id}/progress")
        assert progress_response.status_code == 200
        data = progress_response.json()
        assert data["export_id"] == export_id
    
    def test_list_exports(self):
        """Test listing exports."""
        response = client.get("/api/v1/export/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_exports_with_pagination(self):
        """Test listing exports with pagination."""
        response = client.get("/api/v1/export/?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_delete_export(self):
        """Test deleting an export."""
        # First create an export
        create_response = client.post("/api/v1/export/", json={
            "data_types": ["logs"],
            "batch_size": 100
        })
        export_id = create_response.json()["export_id"]
        
        # Then delete it
        delete_response = client.delete(f"/api/v1/export/{export_id}")
        assert delete_response.status_code == 200
    
    def test_invalid_export_config(self):
        """Test creating export with invalid config."""
        response = client.post("/api/v1/export/", json={
            "data_types": ["invalid_type"],
            "batch_size": 100
        })
        assert response.status_code == 422  # Validation error
    
    def test_invalid_date_range(self):
        """Test creating export with invalid date range."""
        response = client.post("/api/v1/export/", json={
            "start_date": "2024-01-31T23:59:59Z",
            "end_date": "2024-01-01T00:00:00Z",  # End before start
            "data_types": ["logs"],
            "batch_size": 100
        })
        assert response.status_code == 422  # Validation error
    
    def test_get_nonexistent_export_status(self):
        """Test getting status for non-existent export."""
        response = client.get("/api/v1/export/nonexistent-id/status")
        assert response.status_code == 404 