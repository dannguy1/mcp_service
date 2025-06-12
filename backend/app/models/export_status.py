from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, DateTime, Integer, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ExportStatus(Base):
    """Database model for tracking export status."""
    __tablename__ = "export_status"

    export_id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String, default="pending")  # pending, running, completed, failed
    data_types = Column(JSON)  # List of data types being exported
    config = Column(JSON)  # Export configuration
    record_counts = Column(JSON)  # Counts per data type
    file_sizes = Column(JSON)  # File sizes per data type
    error_message = Column(String, nullable=True)
    is_compressed = Column(Boolean, default=False)
    total_records = Column(Integer, default=0)
    total_size = Column(Integer, default=0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "export_id": self.export_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status,
            "data_types": self.data_types,
            "config": self.config,
            "record_counts": self.record_counts,
            "file_sizes": self.file_sizes,
            "error_message": self.error_message,
            "is_compressed": self.is_compressed,
            "total_records": self.total_records,
            "total_size": self.total_size
        }

    @classmethod
    def from_metadata(cls, metadata: Dict[str, Any]) -> "ExportStatus":
        """Create from export metadata."""
        return cls(
            export_id=metadata["export_id"],
            status=metadata["status"],
            data_types=metadata["export_config"]["data_types"],
            config=metadata["export_config"],
            record_counts={},
            file_sizes={},
            error_message=metadata.get("error_message"),
            is_compressed=metadata["export_config"].get("compression", False),
            total_records=metadata["record_count"],
            total_size=metadata["file_size"]
        ) 