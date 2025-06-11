import os
import sqlite3
from mcp_service.config import settings
import logging

def init_db():
    """Initialize the local SQLite database."""
    db_path = settings.SQLITE_DB_PATH
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create mcp_anomalies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mcp_anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            device_id INTEGER,
            timestamp TEXT NOT NULL,
            anomaly_type TEXT NOT NULL,
            severity INTEGER NOT NULL,
            confidence REAL NOT NULL,
            description TEXT,
            features TEXT,  -- JSON stored as TEXT
            status TEXT DEFAULT 'new',
            synced INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            resolution_status TEXT DEFAULT 'open',
            resolution_notes TEXT
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mcp_anomalies_device_id ON mcp_anomalies(device_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mcp_anomalies_timestamp ON mcp_anomalies(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mcp_anomalies_status ON mcp_anomalies(status)")
    
    # Configure SQLite for better performance
    cursor.execute(f"PRAGMA journal_mode = {settings.SQLITE_JOURNAL_MODE}")
    cursor.execute(f"PRAGMA synchronous = {settings.SQLITE_SYNCHRONOUS}")
    cursor.execute(f"PRAGMA cache_size = {settings.SQLITE_CACHE_SIZE}")
    cursor.execute(f"PRAGMA temp_store = {settings.SQLITE_TEMP_STORE}")
    cursor.execute(f"PRAGMA mmap_size = {settings.SQLITE_MMAP_SIZE}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    init_db() 