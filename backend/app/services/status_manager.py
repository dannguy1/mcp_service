import redis
import time
import threading
import os
from datetime import datetime
import logging
from dotenv import load_dotenv
from typing import Dict, Any
import json

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ServiceStatusManager:
    def __init__(self, service_name):
        self.service_name = service_name
        # Use the same Redis configuration as mcp-service
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        
        # Initialize Redis client without password
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        
        # Service-specific keys
        self.status_key = f'service:{service_name}:status'
        self.error_key = f'service:{service_name}:error'
        self.last_check_key = f'service:{service_name}:last_check'
        self.health_key = f'service:{service_name}:health'
        self.start_time_key = f'service:{service_name}:start_time'
        self._stop_event = threading.Event()
        self._thread = None
        
        # Test Redis connection on initialization
        self._test_redis_connection()
        # Set initial start time
        self._set_start_time()

    def _set_start_time(self):
        """Set the service start time"""
        try:
            self.redis_client.set(self.start_time_key, datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Failed to set start time for {self.service_name}: {str(e)}")

    def _test_redis_connection(self):
        """Test Redis connection and log the result"""
        try:
            self.redis_client.ping()
            logger.info(f"Successfully connected to Redis for {self.service_name}")
            # Update Redis status
            self._update_redis_status(True)
        except redis.ConnectionError as e:
            logger.error(f"Could not connect to Redis for {self.service_name}: {str(e)}")
            self._update_redis_status(False)
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis for {self.service_name}: {str(e)}")
            self._update_redis_status(False)

    def _update_redis_status(self, is_connected: bool):
        """Update Redis connection status"""
        try:
            status = 'connected' if is_connected else 'error'
            self.redis_client.set(self.status_key, status)
            self.redis_client.set(self.last_check_key, datetime.now().isoformat())
            logger.debug(f"Updated Redis status to {status}")
        except Exception as e:
            logger.error(f"Failed to update Redis status: {str(e)}")

    def update_status(self, status, error=None):
        """Update service status in Redis"""
        try:
            self.redis_client.set(self.status_key, status)
            if error:
                self.redis_client.set(self.error_key, str(error))
            else:
                self.redis_client.delete(self.error_key)
            self.redis_client.set(self.last_check_key, datetime.now().isoformat())
            logger.debug(f"Updated {self.service_name} status to {status}")
        except Exception as e:
            logger.error(f"Failed to update status for {self.service_name}: {str(e)}")

    def start_status_updates(self, health_check_func, interval=30):
        """Start periodic status updates in a background thread"""
        def update_loop():
            while not self._stop_event.is_set():
                try:
                    is_healthy = health_check_func()
                    if is_healthy:
                        self.update_status('connected')
                        self._update_health(True)
                        logger.debug(f"{self.service_name} health check passed")
                    else:
                        self.update_status('error', 'Health check failed')
                        self._update_health(False)
                        logger.warning(f"{self.service_name} health check failed")
                except Exception as e:
                    self.update_status('error', str(e))
                    self._update_health(False)
                    logger.error(f"{self.service_name} health check error: {str(e)}")
                time.sleep(interval)

        self._thread = threading.Thread(target=update_loop, daemon=True)
        self._thread.start()
        logger.info(f"Started status updates for {self.service_name}")

    def _update_health(self, is_healthy):
        """Update service health status"""
        try:
            self.redis_client.set(self.health_key, str(is_healthy).lower())
        except Exception as e:
            logger.error(f"Failed to update health status for {self.service_name}: {str(e)}")

    def stop_status_updates(self):
        """Stop the status update thread"""
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        logger.info(f"Stopped status updates for {self.service_name}")

    def get_current_status(self):
        """Get the current status from Redis"""
        try:
            status = self.redis_client.get(self.status_key)
            error = self.redis_client.get(self.error_key)
            last_check = self.redis_client.get(self.last_check_key)
            health = self.redis_client.get(self.health_key)
            start_time = self.redis_client.get(self.start_time_key)
            
            return {
                'service': self.service_name,
                'status': status or 'disconnected',
                'error': error,
                'last_check': last_check,
                'health': health == 'true' if health else False,
                'start_time': start_time,
                'uptime': self._calculate_uptime(start_time) if start_time else None
            }
        except Exception as e:
            logger.error(f"Failed to get status for {self.service_name}: {str(e)}")
            return {
                'service': self.service_name,
                'status': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat(),
                'health': False,
                'start_time': None,
                'uptime': None
            }

    def _calculate_uptime(self, start_time_str):
        """Calculate service uptime"""
        try:
            start_time = datetime.fromisoformat(start_time_str)
            uptime = datetime.now() - start_time
            return str(uptime)
        except Exception as e:
            logger.error(f"Failed to calculate uptime for {self.service_name}: {str(e)}")
            return None

    @staticmethod
    def get_all_services_status():
        """Get status of all services"""
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', '6379'))
            r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
            service_keys = r.keys('service:*:status')
            services = []
            
            for key in service_keys:
                service_name = key.split(':')[1]
                status_manager = ServiceStatusManager(service_name)
                services.append(status_manager.get_current_status())
            
            return services
        except Exception as e:
            logger.error(f"Failed to get all services status: {str(e)}")
            return []

class StatusManager:
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        """Initialize the status manager with Redis connection."""
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        self._stop_event = threading.Event()
        self._status_thread = None
        self._last_status = {}
        
    def start(self):
        """Start the status monitoring thread."""
        if self._status_thread is None or not self._status_thread.is_alive():
            self._stop_event.clear()
            self._status_thread = threading.Thread(target=self._monitor_status)
            self._status_thread.daemon = True
            self._status_thread.start()
            logger.info("Status monitoring started")
            
    def stop(self):
        """Stop the status monitoring thread."""
        if self._status_thread and self._status_thread.is_alive():
            self._stop_event.set()
            self._status_thread.join()
            logger.info("Status monitoring stopped")
            
    def _monitor_status(self):
        """Monitor and update service status."""
        while not self._stop_event.is_set():
            try:
                # Get current status
                current_status = self._get_current_status()
                
                # Update Redis with current status
                self._update_redis_status(current_status)
                
                # Store last status
                self._last_status = current_status
                
                # Wait for next update
                time.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in status monitoring: {str(e)}")
                time.sleep(5)  # Wait before retrying
                
    def _get_current_status(self) -> Dict[str, Any]:
        """Get the current status of the service."""
        try:
            # Basic service status
            status = {
                'service': 'backend',
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'components': {
                    'redis': self._check_redis_status()
                }
            }
            return status
        except Exception as e:
            logger.error(f"Error getting current status: {str(e)}")
            return {
                'service': 'backend',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
            
    def _check_redis_status(self) -> Dict[str, Any]:
        """Check Redis connection status."""
        try:
            self.redis_client.ping()
            return {
                'status': 'healthy',
                'message': 'Connected to Redis'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Redis connection error: {str(e)}'
            }
            
    def _update_redis_status(self, status: Dict[str, Any]):
        """Update status in Redis."""
        try:
            # Convert status dictionary to JSON string
            status_json = json.dumps(status)
            
            # Store status in Redis
            self.redis_client.set(
                'service:status:backend',
                status_json,
                ex=3600  # 1 hour expiry
            )
            logger.info("Successfully updated Redis status")
        except Exception as e:
            logger.error(f"Error updating Redis status: {str(e)}")
            
    def get_status(self) -> Dict[str, Any]:
        """Get the current service status."""
        return self._last_status 