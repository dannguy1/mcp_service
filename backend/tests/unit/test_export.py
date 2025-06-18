import pytest
from datetime import datetime, timedelta
from app.models.export import ExportConfig
from app.services.export.data_exporter import DataExporter
from app.services.export.data_validator import DataValidator

class TestDataExporter:
    @pytest.fixture
    def config(self):
        return ExportConfig(
            data_types=["logs"],
            batch_size=100,
            include_metadata=True,
            validation_level="basic",
            output_format="json",
            compression=False
        )
    
    @pytest.fixture
    def exporter(self, config):
        return DataExporter(config)
    
    async def test_export_without_date_range(self, exporter, config):
        """Test export without date range constraints."""
        metadata = await exporter.export_data(config)
        assert metadata.status == "completed"
        assert metadata.record_count >= 0
    
    async def test_export_with_date_range(self, exporter):
        """Test export with date range constraints."""
        config = ExportConfig(
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow(),
            data_types=["logs"],
            batch_size=100
        )
        metadata = await exporter.export_data(config)
        assert metadata.status == "completed"
    
    async def test_export_with_process_filter(self, exporter):
        """Test export with process filtering."""
        config = ExportConfig(
            data_types=["logs"],
            processes=["nginx", "apache"],
            batch_size=100
        )
        metadata = await exporter.export_data(config)
        assert metadata.status == "completed"
    
    async def test_export_multiple_data_types(self, exporter):
        """Test export with multiple data types."""
        config = ExportConfig(
            data_types=["logs", "anomalies"],
            batch_size=100
        )
        metadata = await exporter.export_data(config)
        assert metadata.status == "completed"

class TestExportConfig:
    def test_valid_data_types(self):
        """Test valid data types validation."""
        config = ExportConfig(
            data_types=["logs", "anomalies", "ips"],
            batch_size=100
        )
        assert config.data_types == ["logs", "anomalies", "ips"]
    
    def test_invalid_data_type(self):
        """Test invalid data type validation."""
        with pytest.raises(ValueError, match="Invalid data type"):
            ExportConfig(
                data_types=["invalid_type"],
                batch_size=100
            )
    
    def test_date_range_validation(self):
        """Test date range validation."""
        start_date = datetime.utcnow()
        end_date = start_date - timedelta(days=1)
        
        with pytest.raises(ValueError, match="End date must be after start date"):
            ExportConfig(
                start_date=start_date,
                end_date=end_date,
                data_types=["logs"],
                batch_size=100
            )
    
    def test_optional_date_ranges(self):
        """Test that date ranges are optional."""
        config = ExportConfig(
            data_types=["logs"],
            batch_size=100
        )
        assert config.start_date is None
        assert config.end_date is None 