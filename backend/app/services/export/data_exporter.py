import os
import json
import uuid
import logging
import gzip
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.export import ExportConfig, ExportMetadata
from app.services.export.data_validator import DataValidator
from app.services.export.data_transformer import DataTransformer
from app.db import get_db
from app.models.log import LogEntry
from app.models.anomaly import AnomalyDetection
from app.models.ip import IPAddress

logger = logging.getLogger(__name__)

class DataExporter:
    """Exports data for training purposes."""
    
    def __init__(self, config: ExportConfig):
        self.config = config
        self.validator = DataValidator(config.validation_level)
        self.transformer = DataTransformer(config)
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)

    def _write_data(self, data: List[Dict[str, Any]], file_path: Path) -> int:
        """Write data to file with optional compression."""
        if self.config.compression:
            with gzip.open(file_path, 'wt', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        else:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        return file_path.stat().st_size

    async def export_logs(self, start_date: datetime, end_date: datetime) -> ExportMetadata:
        """Export log entries."""
        try:
            # Generate export ID
            export_id = str(uuid.uuid4())
            
            # Initialize metadata
            metadata = ExportMetadata(
                export_id=export_id,
                data_version="1.0.0",
                export_config=self.config.dict(),
                record_count=0,
                file_size=0,
                status="running"
            )

            # Create export directory
            export_path = self.export_dir / f"logs_{export_id}"
            export_path.mkdir(exist_ok=True)

            # Export data in batches
            total_records = 0
            batch_number = 0
            
            while True:
                # Fetch batch of logs
                logs = await self._fetch_logs(start_date, end_date, batch_number)
                if not logs:
                    break

                # Validate and transform batch
                valid_logs = []
                for log in logs:
                    validation = self.validator.validate_log_entry(log)
                    if validation.is_valid:
                        transformed = self.transformer.transform("log_entry", log)
                        valid_logs.append(transformed)

                # Write batch to file
                if valid_logs:
                    batch_file = export_path / f"batch_{batch_number}.json"
                    if self.config.compression:
                        batch_file = batch_file.with_suffix('.json.gz')
                    file_size = self._write_data(valid_logs, batch_file)
                    total_records += len(valid_logs)

                batch_number += 1

            # Update metadata
            metadata.record_count = total_records
            metadata.file_size = self._get_export_size(export_path)
            metadata.status = "completed"

            # Save metadata
            metadata_file = export_path / "metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata.dict(), f, indent=2)

            return metadata

        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            if metadata:
                metadata.status = "failed"
                metadata.error_message = str(e)
            raise

    async def export_anomalies(self, start_date: datetime, end_date: datetime) -> ExportMetadata:
        """Export anomaly detection results."""
        try:
            # Generate export ID
            export_id = str(uuid.uuid4())
            
            # Initialize metadata
            metadata = ExportMetadata(
                export_id=export_id,
                data_version="1.0.0",
                export_config=self.config.dict(),
                record_count=0,
                file_size=0,
                status="running"
            )

            # Create export directory
            export_path = self.export_dir / f"anomalies_{export_id}"
            export_path.mkdir(exist_ok=True)

            # Export data in batches
            total_records = 0
            batch_number = 0
            
            while True:
                # Fetch batch of anomalies
                anomalies = await self._fetch_anomalies(start_date, end_date, batch_number)
                if not anomalies:
                    break

                # Validate and transform batch
                valid_anomalies = []
                for anomaly in anomalies:
                    validation = self.validator.validate_anomaly(anomaly)
                    if validation.is_valid:
                        transformed = self.transformer.transform("anomaly", anomaly)
                        valid_anomalies.append(transformed)

                # Write batch to file
                if valid_anomalies:
                    batch_file = export_path / f"batch_{batch_number}.json"
                    if self.config.compression:
                        batch_file = batch_file.with_suffix('.json.gz')
                    file_size = self._write_data(valid_anomalies, batch_file)
                    total_records += len(valid_anomalies)

                batch_number += 1

            # Update metadata
            metadata.record_count = total_records
            metadata.file_size = self._get_export_size(export_path)
            metadata.status = "completed"

            # Save metadata
            metadata_file = export_path / "metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata.dict(), f, indent=2)

            return metadata

        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            if metadata:
                metadata.status = "failed"
                metadata.error_message = str(e)
            raise

    async def export_ips(self, start_date: datetime, end_date: datetime) -> ExportMetadata:
        """Export IP address records."""
        try:
            # Generate export ID
            export_id = str(uuid.uuid4())
            
            # Initialize metadata
            metadata = ExportMetadata(
                export_id=export_id,
                data_version="1.0.0",
                export_config=self.config.dict(),
                record_count=0,
                file_size=0,
                status="running"
            )

            # Create export directory
            export_path = self.export_dir / f"ips_{export_id}"
            export_path.mkdir(exist_ok=True)

            # Export data in batches
            total_records = 0
            batch_number = 0
            
            while True:
                # Fetch batch of IPs
                ips = await self._fetch_ips(start_date, end_date, batch_number)
                if not ips:
                    break

                # Validate and transform batch
                valid_ips = []
                for ip in ips:
                    validation = self.validator.validate_ip(ip)
                    if validation.is_valid:
                        transformed = self.transformer.transform("ip", ip)
                        valid_ips.append(transformed)

                # Write batch to file
                if valid_ips:
                    batch_file = export_path / f"batch_{batch_number}.json"
                    if self.config.compression:
                        batch_file = batch_file.with_suffix('.json.gz')
                    file_size = self._write_data(valid_ips, batch_file)
                    total_records += len(valid_ips)

                batch_number += 1

            # Update metadata
            metadata.record_count = total_records
            metadata.file_size = self._get_export_size(export_path)
            metadata.status = "completed"

            # Save metadata
            metadata_file = export_path / "metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata.dict(), f, indent=2)

            return metadata

        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            if metadata:
                metadata.status = "failed"
                metadata.error_message = str(e)
            raise

    async def _fetch_logs(self, start_date: datetime, end_date: datetime, batch_number: int) -> List[Dict[str, Any]]:
        """Fetch a batch of log entries."""
        try:
            # Calculate offset and limit for pagination
            offset = batch_number * self.config.batch_size
            limit = self.config.batch_size

            # Start with base query
            query = self.db.query(LogEntry).filter(
                LogEntry.timestamp >= start_date,
                LogEntry.timestamp <= end_date
            )
            
            # Add process filtering if specified
            if hasattr(self.config, 'processes') and self.config.processes:
                query = query.filter(LogEntry.process_name.in_(self.config.processes))
            
            # Execute query with pagination
            logs = query.offset(offset).limit(limit).all()
            
            # Convert to dictionaries
            return [log.to_dict() for log in logs]
            
        except Exception as e:
            logger.error(f"Error fetching logs: {str(e)}")
            raise

    async def _fetch_anomalies(self, start_date: datetime, end_date: datetime, batch_number: int) -> List[Dict[str, Any]]:
        """Fetch a batch of anomaly detection results."""
        async with AsyncSession(get_db()) as session:
            # Calculate offset and limit for pagination
            offset = batch_number * self.config.batch_size
            limit = self.config.batch_size

            # Query anomalies within date range
            query = select(AnomalyDetection).where(
                and_(
                    AnomalyDetection.timestamp >= start_date,
                    AnomalyDetection.timestamp <= end_date
                )
            ).offset(offset).limit(limit)

            result = await session.execute(query)
            anomalies = result.scalars().all()

            # Convert to dictionaries
            return [anomaly.to_dict() for anomaly in anomalies]

    async def _fetch_ips(self, start_date: datetime, end_date: datetime, batch_number: int) -> List[Dict[str, Any]]:
        """Fetch a batch of IP address records."""
        async with AsyncSession(get_db()) as session:
            # Calculate offset and limit for pagination
            offset = batch_number * self.config.batch_size
            limit = self.config.batch_size

            # Query IPs within date range
            query = select(IPAddress).where(
                and_(
                    IPAddress.last_seen >= start_date,
                    IPAddress.last_seen <= end_date
                )
            ).offset(offset).limit(limit)

            result = await session.execute(query)
            ips = result.scalars().all()

            # Convert to dictionaries
            return [ip.to_dict() for ip in ips]

    def _get_export_size(self, export_path: Path) -> int:
        """Calculate total size of exported files."""
        total_size = 0
        for file in export_path.glob("**/*"):
            if file.is_file():
                total_size += file.stat().st_size
        return total_size 