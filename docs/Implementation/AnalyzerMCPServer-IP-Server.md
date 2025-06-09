# AnalyzerMCPServer Implementation Plan - Server

## Overview

This document details the implementation of the core server components of the AnalyzerMCPServer, including the DataService, configuration management, and main service entry point.

## 1. Configuration Management

### 1.1 Environment Configuration

Create `.env` file:
```ini
# Database Configuration
DB_HOST=192.168.10.14
DB_PORT=5432
DB_NAME=netmonitor_db
DB_USER=netmonitor_user
DB_PASSWORD=netmonitor_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=5555
LOG_LEVEL=INFO
ANALYSIS_INTERVAL=300  # 5 minutes

# Notification Configuration
NOTIFICATION_ENABLED=true
NOTIFICATION_URL=http://notification-service:8080/notify
NOTIFICATION_TOKEN=your_token

# SFTP Configuration (for model deployment)
SFTP_HOST=model-server
SFTP_PORT=22
SFTP_USER=model-user
SFTP_PASSWORD=your_password
SFTP_REMOTE_PATH=/models/wifi
```

### 1.2 Configuration Management (`config.py`)

```python
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    min_connections: int = 5
    max_connections: int = 20
    pool_timeout: int = 30

@dataclass
class RedisConfig:
    host: str
    port: int
    db: int
    max_connections: int = 10
    socket_timeout: int = 5

@dataclass
class ServiceConfig:
    host: str
    port: int
    log_level: str
    analysis_interval: int
    batch_size: int = 1000
    max_retries: int = 3
    retry_delay: int = 5

@dataclass
class NotificationConfig:
    enabled: bool
    url: str
    token: str
    timeout: int = 10
    max_retries: int = 3

@dataclass
class SFTPConfig:
    host: str
    port: int
    user: str
    password: str
    remote_path: str
    timeout: int = 30

class Config:
    def __init__(self):
        self.db = DatabaseConfig(
            host=os.getenv('DB_HOST', '192.168.10.14'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'netmonitor_db'),
            user=os.getenv('DB_USER', 'netmonitor_user'),
            password=os.getenv('DB_PASSWORD', 'netmonitor_password'),
            min_connections=int(os.getenv('DB_MIN_CONNECTIONS', '5')),
            max_connections=int(os.getenv('DB_MAX_CONNECTIONS', '20')),
            pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', '30'))
        )
        
        self.redis = RedisConfig(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', '10')),
            socket_timeout=int(os.getenv('REDIS_SOCKET_TIMEOUT', '5'))
        )
        
        self.service = ServiceConfig(
            host=os.getenv('SERVICE_HOST', '0.0.0.0'),
            port=int(os.getenv('SERVICE_PORT', '5555')),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            analysis_interval=int(os.getenv('ANALYSIS_INTERVAL', '300')),
            batch_size=int(os.getenv('BATCH_SIZE', '1000')),
            max_retries=int(os.getenv('MAX_RETRIES', '3')),
            retry_delay=int(os.getenv('RETRY_DELAY', '5'))
        )
        
        self.notification = NotificationConfig(
            enabled=os.getenv('NOTIFICATION_ENABLED', 'true').lower() == 'true',
            url=os.getenv('NOTIFICATION_URL', ''),
            token=os.getenv('NOTIFICATION_TOKEN', ''),
            timeout=int(os.getenv('NOTIFICATION_TIMEOUT', '10')),
            max_retries=int(os.getenv('NOTIFICATION_MAX_RETRIES', '3'))
        )
        
        self.sftp = SFTPConfig(
            host=os.getenv('SFTP_HOST', ''),
            port=int(os.getenv('SFTP_PORT', '22')),
            user=os.getenv('SFTP_USER', ''),
            password=os.getenv('SFTP_PASSWORD', ''),
            remote_path=os.getenv('SFTP_REMOTE_PATH', ''),
            timeout=int(os.getenv('SFTP_TIMEOUT', '30'))
        )
```

## 2. Database Interface

### 2.1 Database Schema (`init_db.py`)

```python
import asyncpg
import logging
from config import Config

async def init_db(config: Config) -> None:
    """Initialize database schema.
    
    Note: This service only creates and manages tables it writes to:
    - anomaly_records: Stores detected anomalies
    - anomaly_patterns: Stores active anomaly detection patterns
    
    The log_entries table is managed by the ExternalAIAnalyzer system
    and this service only reads from it.
    """
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=config.db.host,
            port=config.db.port,
            user=config.db.user,
            password=config.db.password,
            database=config.db.database
        )
        
        # Create tables if they don't exist
        await conn.execute('''
            -- Note: log_entries table is managed by ExternalAIAnalyzer
            -- This service only reads from it, no schema modifications needed
            
            -- Table for storing detected anomalies
            CREATE TABLE IF NOT EXISTS anomaly_records (
                id SERIAL PRIMARY KEY,
                log_entry_id INTEGER REFERENCES log_entries(id),
                device_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                anomaly_type VARCHAR(50) NOT NULL,
                severity INTEGER NOT NULL,
                confidence FLOAT NOT NULL,
                description TEXT,
                metadata JSONB,
                status VARCHAR(20) DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices(id)
            );

            -- Indexes for efficient querying of anomaly records
            CREATE INDEX IF NOT EXISTS idx_anomaly_records_device_id ON anomaly_records(device_id);
            CREATE INDEX IF NOT EXISTS idx_anomaly_records_timestamp ON anomaly_records(timestamp);
            CREATE INDEX IF NOT EXISTS idx_anomaly_records_anomaly_type ON anomaly_records(anomaly_type);
            CREATE INDEX IF NOT EXISTS idx_anomaly_records_severity ON anomaly_records(severity);
            CREATE INDEX IF NOT EXISTS idx_anomaly_records_status ON anomaly_records(status);

            -- Table for storing active anomaly detection patterns
            CREATE TABLE IF NOT EXISTS anomaly_patterns (
                id SERIAL PRIMARY KEY,
                pattern_name VARCHAR(100) NOT NULL,
                pattern_type VARCHAR(50) NOT NULL,
                pattern_definition JSONB NOT NULL,
                severity INTEGER NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );

            -- Indexes for efficient querying of anomaly patterns
            CREATE INDEX IF NOT EXISTS idx_anomaly_patterns_pattern_type ON anomaly_patterns(pattern_type);
            CREATE INDEX IF NOT EXISTS idx_anomaly_patterns_is_active ON anomaly_patterns(is_active);
        ''')
        
        await conn.close()
        logging.info("Database initialized successfully")
        
    except Exception as e:
        logging.error(f"Failed to initialize database: {str(e)}")
        raise
```

### 2.2 Data Service (`data_service.py`)

