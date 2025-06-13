from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
import uuid
import logging

from app.models.export import ExportConfig, ExportMetadata
from app.services.export.data_exporter import DataExporter
from app.services.export.status_manager import ExportStatusManager

router = APIRouter()

logger = logging.getLogger(__name__)

class ExportRequest(BaseModel):
    """Export request model."""
    start_date: datetime
    end_date: datetime
    data_types: List[str]
    batch_size: Optional[int] = 1000
    include_metadata: Optional[bool] = True
    validation_level: Optional[str] = "basic"
    output_format: Optional[str] = "json"
    compression: Optional[bool] = False
    processes: Optional[List[str]] = Field(default_factory=list, description="List of processes to filter by")

@router.post("/export", response_model=ExportMetadata)
async def create_export(request: ExportRequest, background_tasks: BackgroundTasks):
    """Create a new export."""
    try:
        # Create export config
        config = ExportConfig(
            start_date=request.start_date,
            end_date=request.end_date,
            data_types=request.data_types,
            batch_size=request.batch_size,
            include_metadata=request.include_metadata,
            validation_level=request.validation_level,
            output_format=request.output_format,
            compression=request.compression
        )

        # Initialize exporter
        exporter = DataExporter(config)

        # Create initial metadata
        metadata = ExportMetadata(
            export_id=str(uuid.uuid4()),
            data_version="1.0.0",
            export_config=config.dict(),
            record_count=0,
            file_size=0,
            status="pending"
        )

        # Create status in database
        await ExportStatusManager.create_status(metadata.dict())

        # Start export in background
        background_tasks.add_task(run_export, exporter, config, metadata.export_id)
        
        return metadata

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{export_id}", response_model=ExportMetadata)
async def get_export_status(export_id: str):
    """Get export status."""
    try:
        status = await ExportStatusManager.get_status(export_id)
        if not status:
            raise HTTPException(status_code=404, detail="Export not found")
        
        return ExportMetadata(
            export_id=status.export_id,
            data_version="1.0.0",
            export_config=status.config,
            record_count=status.total_records,
            file_size=status.total_size,
            status=status.status,
            error_message=status.error_message
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export", response_model=List[ExportMetadata])
async def list_exports(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all exports."""
    try:
        statuses = await ExportStatusManager.list_statuses(limit, offset)
        return [
            ExportMetadata(
                export_id=status.export_id,
                data_version="1.0.0",
                export_config=status.config,
                record_count=status.total_records,
                file_size=status.total_size,
                status=status.status,
                error_message=status.error_message
            )
            for status in statuses
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def run_export(exporter: DataExporter, config: ExportConfig, export_id: str):
    """Run export in background."""
    try:
        # Update status to running
        await ExportStatusManager.update_status(export_id, {"status": "running"})

        for data_type in config.data_types:
            try:
                if data_type == "logs":
                    metadata = await exporter.export_logs(config.start_date, config.end_date)
                elif data_type == "anomalies":
                    metadata = await exporter.export_anomalies(config.start_date, config.end_date)
                elif data_type == "ips":
                    metadata = await exporter.export_ips(config.start_date, config.end_date)
                else:
                    logger.warning(f"Unsupported data type: {data_type}")
                    continue

                # Update record counts and file sizes
                await ExportStatusManager.update_record_counts(export_id, data_type, metadata.record_count)
                await ExportStatusManager.update_file_sizes(export_id, data_type, metadata.file_size)

            except Exception as e:
                logger.error(f"Failed to export {data_type}: {str(e)}")
                await ExportStatusManager.update_status(export_id, {
                    "status": "failed",
                    "error_message": f"Failed to export {data_type}: {str(e)}"
                })
                return

        # Update status to completed
        await ExportStatusManager.update_status(export_id, {"status": "completed"})

    except Exception as e:
        logger.error(f"Background export failed: {str(e)}")
        await ExportStatusManager.update_status(export_id, {
            "status": "failed",
            "error_message": str(e)
        }) 