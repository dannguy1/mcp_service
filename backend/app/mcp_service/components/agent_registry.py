import logging
import json
import redis
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import yaml
import asyncio

from ..agents.base_agent import BaseAgent
from .model_manager import ModelManager

logger = logging.getLogger(__name__)

class AgentRegistry:
    """Registry for managing agents and their model associations."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize the agent registry.
        
        Args:
            redis_client: Redis client for status storage
        """
        self.redis_client = redis_client
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_configs: Dict[str, Dict[str, Any]] = {}
        self.model_manager = ModelManager()
        self.logger = logger
        
        # Load agent configurations
        self._load_agent_configs()
    
    def _load_agent_configs(self):
        """Load agent configurations from files."""
        try:
            config_dir = Path("backend/app/config")
            agent_config_file = config_dir / "agent_config.yaml"
            
            if agent_config_file.exists():
                with open(agent_config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    self.agent_configs['wifi_agent'] = config
                    self.logger.info("Loaded WiFi agent configuration")
            
            # Load additional agent configs if they exist
            for config_file in config_dir.glob("agent_*.yaml"):
                if config_file.name != "agent_config.yaml":
                    agent_name = config_file.stem.replace("agent_", "")
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f)
                        self.agent_configs[agent_name] = config
                        self.logger.info(f"Loaded {agent_name} agent configuration")
                        
        except Exception as e:
            self.logger.error(f"Error loading agent configurations: {e}")
    
    def register_agent(self, agent: BaseAgent, agent_id: str) -> bool:
        """Register an agent with the registry.
        
        Args:
            agent: Agent instance to register
            agent_id: Unique identifier for the agent
            
        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            self.agents[agent_id] = agent
            self.logger.info(f"Registered agent: {agent_id}")
            
            # Update status in Redis
            self._update_agent_status(agent_id, {
                'id': agent_id,
                'name': agent.__class__.__name__,
                'status': 'registered',
                'is_running': agent.is_running,
                'last_run': agent.last_run.isoformat() if agent.last_run else None,
                'capabilities': agent.capabilities,
                'description': agent.description,
                'model_path': getattr(agent, 'model_path', None)
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering agent {agent_id}: {e}")
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the registry.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            bool: True if unregistration successful, False otherwise
        """
        try:
            if agent_id in self.agents:
                del self.agents[agent_id]
                self.logger.info(f"Unregistered agent: {agent_id}")
                
                # Remove status from Redis
                if self.redis_client:
                    key = f"mcp:agent:{agent_id}:status"
                    self.redis_client.delete(key)
                
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error unregistering agent {agent_id}: {e}")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            BaseAgent: Agent instance or None if not found
        """
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents with their status.
        
        Returns:
            List[Dict[str, Any]]: List of agent information
        """
        agents_info = []
        
        for agent_id, agent in self.agents.items():
            agent_info = {
                'id': agent_id,
                'name': agent.__class__.__name__,
                'status': agent.status,
                'is_running': agent.is_running,
                'last_run': agent.last_run.isoformat() if agent.last_run else None,
                'capabilities': agent.capabilities,
                'description': agent.description,
                'model_path': getattr(agent, 'model_path', None),
                'config': self.agent_configs.get(agent_id, {})
            }
            
            # Get additional status from Redis if available
            if self.redis_client:
                try:
                    # Check model status first (what WiFi agent updates)
                    model_key = f"mcp:model:{agent_id}:status"
                    model_status_data = self.redis_client.get(model_key)
                    if model_status_data:
                        model_status = json.loads(model_status_data)
                        agent_info.update(model_status)
                    else:
                        # Fallback to agent status
                        agent_key = f"mcp:agent:{agent_id}:status"
                        agent_status_data = self.redis_client.get(agent_key)
                        if agent_status_data:
                            agent_status = json.loads(agent_status_data)
                            agent_info.update(agent_status)
                except Exception as e:
                    self.logger.warning(f"Error getting Redis status for {agent_id}: {e}")
            
            agents_info.append(agent_info)
        
        return agents_info
    
    def set_agent_model(self, agent_id: str, model_path: str) -> bool:
        """Set the model for a specific agent.
        
        Args:
            agent_id: Unique identifier for the agent
            model_path: Path to the model file
            
        Returns:
            bool: True if model was set successfully, False otherwise
        """
        try:
            if agent_id not in self.agents:
                self.logger.error(f"Agent {agent_id} not found")
                return False
            
            agent = self.agents[agent_id]
            
            # Update agent's model path
            if hasattr(agent, 'model_path'):
                agent.model_path = model_path
                self.logger.info(f"Updated model path for {agent_id}: {model_path}")
            
            # Update configuration
            if agent_id in self.agent_configs:
                self.agent_configs[agent_id]['model_path'] = model_path
                
                # Save updated configuration
                config_file = Path("backend/app/config") / f"agent_{agent_id}.yaml"
                with open(config_file, 'w') as f:
                    yaml.dump(self.agent_configs[agent_id], f, default_flow_style=False)
            
            # Update status in Redis
            self._update_agent_status(agent_id, {
                'model_path': model_path,
                'model_updated_at': datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting model for agent {agent_id}: {e}")
            return False
    
    def get_agent_model(self, agent_id: str) -> Optional[str]:
        """Get the current model path for an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            str: Model path or None if not found
        """
        agent = self.agents.get(agent_id)
        if agent and hasattr(agent, 'model_path'):
            return agent.model_path
        return None
    
    async def restart_agent(self, agent_id: str) -> bool:
        """Restart an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            bool: True if restart successful, False otherwise
        """
        try:
            if agent_id not in self.agents:
                self.logger.error(f"Agent {agent_id} not found")
                return False
            
            agent = self.agents[agent_id]
            
            # Stop the agent without unregistering it
            await agent.stop(unregister=False)
            
            # Start the agent
            await agent.start()
            
            self.logger.info(f"Restarted agent: {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restarting agent {agent_id}: {e}")
            return False
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models for agents.
        
        Returns:
            List[Dict[str, Any]]: List of available models
        """
        try:
            # Use the enhanced model management system
            from app.components.model_manager import ModelManager
            from app.models.config import ModelConfig
            
            config = ModelConfig()
            model_manager_instance = ModelManager(config)
            
            # Get models from the enhanced system using asyncio
            import asyncio
            try:
                # Try to get the current event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, we need to create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    models = loop.run_until_complete(model_manager_instance.list_models())
                    loop.close()
                else:
                    # Use the existing loop
                    models = loop.run_until_complete(model_manager_instance.list_models())
            except RuntimeError:
                # No event loop, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    models = loop.run_until_complete(model_manager_instance.list_models())
                finally:
                    loop.close()
            
            # Transform to the expected format
            available_models = []
            for model in models:
                # Get the model name from metadata
                metadata = model.get('metadata', {})
                model_info = metadata.get('model_info', {})
                name = model_info.get('description', model.get('version', 'Unknown'))
                
                model_info = {
                    'name': name,
                    'path': model.get('path', ''),
                    'size': 0,  # Size not available in enhanced system
                    'modified': model.get('last_updated', model.get('created_at', ''))
                }
                available_models.append(model_info)
            
            self.logger.info(f"Found {len(available_models)} available models")
            return available_models
            
        except Exception as e:
            self.logger.error(f"Error getting available models: {e}")
            return []
    
    def _update_agent_status(self, agent_id: str, status_data: Dict[str, Any]):
        """Update agent status in Redis.
        
        Args:
            agent_id: Unique identifier for the agent
            status_data: Status data to update
        """
        if not self.redis_client:
            return
        
        try:
            key = f"mcp:agent:{agent_id}:status"
            
            # Get existing status
            existing_data = self.redis_client.get(key)
            if existing_data:
                current_status = json.loads(existing_data)
                current_status.update(status_data)
            else:
                current_status = status_data
            
            # Update timestamp
            current_status['updated_at'] = datetime.now().isoformat()
            
            # Save to Redis
            self.redis_client.set(key, json.dumps(current_status))
            
        except Exception as e:
            self.logger.error(f"Error updating agent status for {agent_id}: {e}")

# Global instance
agent_registry = AgentRegistry() 