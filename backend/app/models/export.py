from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class ExportMetadata(BaseModel):
    """Metadata for exported data."""
    export_id: str = Field(..., description="Unique identifier for the export")
    export_timestamp: datetime = Field(default_factory=datetime.utcnow)
    data_version: str = Field(..., description="Version of the data format")
    export_config: Dict[str, Any] = Field(..., description="Configuration used for export")
    record_count: int = Field(..., description="Number of records exported")
    file_size: int = Field(..., description="Size of exported file in bytes")
    data_quality_metrics: Dict[str, float] = Field(default_factory=dict)
    status: str = Field(default="pending", description="Export status: pending, running, completed, failed")
    error_message: Optional[str] = Field(default=None, description="Error message if export failed")

class DataValidationResult(BaseModel):
    """Results of data validation."""
    is_valid: bool = Field(..., description="Whether the data is valid")
    validation_errors: List[str] = Field(default_factory=list)
    quality_metrics: Dict[str, float] = Field(default_factory=dict)
    missing_fields: List[str] = Field(default_factory=list)
    invalid_values: Dict[str, List[Any]] = Field(default_factory=dict)

class ExportConfig(BaseModel):
    """Configuration for data export."""
    start_date: datetime = Field(..., description="Start date for data export")
    end_date: datetime = Field(..., description="End date for data export")
    data_types: List[str] = Field(..., description="Types of data to export")
    batch_size: int = Field(default=1000, description="Number of records per batch")
    include_metadata: bool = Field(default=True, description="Whether to include metadata")
    validation_level: str = Field(default="basic", description="Level of validation to perform")
    output_format: str = Field(default="json", description="Output format for export")
    compression: bool = Field(default=False, description="Whether to compress output")
    processes: List[str] = Field(default_factory=list, description="List of processes to filter by") 