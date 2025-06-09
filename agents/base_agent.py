import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from prometheus_client import Counter, Gauge, Histogram

from config import settings
from data_service import data_service

# Setup logging
logger = logging.getLogger(__name__)

# Prometheus metrics
AGENT_PROCESSING_TIME = Histogram(
    'agent_processing_seconds',
    'Time spent processing data',
    ['agent_type']
)
AGENT_ERRORS = Counter(
    'agent_errors_total',
    'Number of errors encountered',
    ['agent_type', 'error_type']
)
AGENT_PROCESSED_ITEMS = Counter(
    'agent_processed_items_total',
    'Number of items processed',
    ['agent_type']
)
AGENT_ACTIVE = Gauge(
    'agent_active',
    'Whether the agent is currently active',
    ['agent_type']
)

class BaseAgent(ABC):
    """Base class for all analysis agents."""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self._running = False
        self._last_run: Optional[datetime] = None
        self._processing_interval = 300  # 5 minutes default
        
    @property
    def is_running(self) -> bool:
        """Check if the agent is currently running."""
        return self._running
    
    @property
    def last_run(self) -> Optional[datetime]:
        """Get the timestamp of the last successful run."""
        return self._last_run
    
    async def start(self) -> None:
        """Start the agent's processing loop."""
        if self._running:
            logger.warning(f"{self.agent_type} agent is already running")
            return
            
        self._running = True
        AGENT_ACTIVE.labels(self.agent_type).set(1)
        logger.info(f"Starting {self.agent_type} agent")
        
        try:
            while self._running:
                try:
                    await self._process()
                    self._last_run = datetime.utcnow()
                except Exception as e:
                    AGENT_ERRORS.labels(self.agent_type, type(e).__name__).inc()
                    logger.error(f"Error in {self.agent_type} agent: {e}")
                
                await asyncio.sleep(self._processing_interval)
        finally:
            self._running = False
            AGENT_ACTIVE.labels(self.agent_type).set(0)
            logger.info(f"Stopped {self.agent_type} agent")
    
    async def stop(self) -> None:
        """Stop the agent's processing loop."""
        self._running = False
        logger.info(f"Stopping {self.agent_type} agent")
    
    @abstractmethod
    async def _process(self) -> None:
        """Process data. Must be implemented by subclasses."""
        pass
    
    async def _fetch_data(self, query: str, *args: Any) -> List[Dict[str, Any]]:
        """Fetch data from the database with error handling."""
        try:
            return await data_service.fetch_all(query, *args)
        except Exception as e:
            AGENT_ERRORS.labels(self.agent_type, "database_error").inc()
            logger.error(f"Database error in {self.agent_type} agent: {e}")
            raise
    
    async def _save_anomaly(
        self,
        device_id: str,
        anomaly_type: str,
        severity: int,
        confidence: float,
        description: str
    ) -> None:
        """Save an anomaly detection result."""
        try:
            query = """
                INSERT INTO anomalies (
                    timestamp, device_id, anomaly_type,
                    severity, confidence, description
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """
            await data_service.execute_query(
                query,
                datetime.utcnow(),
                device_id,
                anomaly_type,
                severity,
                confidence,
                description
            )
        except Exception as e:
            AGENT_ERRORS.labels(self.agent_type, "save_error").inc()
            logger.error(f"Error saving anomaly in {self.agent_type} agent: {e}")
            raise
    
    def _get_cache_key(self, prefix: str, *args: Any) -> str:
        """Generate a cache key for the agent."""
        return f"{self.agent_type}:{prefix}:{':'.join(str(arg) for arg in args)}"
    
    async def _get_cached(self, key: str) -> Optional[str]:
        """Get a value from cache with error handling."""
        try:
            return await data_service.get_cached(key)
        except Exception as e:
            AGENT_ERRORS.labels(self.agent_type, "cache_error").inc()
            logger.error(f"Cache error in {self.agent_type} agent: {e}")
            return None
    
    async def _set_cached(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Set a value in cache with error handling."""
        try:
            await data_service.set_cached(key, value, ttl)
        except Exception as e:
            AGENT_ERRORS.labels(self.agent_type, "cache_error").inc()
            logger.error(f"Cache error in {self.agent_type} agent: {e}")
