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
                'name': 'WiFiAgent',
                'version': '1.0.0',
                'created_at': datetime.now().isoformat(),
                'metrics': {
                    'accuracy': 0.92,
                    'false_positive_rate': 0.03,
                    'false_negative_rate': 0.05
                },
                'status': 'active',
                'description': 'WiFi anomaly detection agent',
                'capabilities': [
                    'Authentication failure detection',
                    'Deauthentication flood detection',
                    'Beacon frame flood detection'
                ]
            },
            'dns_agent': {
                'id': 'dns_agent',
                'name': 'DNSAgent',
                'version': '1.0.0',
                'created_at': datetime.now().isoformat(),
                'metrics': {
                    'accuracy': 0.89,
                    'false_positive_rate': 0.04,
                    'false_negative_rate': 0.07
                },
                'status': 'active',
                'description': 'DNS query anomaly detection',
                'capabilities': [
                    'DNS amplification detection',
                    'Query flood detection',
                    'Suspicious domain detection'
                ]
            },
            'system_agent': {
                'id': 'system_agent',
                'name': 'SystemAgent',
                'version': '1.0.0',
                'created_at': datetime.now().isoformat(),
                'metrics': {
                    'accuracy': 0.91,
                    'false_positive_rate': 0.03,
                    'false_negative_rate': 0.06
                },
                'status': 'active',
                'description': 'System-level anomaly detection',
                'capabilities': [
                    'System resource anomaly detection',
                    'Authentication failure detection',
                    'Process behavior analysis'
                ]
            },
            'log_level_agent': {
                'id': 'log_level_agent',
                'name': 'LogLevelAgent',
                'version': '1.0.0',
                'created_at': datetime.now().isoformat(),
                'metrics': {
                    'accuracy': 0.95,
                    'false_positive_rate': 0.02,
                    'false_negative_rate': 0.03
                },
                'status': 'active',
                'description': 'Rule-based log level monitoring',
                'capabilities': [
                    'Error log level detection',
                    'Critical log level detection',
                    'Warning level monitoring'
                ]
            },
            'threshold_agent': {
                'id': 'threshold_agent',
                'name': 'ThresholdAgent',
                'version': '1.0.0',
                'created_at': datetime.now().isoformat(),
                'metrics': {
                    'accuracy': 0.93,
                    'false_positive_rate': 0.03,
                    'false_negative_rate': 0.04
                },
                'status': 'active',
                'description': 'Threshold-based anomaly detection',
                'capabilities': [
                    'Threshold violation detection',
                    'Rate limiting detection',
                    'Resource usage monitoring'
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

    def load_model(self, model_path: str):
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

    def _update_model_status(self, model_id: str, model_entry: Dict[str, Any]):
        """Update model status in Redis."""
        try:
            if not self.redis_client:
                self.logger.warning("Redis client not available, skipping status update")
                return

            # Clean up old keys with variations of the model ID
            old_keys = [
                f"mcp:model:wi_fi_agent:status",
                f"mcp:model:WiFiAgent:status",
                f"mcp:model:wifiagent:status",
                f"mcp:model:wifi_agent:status"
            ]
            for key in old_keys:
                self.redis_client.delete(key)

            # Use consistent key format
            key = f"mcp:model:{model_id}:status"
            
            # Map agent status to frontend status
            if model_entry['status'] in ['active', 'analyzing', 'initialized']:
                frontend_status = 'active'
            elif model_entry['status'] == 'error':
                frontend_status = 'error'
            else:
                frontend_status = 'inactive'
            
            # Create frontend-compatible status object
            status_obj = {
                'id': model_id,
                'name': model_entry['name'],
                'status': frontend_status,
                'is_running': model_entry['is_running'],
                'last_run': model_entry['last_run'],
                'capabilities': model_entry['capabilities'],
                'description': model_entry['description']
            }
            
            value = json.dumps(status_obj)
            self.logger.info(f"Setting Redis key: {key}")
            self.logger.info(f"Setting Redis value: {value}")
            
            # Store full model entry as JSON
            self.redis_client.set(key, value)
            
            # Verify the value was stored correctly
            stored_value = self.redis_client.get(key)
            self.logger.info(f"Stored Redis value: {stored_value}")

            # Update in-memory model entry
            if model_id in self.models:
                self.models[model_id].update(model_entry)
            
            # Update registry status
            if model_id in self.model_registry:
                self.model_registry[model_id]['status'] = frontend_status
            
            self.logger.info(f"Updated model {model_id} status to {frontend_status}")
            
        except Exception as e:
            self.logger.error(f"Failed to update model {model_id} status: {e}")
            raise

    def set_redis_client(self, redis_client: redis.Redis) -> None:
        """Set the Redis client for status updates."""
        if not redis_client:
            self.logger.warning("Attempted to set None Redis client")
            return
            
        self.redis_client = redis_client
        self.logger.info("Setting Redis client for ModelManager")
        self.status_manager = ServiceStatusManager('model_service', self.redis_client)
        self.logger.info("Status manager initialized")
        
        # Update model registry status in Redis
        for model_id, model_data in self.model_registry.items():
            # Determine if the model should be running based on its status
            is_running = model_data['status'] in ['active', 'analyzing', 'initialized']
            
            # Use the correct name from model_data or fall back to model_id
            agent_name = model_data.get('name', model_id)
            
            self._update_model_status(model_id, {
                'id': model_id,
                'name': agent_name,
                'status': model_data['status'],
                'is_running': is_running,
                'last_run': None,
                'capabilities': model_data['capabilities'],
                'description': model_data['description']
            })

    def register_model(self, agent: BaseAgent, model_id: str) -> bool:
        """Register a model with the manager."""
        try:
            if model_id in self.models:
                self.logger.warning(f"Model {model_id} already registered")
                return False

            # Get agent name from configuration or fall back to class name
            agent_name = getattr(agent, 'agent_name', None)
            if not agent_name:
                # Try to get name from agent configuration
                agent_name = getattr(agent, 'name', None)
            if not agent_name:
                # Fall back to class name
                agent_name = agent.__class__.__name__

            # Create model entry
            model_entry = {
                'id': model_id,
                'name': agent_name,
                'status': 'initialized',
                'is_running': False,
                'last_run': None,
                'capabilities': agent.capabilities,
                'description': agent.description
            }
            
            # Store in memory
            self.models[model_id] = {
                'agent': agent,
                'entry': model_entry
            }
            
            # Update Redis status
            self._update_model_status(model_id, model_entry)
            
            # Update service status
            if self.status_manager:
                self.status_manager.update_status('connected')
            
            self.logger.info(f"Successfully registered model: {model_id} with name: {agent_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register model {model_id}: {e}")
            return False

    def unregister_model(self, model_id: str) -> bool:
        """Unregister a model from the manager."""
        try:
            if model_id not in self.models:
                self.logger.warning(f"Model {model_id} not registered")
                return False

            # Get model entry
            model_entry = self.models[model_id]['entry']
            model_entry['status'] = 'inactive'
            model_entry['is_running'] = False
            model_entry['last_run'] = datetime.now().isoformat()
            
            # Update Redis
            self._update_model_status(model_id, model_entry)
            
            # Remove from memory
            del self.models[model_id]
            
            self.logger.info(f"Successfully unregistered model: {model_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unregister model {model_id}: {e}")
            return False

    def start(self):
        """Start the model manager."""
        try:
            self.logger.info("Starting ModelManager...")
            
            # Start status updates
            if self.status_manager:
                self.status_manager.start_status_updates(self.health_check, interval=10)
            
            self.logger.info("ModelManager started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start ModelManager: {e}")
            raise

    def stop(self):
        """Stop the model manager."""
        try:
            self.logger.info("Stopping ModelManager...")
            
            # Stop status updates
            if self.status_manager:
                self.status_manager.stop_status_updates()
            
            # Unregister all models
            for model_id in list(self.models.keys()):
                self.unregister_model(model_id)
            
            self.logger.info("ModelManager stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to stop ModelManager: {e}")
            raise

    def health_check(self) -> bool:
        """Check if the model manager is healthy."""
        try:
            # Check Redis connection
            if not self.redis_client:
                self.logger.warning("Redis client not available")
                return False
                
            try:
                self.redis_client.ping()
            except Exception as e:
                self.logger.error(f"Redis connection failed: {e}")
                return False
                
            # Check model status
            for model_id, model_data in self.models.items():
                if model_data['entry']['status'] == 'error':
                    self.logger.warning(f"Model {model_id} is in error state")
                    return False
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

    def is_running(self) -> bool:
        """Check if the model manager is running."""
        return self.health_check()

    def get_all_models(self) -> Dict[str, Any]:
        """Get all registered models with their current status."""
        models = []
        
        for model_id, model_info in self.model_registry.items():
            # Default to the registry status instead of 'inactive'
            status = model_info.get('status', 'active')
            self.logger.info(f"Initial status from registry for {model_id}: {status}")
            
            # Get current status from Redis
            if self.redis_client:
                try:
                    key = f"mcp:model:{model_id}:status"
                    self.logger.debug(f"Getting status from Redis with key: {key}")
                    status_data = self.redis_client.get(key)
                    if status_data:
                        try:
                            agent_status = json.loads(status_data)
                            self.logger.debug(f"Retrieved status from Redis: {agent_status}")
                            # Use the status directly from Redis since it's already mapped
                            status = agent_status.get('status', status)
                            self.logger.debug(f"Using status from Redis: {status}")
                        except json.JSONDecodeError:
                            self.logger.error(f"Failed to parse JSON from Redis for {model_id}")
                            # Keep the registry status if Redis parsing fails
                    else:
                        self.logger.debug(f"No status found in Redis for key: {key}")
                        # Keep the registry status if no Redis data
                except Exception as e:
                    self.logger.error(f"Error getting Redis status for {model_id}: {e}")
                    # Keep the registry status if Redis error
            
            self.logger.info(f"Final status for {model_id} after Redis check: {status}")
            
            # Format model info for API response
            api_model = {
                'id': model_id,
                'name': model_info.get('name', model_id),
                'version': model_info['version'],
                'created_at': model_info['created_at'],
                'metrics': model_info['metrics'],
                'status': status,
                'description': model_info.get('description', ''),
                'capabilities': model_info.get('capabilities', [])
            }
            self.logger.debug(f"Created API model with status: {status}")
            models.append(api_model)
        
        response = {
            'models': models,
            'total': len(models)
        }
        
        # Log the final response data
        self.logger.info(f"Preparing model data for API: {json.dumps(response, indent=2)}")
        return response

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model."""
        try:
            # Check if model exists in registry
            if model_id not in self.model_registry:
                self.logger.warning(f"Model {model_id} not found in registry")
                return None
            
            model_info = self.model_registry[model_id]
            
            # Get current status from Redis
            status = model_info.get('status', 'active')
            if self.redis_client:
                try:
                    key = f"mcp:model:{model_id}:status"
                    status_data = self.redis_client.get(key)
                    if status_data:
                        try:
                            agent_status = json.loads(status_data)
                            # Use the status directly from Redis since it's already mapped
                            status = agent_status.get('status', status)
                        except json.JSONDecodeError:
                            self.logger.error(f"Failed to parse JSON from Redis for {model_id}")
                            # Keep the registry status if Redis parsing fails
                except Exception as e:
                    self.logger.error(f"Error getting Redis status for {model_id}: {e}")
                    # Keep the registry status if Redis error
            
            # Get additional info from memory if available
            memory_info = {}
            if model_id in self.models:
                memory_info = {
                    'is_running': self.models[model_id]['entry'].get('is_running', False),
                    'last_run': self.models[model_id]['entry'].get('last_run'),
                    'agent_class': self.models[model_id]['agent'].__class__.__name__
                }
            
            # Build comprehensive model info
            detailed_info = {
                'id': model_id,
                'name': model_info.get('name', model_id),
                'version': model_info['version'],
                'created_at': model_info['created_at'],
                'status': status,
                'description': model_info.get('description', ''),
                'capabilities': model_info.get('capabilities', []),
                'metrics': model_info['metrics'],
                'configuration': {
                    'type': 'wifi_anomaly_detection',
                    'framework': 'scikit-learn',
                    'input_features': ['authentication_failures', 'deauth_requests', 'beacon_frames'],
                    'output_classes': ['normal', 'anomaly']
                },
                'performance': {
                    'accuracy': model_info['metrics']['accuracy'],
                    'false_positive_rate': model_info['metrics']['false_positive_rate'],
                    'false_negative_rate': model_info['metrics']['false_negative_rate'],
                    'total_predictions': 0,
                    'last_updated': model_info['created_at']
                },
                'runtime_info': memory_info
            }
            
            self.logger.info(f"Retrieved detailed info for model {model_id}")
            return detailed_info
            
        except Exception as e:
            self.logger.error(f"Error getting model info for {model_id}: {e}")
            return None

    def activate_model(self, model_id: str) -> bool:
        """Activate a model."""
        try:
            if model_id not in self.model_registry:
                self.logger.warning(f"Model {model_id} not found in registry")
                return False
            
            # Update registry status
            self.model_registry[model_id]['status'] = 'active'
            
            # Update Redis status
            if model_id in self.models:
                model_entry = self.models[model_id]['entry']
                model_entry['status'] = 'active'
                model_entry['is_running'] = True
                model_entry['last_run'] = datetime.now().isoformat()
                self._update_model_status(model_id, model_entry)
            
            self.logger.info(f"Model {model_id} activated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error activating model {model_id}: {e}")
            return False

    def deactivate_model(self, model_id: str) -> bool:
        """Deactivate a model."""
        try:
            if model_id not in self.model_registry:
                self.logger.warning(f"Model {model_id} not found in registry")
                return False
            
            # Update registry status
            self.model_registry[model_id]['status'] = 'inactive'
            
            # Update Redis status
            if model_id in self.models:
                model_entry = self.models[model_id]['entry']
                model_entry['status'] = 'inactive'
                model_entry['is_running'] = False
                model_entry['last_run'] = datetime.now().isoformat()
                self._update_model_status(model_id, model_entry)
            
            self.logger.info(f"Model {model_id} deactivated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deactivating model {model_id}: {e}")
            return False

# Create the singleton instance
model_manager = ModelManager()