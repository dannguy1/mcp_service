import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncpg
import json

from .base_agent import BaseAgent
from ..components.agent_registry import agent_registry

class LogLevelAgent(BaseAgent):
    def __init__(self, config, data_service):
        """Initialize the Log Level agent."""
        super().__init__(config, data_service)
        self.description = "Log level monitoring agent for error and critical severity detection"
        self.capabilities = [
            "Error log level detection",
            "Critical log level detection",
            "Automatic anomaly generation for high severity logs"
        ]
        self.status = "initialized"
        self.is_running = False
        self.last_run = None
        self.logger = logging.getLogger(__name__)
        self.agent_id = "log_level_agent"
        
        # Configuration for log level monitoring
        self.target_levels = ['error', 'critical']  # Case insensitive
        self.lookback_minutes = getattr(config, 'log_level_lookback_minutes', 5)
        self.severity_mapping = {
            'error': 4,      # High severity
            'critical': 5    # Critical severity
        }

    async def start(self):
        """Start the Log Level agent."""
        try:
            self.logger.info("Starting Log Level agent...")
            
            # Register with AgentRegistry
            if not agent_registry.register_agent(self, self.agent_id):
                self.logger.warning("Failed to register with agent registry")
            
            # Set running state
            self.is_running = True
            self.status = 'active'
            self.last_run = datetime.now()
            
            # Update status in Redis
            self._update_redis_status({
                'id': self.agent_id,
                'name': self.__class__.__name__,
                'status': 'active',
                'is_running': True,
                'last_run': self.last_run.isoformat(),
                'capabilities': self.capabilities,
                'description': self.description
            })
            
            self.logger.info("Log Level agent started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start Log Level agent: {e}")
            self.status = 'error'
            # Update status in Redis
            self._update_redis_status({
                'id': self.agent_id,
                'name': self.__class__.__name__,
                'status': 'error',
                'is_running': False,
                'last_run': datetime.now().isoformat(),
                'capabilities': self.capabilities,
                'description': self.description
            })
            raise

    async def stop(self, unregister=True):
        """Stop the Log Level agent.
        
        Args:
            unregister: Whether to unregister the agent from the registry
        """
        try:
            self.logger.info("Stopping Log Level agent...")
            
            # Stop the agent
            self.is_running = False
            self.status = 'inactive'
            self.last_run = datetime.now()
            
            # Update status in Redis
            self._update_redis_status({
                'id': self.agent_id,
                'name': self.__class__.__name__,
                'status': 'inactive',
                'is_running': False,
                'last_run': self.last_run.isoformat(),
                'capabilities': self.capabilities,
                'description': self.description
            })
            
            # Unregister from AgentRegistry only if requested
            if unregister:
                agent_registry.unregister_agent(self.agent_id)
            
            self.logger.info("Log Level agent stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping Log Level agent: {e}")
            self.status = 'error'
            # Update status in Redis
            self._update_redis_status({
                'id': self.agent_id,
                'name': self.__class__.__name__,
                'status': 'error',
                'is_running': False,
                'last_run': datetime.now().isoformat(),
                'capabilities': self.capabilities,
                'description': self.description
            })
            raise

    def _update_redis_status(self, status_data: Dict[str, Any]):
        """Update agent status in Redis.
        
        Args:
            status_data: Dictionary containing status information
        """
        try:
            if hasattr(self.data_service, 'redis_client') and self.data_service.redis_client:
                key = f"mcp:agent:{self.agent_id}:status"
                self.data_service.redis_client.set(key, json.dumps(status_data))
                self.logger.debug(f"Updated Redis status for {self.agent_id}")
        except Exception as e:
            self.logger.warning(f"Failed to update Redis status: {e}")

    async def run_analysis_cycle(self):
        """Run a single analysis cycle."""
        if not self.is_running:
            return

        try:
            self.status = 'analyzing'
            cycle_start_time = datetime.now()
            
            # Update status in Redis
            self._update_redis_status({
                'id': self.agent_id,
                'name': self.__class__.__name__,
                'status': 'analyzing',
                'is_running': True,
                'last_run': datetime.now().isoformat(),
                'capabilities': self.capabilities,
                'description': self.description
            })
            
            self.logger.info("Starting Log Level analysis cycle")

            # Get recent logs with error or critical levels
            logs = await self._get_logs_by_level()
            self.logger.info(f"Retrieved {len(logs)} error/critical logs")

            if not logs:
                self.logger.info("No error or critical logs found")
                return

            # Process each log and generate anomalies
            anomalies_created = 0
            for log in logs:
                try:
                    await self._process_log_for_anomaly(log)
                    anomalies_created += 1
                except Exception as e:
                    self.logger.error(f"Error processing log {log.get('id')}: {e}")
                    continue

            # Update cycle statistics
            cycle_duration = datetime.now() - cycle_start_time
            self.logger.info(f"Analysis cycle completed in {cycle_duration.total_seconds():.2f}s")
            self.logger.info(f"Created {anomalies_created} anomalies from {len(logs)} logs")

            # Update last run time
            self.update_last_run()
            self.status = 'active'
            
            # Update status in Redis
            self._update_redis_status({
                'id': self.agent_id,
                'name': self.__class__.__name__,
                'status': 'active',
                'is_running': True,
                'last_run': self.last_run.isoformat(),
                'capabilities': self.capabilities,
                'description': self.description
            })

        except Exception as e:
            self.logger.error(f"Error in analysis cycle: {e}")
            self.status = 'error'
            # Update status in Redis
            self._update_redis_status({
                'id': self.agent_id,
                'name': self.__class__.__name__,
                'status': 'error',
                'is_running': False,
                'last_run': datetime.now().isoformat(),
                'capabilities': self.capabilities,
                'description': self.description
            })
            raise

    async def _get_logs_by_level(self) -> List[Dict[str, Any]]:
        """
        Get logs with error or critical log levels from the database.
        
        Returns:
            List of log entries with error or critical levels
        """
        try:
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=self.lookback_minutes)
            
            # Connect to the database
            conn = await asyncpg.connect(
                host=self.data_service.db_config['host'],
                port=self.data_service.db_config['port'],
                user=self.data_service.db_config['user'],
                password=self.data_service.db_config['password'],
                database=self.data_service.db_config['database']
            )
            
            try:
                # Query for logs with error or critical levels
                query = """
                    SELECT 
                        id, device_id, device_ip, timestamp, log_level, 
                        process_name, message, raw_message, structured_data,
                        pushed_to_ai, pushed_at, push_attempts, last_push_error
                    FROM log_entries
                    WHERE timestamp >= $1 AND timestamp <= $2
                    AND LOWER(log_level) = ANY($3::text[])
                    ORDER BY timestamp DESC
                """
                
                # Convert target levels to lowercase for case-insensitive comparison
                target_levels_lower = [level.lower() for level in self.target_levels]
                params = [start_time, end_time, target_levels_lower]
                
                logs = await conn.fetch(query, *params)
                logs = [dict(record) for record in logs]
                
                self.logger.info(f"Retrieved {len(logs)} logs with levels {self.target_levels}")
                return logs
                
            finally:
                await conn.close()
                
        except Exception as e:
            self.logger.error(f"Error getting logs by level: {e}")
            raise

    async def _process_log_for_anomaly(self, log: Dict[str, Any]):
        """
        Process a single log entry and create an anomaly if needed.
        
        Args:
            log: Log entry dictionary
        """
        try:
            log_level = log.get('log_level', '').lower()
            
            # Check if this is a target level
            if log_level not in self.target_levels:
                return
            
            # Determine severity based on log level
            severity = self.severity_mapping.get(log_level, 3)
            
            # Create anomaly description
            description = self._create_anomaly_description(log)
            
            # Create features dictionary
            features = {
                'log_level': log_level,
                'process_name': log.get('process_name'),
                'device_ip': log.get('device_ip'),
                'message_length': len(log.get('message', '')),
                'timestamp': log.get('timestamp').isoformat() if log.get('timestamp') else None
            }
            
            # Store the anomaly
            await self.store_anomaly(
                anomaly_type=f"log_level_{log_level}",
                severity=severity,
                confidence=1.0,  # High confidence for rule-based detection
                description=description,
                features=features,
                device_id=log.get('device_id')
            )
            
            self.logger.info(f"Created anomaly for {log_level} log: {log.get('id')}")
            
        except Exception as e:
            self.logger.error(f"Error processing log for anomaly: {e}")
            raise

    def _create_anomaly_description(self, log: Dict[str, Any]) -> str:
        """
        Create a human-readable description for the anomaly.
        
        Args:
            log: Log entry dictionary
            
        Returns:
            String description of the anomaly
        """
        log_level = log.get('log_level', '').lower()
        process_name = log.get('process_name', 'Unknown')
        device_ip = log.get('device_ip', 'Unknown')
        message = log.get('message', 'No message')
        
        if log_level == 'error':
            return f"Error log detected from {process_name} on device {device_ip}: {message[:100]}..."
        elif log_level == 'critical':
            return f"Critical log detected from {process_name} on device {device_ip}: {message[:100]}..."
        else:
            return f"{log_level.title()} log detected from {process_name} on device {device_ip}: {message[:100]}..."

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.
        
        Returns:
            dict: Dictionary containing agent status information
        """
        base_status = super().get_status()
        base_status.update({
            'target_levels': self.target_levels,
            'lookback_minutes': self.lookback_minutes,
            'severity_mapping': self.severity_mapping
        })
        return base_status

    def check_running(self) -> bool:
        """
        Check if the agent is currently running.
        
        Returns:
            bool: True if the agent is running, False otherwise
        """
        return self.is_running 