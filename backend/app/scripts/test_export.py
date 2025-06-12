#!/usr/bin/env python3
import asyncio
import logging
from datetime import datetime, timedelta
from app.models.export import ExportConfig
from app.services.export.data_exporter import DataExporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_export():
    """Test the export functionality."""
    try:
        # Create export config
        config = ExportConfig(
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow(),
            data_types=["logs", "anomalies", "ips"],
            batch_size=1000,
            include_metadata=True,
            validation_level="basic",
            output_format="json",
            compression=False
        )

        # Initialize exporter
        exporter = DataExporter(config)

        # Test log export
        logger.info("Testing log export...")
        metadata = await exporter.export_logs(config.start_date, config.end_date)
        logger.info(f"Log export completed: {metadata.dict()}")

        # Test anomaly export
        logger.info("Testing anomaly export...")
        metadata = await exporter.export_anomalies(config.start_date, config.end_date)
        logger.info(f"Anomaly export completed: {metadata.dict()}")

        # Test IP export
        logger.info("Testing IP export...")
        metadata = await exporter.export_ips(config.start_date, config.end_date)
        logger.info(f"IP export completed: {metadata.dict()}")

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_export()) 