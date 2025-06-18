import os
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from app.services.export.status_manager import ExportStatusManager

logger = logging.getLogger(__name__)

class ExportCleanupService:
    """Service for cleaning up old export files and metadata."""
    
    def __init__(self, exports_dir: str = "exports", max_age_days: int = 7):
        self.exports_dir = Path(exports_dir)
        self.max_age_days = max_age_days
        self.exports_dir.mkdir(exist_ok=True)
    
    async def cleanup_old_exports(self) -> Dict[str, Any]:
        """Clean up old export files and metadata."""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.max_age_days)
            deleted_files = 0
            deleted_metadata = 0
            errors = []
            
            # Get all export files
            export_files = list(self.exports_dir.glob("export_*"))
            
            for file_path in export_files:
                try:
                    # Check file modification time
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if file_mtime < cutoff_time:
                        # Extract export_id from filename
                        # Expected format: export_{export_id}_{timestamp}.{ext}
                        filename = file_path.name
                        if filename.startswith("export_") and "_" in filename:
                            parts = filename.split("_")
                            if len(parts) >= 3:
                                export_id = parts[1]
                                
                                # Delete metadata from Redis
                                if ExportStatusManager.delete_export_metadata(export_id):
                                    deleted_metadata += 1
                                    logger.info(f"Deleted metadata for export: {export_id}")
                                
                                # Delete the file
                                file_path.unlink()
                                deleted_files += 1
                                logger.info(f"Deleted old export file: {file_path}")
                            else:
                                # If we can't parse the filename, just delete the file
                                file_path.unlink()
                                deleted_files += 1
                                logger.info(f"Deleted unparseable export file: {file_path}")
                
                except Exception as e:
                    error_msg = f"Error cleaning up file {file_path}: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Also clean up orphaned metadata (metadata without files)
            orphaned_metadata = await self._cleanup_orphaned_metadata()
            deleted_metadata += orphaned_metadata
            
            result = {
                "deleted_files": deleted_files,
                "deleted_metadata": deleted_metadata,
                "errors": errors,
                "cleanup_time": datetime.now().isoformat()
            }
            
            logger.info(f"Export cleanup completed: {deleted_files} files, {deleted_metadata} metadata entries deleted")
            return result
            
        except Exception as e:
            logger.error(f"Error during export cleanup: {e}")
            raise
    
    async def _cleanup_orphaned_metadata(self) -> int:
        """Clean up metadata entries that don't have corresponding files."""
        try:
            deleted_count = 0
            
            # Get all export metadata from Redis
            redis_client = ExportStatusManager._get_redis_client()
            pattern = "export:metadata:*"
            keys = redis_client.keys(pattern)
            
            for key in keys:
                try:
                    export_id = key.split(":")[-1]
                    metadata = ExportStatusManager.get_export_metadata(export_id)
                    
                    if metadata:
                        file_path = metadata.get("file_path")
                        if file_path and not os.path.exists(file_path):
                            # File doesn't exist, delete metadata
                            if ExportStatusManager.delete_export_metadata(export_id):
                                deleted_count += 1
                                logger.info(f"Deleted orphaned metadata for export: {export_id}")
                
                except Exception as e:
                    logger.warning(f"Error checking orphaned metadata for key {key}: {e}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up orphaned metadata: {e}")
            return 0
    
    async def get_export_stats(self) -> Dict[str, Any]:
        """Get statistics about export files and metadata."""
        try:
            # Count files
            export_files = list(self.exports_dir.glob("export_*"))
            total_files = len(export_files)
            total_size = sum(f.stat().st_size for f in export_files)
            
            # Count metadata entries
            redis_client = ExportStatusManager._get_redis_client()
            pattern = "export:metadata:*"
            metadata_keys = redis_client.keys(pattern)
            total_metadata = len(metadata_keys)
            
            # Find old files
            cutoff_time = datetime.now() - timedelta(days=self.max_age_days)
            old_files = [f for f in export_files if datetime.fromtimestamp(f.stat().st_mtime) < cutoff_time]
            
            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_metadata": total_metadata,
                "old_files": len(old_files),
                "exports_dir": str(self.exports_dir),
                "max_age_days": self.max_age_days
            }
            
        except Exception as e:
            logger.error(f"Error getting export stats: {e}")
            return {"error": str(e)}
    
    async def start_cleanup_scheduler(self, interval_hours: int = 24):
        """Start the cleanup scheduler to run periodically."""
        logger.info(f"Starting export cleanup scheduler (interval: {interval_hours} hours)")
        
        while True:
            try:
                await self.cleanup_old_exports()
                await asyncio.sleep(interval_hours * 3600)  # Convert hours to seconds
            except Exception as e:
                logger.error(f"Error in cleanup scheduler: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying 