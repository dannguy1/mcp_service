import asyncio
import logging
from pathlib import Path
from datetime import datetime

import asyncpg
import aiosqlite
import os
from app.config.config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQL schema
SCHEMA = """
-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables
CREATE TABLE IF NOT EXISTS wifi_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    log_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    severity INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS anomalies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    severity INTEGER NOT NULL,
    confidence FLOAT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS model_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT false,
    performance_metrics JSONB,
    UNIQUE(version)
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    device_id VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_wifi_logs_timestamp ON wifi_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_wifi_logs_device_id ON wifi_logs(device_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_timestamp ON anomalies(timestamp);
CREATE INDEX IF NOT EXISTS idx_anomalies_device_id ON anomalies(device_id);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_device_id ON alerts(device_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
"""

async def init_db() -> None:
    """Initialize database schema.
    
    Note: This service only reads from the log_entries table which is
    managed by the ExternalAIAnalyzer system. Anomalies are stored in
    a local SQLite database.
    """
    try:
        # Connect to PostgreSQL (read-only)
        conn = await asyncpg.connect(
            host=config.db['host'],
            port=config.db['port'],
            user=config.db['user'],
            password=config.db['password'],
            database=config.db['database']
        )
        
        # Verify log_entries table exists
        await conn.execute('SELECT 1 FROM log_entries LIMIT 1')
        await conn.close()
        
        # Initialize SQLite database
        os.makedirs(os.path.dirname(config.sqlite['db_path']), exist_ok=True)
        async with aiosqlite.connect(config.sqlite['db_path']) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS mcp_anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    device_id INTEGER,
                    timestamp TEXT NOT NULL,
                    anomaly_type TEXT NOT NULL,
                    severity INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    description TEXT,
                    features TEXT,  -- Storing JSON as TEXT
                    status TEXT DEFAULT 'new',
                    synced INTEGER DEFAULT 0,  -- Track sync status
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT,
                    resolution_status TEXT DEFAULT 'open',
                    resolution_notes TEXT
                );

                -- Indexes for efficient querying
                CREATE INDEX IF NOT EXISTS idx_anomalies_timestamp ON mcp_anomalies(timestamp);
                CREATE INDEX IF NOT EXISTS idx_anomalies_agent ON mcp_anomalies(agent_name);
                CREATE INDEX IF NOT EXISTS idx_anomalies_synced ON mcp_anomalies(synced);
                CREATE INDEX IF NOT EXISTS idx_anomalies_status ON mcp_anomalies(status);
                CREATE INDEX IF NOT EXISTS idx_anomalies_resolution ON mcp_anomalies(resolution_status);
            ''')
            await db.commit()
        
        logging.info("Database initialized successfully")
        
    except Exception as e:
        logging.error(f"Failed to initialize database: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(init_db())