```python
import asyncpg
import redis
import logging
import json
from datetime import datetime, timedelta
from prometheus_client import Counter, Histogram, Gauge
from config import Config

class DataService:
    def __init__(self, config: Config):
        self.config = config
        self.pool = None
        self.redis = None
        
        # Prometheus metrics
        self.query_duration = Histogram(
            'query_duration_seconds',
            'Time spent executing queries',
            ['operation']
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
    
    async def start(self):
        """Initialize database and cache connections."""
        try:
            # Initialize connection pool
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
        if self.redis:
            self.redis.close()
    
    async def get_logs(self, start_time: datetime, end_time: datetime, 
                      device_id: Optional[int] = None, 
                      severity: Optional[int] = None,
                      batch_size: Optional[int] = None) -> list:
        """Retrieve logs from database with caching.
        
        Note: This method only reads from the log_entries table which is
        managed by the ExternalAIAnalyzer system. No modifications to the
        table structure are made.
        """
        cache_key = f"logs:{start_time}:{end_time}:{device_id}:{severity}"
        
        # Try cache first
        cached_data = self.redis.get(cache_key)
        if cached_data:
            self.cache_hits.labels('get_logs').inc()
            return json.loads(cached_data)
        
        self.cache_misses.labels('get_logs').inc()
        
        # Query database
        with self.query_duration.labels('get_logs').time():
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
        """Store anomaly detection result.
        
        Note: This method writes to the anomaly_records table which is
        managed by this service. The table structure is defined in init_db.py.
        """
        with self.query_duration.labels('store_anomaly').time():
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('''
                    INSERT INTO anomaly_records 
                    (log_entry_id, device_id, timestamp, anomaly_type,
                     severity, confidence, description, metadata, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                ''',
                anomaly_data.get('log_entry_id'),
                anomaly_data['device_id'],
                anomaly_data.get('timestamp', datetime.utcnow()),
                anomaly_data['anomaly_type'],
                anomaly_data['severity'],
                anomaly_data['confidence'],
                anomaly_data['description'],
                json.dumps(anomaly_data.get('metadata', {})),
                anomaly_data.get('status', 'new')
                )
                
                self.anomaly_detection_rate.labels(
                    anomaly_data['anomaly_type'],
                    str(anomaly_data['severity'])
                ).inc()
                
                return row['id']
    
    async def update_anomaly_status(self, anomaly_id: int, status: str) -> bool:
        """Update anomaly record status.
        
        Note: This method updates the anomaly_records table which is
        managed by this service. The table structure is defined in init_db.py.
        """
        with self.query_duration.labels('update_anomaly').time():
            async with self.pool.acquire() as conn:
                result = await conn.execute('''
                    UPDATE anomaly_records 
                    SET status = $1, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = $2
                ''', status, anomaly_id)
                return result == 'UPDATE 1'
    
    async def get_anomaly_patterns(self) -> list:
        """Retrieve active anomaly patterns.
        
        Note: This method reads from the anomaly_patterns table which is
        managed by this service. The table structure is defined in init_db.py.
        """
        cache_key = 'anomaly_patterns'
        
        # Try cache first
        cached_data = self.redis.get(cache_key)
        if cached_data:
            self.cache_hits.labels('get_patterns').inc()
            return json.loads(cached_data)
        
        self.cache_misses.labels('get_patterns').inc()
        
        # Query database
        with self.query_duration.labels('get_patterns').time():
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT * FROM anomaly_patterns 
                    WHERE is_active = true
                ''')
        
        # Cache results
        self.redis.setex(
            cache_key,
            300,  # 5 minutes
            json.dumps([dict(row) for row in rows])
        )
        
        return [dict(row) for row in rows]
```

## 3. Main Service Implementation

### 3.1 Main Service (`mcp_service.py`)

