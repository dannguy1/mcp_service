import os
import json
import uuid
import logging
import gzip
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import asyncio
import yaml
import csv
import zipfile
import tempfile

from app.models.export import ExportConfig, ExportMetadata
from app.services.export.data_validator import DataValidator
from app.services.export.data_transformer import DataTransformer
from app.services.export.status_manager import ExportStatusManager
from app.mcp_service.data_service import DataService

logger = logging.getLogger(__name__)

class DataExporter:
    """Exports data from the remote PostgreSQL database to various formats."""

    def __init__(self, config_path: str = "app/config/data_source_config.yaml"):
        self.config_path = config_path
        self.data_service = None
        self.db_config = None
        self._load_config()

    def _load_config(self):
        """Load database configuration from YAML file."""
        try:
            config_path = Path(self.config_path)
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            with open(config_path, "r") as f:
                self.db_config = yaml.safe_load(f)
            
            logger.info("Database configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    async def _initialize_data_service(self):
        """Initialize the DataService with database connection."""
        if self.data_service is None:
            try:
                # Create DataService instance with config
                self.data_service = DataService(self.db_config)
                await self.data_service.start()
                logger.info("DataService initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize DataService: {e}")
                raise

    async def export_data(
        self,
        export_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        programs: Optional[List[str]] = None,
        format: str = "json",
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Export data from the remote PostgreSQL database.
        
        Args:
            export_id: Unique identifier for this export
            start_date: Start date for data range (None for no lower bound)
            end_date: End date for data range (None for no upper bound)
            programs: List of program names to filter by (None for all programs)
            format: Export format ('json', 'csv', 'zip')
            progress_callback: Callback function for progress updates
            
        Returns:
            Dictionary containing export metadata and file path
        """
        try:
            await self._initialize_data_service()
            
            # Update progress
            if progress_callback:
                progress_callback(export_id, 10, "Connecting to database...")
            
            # Get logs from the real database using DataService
            logs = await self.data_service.get_logs_by_program(
                start_time=start_date,
                end_time=end_date,
                programs=programs
            )
            
            if progress_callback:
                progress_callback(export_id, 30, f"Retrieved {len(logs)} log entries")
            
            if not logs:
                logger.warning("No logs found for the specified criteria")
                return {
                    "export_id": export_id,
                    "status": "completed",
                    "records_exported": 0,
                    "file_path": None,
                    "message": "No data found for export criteria"
                }
            
            # Update progress
            if progress_callback:
                progress_callback(export_id, 50, "Processing data...")
            
            # Process and format the data
            processed_data = await self._process_logs(logs)
            
            if progress_callback:
                progress_callback(export_id, 70, "Generating export file...")
            
            # Generate export file
            file_path = await self._generate_export_file(
                processed_data, export_id, format
            )
            
            if progress_callback:
                progress_callback(export_id, 90, "Finalizing export...")
            
            # Create export metadata
            export_metadata = {
                "export_id": export_id,
                "status": "completed",
                "created_at": datetime.now().isoformat(),
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "programs": programs,
                "format": format,
                "records_exported": len(logs),
                "file_path": file_path,
                "file_size": os.path.getsize(file_path) if file_path else 0
            }
            
            # Store final metadata in Redis
            ExportStatusManager.store_export_metadata(export_id, export_metadata)
            
            if progress_callback:
                progress_callback(export_id, 100, "Export completed successfully")
            
            logger.info(f"Export {export_id} completed: {len(logs)} records exported")
            return export_metadata
            
        except Exception as e:
            logger.error(f"Export failed for {export_id}: {e}")
            if progress_callback:
                progress_callback(export_id, -1, f"Export failed: {str(e)}")
            raise

    async def _process_logs(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and clean log data for export.
        
        Args:
            logs: Raw log entries from database
            
        Returns:
            Processed log entries ready for export
        """
        processed_logs = []
        
        for log in logs:
            try:
                # Clean and structure the log entry
                processed_log = {
                    "id": log.get("id"),
                    "device_id": log.get("device_id"),
                    "device_ip": log.get("device_ip"),
                    "timestamp": log.get("timestamp").isoformat() if log.get("timestamp") else None,
                    "log_level": log.get("log_level"),
                    "process_name": log.get("process_name"),
                    "message": log.get("message"),
                    "raw_message": log.get("raw_message"),
                    "structured_data": self._parse_structured_data(log.get("structured_data")),
                    "pushed_to_ai": log.get("pushed_to_ai"),
                    "pushed_at": log.get("pushed_at").isoformat() if log.get("pushed_at") else None,
                    "push_attempts": log.get("push_attempts"),
                    "last_push_error": log.get("last_push_error")
                }
                
                processed_logs.append(processed_log)
                
            except Exception as e:
                logger.warning(f"Failed to process log entry {log.get('id')}: {e}")
                continue
        
        return processed_logs

    def _parse_structured_data(self, structured_data: Any) -> Dict[str, Any]:
        """Parse structured data from database format."""
        if not structured_data:
            return {}
        
        try:
            if isinstance(structured_data, str):
                return json.loads(structured_data)
            elif isinstance(structured_data, dict):
                return structured_data
            else:
                return {"raw_data": str(structured_data)}
        except Exception as e:
            logger.warning(f"Failed to parse structured data: {e}")
            return {"parse_error": str(e), "raw_data": str(structured_data)}

    async def _generate_export_file(
        self, 
        data: List[Dict[str, Any]], 
        export_id: str, 
        format: str
    ) -> str:
        """
        Generate export file in the specified format.
        
        Args:
            data: Processed data to export
            export_id: Export identifier
            format: Export format
            
        Returns:
            Path to the generated file
        """
        # Create exports directory if it doesn't exist
        exports_dir = Path("exports")
        exports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == "json":
            file_path = exports_dir / f"export_{export_id}_{timestamp}.json"
            await self._export_to_json(data, file_path)
            
        elif format.lower() == "csv":
            file_path = exports_dir / f"export_{export_id}_{timestamp}.csv"
            await self._export_to_csv(data, file_path)
            
        elif format.lower() == "zip":
            file_path = exports_dir / f"export_{export_id}_{timestamp}.zip"
            await self._export_to_zip(data, file_path)
            
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        logger.info(f"Export file generated: {file_path}")
        return str(file_path)

    async def _export_to_json(self, data: List[Dict[str, Any]], file_path: Path):
        """Export data to JSON format."""
        export_data = {
            "export_metadata": {
                "created_at": datetime.now().isoformat(),
                "total_records": len(data),
                "format": "json"
            },
            "data": data
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    async def _export_to_csv(self, data: List[Dict[str, Any]], file_path: Path):
        """Export data to CSV format."""
        if not data:
            return
        
        # Get all unique field names
        fieldnames = set()
        for record in data:
            fieldnames.update(record.keys())
        
        fieldnames = sorted(list(fieldnames))
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in data:
                # Ensure all fields are present
                row = {field: record.get(field, '') for field in fieldnames}
                writer.writerow(row)

    async def _export_to_zip(self, data: List[Dict[str, Any]], file_path: Path):
        """Export data to ZIP format containing JSON and CSV files."""
        with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add JSON file
            json_data = {
                "export_metadata": {
                    "created_at": datetime.now().isoformat(),
                    "total_records": len(data),
                    "format": "zip"
                },
                "data": data
            }
            
            zipf.writestr("data.json", json.dumps(json_data, indent=2, ensure_ascii=False))
            
            # Add CSV file
            if data:
                fieldnames = set()
                for record in data:
                    fieldnames.update(record.keys())
                fieldnames = sorted(list(fieldnames))
                
                csv_content = []
                csv_content.append(','.join(fieldnames))
                
                for record in data:
                    row = [str(record.get(field, '')) for field in fieldnames]
                    csv_content.append(','.join(row))
                
                zipf.writestr("data.csv", '\n'.join(csv_content))

    async def cleanup_old_exports(self, max_age_days: int = 7):
        """Clean up old export files."""
        try:
            exports_dir = Path("exports")
            if not exports_dir.exists():
                return
            
            cutoff_time = datetime.now() - timedelta(days=max_age_days)
            deleted_count = 0
            
            for file_path in exports_dir.glob("export_*"):
                if file_path.stat().st_mtime < cutoff_time.timestamp():
                    file_path.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old export files")
                
        except Exception as e:
            logger.error(f"Error cleaning up old exports: {e}")

    async def close(self):
        """Close database connections."""
        if self.data_service:
            await self.data_service.stop() 