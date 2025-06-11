import asyncio
import logging
from typing import Any, Dict, List, Optional
from functools import wraps
import pickle
import json
from datetime import datetime, timedelta
import os

import asyncpg
import aiosqlite
import redis
from prometheus_client import Counter, Gauge, Histogram
from tenacity import retry, stop_after_attempt, wait_exponential
from pybreaker import CircuitBreaker
import aioredis

from config import settings, Config

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
    def __init__(self, config: Config):
        self.config = config
        self.pool = None
        self.sqlite_conn = None
        self.redis = None
        
        # Prometheus metrics
        self.query_duration = Histogram(
            'query_duration_seconds',
            'Time spent executing queries',
            ['operation', 'database']
        )
        self.cache_hits = Counter(
            'cache_hits_total',
            'Number of cache hits',
            ['operation']
        )
        self.cache_misses = Counter(
            'cache_misses_total',
            'Number of cache misses',
            ['operation']
        )
        self.log_processing_rate = Counter(
            'log_processing_total',
            'Number of logs processed',
            ['status']
        )
        self.anomaly_detection_rate = Counter(
            'anomaly_detection_total',
            'Number of anomalies detected',
            ['type', 'severity']
        )
        self.sqlite_size = Gauge(
            'sqlite_database_size_bytes',
            'Size of SQLite database in bytes'
        )

    async def start(self):
        """Initialize database and cache connections."""
        try:
            # Initialize PostgreSQL connection pool (read-only)
            self.pool = await asyncpg.create_pool(
                host=self.config.db.host,
                port=self.config.db.port,
                user=self.config.db.user,
                password=self.config.db.password,
                database=self.config.db.database,
                min_size=self.config.db.min_connections,
                max_size=self.config.db.max_connections,
                command_timeout=self.config.db.pool_timeout
            )
            DB_CONNECTION_GAUGE.set(settings.POSTGRES_POOL_MIN)
            
            # Initialize SQLite connection
            self.sqlite_conn = await aiosqlite.connect(self.config.sqlite_db_path)
            await self.sqlite_conn.execute('PRAGMA journal_mode=WAL')  # Enable WAL mode
            await self.sqlite_conn.execute('PRAGMA synchronous=NORMAL')  # Optimize for performance
            
            # Initialize Redis connection
            self.redis = redis.Redis(
                host=self.config.redis.host,
                port=self.config.redis.port,
                db=self.config.redis.db,
                max_connections=self.config.redis.max_connections,
                socket_timeout=self.config.redis.socket_timeout
            )
            
            logging.info("DataService started successfully")
            
        except Exception as e:
            logging.error(f"Failed to start DataService: {str(e)}")
            raise

    async def stop(self):
        """Close database and cache connections."""
        if self.pool:
            await self.pool.close()
        if self.sqlite_conn:
            await self.sqlite_conn.close()
        if self.redis:
            self.redis.close()
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
        if not self.pool:
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
        if not self.pool:
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
        if not self.pool:
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

    async def get_cached(self, key: str) -> Optional[Any]:
        """Get a value from cache with metrics tracking."""
        if not self.redis:
            raise RuntimeError("DataService not initialized")

        start_time = asyncio.get_event_loop().time()
        try:
            data = await self.redis.get(key)
            
            duration = asyncio.get_event_loop().time() - start_time
            REDIS_OPERATION_DURATION.labels(operation='get').observe(duration)
            REDIS_OPERATION_COUNT.labels(operation='get', status='success').inc()
            
            return pickle.loads(data) if data else None
            
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            REDIS_OPERATION_DURATION.labels(operation='get').observe(duration)
            REDIS_OPERATION_COUNT.labels(operation='get', status='error').inc()
            logger.error(f"Error getting cache: {str(e)}")
            raise

    async def set_cached(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL."""
        if not self.redis:
            raise RuntimeError("DataService not initialized")

        try:
            data = pickle.dumps(value)
            if ttl:
                await self.redis.setex(key, ttl, data)
            else:
                await self.redis.set(key, data)
        except Exception as e:
            logger.error(f"Error setting cached value: {e}")
            raise

    async def get_logs(self, start_time: datetime, end_time: datetime, 
                      device_id: Optional[int] = None, 
                      severity: Optional[int] = None,
                      batch_size: Optional[int] = None) -> list:
        """Retrieve logs from PostgreSQL database with caching."""
        cache_key = f"logs:{start_time}:{end_time}:{device_id}:{severity}"
        
        # Try cache first
        cached_data = self.redis.get(cache_key)
        if cached_data:
            self.cache_hits.labels('get_logs').inc()
            return json.loads(cached_data)
        
        self.cache_misses.labels('get_logs').inc()
        
        # Query PostgreSQL database
        with self.query_duration.labels('get_logs', 'postgresql').time():
            async with self.pool.acquire() as conn:
                query = """
                    SELECT * FROM log_entries 
                    WHERE timestamp BETWEEN $1 AND $2
                """
                params = [start_time, end_time]
                
                if device_id is not None:
                    query += " AND device_id = $" + str(len(params) + 1)
                    params.append(device_id)
                
                if severity is not None:
                    query += " AND severity <= $" + str(len(params) + 1)
                    params.append(severity)
                
                query += " ORDER BY timestamp DESC"
                
                if batch_size:
                    query += " LIMIT $" + str(len(params) + 1)
                    params.append(batch_size)
                
                rows = await conn.fetch(query, *params)
        
        # Cache results
        self.redis.setex(
            cache_key,
            300,  # 5 minutes
            json.dumps([dict(row) for row in rows])
        )
        
        self.log_processing_rate.labels('success').inc(len(rows))
        return [dict(row) for row in rows]
    
    async def store_anomaly(self, anomaly_data: dict) -> int:
        """Store anomaly detection result in SQLite database."""
        with self.query_duration.labels('store_anomaly', 'sqlite').time():
            async with self.sqlite_conn.execute('''
                INSERT INTO mcp_anomalies 
                (agent_name, device_id, timestamp, anomaly_type,
                 severity, confidence, description, features, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                anomaly_data['agent_name'],
                anomaly_data.get('device_id'),
                anomaly_data.get('timestamp', datetime.utcnow().isoformat()),
                anomaly_data['anomaly_type'],
                anomaly_data['severity'],
                anomaly_data['confidence'],
                anomaly_data['description'],
                json.dumps(anomaly_data.get('features', {})),
                anomaly_data.get('status', 'new')
            )) as cursor:
                await self.sqlite_conn.commit()
                anomaly_id = cursor.lastrowid
                
                self.anomaly_detection_rate.labels(
                    anomaly_data['anomaly_type'],
                    str(anomaly_data['severity'])
                ).inc()
                
                return anomaly_id
    
    async def get_anomalies(self, limit: int = 100, offset: int = 0,
                          agent_name: Optional[str] = None,
                          status: Optional[str] = None) -> list:
        """Retrieve anomalies from SQLite database."""
        with self.query_duration.labels('get_anomalies', 'sqlite').time():
            query = "SELECT * FROM mcp_anomalies"
            params = []
            
            conditions = []
            if agent_name:
                conditions.append("agent_name = ?")
                params.append(agent_name)
            if status:
                conditions.append("status = ?")
                params.append(status)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            async with self.sqlite_conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                anomalies = []
                for row in rows:
                    anomaly = dict(zip(columns, row))
                    if anomaly.get('features'):
                        anomaly['features'] = json.loads(anomaly['features'])
                    anomalies.append(anomaly)
                
                return anomalies
    
    async def update_anomaly_status(self, anomaly_id: int, status: str,
                                  resolution_notes: Optional[str] = None) -> bool:
        """Update anomaly record status in SQLite database."""
        with self.query_duration.labels('update_anomaly', 'sqlite').time():
            query = '''
                UPDATE mcp_anomalies 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
            '''
            params = [status]
            
            if resolution_notes:
                query += ", resolution_notes = ?, resolution_status = 'resolved'"
                params.append(resolution_notes)
            
            query += " WHERE id = ?"
            params.append(anomaly_id)
            
            async with self.sqlite_conn.execute(query, params) as cursor:
                await self.sqlite_conn.commit()
                return cursor.rowcount > 0
    
    async def cleanup_old_anomalies(self, retention_days: int = 30) -> int:
        """Remove anomalies older than retention period."""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        with self.query_duration.labels('cleanup_anomalies', 'sqlite').time():
            async with self.sqlite_conn.execute(
                "DELETE FROM mcp_anomalies WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            ) as cursor:
                await self.sqlite_conn.commit()
                return cursor.rowcount
    
    async def get_database_stats(self) -> dict:
        """Get database statistics."""
        stats = {
            'sqlite_size': os.path.getsize(self.config.sqlite_db_path),
            'anomaly_count': 0,
            'new_anomalies': 0,
            'resolved_anomalies': 0
        }
        
        async with self.sqlite_conn.execute(
            "SELECT COUNT(*) FROM mcp_anomalies"
        ) as cursor:
            stats['anomaly_count'] = (await cursor.fetchone())[0]
        
        async with self.sqlite_conn.execute(
            "SELECT COUNT(*) FROM mcp_anomalies WHERE status = 'new'"
        ) as cursor:
            stats['new_anomalies'] = (await cursor.fetchone())[0]
        
        async with self.sqlite_conn.execute(
            "SELECT COUNT(*) FROM mcp_anomalies WHERE resolution_status = 'resolved'"
        ) as cursor:
            stats['resolved_anomalies'] = (await cursor.fetchone())[0]
        
        self.sqlite_size.set(stats['sqlite_size'])
        return stats

# Create global instance
data_service = DataService(settings)
