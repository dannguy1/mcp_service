import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os
import redis

from config.config import config
from app.mcp_service.data_service import DataService
from app.mcp_service.agents.wifi_agent import WiFiAgent
from app.mcp_service.components.resource_monitor import ResourceMonitor
from app.mcp_service.components.model_manager import ModelManager
from app.services.status_manager import ServiceStatusManager

# Configure logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global ModelManager instance
model_manager = ModelManager()

class MCPService:
    def __init__(self):
        self.config = config
        self.data_service = DataService(self.config)
        self.resource_monitor = ResourceMonitor()
        
        # Initialize Redis client
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        
        # Initialize components with Redis client
        model_manager.set_redis_client(self.redis_client)
        
        # Initialize status manager with Redis client
        self.status_manager = ServiceStatusManager('mcp_service', self.redis_client)
        self.running = False
        self.wifi_agent = None  # Initialize to None, will be created in start()

    def health_check(self) -> bool:
        """Check if the service is healthy."""
        try:
            # Check if service is running
            if not self.running:
                logger.warning("Service is not running")
                return False

            # Check resource usage
            if not self.resource_monitor.check_resources():
                logger.warning("Resource usage too high")
                return False

            # Check Redis connection
            try:
                self.status_manager.redis_client.ping()
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                return False

            logger.debug("Health check passed")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def start(self):
        """Start the MCP service."""
        try:
            logger.info("Starting MCP service...")
            
            # Initialize components
            await self.data_service.start()
            
            # Ensure Redis client is set in ModelManager
            if not model_manager.redis_client:
                model_manager.set_redis_client(self.redis_client)
            
            # Start ModelManager first
            model_manager.start()
            
            # Create and start WiFi agent
            self.wifi_agent = WiFiAgent(self.config, self.data_service, model_manager)
            await self.wifi_agent.start()
            
            # Start status updates with more frequent checks
            self.running = True
            self.status_manager.update_status("connected")
            self.status_manager.start_status_updates(self.health_check, interval=10)
            
            logger.info("MCP service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start MCP service: {e}")
            self.status_manager.update_status('error', str(e))
            await self.stop()
            raise

    async def stop(self):
        """Stop the MCP service."""
        try:
            logger.info("Stopping MCP service...")
            self.running = False
            
            # Update status before stopping
            self.status_manager.update_status('disconnected')
            
            # Stop components
            if self.wifi_agent:
                await self.wifi_agent.stop()
            await self.data_service.stop()
            model_manager.stop()
            self.status_manager.stop_status_updates()
            
            logger.info("MCP service stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping MCP service: {e}")
            raise

    async def run(self):
        """Main service loop."""
        try:
            while self.running:
                # Check resource usage
                if not self.resource_monitor.check_resources():
                    logger.warning("Resource usage too high, skipping analysis cycle")
                    await asyncio.sleep(60)  # Wait a minute before retrying
                    continue
                
                # Run analysis cycle
                if self.wifi_agent:
                    await self.wifi_agent.run_analysis_cycle()
                
                # Wait for next cycle
                await asyncio.sleep(config.ANALYSIS_INTERVAL)
                
        except Exception as e:
            logger.error(f"Error in main service loop: {e}")
            await self.stop()
            raise

async def main():
    """Main entry point."""
    service = MCPService()
    try:
        await service.start()
        await service.run()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await service.stop()

if __name__ == "__main__":
    asyncio.run(main()) 