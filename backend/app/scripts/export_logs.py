import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
import pandas as pd
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import LogEntry, AnomalyDetection, IPAddress

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExportMetadata(BaseModel):
    """Metadata for exported data"""
    export_timestamp: datetime = Field(default_factory=datetime.utcnow)
    data_version: str = "1.0"
    export_config: Dict[str, Any] = Field(default_factory=dict)
    record_count: int = 0
    file_size: int = 0
    data_quality_metrics: Dict[str, float] = Field(default_factory=dict)

class DataValidationResult(BaseModel):
    """Results of data validation"""
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    quality_metrics: Dict[str, float] = Field(default_factory=dict)

class DataValidator:
    """Validates data before export"""
    
    @staticmethod
    def validate_log_entry(entry: LogEntry) -> DataValidationResult:
        errors = []
        metrics = {}
        
        # Required field validation
        if not entry.timestamp:
            errors.append("Missing timestamp")
        if not entry.message:
            errors.append("Missing message")
            
        # Data quality metrics
        if entry.message:
            metrics["message_length"] = len(entry.message)
            metrics["has_timestamp"] = bool(entry.timestamp)
            
        return DataValidationResult(
            is_valid=len(errors) == 0,
            validation_errors=errors,
            quality_metrics=metrics
        )

class DataTransformer:
    """Transforms data before export"""
    
    @staticmethod
    def transform_log_entry(entry: LogEntry) -> Dict[str, Any]:
        """Transform a log entry into export format"""
        return {
            "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
            "message": entry.message,
            "level": entry.level,
            "source": entry.source,
            "metadata": entry.metadata,
            "transformed_at": datetime.utcnow().isoformat()
        }

class DataExporter:
    """Handles data export with validation and transformation"""
    
    def __init__(self, export_dir: str = "exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
        self.validator = DataValidator()
        self.transformer = DataTransformer()
        
    def export_logs(self, 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   batch_size: int = 1000) -> ExportMetadata:
        """Export logs with validation and transformation"""
        metadata = ExportMetadata()
        db = next(get_db())
        
        try:
            # Query logs
            query = db.query(LogEntry)
            if start_date:
                query = query.filter(LogEntry.timestamp >= start_date)
            if end_date:
                query = query.filter(LogEntry.timestamp <= end_date)
                
            # Process in batches
            total_records = 0
            all_data = []
            
            for batch in self._batch_query(query, batch_size):
                for entry in batch:
                    # Validate
                    validation = self.validator.validate_log_entry(entry)
                    if not validation.is_valid:
                        logger.warning(f"Invalid log entry: {validation.validation_errors}")
                        continue
                        
                    # Transform
                    transformed_data = self.transformer.transform_log_entry(entry)
                    all_data.append(transformed_data)
                    total_records += 1
                    
                    # Update quality metrics
                    metadata.data_quality_metrics.update(validation.quality_metrics)
            
            # Export to file
            if all_data:
                export_path = self._write_export_file(all_data, "logs")
                metadata.record_count = total_records
                metadata.file_size = export_path.stat().st_size
                
            return metadata
            
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            raise
            
    def _batch_query(self, query, batch_size: int):
        """Helper to process query in batches"""
        offset = 0
        while True:
            batch = query.offset(offset).limit(batch_size).all()
            if not batch:
                break
            yield batch
            offset += batch_size
            
    def _write_export_file(self, data: List[Dict], data_type: str) -> Path:
        """Write export data to file"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{data_type}_{timestamp}.json"
        filepath = self.export_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump({
                "metadata": ExportMetadata(
                    record_count=len(data),
                    file_size=0  # Will be updated after write
                ).dict(),
                "data": data
            }, f, indent=2)
            
        return filepath

def main():
    """Main export function"""
    exporter = DataExporter()
    
    # Example usage
    try:
        metadata = exporter.export_logs()
        logger.info(f"Export completed successfully:")
        logger.info(f"Records exported: {metadata.record_count}")
        logger.info(f"File size: {metadata.file_size} bytes")
        logger.info(f"Quality metrics: {metadata.data_quality_metrics}")
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
