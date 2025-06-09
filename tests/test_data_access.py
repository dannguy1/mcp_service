"""
Test script for data access and mock anomaly generation.
This script demonstrates:
1. Connecting to the source database
2. Retrieving and analyzing log data
3. Generating mock anomalies based on patterns
4. Testing the data extraction interface
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import yaml
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("test_data_access.log"),
    ],
)

logger = logging.getLogger(__name__)


class DataAccessTester:
    """Test data access and generate mock anomalies."""

    def __init__(self, config_path: str = "config/data_source_config.yaml"):
        """Initialize with configuration."""
        self.config = self._load_config(config_path)
        self.engine = self._create_engine()

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise

    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine."""
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

    def get_recent_logs(self, hours: int = 24) -> pd.DataFrame:
        """Get recent log entries."""
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

            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn)

            logger.info(f"Retrieved {len(df)} log entries")
            return df

        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            raise

    def analyze_log_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze log patterns for anomaly detection."""
        patterns = {
            "device_activity": df.groupby("device_id").size().to_dict(),
            "message_lengths": {
                "mean": df["message"].str.len().mean(),
                "std": df["message"].str.len().std(),
            },
            "hourly_distribution": df["timestamp"].dt.hour.value_counts().to_dict(),
        }
        return patterns

    def generate_mock_anomaly(self, patterns: Dict) -> Dict:
        """Generate a mock anomaly based on analyzed patterns."""
        # Select a random device with high activity
        device_id = max(patterns["device_activity"].items(), key=lambda x: x[1])[0]
        
        # Generate anomaly details
        anomaly = {
            "device_id": device_id,
            "timestamp": datetime.now().isoformat(),
            "anomaly_type": "unusual_activity",
            "severity": np.random.randint(1, 5),
            "details": {
                "pattern": "unusual_message_length",
                "expected_length": patterns["message_lengths"]["mean"],
                "threshold": patterns["message_lengths"]["std"] * 2,
                "device_activity": patterns["device_activity"][device_id],
            },
        }
        return anomaly

    def test_data_access(self) -> None:
        """Run data access tests."""
        try:
            # Get recent logs
            df = self.get_recent_logs(hours=24)
            
            if df.empty:
                logger.warning("No log entries found")
                return

            # Analyze patterns
            patterns = self.analyze_log_patterns(df)
            logger.info("Log patterns analyzed successfully")

            # Generate mock anomaly
            anomaly = self.generate_mock_anomaly(patterns)
            logger.info(f"Generated mock anomaly: {json.dumps(anomaly, indent=2)}")

            # Save test results
            self._save_test_results(df, patterns, anomaly)

        except Exception as e:
            logger.error(f"Data access test failed: {e}")
            raise

    def _save_test_results(
        self, df: pd.DataFrame, patterns: Dict, anomaly: Dict
    ) -> None:
        """Save test results to files."""
        try:
            # Create test results directory
            os.makedirs("test_results", exist_ok=True)

            # Save log entries sample
            df.head(100).to_csv("test_results/log_entries_sample.csv", index=False)
            
            # Save patterns
            with open("test_results/log_patterns.json", "w") as f:
                json.dump(patterns, f, indent=2)
            
            # Save mock anomaly
            with open("test_results/mock_anomaly.json", "w") as f:
                json.dump(anomaly, f, indent=2)

            logger.info("Test results saved successfully")

        except Exception as e:
            logger.error(f"Failed to save test results: {e}")
            raise


def main():
    """Main entry point for the test script."""
    try:
        tester = DataAccessTester()
        tester.test_data_access()
        logger.info("Data access tests completed successfully")
    except Exception as e:
        logger.error(f"Test script failed: {e}")
        raise


if __name__ == "__main__":
    main() 