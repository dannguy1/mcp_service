import logging
import redis
import os
from typing import Dict, Any, List
from app.services.status_manager import ServiceStatusManager
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self, config):
        self.config = config
        self.db = None
        
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
        
        # Initialize status manager with Redis client
        self.status_manager = ServiceStatusManager('data_source', self.redis_client)

    async def start(self):
        """Initialize database connection."""
        try:
            # TODO: Initialize database connection using self.config.db
            self.status_manager.update_status('connected')
            logger.info("DataService started successfully")
        except Exception as e:
            logger.error(f"Failed to start DataService: {e}")
            self.status_manager.update_status('error', str(e))
            raise

    async def stop(self):
        """Close database connection."""
        try:
            if self.db:
                # TODO: Close database connection
                pass
            self.status_manager.update_status('disconnected')
            logger.info("DataService stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping DataService: {e}")
            self.status_manager.update_status('error', str(e))
            raise

    async def get_logs_by_program(
        self,
        start_time: str,
        end_time: str,
        programs: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get logs for specific programs within a time range.
        
        Args:
            start_time: Start time in ISO format
            end_time: End time in ISO format
            programs: List of program names to filter by
            
        Returns:
            List of log entries matching the criteria
        """
        try:
            logs = []
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            
            # For each program, get logs from Redis
            for program in programs:
                # Get all logs for this program
                program_logs = self.redis_client.lrange(f"logs:{program}", 0, -1)
                
                # Filter logs by time range
                for log_str in program_logs:
                    try:
                        log = eval(log_str)  # Convert string representation to dict
                        log_time = datetime.fromisoformat(log['timestamp'])
                        
                        if start_dt <= log_time <= end_dt:
                            logs.append(log)
                    except Exception as e:
                        logger.error(f"Error parsing log entry: {e}")
                        continue
            
            logger.info(f"Retrieved {len(logs)} logs for programs {programs}")
            return logs
            
        except Exception as e:
            logger.error(f"Error getting logs by program: {e}")
            raise

    async def store_anomaly(self, anomaly: Dict[str, Any]):
        """
        Store an anomaly in the database.
        
        Args:
            anomaly: Dictionary containing anomaly information
        """
        try:
            # Store anomaly in Redis
            anomaly_id = f"anomaly:{datetime.now().isoformat()}"
            self.redis_client.hmset(anomaly_id, anomaly)
            self.redis_client.expire(anomaly_id, 86400)  # Expire after 24 hours
            
            logger.info(f"Stored anomaly: {anomaly_id}")
            
        except Exception as e:
            logger.error(f"Error storing anomaly: {e}")
            raise

    async def get_recent_logs(self, programs: List[str], minutes: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent logs for specific programs.
        
        Args:
            programs: List of program names to filter by
            minutes: Number of minutes to look back
            
        Returns:
            List of log entries matching the criteria
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=minutes)
            
            logs = []
            for program in programs:
                # Get all logs for this program
                program_logs = self.redis_client.lrange(f"logs:{program}", 0, -1)
                
                # Filter logs by time range
                for log_str in program_logs:
                    try:
                        log = eval(log_str)  # Convert string representation to dict
                        log_time = datetime.fromisoformat(log['timestamp'])
                        
                        if start_time <= log_time <= end_time:
                            logs.append(log)
                    except Exception as e:
                        logger.error(f"Error parsing log entry: {e}")
                        continue
            
            logger.info(f"Retrieved {len(logs)} logs for programs {programs}")
            return logs
            
        except Exception as e:
            logger.error(f"Error getting recent logs: {e}")
            raise 