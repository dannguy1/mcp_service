import asyncio
import logging
from typing import Any, Dict, List, Optional
from functools import wraps

import asyncpg
import redis.asyncio as redis
from prometheus_client import Counter, Gauge, Histogram
from tenacity import retry, stop_after_attempt, wait_exponential
from pybreaker import CircuitBreaker

from config import settings

# Setup logging
logger = logging.getLogger(__name__)

# Prometheus metrics
DB_CONNECTION_GAUGE = Gauge('db_connections', 'Number of active database connections')
DB_QUERY_DURATION = Histogram('db_query_duration_seconds', 'Database query duration in seconds')
CACHE_HITS = Counter('cache_hits_total', 'Number of cache hits')
CACHE_MISSES = Counter('cache_misses_total', 'Number of cache misses')

DB_OPERATION_DURATION = Histogram(
    'db_operation_duration_seconds',
    'Time spent performing database operations',
    ['operation']
)

DB_OPERATION_COUNT = Counter(
    'db_operation_count_total',
    'Total number of database operations',
    ['operation', 'status']
)

REDIS_OPERATION_DURATION = Histogram(
    'redis_operation_duration_seconds',
    'Time spent performing Redis operations',
    ['operation']
)

REDIS_OPERATION_COUNT = Counter(
    'redis_operation_count_total',
    'Total number of Redis operations',
    ['operation', 'status']
)

# Circuit breaker settings
DB_CIRCUIT_BREAKER = CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    exclude=[asyncpg.InvalidCatalogNameError]
)

class DataService:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.redis: Optional[redis.Redis] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize database and cache connections."""
        if self._initialized:
            return

        try:
            # Initialize PostgreSQL connection pool
            self.pool = await asyncpg.create_pool(
                dsn=str(settings.postgres_dsn),
                min_size=settings.POSTGRES_POOL_MIN,
                max_size=settings.POSTGRES_POOL_MAX,
            )
            DB_CONNECTION_GAUGE.set(settings.POSTGRES_POOL_MIN)

            # Initialize Redis connection
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
            )

            self._initialized = True
            logger.info("DataService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize DataService: {e}")
            raise

    async def close(self) -> None:
        """Close all database and cache connections."""
        if self.pool:
            await self.pool.close()
        if self.redis:
            await self.redis.close()
        self._initialized = False
        logger.info("DataService connections closed")

    def _with_retry(func):
        """Decorator for adding retry logic to database operations."""
        @wraps(func)
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=10),
            reraise=True
        )
        async def wrapper(self, *args, **kwargs):
            return await func(self, *args, **kwargs)
        return wrapper

    @DB_CIRCUIT_BREAKER
    @_with_retry
    async def execute(self, query: str, *args: Any) -> None:
        """Execute a database query with retry logic and circuit breaker."""
        if not self._initialized:
            raise RuntimeError("DataService not initialized")

        start_time = asyncio.get_event_loop().time()
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(query, *args)
            
            duration = asyncio.get_event_loop().time() - start_time
            DB_OPERATION_DURATION.labels(operation='execute').observe(duration)
            DB_OPERATION_COUNT.labels(operation='execute', status='success').inc()
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            DB_OPERATION_DURATION.labels(operation='execute').observe(duration)
            DB_OPERATION_COUNT.labels(operation='execute', status='error').inc()
            logger.error(f"Error executing query: {str(e)}")
            raise

    @DB_CIRCUIT_BREAKER
    @_with_retry
    async def fetch_one(self, query: str, *args: Any) -> Optional[Dict[str, Any]]:
        """Fetch a single record from the database."""
        if not self._initialized:
            raise RuntimeError("DataService not initialized")

        start_time = asyncio.get_event_loop().time()
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *args)
            
            duration = asyncio.get_event_loop().time() - start_time
            DB_OPERATION_DURATION.labels(operation='fetch_one').observe(duration)
            DB_OPERATION_COUNT.labels(operation='fetch_one', status='success').inc()
            
            return dict(row) if row else None
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            DB_OPERATION_DURATION.labels(operation='fetch_one').observe(duration)
            DB_OPERATION_COUNT.labels(operation='fetch_one', status='error').inc()
            logger.error(f"Error fetching row: {str(e)}")
            raise

    @DB_CIRCUIT_BREAKER
    @_with_retry
    async def fetch_all(self, query: str, *args: Any) -> List[Dict[str, Any]]:
        """Fetch all records from the database."""
        if not self._initialized:
            raise RuntimeError("DataService not initialized")

        start_time = asyncio.get_event_loop().time()
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *args)
            
            duration = asyncio.get_event_loop().time() - start_time
            DB_OPERATION_DURATION.labels(operation='fetch_all').observe(duration)
            DB_OPERATION_COUNT.labels(operation='fetch_all', status='success').inc()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            DB_OPERATION_DURATION.labels(operation='fetch_all').observe(duration)
            DB_OPERATION_COUNT.labels(operation='fetch_all', status='error').inc()
            logger.error(f"Error fetching rows: {str(e)}")
            raise

    async def get_cached(self, key: str) -> Optional[str]:
        """Get a value from cache with metrics tracking."""
        if not self._initialized:
            raise RuntimeError("DataService not initialized")

        start_time = asyncio.get_event_loop().time()
        try:
            value = await self.redis.get(key)
            
            duration = asyncio.get_event_loop().time() - start_time
            REDIS_OPERATION_DURATION.labels(operation='get').observe(duration)
            REDIS_OPERATION_COUNT.labels(operation='get', status='success').inc()
            
            return value
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            REDIS_OPERATION_DURATION.labels(operation='get').observe(duration)
            REDIS_OPERATION_COUNT.labels(operation='get', status='error').inc()
            logger.error(f"Error getting cache: {str(e)}")
            raise

    async def set_cached(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL."""
        if not self._initialized:
            raise RuntimeError("DataService not initialized")

        await self.redis.set(key, value, ex=ttl or settings.REDIS_TTL)

# Create global instance
data_service = DataService()
