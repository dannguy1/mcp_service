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
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import argparse

import psycopg2
import yaml
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
import asyncpg

# Add backend directory to Python path
backend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
sys.path.append(backend_path)

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

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.conn = None

    async def connect(self):
        """Establish database connection."""
        try:
            self.conn = await asyncpg.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            logger.info("Successfully connected to the database")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False

    async def verify_schema(self) -> bool:
        """Verify database schema matches expected structure."""
        try:
            # Get column information
            columns = await self.conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'log_entries'
                ORDER BY ordinal_position;
            """)

            # Log actual schema for debugging
            logger.info("Actual schema:")
            for col in columns:
                logger.info(f"- {col['column_name']}: {col['data_type']}")

            # Expected schema based on actual database
            required_columns = {
                'id': 'integer',
                'device_id': 'integer',
                'device_ip': 'character varying',
                'timestamp': 'timestamp without time zone',
                'log_level': 'character varying',
                'process_name': 'character varying',
                'message': 'text',
                'raw_message': 'text',
                'structured_data': 'json',
                'pushed_to_ai': 'boolean',
                'pushed_at': 'timestamp without time zone',
                'push_attempts': 'integer',
                'last_push_error': 'text'
            }

            # Convert columns to dict for easier lookup
            column_dict = {col['column_name']: col['data_type'] for col in columns}
            
            # Verify each required column exists and has correct type
            for col_name, expected_type in required_columns.items():
                if col_name not in column_dict:
                    logger.error(f"Required column {col_name} not found in log_entries")
                    return False
                
                if column_dict[col_name] != expected_type:
                    logger.error(
                        f"Column {col_name} has type {column_dict[col_name]}, "
                        f"expected {expected_type}"
                    )
                    return False

            logger.info("Schema verification passed")
            return True

        except Exception as e:
            logger.error(f"Schema verification failed: {e}")
            return False

    async def verify_data_access(self) -> bool:
        """Verify data can be accessed and processed correctly."""
        try:
            # Get logs from last 24 hours
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            # Use SELECT * to get all columns
            query = """
                SELECT * FROM log_entries
                WHERE timestamp BETWEEN $1 AND $2
                ORDER BY timestamp DESC
                LIMIT 1000;
            """
            
            rows = await self.conn.fetch(query, start_time, end_time)
            logger.info(f"Found {len(rows)} log entries in the last 24 hours")

            if not rows:
                logger.warning("No log entries found in the last 24 hours")
                return True  # Not an error, just no data

            # Define required fields based on schema
            required_fields = [
                'id', 'device_id', 'device_ip', 'timestamp', 'log_level',
                'process_name', 'message', 'raw_message', 'structured_data',
                'pushed_to_ai', 'pushed_at', 'push_attempts', 'last_push_error'
            ]
            
            for row in rows:
                for field in required_fields:
                    if field not in row:
                        raise ValueError(f"Missing required field {field} in row")
                    
                    # Type validation
                    if field == 'timestamp' and not isinstance(row[field], datetime):
                        raise ValueError(f"Invalid timestamp type: {type(row[field])}")
                    if field == 'pushed_at' and row[field] and not isinstance(row[field], datetime):
                        raise ValueError(f"Invalid pushed_at type: {type(row[field])}")
                    if field == 'message' and not isinstance(row[field], str):
                        raise ValueError(f"Invalid message type: {type(row[field])}")
                    if field == 'raw_message' and not isinstance(row[field], str):
                        raise ValueError(f"Invalid raw_message type: {type(row[field])}")
                    if field == 'device_id' and not isinstance(row[field], int):
                        raise ValueError(f"Invalid device_id type: {type(row[field])}")
                    if field == 'push_attempts' and not isinstance(row[field], int):
                        raise ValueError(f"Invalid push_attempts type: {type(row[field])}")
                    if field == 'pushed_to_ai' and not isinstance(row[field], bool):
                        raise ValueError(f"Invalid pushed_to_ai type: {type(row[field])}")
                    if field == 'structured_data' and row[field]:
                        # PostgreSQL returns JSON as string, so we just verify it's a string
                        if not isinstance(row[field], str):
                            raise ValueError(f"Invalid structured_data type: {type(row[field])}")
                        # Optionally verify it's valid JSON
                        try:
                            import json
                            json.loads(row[field])
                        except json.JSONDecodeError:
                            raise ValueError(f"Invalid JSON in structured_data: {row[field]}")

            logger.info("Data access verification passed")
            return True

        except Exception as e:
            logger.error(f"Data access verification failed: {e}")
            return False

    async def verify_performance(self) -> bool:
        """Verify query performance."""
        try:
            start_time = time.time()
            
            # Test query performance with all columns
            query = """
                SELECT * FROM log_entries
                ORDER BY timestamp DESC
                LIMIT 1000;
            """
            
            rows = await self.conn.fetch(query)
            end_time = time.time()
            
            duration = end_time - start_time
            rows_per_second = len(rows) / duration if duration > 0 else 0
            
            logger.info(f"Log entries query performance: {duration:.2f}s for {len(rows)} rows")
            logger.info(f"Log entries throughput: {rows_per_second:.2f} rows/s")
            
            # Performance thresholds
            if duration > 1.0:  # More than 1 second for 1000 rows
                logger.error("Query performance below threshold")
                return False
                
            logger.info("Performance verification passed")
            return True

        except Exception as e:
            logger.error(f"Performance verification failed: {e}")
            return False

    async def verify_all(self) -> bool:
        """Run all verification steps."""
        logger.info("Starting data source verification...")
        
        # Connection verification
        logger.info("Running Connection verification...")
        if not await self.connect():
            return False
        logger.info("Connection verification passed")
        
        # Schema verification
        logger.info("Running Schema verification...")
        schema_ok = await self.verify_schema()
        if not schema_ok:
            logger.error("Schema verification failed")
        
        # Data access verification
        logger.info("Running Data Access verification...")
        data_ok = await self.verify_data_access()
        if not data_ok:
            logger.error("Data Access verification failed")
        
        # Performance verification
        logger.info("Running Performance verification...")
        perf_ok = await self.verify_performance()
        if not perf_ok:
            logger.error("Performance verification failed")
        
        # Cleanup
        if self.conn:
            await self.conn.close()
        
        # Final result
        all_passed = schema_ok and data_ok and perf_ok
        if not all_passed:
            logger.error("Some verification steps failed")
        else:
            logger.info("All verification steps passed")
        
        return all_passed


async def main():
    parser = argparse.ArgumentParser(description='Verify data source connectivity and data availability')
    parser.add_argument('--config', default='backend/app/config/data_source_config.yaml',
                      help='Path to data source configuration file')
    parser.add_argument('--days', type=int, default=7,
                      help='Number of days to check for data')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose logging')
    args = parser.parse_args()

    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data_source_verification.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    # Verify config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        logger.info("Please ensure the config file exists in backend/app/config/")
        sys.exit(1)

    # Load configuration
    with open(args.config, "r") as f:
        db_config = yaml.safe_load(f)

    verifier = DataSourceVerifier(db_config)
    success = await verifier.verify_all()
    
    if not success:
        exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 