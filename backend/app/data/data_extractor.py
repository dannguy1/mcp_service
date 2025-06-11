"""
Data Extraction Interface

This module provides an interface for extracting and preprocessing data from the source database.
It handles data quality issues and provides a clean interface for the model training pipeline.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class DataExtractor:
    """Extracts and preprocesses data from the source database."""

    def __init__(self, config: Dict):
        """Initialize the data extractor with configuration."""
        self.config = config
        self.engine = self._create_engine()
        self._validate_connection()

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

    def _validate_connection(self) -> None:
        """Validate database connection."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Successfully connected to the database")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def _handle_missing_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing data in the DataFrame."""
        # Drop rows with missing required fields
        required_fields = ["device_id", "message", "raw_message", "timestamp"]
        df = df.dropna(subset=required_fields)
        
        # Log data quality metrics
        total_rows = len(df)
        for field in required_fields:
            missing = df[field].isna().sum()
            if missing > 0:
                logger.warning(f"Missing {missing} values in {field} ({missing/total_rows*100:.2f}%)")
        
        return df

    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract features from raw log data."""
        # Basic features
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["hour"] = df["timestamp"].dt.hour
        df["day_of_week"] = df["timestamp"].dt.dayofweek
        
        # Message length features
        df["message_length"] = df["message"].str.len()
        df["raw_message_length"] = df["raw_message"].str.len()
        
        # Device activity features
        device_activity = df.groupby("device_id").size().reset_index(name="device_activity")
        df = df.merge(device_activity, on="device_id", how="left")
        
        return df

    def get_recent_logs(
        self, hours: int = 24, limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Get recent log entries from the database."""
        try:
            query = f"""
                SELECT 
                    device_id,
                    message,
                    raw_message,
                    timestamp
                FROM log_entries 
                WHERE timestamp >= NOW() - INTERVAL '{hours} hours'
                ORDER BY timestamp DESC
            """
            if limit:
                query += f" LIMIT {limit}"

            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn)
                
            if df.empty:
                logger.warning(f"No log entries found in the last {hours} hours")
                return pd.DataFrame()

            # Handle missing data
            df = self._handle_missing_data(df)
            
            # Extract features
            df = self._extract_features(df)
            
            logger.info(f"Retrieved {len(df)} log entries")
            return df

        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            raise

    def get_device_logs(
        self, device_id: str, hours: int = 24
    ) -> pd.DataFrame:
        """Get log entries for a specific device."""
        try:
            query = f"""
                SELECT 
                    device_id,
                    message,
                    raw_message,
                    timestamp
                FROM log_entries 
                WHERE device_id = :device_id
                AND timestamp >= NOW() - INTERVAL '{hours} hours'
                ORDER BY timestamp DESC
            """

            with self.engine.connect() as conn:
                df = pd.read_sql(
                    query,
                    conn,
                    params={"device_id": device_id}
                )

            if df.empty:
                logger.warning(f"No log entries found for device {device_id}")
                return pd.DataFrame()

            # Handle missing data
            df = self._handle_missing_data(df)
            
            # Extract features
            df = self._extract_features(df)
            
            logger.info(f"Retrieved {len(df)} log entries for device {device_id}")
            return df

        except Exception as e:
            logger.error(f"Failed to get device logs: {e}")
            raise

    def get_anomaly_records(
        self, hours: int = 24, device_id: Optional[str] = None
    ) -> pd.DataFrame:
        """Get anomaly records from the database."""
        try:
            query = f"""
                SELECT 
                    device_id,
                    anomaly_type,
                    severity,
                    details,
                    timestamp
                FROM anomaly_records 
                WHERE timestamp >= NOW() - INTERVAL '{hours} hours'
            """
            
            if device_id:
                query += " AND device_id = :device_id"
            
            query += " ORDER BY timestamp DESC"

            with self.engine.connect() as conn:
                df = pd.read_sql(
                    query,
                    conn,
                    params={"device_id": device_id} if device_id else {}
                )

            if df.empty:
                logger.warning("No anomaly records found")
                return pd.DataFrame()

            logger.info(f"Retrieved {len(df)} anomaly records")
            return df

        except Exception as e:
            logger.error(f"Failed to get anomaly records: {e}")
            raise

    def get_training_data(
        self, hours: int = 24, sample_size: Optional[int] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Get data for model training."""
        try:
            # Get log entries
            logs_df = self.get_recent_logs(hours=hours, limit=sample_size)
            
            # Get anomaly records if available
            try:
                anomalies_df = self.get_anomaly_records(hours=hours)
            except Exception as e:
                logger.warning(f"Could not retrieve anomaly records: {e}")
                anomalies_df = pd.DataFrame()

            return logs_df, anomalies_df

        except Exception as e:
            logger.error(f"Failed to get training data: {e}")
            raise

    def get_performance_metrics(self) -> Dict[str, float]:
        """Get database performance metrics."""
        try:
            metrics = {}
            
            # Test query performance
            start_time = datetime.now()
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT COUNT(*) FROM log_entries WHERE timestamp >= NOW() - INTERVAL '1 hour'")
                )
                count = result.scalar()
            
            query_time = (datetime.now() - start_time).total_seconds()
            metrics["query_time"] = query_time
            metrics["rows_per_second"] = count / query_time if query_time > 0 else 0
            
            return metrics

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            raise 