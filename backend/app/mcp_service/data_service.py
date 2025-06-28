import logging
import redis
import os
from typing import Dict, Any, List, Optional
from app.services.status_manager import ServiceStatusManager
from datetime import datetime, timedelta
import asyncpg

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
            # Initialize database connection using environment variables
            db_config = {
                'host': os.getenv('DB_HOST', '192.168.10.14'),
                'port': int(os.getenv('DB_PORT', '5432')),
                'database': os.getenv('DB_NAME', 'netmonitor_db'),
                'user': os.getenv('DB_USER', 'netmonitor_user'),
                'password': os.getenv('DB_PASSWORD', 'netmonitor_password'),
                'min_connections': int(os.getenv('DB_MIN_CONNECTIONS', '5')),
                'max_connections': int(os.getenv('DB_MAX_CONNECTIONS', '20')),
                'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30'))
            }
            
            # Store the database configuration
            self.db_config = db_config
            
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

    def is_running(self) -> bool:
        """Check if the service is running."""
        try:
            # Check if Redis is connected
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"DataService health check failed: {e}")
            return False

    async def get_logs_by_program(
        self,
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        programs: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Get logs for specific programs within a time range from the remote PostgreSQL database.
        
        Args:
            start_time: Start time as datetime object (None for no lower bound)
            end_time: End time as datetime object (None for no upper bound)
            programs: List of program names to filter by (None for all programs)
            
        Returns:
            List of log entries matching the criteria
        """
        try:
            # Ensure datetime objects are timezone-naive for PostgreSQL compatibility
            if start_time is not None and start_time.tzinfo is not None:
                start_time = start_time.replace(tzinfo=None)
            if end_time is not None and end_time.tzinfo is not None:
                end_time = end_time.replace(tzinfo=None)
            
            # Connect to the remote PostgreSQL database
            conn = await asyncpg.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database']
            )
            
            try:
                # Build query based on whether time constraints and program filters are provided
                if start_time is not None and end_time is not None:
                    if programs is not None:
                        # Both start/end time and programs provided
                        # Use case-insensitive matching with ILIKE and handle variations
                        program_conditions = []
                        params = [start_time, end_time]
                        param_index = 3  # Start after time parameters
                        
                        for program in programs:
                            # Handle common variations
                            if program.lower() == 'cron':
                                program_conditions.append(f"(process_name ILIKE ${param_index} OR process_name ILIKE ${param_index + 1})")
                                params.extend([f'%{program}%', f'%{program}d%'])  # cron and crond
                                param_index += 2
                            elif program.lower() == 'watchdog':
                                program_conditions.append(f"process_name ILIKE ${param_index}")
                                params.extend([f'%{program}%'])
                                param_index += 1
                            else:
                                program_conditions.append(f"process_name ILIKE ${param_index}")
                                params.extend([f'%{program}%'])
                                param_index += 1
                        
                        query = f"""
                            SELECT 
                                id, device_id, device_ip, timestamp, log_level, 
                                process_name, message, raw_message, structured_data,
                                pushed_to_ai, pushed_at, push_attempts, last_push_error
                            FROM log_entries
                            WHERE timestamp >= $1 AND timestamp <= $2
                            AND ({' OR '.join(program_conditions)})
                            ORDER BY timestamp DESC
                        """
                    else:
                        # Only time constraints, no program filter
                        query = """
                            SELECT 
                                id, device_id, device_ip, timestamp, log_level, 
                                process_name, message, raw_message, structured_data,
                                pushed_to_ai, pushed_at, push_attempts, last_push_error
                            FROM log_entries
                            WHERE timestamp >= $1 AND timestamp <= $2
                            ORDER BY timestamp DESC
                        """
                        params = [start_time, end_time]
                elif start_time is not None:
                    if programs is not None:
                        # Only start time and programs provided
                        # Use case-insensitive matching with ILIKE and handle variations
                        program_conditions = []
                        params = [start_time]
                        param_index = 2  # Start after time parameter
                        
                        for program in programs:
                            # Handle common variations
                            if program.lower() == 'cron':
                                program_conditions.append(f"(process_name ILIKE ${param_index} OR process_name ILIKE ${param_index + 1})")
                                params.extend([f'%{program}%', f'%{program}d%'])  # cron and crond
                                param_index += 2
                            elif program.lower() == 'watchdog':
                                program_conditions.append(f"process_name ILIKE ${param_index}")
                                params.extend([f'%{program}%'])
                                param_index += 1
                            else:
                                program_conditions.append(f"process_name ILIKE ${param_index}")
                                params.extend([f'%{program}%'])
                                param_index += 1
                        
                        query = f"""
                            SELECT 
                                id, device_id, device_ip, timestamp, log_level, 
                                process_name, message, raw_message, structured_data,
                                pushed_to_ai, pushed_at, push_attempts, last_push_error
                            FROM log_entries
                            WHERE timestamp >= $1
                            AND ({' OR '.join(program_conditions)})
                            ORDER BY timestamp DESC
                        """
                    else:
                        # Only start time, no program filter
                        query = """
                            SELECT 
                                id, device_id, device_ip, timestamp, log_level, 
                                process_name, message, raw_message, structured_data,
                                pushed_to_ai, pushed_at, push_attempts, last_push_error
                            FROM log_entries
                            WHERE timestamp >= $1
                            ORDER BY timestamp DESC
                        """
                        params = [start_time]
                elif end_time is not None:
                    if programs is not None:
                        # Only end time and programs provided
                        # Use case-insensitive matching with ILIKE and handle variations
                        program_conditions = []
                        params = [end_time]
                        param_index = 2  # Start after time parameter
                        
                        for program in programs:
                            # Handle common variations
                            if program.lower() == 'cron':
                                program_conditions.append(f"(process_name ILIKE ${param_index} OR process_name ILIKE ${param_index + 1})")
                                params.extend([f'%{program}%', f'%{program}d%'])  # cron and crond
                                param_index += 2
                            elif program.lower() == 'watchdog':
                                program_conditions.append(f"process_name ILIKE ${param_index}")
                                params.extend([f'%{program}%'])
                                param_index += 1
                            else:
                                program_conditions.append(f"process_name ILIKE ${param_index}")
                                params.extend([f'%{program}%'])
                                param_index += 1
                        
                        query = f"""
                            SELECT 
                                id, device_id, device_ip, timestamp, log_level, 
                                process_name, message, raw_message, structured_data,
                                pushed_to_ai, pushed_at, push_attempts, last_push_error
                            FROM log_entries
                            WHERE timestamp <= $1
                            AND ({' OR '.join(program_conditions)})
                            ORDER BY timestamp DESC
                        """
                    else:
                        # Only end time, no program filter
                        query = """
                            SELECT 
                                id, device_id, device_ip, timestamp, log_level, 
                                process_name, message, raw_message, structured_data,
                                pushed_to_ai, pushed_at, push_attempts, last_push_error
                            FROM log_entries
                            WHERE timestamp <= $1
                            ORDER BY timestamp DESC
                        """
                        params = [end_time]
                else:
                    if programs is not None:
                        # Only programs provided, no time constraints
                        # Use case-insensitive matching with ILIKE and handle variations
                        program_conditions = []
                        params = []
                        param_index = 1  # Start from 1
                        
                        for program in programs:
                            # Handle common variations
                            if program.lower() == 'cron':
                                program_conditions.append(f"(process_name ILIKE ${param_index} OR process_name ILIKE ${param_index + 1})")
                                params.extend([f'%{program}%', f'%{program}d%'])  # cron and crond
                                param_index += 2
                            elif program.lower() == 'watchdog':
                                program_conditions.append(f"process_name ILIKE ${param_index}")
                                params.extend([f'%{program}%'])
                                param_index += 1
                            else:
                                program_conditions.append(f"process_name ILIKE ${param_index}")
                                params.extend([f'%{program}%'])
                                param_index += 1
                        
                        query = f"""
                            SELECT 
                                id, device_id, device_ip, timestamp, log_level, 
                                process_name, message, raw_message, structured_data,
                                pushed_to_ai, pushed_at, push_attempts, last_push_error
                            FROM log_entries
                            WHERE ({' OR '.join(program_conditions)})
                            ORDER BY timestamp DESC
                        """
                    else:
                        # No constraints - get all logs
                        query = """
                            SELECT 
                                id, device_id, device_ip, timestamp, log_level, 
                                process_name, message, raw_message, structured_data,
                                pushed_to_ai, pushed_at, push_attempts, last_push_error
                            FROM log_entries
                            ORDER BY timestamp DESC
                        """
                        params = []
                
                logs = await conn.fetch(query, *params)
                logs = [dict(record) for record in logs]
                
                logger.info(f"Retrieved {len(logs)} logs for programs {programs if programs else 'all'}")
                return logs
                
            finally:
                await conn.close()
            
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

    async def get_recent_logs(self, programs: Optional[List[str]], minutes: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent logs for specific programs from the database.
        
        Args:
            programs: List of program names to filter by (None for all programs)
            minutes: Number of minutes to look back
            
        Returns:
            List of log entries matching the criteria
        """
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=minutes)
            
            # Use the existing get_logs_by_program method to get logs from database
            logs = await self.get_logs_by_program(
                start_time=start_time,
                end_time=end_time,
                programs=programs
            )
            
            logger.info(f"Retrieved {len(logs)} logs for programs {programs if programs else 'all'} from database")
            return logs
            
        except Exception as e:
            logger.error(f"Error getting recent logs: {e}")
            raise 