import asyncpg
import aiosqlite
import redis.asyncio as redis
import logging
import json
from tenacity import retry, wait_fixed, stop_after_attempt
from datetime import datetime

class DataService:
    def __init__(self, config):
        self.db_config = config.db
        self.redis_config = config.redis
        self.sqlite_config = config.sqlite
        self.log_columns = config.log_columns
        self.pool = None
        self.redis = None
        self.sqlite_conn = None
        self.logger = logging.getLogger("DataService")

    async def start(self):
        try:
            # Start PostgreSQL pool
            self.pool = await asyncpg.create_pool(**self.db_config)
            
            # Start SQLite connection
            self.sqlite_conn = await aiosqlite.connect(self.sqlite_config.db_path)
            
            # Configure SQLite
            await self.sqlite_conn.execute('PRAGMA journal_mode=WAL')
            await self.sqlite_conn.execute(f'PRAGMA synchronous={self.sqlite_config.synchronous}')
            await self.sqlite_conn.execute(f'PRAGMA cache_size={self.sqlite_config.cache_size}')
            await self.sqlite_conn.execute(f'PRAGMA temp_store={self.sqlite_config.temp_store}')
            await self.sqlite_conn.execute(f'PRAGMA mmap_size={self.sqlite_config.mmap_size}')
            
            # Start Redis
            self.redis = redis.Redis(**self.redis_config)
            self.logger.info("Initialized PostgreSQL, SQLite, and Redis connections")
        except Exception as e:
            self.logger.error(f"Failed to start DataService: {e}")
            raise

    async def stop(self):
        try:
            if self.pool:
                await self.pool.close()
            if self.sqlite_conn:
                await self.sqlite_conn.close()
            if self.redis:
                await self.redis.close()
            self.logger.info("Closed all database and Redis connections")
        except Exception as e:
            self.logger.error(f"Failed to stop DataService cleanly: {e}")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
    async def get_logs_by_program(self, start_time, end_time, programs, device_id=None):
        cache_key = f"get_logs_by_program:{start_time}:{end_time}:{programs}:{device_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            self.logger.info(f"Cache hit for {cache_key}")
            return json.loads(cached)

        async with self.pool.acquire() as conn:
            columns = ', '.join(self.log_columns.values())
            query = f"""
                SELECT {columns}
                FROM log_entries
                WHERE timestamp >= $1 AND timestamp <= $2
                AND program = ANY($3::text[])
            """
            params = [start_time, end_time, programs]
            if device_id and 'device_id' in self.log_columns:
                query += " AND device_id = $4"
                params.append(device_id)
            logs = await conn.fetch(query, *params)
            logs = [dict(record) for record in logs]
            await self.redis.setex(cache_key, 300, json.dumps(logs))
            self.logger.info(f"Retrieved {len(logs)} logs")
            return logs

    async def store_anomaly(self, anomaly):
        """Store a single anomaly in the local SQLite database."""
        try:
            await self.sqlite_conn.execute(
                """
                INSERT INTO mcp_anomalies (
                    agent_name, device_id, timestamp, anomaly_type,
                    severity, confidence, description, features
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    anomaly.get("agent_name"),
                    anomaly.get("device_id"),
                    anomaly.get("timestamp"),
                    anomaly.get("anomaly_type"),
                    anomaly.get("severity", 1),
                    anomaly.get("confidence"),
                    anomaly.get("description"),
                    json.dumps(anomaly.get("features", {}))
                )
            )
            await self.sqlite_conn.commit()
            self.logger.info(f"Stored anomaly for agent {anomaly.get('agent_name')}")
        except Exception as e:
            self.logger.error(f"Failed to store anomaly to SQLite: {e}")
            raise

    async def get_anomalies(self, limit=100, offset=0, agent_name=None, status=None, resolution_status=None):
        """Retrieve anomalies from the local SQLite database with filtering."""
        try:
            query = "SELECT * FROM mcp_anomalies"
            params = []
            conditions = []
            
            if agent_name:
                conditions.append("agent_name = ?")
                params.append(agent_name)
            
            if status:
                conditions.append("status = ?")
                params.append(status)
                
            if resolution_status:
                conditions.append("resolution_status = ?")
                params.append(resolution_status)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = await self.sqlite_conn.execute(query, tuple(params))
            rows = await cursor.fetchall()
            
            # Convert rows to dictionaries
            columns = [desc[0] for desc in cursor.description]
            anomalies = [dict(zip(columns, row)) for row in rows]

            # Parse features string back to dict
            for anomaly in anomalies:
                if anomaly.get('features'):
                    anomaly['features'] = json.loads(anomaly['features'])

            return anomalies
        except Exception as e:
            self.logger.error(f"Failed to retrieve anomalies from SQLite: {e}")
            return []

    async def update_anomaly_status(self, anomaly_id, status, resolution_status=None, resolution_notes=None):
        """Update the status and resolution of an anomaly."""
        try:
            query = """
                UPDATE mcp_anomalies 
                SET status = ?, updated_at = ?
            """
            params = [status, datetime.now().isoformat()]
            
            if resolution_status:
                query += ", resolution_status = ?"
                params.append(resolution_status)
                
            if resolution_notes:
                query += ", resolution_notes = ?"
                params.append(resolution_notes)
                
            query += " WHERE id = ?"
            params.append(anomaly_id)
            
            await self.sqlite_conn.execute(query, tuple(params))
            await self.sqlite_conn.commit()
            self.logger.info(f"Updated anomaly {anomaly_id} status to {status}")
        except Exception as e:
            self.logger.error(f"Failed to update anomaly status: {e}")
            raise

    async def health(self):
        """Check the health of all database connections."""
        try:
            # Check PostgreSQL
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            
            # Check SQLite
            await self.sqlite_conn.execute("SELECT 1")
            
            # Check Redis
            await self.redis.ping()
            
            return {
                "status": "healthy",
                "postgresql": "connected",
                "sqlite": "connected",
                "redis": "connected"
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            } 