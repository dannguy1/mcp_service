import redis
import time
import threading
import os
from datetime import datetime
import logging
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class MCPStatusManager:
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        self.service_name = 'mcp_service'
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
        self._stop_event = threading.Event()
        self._status_thread = None
        self._last_status = {}
        
        # Redis configuration
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = os.getenv('REDIS_PORT', '6379')
        redis_password = os.getenv('REDIS_PASSWORD', 'default_redis_password')
        self.redis_url = f'redis://:{redis_password}@{redis_host}:{redis_port}/0'
        
        # Service-specific keys
        self.status_key = f'mcp:{self.service_name}:status'
        self.error_key = f'mcp:{self.service_name}:error'
        self.last_check_key = f'mcp:{self.service_name}:last_check'
        self.health_key = f'mcp:{self.service_name}:health'
        self.start_time_key = f'mcp_service:{self.service_name}:start_time'
        
        # Data source keys
        self.data_source_status_key = 'mcp:data_source:status'
        self.data_source_error_key = 'mcp:data_source:error'
        self.data_source_last_check_key = 'mcp:data_source:last_check'
        self.data_source_health_key = 'mcp:data_source:health'
        
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
        except Exception as e:
            logger.error(f"Failed to connect to Redis for {self.service_name}: {str(e)}")

    def _check_data_source(self):
        """Check data source connection"""
        try:
            # Check if data source service is running
            data_source_status = self.redis_client.get(self.data_source_status_key)
            if data_source_status == 'connected':
                return True
            return False
        except Exception as e:
            logger.error(f"Data source health check failed: {str(e)}")
            return False

    def _update_data_source_status(self, is_connected, error=None):
        """Update data source connection status"""
        try:
            status = 'connected' if is_connected else 'error'
            self.redis_client.set(self.data_source_status_key, status)
            self.redis_client.set(self.data_source_last_check_key, datetime.now().isoformat())
            self.redis_client.set(self.data_source_health_key, str(is_connected).lower())
            if error:
                self.redis_client.set(self.data_source_error_key, str(error))
            else:
                self.redis_client.delete(self.data_source_error_key)
            logger.debug(f"Updated data source status to {status}")
        except Exception as e:
            logger.error(f"Failed to update data source status: {str(e)}")

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

    def start_status_updates(self):
        """Start periodic status updates in a background thread"""
        if self._status_thread is None or not self._status_thread.is_alive():
            self._stop_event.clear()
            self._status_thread = threading.Thread(target=self._monitor_status)
            self._status_thread.daemon = True
            self._status_thread.start()
            logger.info("Status monitoring started")

    def stop_status_updates(self):
        """Stop the status update thread"""
        if self._status_thread and self._status_thread.is_alive():
            self._stop_event.set()
            self._status_thread.join()
            logger.info("Status monitoring stopped")

    def _monitor_status(self):
        """Monitor and update service status."""
        while not self._stop_event.is_set():
            try:
                # Check data source status
                data_source_connected = self._check_data_source()
                self._update_data_source_status(data_source_connected)
                
                # Get current status
                current_status = self._get_current_status()
                
                # Update Redis with current status
                self._update_redis_status(current_status)
                
                # Store last status
                self._last_status = current_status
                
                # Wait for next update
                time.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in status monitoring: {str(e)}")
                time.sleep(5)  # Wait before retrying
                
    def _get_current_status(self) -> Dict[str, Any]:
        """Get the current status of the service."""
        try:
            # Check data source status
            data_source_connected = self._check_data_source()
            
            # Basic service status
            status = {
                'service': self.service_name,
                'status': 'healthy' if data_source_connected else 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'components': {
                    'redis': self._check_redis_status(),
                    'data_source': {
                        'status': 'healthy' if data_source_connected else 'error',
                        'message': 'Data source is available' if data_source_connected else 'Data source is not available'
                    }
                }
            }
            return status
        except Exception as e:
            logger.error(f"Error getting current status: {str(e)}")
            return {
                'service': self.service_name,
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
            
    def _check_data_source_status(self) -> Dict[str, Any]:
        """Check data source status."""
        try:
            is_connected = self._check_data_source()
            return {
                'status': 'healthy' if is_connected else 'error',
                'message': 'Data source is available' if is_connected else 'Data source is not available'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Data source error: {str(e)}'
            }
            
    def _update_redis_status(self, status: Dict[str, Any]):
        """Update status in Redis."""
        try:
            # Store status in Redis with timestamp
            self.redis_client.hset(
                'mcp_service:status:mcp',
                mapping=status
            )
            # Set expiry for status (1 hour)
            self.redis_client.expire('mcp_service:status:mcp', 3600)
            
            # Update service status
            self.update_status(status['status'])
            
            # Update health status
            self.redis_client.set(self.health_key, str(status['status'] == 'healthy').lower())
        except Exception as e:
            logger.error(f"Error updating Redis status: {str(e)}")
            
    def get_status(self) -> Dict[str, Any]:
        """Get the current service status."""
        return self._last_status

    def get_current_status(self):
        """Get the current status from Redis"""
        try:
            status = self.redis_client.get(self.status_key)
            error = self.redis_client.get(self.error_key)
            last_check = self.redis_client.get(self.last_check_key)
            start_time = self.redis_client.get(self.start_time_key)
            
            return {
                'service': self.service_name,
                'status': status or 'disconnected',
                'error': error,
                'last_check': last_check,
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