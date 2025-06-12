from .status_manager import ServiceStatusManager
import logging

logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self):
        self.status_manager = ServiceStatusManager('model_service')
        
    def check_health(self):
        """Check if the model service is healthy"""
        try:
            # Add your model service health checks here
            # For example:
            # - Check if models are loaded
            # - Check if GPU is available
            # - Check if memory usage is within limits
            return True
        except Exception as e:
            logger.error(f"Model service health check failed: {str(e)}")
            return False

    def start(self):
        """Start the model service"""
        try:
            # Initialize your model service here
            # For example:
            # - Load models
            # - Initialize GPU
            # - Set up queues
            
            # Start status updates
            self.status_manager.start_status_updates(self.check_health)
            logger.info("Model service started successfully")
        except Exception as e:
            logger.error(f"Failed to start model service: {str(e)}")
            self.status_manager.update_status('error', str(e))
            raise

    def stop(self):
        """Stop the model service"""
        try:
            # Clean up resources here
            self.status_manager.stop_status_updates()
            logger.info("Model service stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping model service: {str(e)}")
            raise 