from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Optional
from datetime import datetime
import uuid
from fastapi.responses import FileResponse, JSONResponse
import os
import logging

from app.models.export import ExportConfig, ExportMetadata
from app.services.export.data_exporter import DataExporter
from app.services.export.status_manager import ExportStatusManager
from app.services.export.cleanup_service import ExportCleanupService

router = APIRouter(prefix="/export", tags=["export"])

logger = logging.getLogger(__name__)

# Initialize cleanup service
cleanup_service = ExportCleanupService()

@router.post("/", response_model=ExportMetadata)
async def create_export(
    config: ExportConfig,
    background_tasks: BackgroundTasks
) -> ExportMetadata:
    """Create a new export job"""
    try:
        # Generate export ID
        export_id = str(uuid.uuid4())
        
        # Create initial metadata
        metadata = {
            "export_id": export_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "export_config": config.dict(),
            "data_version": "1.0.0",
            "record_count": 0,
            "file_size": 0
        }
        
        # Store metadata in Redis
        ExportStatusManager.store_export_metadata(export_id, metadata)
        
        # Initialize exporter
        exporter = DataExporter()
        
        # Add to background tasks with proper parameters
        background_tasks.add_task(
            exporter.export_data,
            export_id=export_id,
            start_date=config.start_date,
            end_date=config.end_date,
            programs=config.processes,
            format=config.output_format,
            progress_callback=lambda eid, progress, message: ExportStatusManager.store_export_metadata(
                eid, {"export_id": eid, "progress": progress, "status_message": message, "updated_at": datetime.now().isoformat()}
            )
        )
        
        # Return initial metadata
        return ExportMetadata(
            export_id=export_id,
            data_version="1.0.0",
            export_config=config.dict(),
            record_count=0,
            file_size=0,
            status="pending"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{export_id}", summary="Download export file by export_id")
async def download_export_file(export_id: str):
    """
    Download the export file for a given export_id.
    """
    # Look up export metadata (assume ExportStatusManager or similar is used)
    export_metadata = ExportStatusManager.get_export_metadata(export_id)
    if not export_metadata:
        raise HTTPException(status_code=404, detail="Export not found")
    file_path = export_metadata.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Export file not found")
    filename = os.path.basename(file_path)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

@router.get("/{export_id}/status")
async def get_export_status(export_id: str):
    """Get export status"""
    try:
        status = await ExportStatusManager.get_status(export_id)
        if not status:
            raise HTTPException(status_code=404, detail="Export not found")
        return status.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_exports(
    limit: int = 100,
    offset: int = 0
):
    """List export history"""
    try:
        statuses = await ExportStatusManager.list_statuses(limit, offset)
        return [status.to_dict() for status in statuses]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{export_id}/progress")
async def get_export_progress(export_id: str):
    """Get detailed export progress"""
    try:
        status = await ExportStatusManager.get_status(export_id)
        if not status:
            raise HTTPException(status_code=404, detail="Export not found")
            
        return {
            "export_id": export_id,
            "status": status.status,
            "progress": getattr(status, 'progress', {}),
            "current_batch": getattr(status, 'current_batch', 0),
            "total_batches": getattr(status, 'total_batches', 0),
            "processed_records": status.total_records,
            "total_records": status.total_records,
            "start_time": status.created_at.isoformat() if status.created_at else None,
            "end_time": status.updated_at.isoformat() if status.updated_at and status.status in ["completed", "failed"] else None,
            "error_message": status.error_message
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{export_id}")
async def delete_export(export_id: str):
    """Delete an export job and its associated file."""
    try:
        # Get export metadata to find the file path
        export_metadata = ExportStatusManager.get_export_metadata(export_id)
        if not export_metadata:
            raise HTTPException(status_code=404, detail="Export not found")
        
        # Delete the export file if it exists
        file_path = export_metadata.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted export file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete export file {file_path}: {e}")
        
        # Delete metadata from Redis
        ExportStatusManager.delete_export_metadata(export_id)
        
        return {"status": "success", "message": f"Export {export_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting export {export_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup", summary="Clean up old export files and metadata")
async def cleanup_exports():
    """Clean up old export files and metadata."""
    try:
        result = await cleanup_service.cleanup_old_exports()
        return {
            "status": "success",
            "message": "Export cleanup completed",
            "details": result
        }
    except Exception as e:
        logger.error(f"Error during export cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", summary="Get export statistics")
async def get_export_stats():
    """Get statistics about export files and metadata."""
    try:
        stats = await cleanup_service.get_export_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting export stats: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 