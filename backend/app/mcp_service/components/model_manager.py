import logging
import json
from typing import Dict, Any, List, Optional
from app.services.status_manager import ServiceStatusManager
from datetime import datetime
from app.mcp_service.agents.base_agent import BaseAgent
import pickle
import os
import re
import redis

logger = logging.getLogger(__name__)

class ModelManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            logger.info("Creating new ModelManager instance")
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        logger.info("Initializing ModelManager")
        # Static model registry for UI display
        self.model_registry = {
            'wifi_agent': {
                'id': 'wifi_agent',
                'version': '1.0.0',
                'created_at': datetime.now().isoformat(),
                'metrics': {
                    'accuracy': 0.92,
                    'false_positive_rate': 0.03,
                    'false_negative_rate': 0.05
                },
                'status': 'inactive',
                'description': 'WiFi anomaly detection agent',
                'capabilities': [
                    'Authentication failure detection',
                    'Deauthentication flood detection',
                    'Beacon frame flood detection'
                ]
            }
        }
        # Dynamic model instances
        self.models: Dict[str, Dict[str, Any]] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.status_manager = None
        self.logger = logger
        self._initialized = True
        logger.info("ModelManager initialized")

    def _convert_to_snake_case(self, name: str) -> str:
        """Convert a camelCase or PascalCase name to snake_case."""
        # Handle special cases
        if name == 'WiFiAgent':
            return 'wifi_agent'
            
        # Convert camelCase/PascalCase to snake_case
        import re
        pattern = re.compile(r'(?<!^)(?=[A-Z])')
        return pattern.sub('_', name).lower()

    async def load_model(self, model_path: str):
        """
        Load a model from a file.

        Args:
            model_path: Path to the model file

        Returns:
            The loaded model object
        """
        try:
            if not os.path.exists(model_path):
                logger.warning(f"Model file not found at {model_path}, using default model")
                # For now, return a simple dictionary as a placeholder model
                return {
                    'type': 'wifi_anomaly',
                    'version': '1.0.0',
                    'thresholds': {
                        'auth_failures': 5,
                        'deauth_count': 10,
                        'beacon_count': 100
                    }
                }
            logger.info(f"Loading model from {model_path}")
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            logger.info("Model loaded successfully")
            return model
        except Exception as e:
            logger.error(f"Error loading model from {model_path}: {e}")
            raise

    def set_redis_client(self, redis_client: redis.Redis) -> None:
        """Set the Redis client for status updates."""
        self.redis_client = redis_client
        self.logger.info("Setting Redis client for ModelManager")
        self.status_manager = ServiceStatusManager('model_service', self.redis_client)
        logger.info("Status manager initialized")

    def _update_model_status(self, model_id: str, model_entry: Dict[str, Any]) -> None:
        """Update model status in Redis."""
        try:
            if not self.redis_client:
                self.logger.warning("Redis client not set, skipping status update")
                return

            # Convert model entry to JSON-serializable format
            status_data = {
                'id': model_entry['id'],
                'name': model_entry['name'],
                'status': model_entry['status'],
                'is_running': model_entry['is_running'],
                'last_run': model_entry['last_run'],
                'capabilities': model_entry['capabilities'],
                'description': model_entry['description']
            }
            
            # Store in Redis with proper key format
            self.redis_client.hset(
                f"mcp:model:{model_id}:status",
                mapping={
                    'status': json.dumps(status_data),
                    'last_update': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update model {model_id} status: {e}")
            raise

    def register_model(self, agent: BaseAgent, model_id: str = None) -> None:
        """Register a model agent with the manager."""
        try:
            # Use provided model_id or convert class name
            model_id = model_id or self._convert_to_snake_case(agent.__class__.__name__)
            
            # Create model entry
            model_entry = {
                'id': model_id,
                'name': agent.__class__.__name__,
                'status': agent.status,
                'is_running': agent.is_running,
                'last_run': agent.last_run.isoformat() if agent.last_run else None,
                'capabilities': agent.capabilities,
                'description': agent.description,
                'agent': agent
            }
            
            # Store in memory
            self.models[model_id] = model_entry
            
            # Update Redis status
            self._update_model_status(model_id, model_entry)
            
            # Update service status
            if self.status_manager:
                self.status_manager.update_status('connected')
            
            self.logger.info(f"Successfully registered model: {model_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to register model: {e}")
            raise

    async def start(self):
        """Start the model manager."""
        try:
            self.logger.info("Starting ModelManager...")
            
            # Clear any existing models
            self.models.clear()
            
            # Start status updates
            if self.redis_client:
                self.status_manager.start_status_updates(self.check_health, interval=10)
                self.status_manager.update_status('connected')
            
            self.logger.info("ModelManager started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start ModelManager: {e}")
            raise

    async def stop(self):
        """Stop the model manager."""
        try:
            self.logger.info("Stopping ModelManager...")
            # Stop all models
            for model_id, model_entry in self.models.items():
                try:
                    await model_entry['agent'].stop()
                except Exception as e:
                    self.logger.error(f"Error stopping model {model_id}: {e}")
            
            # Stop status updates
            if hasattr(self, 'status_manager'):
                self.status_manager.stop_status_updates()
            
            # Clear models
            self.models.clear()
            
            self.logger.info("ModelManager stopped successfully")
        except Exception as e:
            self.logger.error(f"Failed to stop ModelManager: {e}")
            if self.status_manager:
                self.status_manager.update_status('error', str(e))
            raise

    def check_health(self) -> bool:
        """Check the health of all models."""
        try:
            for model_id, model_entry in self.models.items():
                agent = model_entry['agent']
                if agent.is_running:
                    # Update status
                    model_entry['status'] = agent.status
                    model_entry['is_running'] = agent.is_running
                    model_entry['last_run'] = agent.last_run.isoformat() if agent.last_run else None
                    
                    # Update Redis
                    self._update_model_status(model_id, model_entry)
            
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    def get_all_models(self) -> Dict[str, Any]:
        """Get information about all registered models."""
        try:
            models = []
            
            # First add models from registry
            for model_id, model_info in self.model_registry.items():
                # Get status from Redis if available
                if self.redis_client:
                    try:
                        status_data = self.redis_client.hget(f"mcp:model:{model_id}:status", 'status')
                        if status_data:
                            model_info.update(json.loads(status_data))
                    except Exception as e:
                        self.logger.error(f"Error getting Redis status for {model_id}: {e}")
                
                # Format model info for API response
                model_info = {
                    'id': model_id,
                    'version': model_info['version'],
                    'created_at': model_info['created_at'],
                    'metrics': model_info['metrics'],
                    'status': 'active' if model_id in self.models and self.models[model_id]['is_running'] else 'inactive'
                }
                models.append(model_info)
            
            return {
                'models': models,
                'total': len(models)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting models: {e}")
            return {
                'models': [],
                'total': 0
            }

# Create the singleton instance
model_manager = ModelManager()