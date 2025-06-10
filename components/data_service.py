import logging
import asyncpg
from typing import Dict, List, Optional, Any
from datetime import datetime
import redis.asyncio as redis
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataService:
    """Service for database operations."""
    
    def __init__(self):
        """Initialize the data service."""
        self.pool = None
        self.redis = None
        self.metrics = None  # Will be set by ModelMonitor
        self._initialized = False
    
    def set_metrics(self, metrics):
        """Set metrics from ModelMonitor.
        
        Args:
            metrics: Dictionary of Prometheus metrics from ModelMonitor
        """
        self.metrics = metrics
    
    async def initialize(self) -> None:
        """Initialize the data service asynchronously."""
        try:
            await self.connect()
            self._initialized = True
            logger.info("Data service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing data service: {e}")
            raise
    
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized
    
    async def connect(self):
        """Connect to database and Redis."""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                dsn=config.DATABASE_URL,
                min_size=5,
                max_size=20
            )
        
        if self.redis is None:
            self.redis = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=0,
                decode_responses=True
            )
    
    async def disconnect(self):
        """Disconnect from database and Redis."""
        if self.pool:
            await self.pool.close()
            self.pool = None
        
        if self.redis:
            await self.redis.close()
            self.redis = None
    
    async def fetch_all(self, query: str, *args) -> List[Dict]:
        """Execute a query and return all results.
        
        Args:
            query: SQL query
            *args: Query parameters
            
        Returns:
            List of dictionaries containing results
        """
        await self.connect()
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict]:
        """Execute a query and return one result.
        
        Args:
            query: SQL query
            *args: Query parameters
            
        Returns:
            Dictionary containing result or None
        """
        await self.connect()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def execute(self, query: str, *args) -> None:
        """Execute a query without returning results.
        
        Args:
            query: SQL query
            *args: Query parameters
        """
        await self.connect()
        
        async with self.pool.acquire() as conn:
            await conn.execute(query, *args)
    
    async def get_cached(self, key: str) -> Optional[str]:
        """Get value from Redis cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        await self.connect()
        return await self.redis.get(key)
    
    async def set_cached(self, key: str, value: str, expire: int = 3600) -> None:
        """Set value in Redis cache.
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds
        """
        await self.connect()
        await self.redis.set(key, value, ex=expire)
    
    async def delete_cached(self, key: str) -> None:
        """Delete value from Redis cache.
        
        Args:
            key: Cache key
        """
        await self.connect()
        await self.redis.delete(key) 