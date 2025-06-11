import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.config.config import config
from mcp_service.data_service import DataService
from mcp_service.agents.wifi_agent import WiFiAgent
from mcp_service.components.resource_monitor import ResourceMonitor
from mcp_service.components.model_manager import ModelManager

# Configure logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MCPService:
    def __init__(self):
        self.data_service = DataService(config)
        self.wifi_agent = WiFiAgent(config, self.data_service)
        self.resource_monitor = ResourceMonitor()
        self.model_manager = ModelManager()
        self.running = False

    async def start(self):
        """Start the MCP service."""
        try:
            logger.info("Starting MCP service...")
            
            # Initialize components
            await self.data_service.start()
            await self.wifi_agent.start()
            await self.model_manager.start()
            
            self.running = True
            logger.info("MCP service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start MCP service: {e}")
            await self.stop()
            raise

    async def stop(self):
        """Stop the MCP service."""
        try:
            logger.info("Stopping MCP service...")
            self.running = False
            
            # Stop components
            await self.wifi_agent.stop()
            await self.data_service.stop()
            await self.model_manager.stop()
            
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