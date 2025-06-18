from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, validator

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
    start_date: Optional[Union[datetime, str]] = Field(None, description="Start date for data export (optional)")
    end_date: Optional[Union[datetime, str]] = Field(None, description="End date for data export (optional)")
    data_types: List[str] = Field(..., description="Types of data to export")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Additional filters")
    batch_size: int = Field(default=1000, description="Number of records per batch")
    include_metadata: bool = Field(default=True, description="Whether to include metadata")
    validation_level: str = Field(default="basic", description="Level of validation to perform")
    output_format: str = Field(default="json", description="Output format for export")
    compression: bool = Field(default=False, description="Whether to compress output")
    processes: List[str] = Field(default_factory=list, description="List of processes to filter by")
    
    @validator('start_date', 'end_date', pre=True)
    def parse_dates(cls, v):
        if isinstance(v, str):
            try:
                # Parse the datetime string
                dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
                # Convert to timezone-naive datetime for PostgreSQL compatibility
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                return dt
            except ValueError:
                raise ValueError(f"Invalid date format: {v}")
        elif isinstance(v, datetime):
            # If it's already a datetime, ensure it's timezone-naive
            if v.tzinfo is not None:
                return v.replace(tzinfo=None)
            return v
        return v
    
    @validator('data_types')
    def validate_data_types(cls, v):
        valid_types = ['logs', 'anomalies', 'ips']
        for data_type in v:
            if data_type not in valid_types:
                raise ValueError(f"Invalid data type: {data_type}")
        return v
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError("End date must be after start date")
        return v 