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
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.status,
            "data_types": self.data_types or [],
            "config": self.config or {},
            "record_counts": self.record_counts or {},
            "file_sizes": self.file_sizes or {},
            "error_message": self.error_message,
            "is_compressed": self.is_compressed,
            "total_records": self.total_records,
            "total_size": self.total_size
        }

    @classmethod
    def from_metadata(cls, metadata: Dict[str, Any]) -> "ExportStatus":
        """Create from export metadata."""
        try:
            # Handle different metadata structures
            export_config = metadata.get("export_config", {})
            data_types = export_config.get("data_types", []) if isinstance(export_config, dict) else []
            
            # Parse datetime fields safely
            created_at = None
            updated_at = None
            
            if metadata.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(metadata["created_at"].replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    created_at = datetime.utcnow()
            
            if metadata.get("updated_at"):
                try:
                    updated_at = datetime.fromisoformat(metadata["updated_at"].replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    updated_at = datetime.utcnow()
            
            # Determine status from progress or status field
            status = metadata.get("status", "pending")
            if "progress" in metadata:
                progress = metadata.get("progress", 0)
                if progress == -1:
                    status = "failed"
                elif progress == 100:
                    status = "completed"
                elif progress > 0:
                    status = "running"
            
            # Extract error message from status_message if status is failed
            error_message = metadata.get("error_message")
            if status == "failed" and not error_message:
                error_message = metadata.get("status_message")
            
            return cls(
                export_id=metadata.get("export_id", ""),
                created_at=created_at,
                updated_at=updated_at,
                status=status,
                data_types=data_types,
                config=export_config,
                record_counts=metadata.get("record_counts", {}),
                file_sizes=metadata.get("file_sizes", {}),
                error_message=error_message,
                is_compressed=export_config.get("compression", False) if isinstance(export_config, dict) else False,
                total_records=metadata.get("records_exported", metadata.get("record_count", 0)),
                total_size=metadata.get("file_size", 0)
            )
        except Exception as e:
            # Return a minimal status object if metadata parsing fails
            return cls(
                export_id=metadata.get("export_id", ""),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                status=metadata.get("status", "unknown"),
                data_types=[],
                config={},
                record_counts={},
                file_sizes={},
                error_message=f"Failed to parse metadata: {str(e)}",
                is_compressed=False,
                total_records=0,
                total_size=0
            ) 