import logging
import json
import redis
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import yaml
import asyncio

from ..agents.base_agent import BaseAgent
from ..agents.generic_agent import GenericAgent
from ..agents.ml_based_agent import MLBasedAgent
from ..agents.rule_based_agent import RuleBasedAgent
from ..agents.hybrid_agent import HybridAgent
from app.components.model_manager import ModelManager

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
            # Always resolve config_dir relative to the project root
            base_dir = Path(__file__).resolve().parent.parent.parent.parent  # Go up to project root
            config_dir = base_dir / "app" / "config"
            agent_config_file = config_dir / "agent_config.yaml"
            
            self.logger.info(f"Loading agent configs from: {config_dir}")
            
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
            
            # Load from new agents directory if it exists
            agents_config_dir = config_dir / "agents"
            if agents_config_dir.exists():
                self.logger.info(f"Loading from agents directory: {agents_config_dir}")
                for config_file in agents_config_dir.glob("*.yaml"):
                    agent_id = config_file.stem
                    self.logger.info(f"Loading config file: {config_file}")
                    with open(config_file, 'r') as f:
                        config = yaml.safe_load(f)
                        self.agent_configs[agent_id] = config
                        self.logger.info(f"Loaded {agent_id} agent configuration from agents directory")
                        self.logger.info(f"  Process Filters: {config.get('process_filters', [])}")
                        self.logger.info(f"  Capabilities: {config.get('capabilities', [])}")
            else:
                self.logger.warning(f"Agents directory not found: {agents_config_dir}")
                        
        except Exception as e:
            self.logger.error(f"Error loading agent configurations: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def create_agent(self, agent_id: str, data_service, model_manager=None) -> Optional[BaseAgent]:
        """Create agent instance from configuration.
        
        Args:
            agent_id: Unique identifier for the agent
            data_service: DataService instance for database access
            model_manager: Optional ModelManager instance
            
        Returns:
            BaseAgent: Created agent instance or None if creation failed
        """
        try:
            # Get agent configuration
            config = self.agent_configs.get(agent_id)
            if not config:
                self.logger.error(f"Configuration not found for agent: {agent_id}")
                return None
            
            agent_type = config.get('agent_type', 'ml_based')
            
            # Create agent based on agent_id and type
            if agent_id == 'wifi_agent':
                from ..agents.wifi_agent import WiFiAgent
                agent = WiFiAgent(config, data_service, model_manager)
            elif agent_type == 'ml_based':
                agent = MLBasedAgent(config, data_service, model_manager)
            elif agent_type == 'rule_based':
                agent = RuleBasedAgent(config, data_service, model_manager)
            elif agent_type == 'hybrid':
                agent = HybridAgent(config, data_service, model_manager)
            else:
                self.logger.error(f"Unknown agent type: {agent_type}")
                return None
            
            self.logger.info(f"Created {agent_type} agent: {agent_id}")
            return agent
            
        except Exception as e:
            self.logger.error(f"Error creating agent {agent_id}: {e}")
            return None
    
    def create_agent_from_config(self, config: Dict[str, Any], data_service, model_manager=None) -> Optional[BaseAgent]:
        """Create agent instance from provided configuration.
        
        Args:
            config: Agent configuration dictionary
            data_service: DataService instance for database access
            model_manager: Optional ModelManager instance
            
        Returns:
            BaseAgent: Created agent instance or None if creation failed
        """
        try:
            agent_id = config.get('agent_id')
            if not agent_id:
                self.logger.error("Agent configuration missing agent_id")
                return None
            
            agent_type = config.get('agent_type', 'ml_based')
            
            # Create agent based on agent_id and type
            if agent_id == 'wifi_agent':
                from ..agents.wifi_agent import WiFiAgent
                agent = WiFiAgent(config, data_service, model_manager)
            elif agent_type == 'ml_based':
                agent = MLBasedAgent(config, data_service, model_manager)
            elif agent_type == 'rule_based':
                agent = RuleBasedAgent(config, data_service, model_manager)
            elif agent_type == 'hybrid':
                agent = HybridAgent(config, data_service, model_manager)
            else:
                self.logger.error(f"Unknown agent type: {agent_type}")
                return None
            
            self.logger.info(f"Created {agent_type} agent from config: {agent_id}")
            return agent
            
        except Exception as e:
            self.logger.error(f"Error creating agent from config: {e}")
            return None
    
    def save_agent_config(self, agent_id: str, config: Dict[str, Any]) -> bool:
        """Save agent configuration to file.
        
        Args:
            agent_id: Unique identifier for the agent
            config: Configuration dictionary to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Create agents directory if it doesn't exist
            # Use the same path resolution as _load_agent_configs
            base_dir = Path(__file__).resolve().parent.parent.parent.parent  # Go up to project root
            agents_config_dir = base_dir / "app" / "config" / "agents"
            agents_config_dir.mkdir(exist_ok=True)
            
            # Save configuration file
            config_file = agents_config_dir / f"{agent_id}.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            # Update in-memory config
            self.agent_configs[agent_id] = config
            
            self.logger.info(f"Saved agent configuration: {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving agent configuration {agent_id}: {e}")
            return False
    
    def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent configuration.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            dict: Agent configuration or None if not found
        """
        # First check in-memory config
        if agent_id in self.agent_configs:
            return self.agent_configs.get(agent_id)
        
        # If not in memory, try to load from file
        try:
            base_dir = Path(__file__).resolve().parent.parent.parent.parent  # Go up to project root
            agents_config_dir = base_dir / "app" / "config" / "agents"
            config_file = agents_config_dir / f"{agent_id}.yaml"
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    # Update in-memory cache
                    self.agent_configs[agent_id] = config
                    self.logger.info(f"Loaded {agent_id} configuration from file")
                    return config
        except Exception as e:
            self.logger.error(f"Error loading {agent_id} configuration from file: {e}")
        
        return None
    
    def list_agent_configs(self) -> List[Dict[str, Any]]:
        """List all available agent configurations.
        
        Returns:
            List[Dict[str, Any]]: List of agent configurations
        """
        configs = []
        for agent_id, config in self.agent_configs.items():
            config_info = {
                'agent_id': agent_id,
                'name': config.get('name', agent_id),
                'description': config.get('description', ''),
                'agent_type': config.get('agent_type', 'unknown'),
                'capabilities': config.get('capabilities', []),
                'is_created': agent_id in self.agents
            }
            configs.append(config_info)
        
        return configs
    
    def delete_agent_config(self, agent_id: str) -> bool:
        """Delete agent configuration.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            # Remove from in-memory configs
            if agent_id in self.agent_configs:
                del self.agent_configs[agent_id]
            
            # Remove from agents if created
            if agent_id in self.agents:
                del self.agents[agent_id]
            
            # Delete configuration file
            base_dir = Path(__file__).resolve().parent.parent.parent.parent  # Go up to project root
            agents_config_dir = base_dir / "app" / "config" / "agents"
            config_file = agents_config_dir / f"{agent_id}.yaml"
            if config_file.exists():
                config_file.unlink()
            
            self.logger.info(f"Deleted agent configuration: {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting agent configuration {agent_id}: {e}")
            return False

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
            
            # Get agent name from agent instance or configuration
            agent_name = getattr(agent, 'agent_name', None)
            if not agent_name and agent_id in self.agent_configs:
                agent_name = self.agent_configs[agent_id].get('name', agent.__class__.__name__)
            elif not agent_name:
                agent_name = agent.__class__.__name__
            
            # Update status in Redis
            self._update_agent_status(agent_id, {
                'id': agent_id,
                'name': agent_name,
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
            # Get agent name from agent instance or fall back to configuration
            agent_name = getattr(agent, 'agent_name', None)
            if not agent_name and agent_id in self.agent_configs:
                agent_name = self.agent_configs[agent_id].get('name', agent.__class__.__name__)
            elif not agent_name:
                agent_name = agent.__class__.__name__
            
            # Get status from agent's get_status method for consistency
            agent_status = agent.get_status() if hasattr(agent, 'get_status') else {}
            
            agent_info = {
                'id': agent_id,
                'name': agent_name,
                'status': agent_status.get('status', agent.status),
                'is_running': agent_status.get('is_running', agent.is_running),
                'last_run': agent_status.get('last_run'),
                'capabilities': agent_status.get('capabilities', agent.capabilities),
                'description': agent_status.get('description', agent.description),
                'model_path': getattr(agent, 'model_path', None),
                'config': self.agent_configs.get(agent_id, {})
            }
            
            # Get additional status from Redis if available
            if self.redis_client:
                try:
                    # Check agent status first (more reliable)
                    agent_key = f"mcp:agent:{agent_id}:status"
                    agent_status_data = self.redis_client.get(agent_key)
                    if agent_status_data:
                        agent_status = json.loads(agent_status_data)
                        # Only update if the agent status is more recent or if we don't have model status
                        agent_info.update(agent_status)
                    
                    # Check model status as fallback (what WiFi agent updates)
                    model_key = f"mcp:model:{agent_id}:status"
                    model_status_data = self.redis_client.get(model_key)
                    if model_status_data:
                        model_status = json.loads(model_status_data)
                        # Only update if we don't have agent status or if model status is more recent
                        if not agent_status_data:
                            agent_info.update(model_status)
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
            
            # For WiFiAgent, reload the model before starting
            if agent_id == 'wifi_agent' and hasattr(agent, 'reload_model'):
                self.logger.info(f"Reloading model for {agent_id}")
                agent.reload_model()
            
            # Start the agent
            await agent.start()
            
            self.logger.info(f"Restarted agent: {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restarting agent {agent_id}: {e}")
            return False
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models.
        
        Returns:
            list: List of model information dictionaries
        """
        try:
            all_models = self.model_manager.get_all_models()
            # If all_models is a dict with 'models' key, use .items(), else treat as list
            if isinstance(all_models, dict) and 'models' in all_models:
                models_iter = all_models['models'].items()
            elif isinstance(all_models, list):
                models_iter = enumerate(all_models)
            else:
                models_iter = []
            models_list = []
            for model_id, model_data in models_iter:
                models_list.append({
                    'name': model_data.get('name', model_id),
                    'path': model_data.get('path', f'/models/{model_id}'),
                    'size': model_data.get('size', 0),
                    'modified': model_data.get('created_at', datetime.now().isoformat())
                })
            return models_list
        except Exception as e:
            self.logger.error(f"Error getting available models: {e}")
            return []
    
    def reset(self):
        """Reset the agent registry by clearing and reloading configurations."""
        self.logger.info("Resetting agent registry...")
        
        # Clear current state
        self.agents.clear()
        self.agent_configs.clear()
        
        self.logger.info("Cleared agents and configurations")
        
        # Reload configurations
        self._load_agent_configs()
        
        self.logger.info(f"Reloaded {len(self.agent_configs)} configurations")
        
        # Log what was loaded
        for agent_id, config in self.agent_configs.items():
            self.logger.info(f"  - {agent_id}:")
            self.logger.info(f"    Process Filters: {config.get('process_filters', [])}")
            self.logger.info(f"    Capabilities: {config.get('capabilities', [])}")
    
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