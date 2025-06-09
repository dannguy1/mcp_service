#!/usr/bin/env python3
import os
import sys
import logging
import shutil
import subprocess
from datetime import datetime, timedelta
import yaml
import psycopg2
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config
from utils.logger import setup_logger

class MaintenanceManager:
    def __init__(self, config_path: str = "config/monitoring_config.yaml"):
        self.config = Config()
        self.logger = setup_logger("maintenance")
        self.monitoring_config = self._load_monitoring_config(config_path)
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

    def _load_monitoring_config(self, config_path: str) -> Dict:
        """Load monitoring configuration."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load monitoring config: {e}")
            return {}

    def perform_backup(self) -> bool:
        """Perform database and model backup."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}"
            backup_path.mkdir(exist_ok=True)

            # Backup database
            self._backup_database(backup_path)
            
            # Backup models
            self._backup_models(backup_path)
            
            # Backup logs
            self._backup_logs(backup_path)
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
            return True
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False

    def _backup_database(self, backup_path: Path) -> None:
        """Backup PostgreSQL database."""
        try:
            db_config = self.config.get_database_config()
            dump_file = backup_path / "database.sql"
            
            # Create database dump
            subprocess.run([
                "pg_dump",
                "-h", db_config["host"],
                "-p", str(db_config["port"]),
                "-U", db_config["user"],
                "-F", "c",
                "-f", str(dump_file),
                db_config["name"]
            ], check=True)
            
            self.logger.info(f"Database backup created: {dump_file}")
        except Exception as e:
            self.logger.error(f"Database backup failed: {e}")
            raise

    def _backup_models(self, backup_path: Path) -> None:
        """Backup model files."""
        try:
            models_dir = Path("models")
            if models_dir.exists():
                shutil.copytree(models_dir, backup_path / "models")
                self.logger.info("Models backup created")
        except Exception as e:
            self.logger.error(f"Models backup failed: {e}")
            raise

    def _backup_logs(self, backup_path: Path) -> None:
        """Backup log files."""
        try:
            logs_dir = Path("logs")
            if logs_dir.exists():
                shutil.copytree(logs_dir, backup_path / "logs")
                self.logger.info("Logs backup created")
        except Exception as e:
            self.logger.error(f"Logs backup failed: {e}")
            raise

    def _cleanup_old_backups(self) -> None:
        """Remove backups older than retention period."""
        try:
            retention_days = self.monitoring_config.get("logging", {}).get("retention", {}).get("days", 30)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            for backup_dir in self.backup_dir.glob("backup_*"):
                try:
                    backup_date = datetime.strptime(backup_dir.name.split("_")[1], "%Y%m%d")
                    if backup_date < cutoff_date:
                        shutil.rmtree(backup_dir)
                        self.logger.info(f"Removed old backup: {backup_dir}")
                except ValueError:
                    continue
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {e}")
            raise

    def cleanup_logs(self) -> None:
        """Clean up old log files."""
        try:
            log_config = self.monitoring_config.get("logging", {})
            max_size = log_config.get("rotation", {}).get("max_size", "100MB")
            backup_count = log_config.get("rotation", {}).get("backup_count", 10)
            
            logs_dir = Path("logs")
            if not logs_dir.exists():
                return
                
            # Convert max_size to bytes
            size_multiplier = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
            size_value = int(max_size[:-2])
            size_unit = max_size[-2:].upper()
            max_bytes = size_value * size_multiplier[size_unit]
            
            # Clean up old log files
            log_files = sorted(logs_dir.glob("*.log*"), key=lambda x: x.stat().st_mtime)
            while len(log_files) > backup_count:
                old_file = log_files.pop(0)
                old_file.unlink()
                self.logger.info(f"Removed old log file: {old_file}")
                
            # Check current log size
            current_log = logs_dir / "app.log"
            if current_log.exists() and current_log.stat().st_size > max_bytes:
                # Rotate log file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_name = f"app_{timestamp}.log"
                current_log.rename(logs_dir / new_name)
                self.logger.info(f"Rotated log file to: {new_name}")
        except Exception as e:
            self.logger.error(f"Log cleanup failed: {e}")
            raise

    def optimize_database(self) -> None:
        """Perform database optimization."""
        try:
            db_config = self.config.get_database_config()
            conn = psycopg2.connect(
                host=db_config["host"],
                port=db_config["port"],
                database=db_config["name"],
                user=db_config["user"],
                password=db_config["password"]
            )
            
            with conn.cursor() as cur:
                # Analyze tables
                cur.execute("ANALYZE VERBOSE;")
                
                # Vacuum tables
                cur.execute("VACUUM ANALYZE;")
                
                # Update statistics
                cur.execute("SELECT schemaname, tablename FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema');")
                tables = cur.fetchall()
                
                for schema, table in tables:
                    cur.execute(f"ANALYZE {schema}.{table};")
                    
            conn.close()
            self.logger.info("Database optimization completed")
        except Exception as e:
            self.logger.error(f"Database optimization failed: {e}")
            raise

    def run_maintenance(self) -> None:
        """Run all maintenance tasks."""
        try:
            self.logger.info("Starting maintenance tasks")
            
            # Perform backup
            if self.perform_backup():
                self.logger.info("Backup completed successfully")
            else:
                self.logger.error("Backup failed")
            
            # Clean up logs
            self.cleanup_logs()
            self.logger.info("Log cleanup completed")
            
            # Optimize database
            self.optimize_database()
            self.logger.info("Database optimization completed")
            
            self.logger.info("All maintenance tasks completed successfully")
        except Exception as e:
            self.logger.error(f"Maintenance tasks failed: {e}")
            raise

def main():
    """Main entry point."""
    try:
        maintenance = MaintenanceManager()
        maintenance.run_maintenance()
    except Exception as e:
        logging.error(f"Maintenance script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 