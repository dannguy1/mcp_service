import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Mock Redis before importing app
with patch.dict('os.environ', {'REDIS_HOST': 'localhost', 'REDIS_PORT': '6379'}):
    with patch('redis.Redis'):
        from app.main import app

client = TestClient(app)

class TestExportDownloadSimple:
    """Test export download functionality with mocked dependencies."""

    @patch('app.services.export.status_manager.ExportStatusManager.get_export_metadata')
    def test_download_export_file_success(self, mock_get_metadata):
        """Test successful download of export file."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"test": "data"}')
            test_file_path = f.name

        # Mock export metadata
        test_export_id = "test-export-123"
        test_metadata = {
            "export_id": test_export_id,
            "file_path": test_file_path,
            "status": "completed"
        }
        mock_get_metadata.return_value = test_metadata

        response = client.get(f"/api/export/download/{test_export_id}")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        assert "attachment" in response.headers.get("content-disposition", "")

        # Clean up
        os.unlink(test_file_path)

    @patch('app.services.export.status_manager.ExportStatusManager.get_export_metadata')
    def test_download_export_file_not_found(self, mock_get_metadata):
        """Test download when export metadata is not found."""
        test_export_id = "non-existent-export"
        mock_get_metadata.return_value = None
        
        response = client.get(f"/api/export/download/{test_export_id}")
        
        assert response.status_code == 404
        assert "Export not found" in response.json()["detail"]

    @patch('app.services.export.status_manager.ExportStatusManager.get_export_metadata')
    def test_download_export_file_missing_file(self, mock_get_metadata):
        """Test download when export file doesn't exist on disk."""
        test_export_id = "test-export-123"
        test_metadata = {
            "export_id": test_export_id,
            "file_path": "/non/existent/file.json",
            "status": "completed"
        }
        mock_get_metadata.return_value = test_metadata

        response = client.get(f"/api/export/download/{test_export_id}")
        
        assert response.status_code == 404
        assert "Export file not found" in response.json()["detail"]

    @patch('app.services.export.status_manager.ExportStatusManager.get_export_metadata')
    def test_download_export_file_no_file_path(self, mock_get_metadata):
        """Test download when export metadata has no file_path."""
        test_export_id = "test-export-123"
        test_metadata = {
            "export_id": test_export_id,
            "status": "completed"
            # No file_path
        }
        mock_get_metadata.return_value = test_metadata

        response = client.get(f"/api/export/download/{test_export_id}")
        
        assert response.status_code == 404
        assert "Export file not found" in response.json()["detail"] 