```python
import asyncio
import logging
from aiohttp import web
from datetime import datetime
from config import Config
from data_service import DataService
from agents.wifi_agent import WiFiAgent

class MCPService:
    def __init__(self):
        self.config = Config()
        self.data_service = DataService(self.config)
        self.agents = []
        
    async def start(self):
        """Start the MCP service."""
        try:
            # Initialize data service
            await self.data_service.start()
            
            # Initialize agents
            wifi_agent = WiFiAgent(self.data_service, self.config)
            await wifi_agent.start()
            self.agents.append(wifi_agent)
            
            # Start web server
            app = web.Application()
            app['agents'] = self.agents
            app.router.add_get('/health', self.health_check)
            app.router.add_get('/metrics', self.metrics)
            app.router.add_post('/anomalies/{id}/status', self.update_anomaly_status)
            
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(
                runner,
                self.config.service.host,
                self.config.service.port
            )
            await site.start()
            
            logging.info(f"Service started on {self.config.service.host}:{self.config.service.port}")
            
            # Keep service running
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logging.error(f"Service failed to start: {str(e)}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the MCP service."""
        for agent in self.agents:
            await agent.stop()
        await self.data_service.stop()
    
    async def health_check(self, request):
        """Health check endpoint."""
        try:
            # Check system resources
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            # Check service status
            status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'resources': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used': memory.used,
                    'memory_total': memory.total
                },
                'agents': [
                    {
                        'name': agent.name,
                        'status': 'running' if agent.running else 'stopped',
                        'last_analysis': agent.last_analysis.isoformat() if agent.last_analysis else None
                    }
                    for agent in request.app['agents']
                ]
            }
            
            return web.json_response(status)
            
        except Exception as e:
            logging.error(f"Health check failed: {str(e)}")
            return web.json_response(
                {'status': 'unhealthy', 'error': str(e)},
                status=500
            )
    
    async def metrics(self, request):
        """Prometheus metrics endpoint."""
        return web.Response(
            body=generate_latest(),
            content_type='text/plain'
        )
    
    async def update_anomaly_status(self, request):
        """Update anomaly status endpoint."""
        try:
            anomaly_id = int(request.match_info['id'])
            data = await request.json()
            status = data.get('status')
            
            if not status:
                return web.json_response(
                    {'error': 'status is required'},
                    status=400
                )
            
            success = await self.data_service.update_anomaly_status(
                anomaly_id,
                status
            )
            
            if success:
                return web.json_response({'status': 'updated'})
            else:
                return web.json_response(
                    {'error': 'anomaly not found'},
                    status=404
                )
                
        except ValueError:
            return web.json_response(
                {'error': 'invalid anomaly id'},
                status=400
            )
        except Exception as e:
            logging.error(f"Failed to update anomaly status: {str(e)}")
            return web.json_response(
                {'error': str(e)},
                status=500
            )

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    service = MCPService()
    asyncio.run(service.start())
```

## 4. Error Handling and Monitoring

### 4.1 Error Handling

```python
# error_handler.py
import logging
from functools import wraps
from typing import Callable, Any

def handle_database_errors(func: Callable) -> Callable:
    """Decorator for handling database errors."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except asyncpg.PostgresError as e:
            logging.error(f"Database error in {func.__name__}: {str(e)}")
            raise
        except redis.RedisError as e:
            logging.error(f"Cache error in {func.__name__}: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise
    return wrapper
```

### 4.2 Monitoring Setup

```python
# monitoring.py
from prometheus_client import start_http_server, Counter, Histogram, Gauge
import psutil
import logging

class ServiceMonitor:
    def __init__(self, port: int = 9090):
        self.port = port
        
        # System metrics
        self.cpu_usage = Gauge(
            'system_cpu_usage',
            'CPU usage percentage'
        )
        self.memory_usage = Gauge(
            'system_memory_usage',
            'Memory usage percentage'
        )
        self.disk_usage = Gauge(
            'system_disk_usage',
            'Disk usage percentage'
        )
        
        # Service metrics
        self.active_agents = Gauge(
            'active_agents',
            'Number of active agents'
        )
        self.analysis_cycles = Counter(
            'analysis_cycles_total',
            'Total number of analysis cycles',
            ['agent']
        )
        self.analysis_duration = Histogram(
            'analysis_duration_seconds',
            'Time spent on analysis',
            ['agent']
        )
    
    def start(self):
        """Start monitoring server."""
        start_http_server(self.port)
        logging.info(f"Monitoring server started on port {self.port}")
    
    def update_system_metrics(self):
        """Update system metrics."""
        self.cpu_usage.set(psutil.cpu_percent())
        self.memory_usage.set(psutil.virtual_memory().percent)
        self.disk_usage.set(psutil.disk_usage('/').percent)
```

## Next Steps

1. Review the [Agent Implementation](AnalyzerMCPServer-IP-Agent.md) for agent development details
2. Check the [Training Implementation](AnalyzerMCPServer-IP-Training.md) for model management
3. Follow the [Deployment Guide](AnalyzerMCPServer-IP-Deployment.md) for setup instructions 