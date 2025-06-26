import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import os

from .base_agent import BaseAgent

class GenericAgent(BaseAgent):
    """
    Generic agent class that provides configuration-driven initialization
    and common functionality for all agent types.
    """
    
    def __init__(self, config: Dict[str, Any], data_service, model_manager=None):
        """
        Initialize the generic agent with configuration.
        
        Args:
            config: Configuration dictionary containing agent settings
            data_service: DataService instance for database access
            model_manager: Optional ModelManager instance
        """
        # Initialize base agent with config object
        super().__init__(config, data_service)
        
        # Configuration-driven initialization
        self.agent_id = config.get('agent_id', self.__class__.__name__.lower())
        self.agent_name = config.get('name', self.__class__.__name__)
        self.description = config.get('description', 'Generic agent')
        self.agent_type = config.get('agent_type', 'generic')
        self.process_filters = config.get('process_filters', [])
        self.model_path = config.get('model_path')
        self.capabilities = config.get('capabilities', [])
        
        # Analysis rules from configuration
        self.analysis_rules = config.get('analysis_rules', {})
        self.lookback_minutes = self.analysis_rules.get('lookback_minutes', 5)
        self.analysis_interval = self.analysis_rules.get('analysis_interval', 60)
        self.severity_mapping = self.analysis_rules.get('severity_mapping', {})
        
        # Model manager integration
        self.model_manager = model_manager
        
        # Status management
        self.status = "initialized"
        self.is_running = False
        self.last_run = None
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{self.agent_id}")
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate the agent configuration."""
        required_fields = ['agent_id', 'agent_name', 'agent_type']
        missing_fields = [field for field in required_fields if not getattr(self, field, None)]
        
        if missing_fields:
            raise ValueError(f"Missing required configuration fields: {missing_fields}")
        
        if self.agent_type not in ['ml_based', 'rule_based', 'hybrid']:
            raise ValueError(f"Invalid agent_type: {self.agent_type}. Must be one of: ml_based, rule_based, hybrid")
    
    async def start(self):
        """Start the generic agent."""
        try:
            self.logger.info(f"Starting {self.agent_name}...")
            
            # Set running state
            self.is_running = True
            self.status = 'active'
            self.last_run = datetime.now()
            
            # Update status in Redis
            self._update_redis_status({
                'id': self.agent_id,
                'name': self.agent_name,
                'status': 'active',
                'is_running': True,
                'last_run': self.last_run.isoformat(),
                'capabilities': self.capabilities,
                'description': self.description,
                'agent_type': self.agent_type
            })
            
            self.logger.info(f"{self.agent_name} started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start {self.agent_name}: {e}")
            self.status = 'error'
            self._update_redis_status({
                'id': self.agent_id,
                'name': self.agent_name,
                'status': 'error',
                'is_running': False,
                'last_run': datetime.now().isoformat(),
                'capabilities': self.capabilities,
                'description': self.description,
                'agent_type': self.agent_type
            })
            raise
    
    async def stop(self, unregister=True):
        """Stop the generic agent.
        
        Args:
            unregister: Whether to unregister the agent from the registry
        """
        try:
            self.logger.info(f"Stopping {self.agent_name}...")
            
            # Stop the agent
            self.is_running = False
            self.status = 'inactive'
            self.last_run = datetime.now()
            
            # Update status in Redis
            self._update_redis_status({
                'id': self.agent_id,
                'name': self.agent_name,
                'status': 'inactive',
                'is_running': False,
                'last_run': self.last_run.isoformat(),
                'capabilities': self.capabilities,
                'description': self.description,
                'agent_type': self.agent_type
            })
            
            self.logger.info(f"{self.agent_name} stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping {self.agent_name}: {e}")
            self.status = 'error'
            self._update_redis_status({
                'id': self.agent_id,
                'name': self.agent_name,
                'status': 'error',
                'is_running': False,
                'last_run': datetime.now().isoformat(),
                'capabilities': self.capabilities,
                'description': self.description,
                'agent_type': self.agent_type
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
        """
        Run a single analysis cycle.
        
        This method should be overridden by specific agent types.
        """
        if not self.is_running:
            return
        
        try:
            self.status = 'analyzing'
            cycle_start_time = datetime.now()
            
            # Update status in Redis
            self._update_redis_status({
                'id': self.agent_id,
                'name': self.agent_name,
                'status': 'analyzing',
                'is_running': True,
                'last_run': datetime.now().isoformat(),
                'capabilities': self.capabilities,
                'description': self.description,
                'agent_type': self.agent_type
            })
            
            self.logger.info(f"Starting analysis cycle for {self.agent_name}")
            
            # Get recent logs based on process filters
            logs = await self.data_service.get_recent_logs(
                programs=self.process_filters if self.process_filters else None,
                minutes=self.lookback_minutes
            )
            
            self.logger.info(f"Retrieved {len(logs)} logs for analysis")
            
            if not logs:
                self.logger.info("No logs to analyze")
                return
            
            # Perform analysis (to be implemented by subclasses)
            await self._perform_analysis(logs)
            
            # Update cycle statistics
            cycle_duration = datetime.now() - cycle_start_time
            self.logger.info(f"Analysis cycle completed in {cycle_duration.total_seconds():.2f}s")
            
            # Update last run time
            self.update_last_run()
            self.status = 'active'
            
            # Update status in Redis
            self._update_redis_status({
                'id': self.agent_id,
                'name': self.agent_name,
                'status': 'active',
                'is_running': True,
                'last_run': self.last_run.isoformat(),
                'capabilities': self.capabilities,
                'description': self.description,
                'agent_type': self.agent_type
            })
            
        except Exception as e:
            self.logger.error(f"Error in analysis cycle: {e}")
            self.status = 'error'
            self._update_redis_status({
                'id': self.agent_id,
                'name': self.agent_name,
                'status': 'error',
                'is_running': True,
                'last_run': datetime.now().isoformat(),
                'capabilities': self.capabilities,
                'description': self.description,
                'agent_type': self.agent_type
            })
            raise
    
    async def _perform_analysis(self, logs: List[Dict[str, Any]]):
        """
        Perform analysis on logs.
        
        This method should be overridden by specific agent types.
        
        Args:
            logs: List of log entries to analyze
        """
        raise NotImplementedError("_perform_analysis must be implemented by subclasses")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.
        
        Returns:
            dict: Dictionary containing agent status information
        """
        return {
            "id": self.agent_id,
            "name": self.agent_name,
            "is_running": self.is_running,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": (
                (self.last_run + timedelta(seconds=self.analysis_interval)).isoformat()
                if self.last_run
                else None
            ),
            "status": self.status,
            "capabilities": self.capabilities,
            "description": self.description,
            "agent_type": self.agent_type,
            "process_filters": self.process_filters,
            "model_path": self.model_path
        }
    
    def should_run(self) -> bool:
        """
        Check if the agent should run based on the last run time.
        
        Returns:
            bool: True if the agent should run, False otherwise
        """
        if not self.last_run:
            return True
            
        time_since_last_run = datetime.now() - self.last_run
        return time_since_last_run >= timedelta(seconds=self.analysis_interval) 