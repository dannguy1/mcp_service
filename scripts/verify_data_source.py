#!/usr/bin/env python3
"""
Data Source Verification Script

This script verifies connectivity and data access with the external data source database.
It performs checks for:
1. Database connectivity
2. Schema validation
3. Data access
4. Query performance
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import psycopg2
import yaml
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data_source_verification.log"),
    ],
)

logger = logging.getLogger(__name__)


class DataSourceVerifier:
    """Verifies connectivity and data access with the external data source."""

    def __init__(self, config_path: str = "config/data_source_config.yaml"):
        """Initialize the verifier with configuration."""
        self.config = self._load_config(config_path)
        self.engine = self._create_engine()
        self.connection = None

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine with connection pooling."""
        try:
            return create_engine(
                self.config["database"]["url"],
                pool_size=self.config["database"]["pool_size"],
                max_overflow=self.config["database"]["max_overflow"],
                pool_timeout=self.config["database"]["timeout"],
            )
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise

    def verify_connection(self) -> bool:
        """Verify database connectivity."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
                logger.info("Successfully connected to the database")
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def verify_indexes(self, table_name: str, required_indexes: List[str]) -> bool:
        """Verify that required indexes exist for a table."""
        try:
            with self.engine.connect() as conn:
                for index_name in required_indexes:
                    result = conn.execute(
                        text(
                            f"""
                            SELECT EXISTS (
                                SELECT 1
                                FROM pg_indexes
                                WHERE tablename = '{table_name}'
                                AND indexname = '{index_name}'
                            )
                            """
                        )
                    )
                    if not result.scalar():
                        logger.error(f"Required index '{index_name}' not found for table '{table_name}'")
                        return False
                logger.info(f"All required indexes verified for table '{table_name}'")
                return True
        except Exception as e:
            logger.error(f"Index verification failed for table '{table_name}': {e}")
            return False

    def verify_table_exists(self, table_name: str) -> bool:
        """Verify that a table exists."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')")
                )
                return result.scalar()
        except Exception as e:
            logger.error(f"Failed to check if table '{table_name}' exists: {e}")
            return False

    def verify_schema(self) -> bool:
        """Verify database schema and required tables."""
        try:
            with self.engine.connect() as conn:
                # Check required tables
                for table_config in self.config["validation"]["required_tables"]:
                    table_name = table_config["name"]
                    if not self.verify_table_exists(table_name):
                        logger.error(f"Required table '{table_name}' not found")
                        return False

                    # Check column types
                    for column, expected_type in table_config["data_types"].items():
                        result = conn.execute(
                            text(
                                f"""
                                SELECT data_type 
                                FROM information_schema.columns 
                                WHERE table_name = '{table_name}' 
                                AND column_name = '{column}'
                                """
                            )
                        )
                        actual_type = result.scalar()
                        if actual_type != expected_type:
                            logger.error(
                                f"Column {column} in table {table_name} has type {actual_type}, expected {expected_type}"
                            )
                            return False

                    # Verify indexes
                    if not self.verify_indexes(table_name, table_config["indexes"]):
                        return False

                # Check optional tables
                for table_config in self.config["validation"]["optional_tables"]:
                    table_name = table_config["name"]
                    if self.verify_table_exists(table_name):
                        logger.info(f"Optional table '{table_name}' exists, verifying schema...")
                        
                        # Check column types
                        for column, expected_type in table_config["data_types"].items():
                            result = conn.execute(
                                text(
                                    f"""
                                    SELECT data_type 
                                    FROM information_schema.columns 
                                    WHERE table_name = '{table_name}' 
                                    AND column_name = '{column}'
                                    """
                                )
                            )
                            actual_type = result.scalar()
                            if actual_type != expected_type:
                                logger.error(
                                    f"Column {column} in table {table_name} has type {actual_type}, expected {expected_type}"
                                )
                                return False

                        # Verify indexes
                        if not self.verify_indexes(table_name, table_config["indexes"]):
                            return False
                    else:
                        logger.info(f"Optional table '{table_name}' not found, skipping verification")

                logger.info("Schema verification successful")
                return True
        except Exception as e:
            logger.error(f"Schema verification failed: {e}")
            return False

    def verify_data_access(self, hours: int = 24, sample_size: int = 1000) -> bool:
        """Verify data access and quality."""
        try:
            with self.engine.connect() as conn:
                start_time = datetime.now() - timedelta(hours=hours)
                
                # Check log entries
                result = conn.execute(
                    text(
                        f"""
                        SELECT COUNT(*) 
                        FROM log_entries 
                        WHERE timestamp >= '{start_time}'
                        """
                    )
                )
                log_count = result.scalar()
                if log_count == 0:
                    logger.error(f"No log entries found in the last {hours} hours")
                    return False
                logger.info(f"Found {log_count} log entries in the last {hours} hours")

                # Check anomaly records if table exists
                if self.verify_table_exists("anomaly_records"):
                    result = conn.execute(
                        text(
                            f"""
                            SELECT COUNT(*) 
                            FROM anomaly_records 
                            WHERE timestamp >= '{start_time}'
                            """
                        )
                    )
                    anomaly_count = result.scalar()
                    logger.info(f"Found {anomaly_count} anomaly records in the last {hours} hours")

                # Check data quality for log entries
                result = conn.execute(
                    text(
                        f"""
                        SELECT 
                            COUNT(*) as total,
                            COUNT(CASE WHEN device_id IS NOT NULL THEN 1 END) as device_id_count,
                            COUNT(CASE WHEN message IS NOT NULL THEN 1 END) as message_count,
                            COUNT(CASE WHEN raw_message IS NOT NULL THEN 1 END) as raw_message_count
                        FROM log_entries 
                        WHERE timestamp >= '{start_time}'
                        LIMIT {sample_size}
                        """
                    )
                )
                quality = result.fetchone()
                # Convert to dict if result is a tuple
                if isinstance(quality, tuple):
                    quality = dict(zip(['total', 'device_id_count', 'message_count', 'raw_message_count'], quality))

                if quality['device_id_count'] < quality['total'] * 0.95:
                    logger.error("Log entries device_id data quality check failed")
                    return False
                if quality['message_count'] < quality['total'] * 0.95:
                    logger.error("Log entries message data quality check failed")
                    return False
                if quality['raw_message_count'] < quality['total'] * 0.95:
                    logger.error("Log entries raw_message data quality check failed")
                    return False

                logger.info("Data quality checks passed")
                return True
        except Exception as e:
            logger.error(f"Data access verification failed: {e}")
            return False

    def verify_performance(self, sample_size: int = 1000) -> bool:
        """Verify query performance."""
        try:
            with self.engine.connect() as conn:
                # Test log entries query performance
                start_time = time.time()
                result = conn.execute(
                    text(
                        f"""
                        SELECT * 
                        FROM log_entries 
                        ORDER BY timestamp DESC 
                        LIMIT {sample_size}
                        """
                    )
                )
                rows = result.fetchall()
                query_time = time.time() - start_time

                if query_time > self.config["performance"]["max_query_time"]:
                    logger.error(f"Log entries query performance check failed: {query_time:.2f}s > {self.config['performance']['max_query_time']}s")
                    return False

                rows_per_second = len(rows) / query_time
                if rows_per_second < self.config["performance"]["min_rows_per_second"]:
                    logger.error(
                        f"Log entries query throughput check failed: {rows_per_second:.2f} rows/s < {self.config['performance']['min_rows_per_second']} rows/s"
                    )
                    return False

                logger.info(f"Log entries query performance: {query_time:.2f}s for {len(rows)} rows")
                logger.info(f"Log entries throughput: {rows_per_second:.2f} rows/s")

                # Test anomaly records query performance if table exists
                if self.verify_table_exists("anomaly_records"):
                    start_time = time.time()
                    result = conn.execute(
                        text(
                            f"""
                            SELECT * 
                            FROM anomaly_records 
                            ORDER BY timestamp DESC 
                            LIMIT {sample_size}
                            """
                        )
                    )
                    rows = result.fetchall()
                    query_time = time.time() - start_time

                    if query_time > self.config["performance"]["max_query_time"]:
                        logger.error(f"Anomaly records query performance check failed: {query_time:.2f}s > {self.config['performance']['max_query_time']}s")
                        return False

                    rows_per_second = len(rows) / query_time
                    if rows_per_second < self.config["performance"]["min_rows_per_second"]:
                        logger.error(
                            f"Anomaly records query throughput check failed: {rows_per_second:.2f} rows/s < {self.config['performance']['min_rows_per_second']} rows/s"
                        )
                        return False

                    logger.info(f"Anomaly records query performance: {query_time:.2f}s for {len(rows)} rows")
                    logger.info(f"Anomaly records throughput: {rows_per_second:.2f} rows/s")

                return True
        except Exception as e:
            logger.error(f"Performance verification failed: {e}")
            return False

    def run_verification(self, hours: int = 24, sample_size: int = 1000) -> bool:
        """Run all verification steps."""
        logger.info("Starting data source verification...")

        steps = [
            ("Connection", self.verify_connection),
            ("Schema", self.verify_schema),
            ("Data Access", lambda: self.verify_data_access(hours, sample_size)),
            ("Performance", lambda: self.verify_performance(sample_size)),
        ]

        all_passed = True
        for step_name, step_func in steps:
            logger.info(f"Running {step_name} verification...")
            if not step_func():
                logger.error(f"{step_name} verification failed")
                all_passed = False
            else:
                logger.info(f"{step_name} verification passed")

        if all_passed:
            logger.info("All verification steps completed successfully")
        else:
            logger.error("Some verification steps failed")

        return all_passed


def main():
    """Main entry point for the verification script."""
    import argparse

    parser = argparse.ArgumentParser(description="Verify data source connectivity and access")
    parser.add_argument("--config", default="config/data_source_config.yaml", help="Path to configuration file")
    parser.add_argument("--hours", type=int, default=24, help="Hours of data to verify")
    parser.add_argument("--sample-size", type=int, default=1000, help="Sample size for performance testing")
    args = parser.parse_args()

    verifier = DataSourceVerifier(args.config)
    success = verifier.run_verification(args.hours, args.sample_size)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 