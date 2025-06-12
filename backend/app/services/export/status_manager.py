from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.export_status import ExportStatus

class ExportStatusManager:
    """Manages export status in the database."""

    @staticmethod
    async def create_status(metadata: Dict[str, Any]) -> ExportStatus:
        """Create a new export status."""
        async with AsyncSession(get_db()) as session:
            status = ExportStatus.from_metadata(metadata)
            session.add(status)
            await session.commit()
            return status

    @staticmethod
    async def get_status(export_id: str) -> Optional[ExportStatus]:
        """Get export status by ID."""
        async with AsyncSession(get_db()) as session:
            query = select(ExportStatus).where(ExportStatus.export_id == export_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def update_status(export_id: str, updates: Dict[str, Any]) -> Optional[ExportStatus]:
        """Update export status."""
        async with AsyncSession(get_db()) as session:
            query = select(ExportStatus).where(ExportStatus.export_id == export_id)
            result = await session.execute(query)
            status = result.scalar_one_or_none()

            if status:
                for key, value in updates.items():
                    setattr(status, key, value)
                await session.commit()
                return status
            return None

    @staticmethod
    async def list_statuses(limit: int = 100, offset: int = 0) -> List[ExportStatus]:
        """List export statuses."""
        async with AsyncSession(get_db()) as session:
            query = select(ExportStatus).order_by(ExportStatus.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def update_record_counts(export_id: str, data_type: str, count: int) -> Optional[ExportStatus]:
        """Update record counts for a data type."""
        async with AsyncSession(get_db()) as session:
            query = select(ExportStatus).where(ExportStatus.export_id == export_id)
            result = await session.execute(query)
            status = result.scalar_one_or_none()

            if status:
                if not status.record_counts:
                    status.record_counts = {}
                status.record_counts[data_type] = count
                status.total_records = sum(status.record_counts.values())
                await session.commit()
                return status
            return None

    @staticmethod
    async def update_file_sizes(export_id: str, data_type: str, size: int) -> Optional[ExportStatus]:
        """Update file sizes for a data type."""
        async with AsyncSession(get_db()) as session:
            query = select(ExportStatus).where(ExportStatus.export_id == export_id)
            result = await session.execute(query)
            status = result.scalar_one_or_none()

            if status:
                if not status.file_sizes:
                    status.file_sizes = {}
                status.file_sizes[data_type] = size
                status.total_size = sum(status.file_sizes.values())
                await session.commit()
                return status
            return None 