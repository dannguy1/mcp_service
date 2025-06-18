import json
import logging
import redis
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_connection
from app.models.export_status import ExportStatus

logger = logging.getLogger(__name__)

class ExportStatusManager:
    """Manages export status using Redis for persistence."""

    def __init__(self):
        # Initialize Redis client
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )

    @classmethod
    def _get_redis_client(cls):
        """Get Redis client instance."""
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        return redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )

    @staticmethod
    def get_export_metadata(export_id: str) -> Optional[Dict[str, Any]]:
        """Get export metadata by export_id from Redis."""
        try:
            redis_client = ExportStatusManager._get_redis_client()
            metadata_key = f"export:metadata:{export_id}"
            metadata_json = redis_client.get(metadata_key)
            
            if metadata_json:
                metadata = json.loads(metadata_json)
                # Ensure export_id is present in metadata
                if "export_id" not in metadata:
                    metadata["export_id"] = export_id
                return metadata
            else:
                logger.warning(f"Export metadata not found for export_id: {export_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving export metadata for {export_id}: {e}")
            return None

    @staticmethod
    def store_export_metadata(export_id: str, metadata: Dict[str, Any]) -> bool:
        """Store export metadata in Redis."""
        try:
            redis_client = ExportStatusManager._get_redis_client()
            metadata_key = f"export:metadata:{export_id}"
            
            # Convert datetime objects to ISO format strings for JSON serialization
            serializable_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, datetime):
                    serializable_metadata[key] = value.isoformat()
                else:
                    serializable_metadata[key] = value
            
            # Store metadata with expiration (7 days)
            redis_client.setex(
                metadata_key,
                7 * 24 * 60 * 60,  # 7 days in seconds
                json.dumps(serializable_metadata)
            )
            
            logger.info(f"Stored export metadata for export_id: {export_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing export metadata for {export_id}: {e}")
            return False

    @staticmethod
    async def create_status(metadata: Dict[str, Any]) -> ExportStatus:
        """Create a new export status and store metadata."""
        try:
            status = ExportStatus.from_metadata(metadata)
            
            # Store metadata in Redis
            export_id = metadata.get('export_id')
            if export_id:
                ExportStatusManager.store_export_metadata(export_id, metadata)
            
            return status
        except Exception as e:
            logger.error(f"Error creating export status: {e}")
            raise

    @staticmethod
    async def get_status(export_id: str) -> Optional[ExportStatus]:
        """Get export status by ID."""
        try:
            metadata = ExportStatusManager.get_export_metadata(export_id)
            if metadata:
                return ExportStatus.from_metadata(metadata)
            return None
        except Exception as e:
            logger.error(f"Error getting export status for {export_id}: {e}")
            return None

    @staticmethod
    async def update_status(export_id: str, updates: Dict[str, Any]) -> Optional[ExportStatus]:
        """Update export status."""
        try:
            # Get existing metadata
            metadata = ExportStatusManager.get_export_metadata(export_id)
            if not metadata:
                return None
            
            # Update metadata
            metadata.update(updates)
            metadata['updated_at'] = datetime.now().isoformat()
            
            # Store updated metadata
            ExportStatusManager.store_export_metadata(export_id, metadata)
            
            return ExportStatus.from_metadata(metadata)
        except Exception as e:
            logger.error(f"Error updating export status for {export_id}: {e}")
            return None

    @staticmethod
    async def list_statuses(limit: int = 100, offset: int = 0) -> List[ExportStatus]:
        """List export statuses from Redis."""
        try:
            redis_client = ExportStatusManager._get_redis_client()
            pattern = "export:metadata:*"
            keys = redis_client.keys(pattern)
            
            statuses = []
            for key in keys[offset:offset + limit]:
                export_id = key.split(":")[-1]
                metadata = ExportStatusManager.get_export_metadata(export_id)
                if metadata:
                    # Ensure export_id is present in metadata
                    if "export_id" not in metadata:
                        metadata["export_id"] = export_id
                    statuses.append(ExportStatus.from_metadata(metadata))
            
            return statuses
        except Exception as e:
            logger.error(f"Error listing export statuses: {e}")
            return []

    @staticmethod
    async def update_record_counts(export_id: str, data_type: str, count: int) -> Optional[ExportStatus]:
        """Update record counts for a data type."""
        try:
            metadata = ExportStatusManager.get_export_metadata(export_id)
            if not metadata:
                return None
            
            if 'record_counts' not in metadata:
                metadata['record_counts'] = {}
            
            metadata['record_counts'][data_type] = count
            metadata['updated_at'] = datetime.now().isoformat()
            
            ExportStatusManager.store_export_metadata(export_id, metadata)
            return ExportStatus.from_metadata(metadata)
        except Exception as e:
            logger.error(f"Error updating record counts for {export_id}: {e}")
            return None

    @staticmethod
    async def update_file_sizes(export_id: str, data_type: str, size: int) -> Optional[ExportStatus]:
        """Update file sizes for a data type."""
        try:
            metadata = ExportStatusManager.get_export_metadata(export_id)
            if not metadata:
                return None
            
            if 'file_sizes' not in metadata:
                metadata['file_sizes'] = {}
            
            metadata['file_sizes'][data_type] = size
            metadata['updated_at'] = datetime.now().isoformat()
            
            ExportStatusManager.store_export_metadata(export_id, metadata)
            return ExportStatus.from_metadata(metadata)
        except Exception as e:
            logger.error(f"Error updating file sizes for {export_id}: {e}")
            return None

    @staticmethod
    async def update_progress(
        export_id: str,
        data_type: str,
        processed: int,
        total: int
    ) -> None:
        """Update progress for a specific data type."""
        try:
            metadata = ExportStatusManager.get_export_metadata(export_id)
            if not metadata:
                return
            
            if 'progress' not in metadata:
                metadata['progress'] = {}
            
            metadata['progress'][data_type] = {
                'processed': processed,
                'total': total,
                'percentage': (processed / total * 100) if total > 0 else 0
            }
            metadata['updated_at'] = datetime.now().isoformat()
            
            ExportStatusManager.store_export_metadata(export_id, metadata)
        except Exception as e:
            logger.error(f"Error updating progress for {export_id}: {e}")

    @staticmethod
    async def update_batch_progress(
        export_id: str,
        current_batch: int,
        total_batches: int
    ) -> None:
        """Update batch processing progress."""
        try:
            metadata = ExportStatusManager.get_export_metadata(export_id)
            if not metadata:
                return
            
            metadata['batch_progress'] = {
                'current_batch': current_batch,
                'total_batches': total_batches,
                'percentage': (current_batch / total_batches * 100) if total_batches > 0 else 0
            }
            metadata['updated_at'] = datetime.now().isoformat()
            
            ExportStatusManager.store_export_metadata(export_id, metadata)
        except Exception as e:
            logger.error(f"Error updating batch progress for {export_id}: {e}")

    @staticmethod
    def delete_export_metadata(export_id: str) -> bool:
        """Delete export metadata from Redis."""
        try:
            redis_client = ExportStatusManager._get_redis_client()
            metadata_key = f"export:metadata:{export_id}"
            redis_client.delete(metadata_key)
            
            logger.info(f"Deleted export metadata for export_id: {export_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting export metadata for {export_id}: {e}")
            return False 