import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncpg
import json

from .base_agent import BaseAgent

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
                'is_running': True,
                'last_run': datetime.now().isoformat(),
                'capabilities': self.capabilities,
                'description': self.description
            })
            raise

    async def _get_logs_by_level(self) -> List[Dict[str, Any]]:
        """Get recent logs with error or critical levels.
        
        Returns:
            List[Dict[str, Any]]: List of log entries with error or critical levels
        """
        try:
            # Get recent logs from the last lookback_minutes
            logs = await self.data_service.get_recent_logs(
                programs=None,  # All programs
                minutes=self.lookback_minutes
            )
            
            # Filter logs by level
            filtered_logs = []
            for log in logs:
                log_level = log.get('log_level', '').lower()
                if log_level in [level.lower() for level in self.target_levels]:
                    filtered_logs.append(log)
            
            return filtered_logs
            
        except Exception as e:
            self.logger.error(f"Error getting logs by level: {e}")
            return []

    async def _process_log_for_anomaly(self, log: Dict[str, Any]):
        """Process a single log entry and create an anomaly.
        
        Args:
            log: Log entry to process
        """
        try:
            # Get log level and determine severity
            log_level = log.get('log_level', '').lower()
            severity = self.severity_mapping.get(log_level, 3)
            
            # Create anomaly description
            description = self._create_anomaly_description(log)
            
            # Store the anomaly
            await self.store_anomaly(
                anomaly_type=f"{log_level}_log_detected",
                severity=severity,
                confidence=1.0,  # High confidence for rule-based detection
                description=description,
                features={
                    'log_level': log_level,
                    'program': log.get('process_name', 'unknown'),
                    'message': log.get('message', ''),
                    'timestamp': log.get('timestamp', ''),
                    'source': 'log_level_agent'
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error processing log for anomaly: {e}")
            raise

    def _create_anomaly_description(self, log: Dict[str, Any]) -> str:
        """Create a human-readable description for the anomaly.
        
        Args:
            log: Log entry that triggered the anomaly
            
        Returns:
            str: Description of the anomaly
        """
        log_level = log.get('log_level', 'unknown')
        program = log.get('process_name', 'unknown')
        message = log.get('message', '')
        
        # Truncate message if too long
        if len(message) > 200:
            message = message[:200] + "..."
        
        return f"{log_level.upper()} log detected from {program}: {message}"

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent.
        
        Returns:
            dict: Dictionary containing agent status information
        """
        return {
            "id": self.agent_id,
            "name": self.__class__.__name__,
            "is_running": self.is_running,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": (
                (self.last_run + timedelta(seconds=self.config.analysis_interval)).isoformat()
                if self.last_run
                else None
            ),
            "status": self.status,
            "capabilities": self.capabilities,
            "description": self.description
        }

    def check_running(self) -> bool:
        """Check if the agent is currently running.
        
        Returns:
            bool: True if the agent is running, False otherwise
        """
        return self.is_running 