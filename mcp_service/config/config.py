import os
from typing import Dict, Any

class Config:
    def __init__(self):
        # Database Configuration (PostgreSQL - Read Only)
        self.DB_HOST = os.getenv('DB_HOST', '192.168.10.14')
        self.DB_PORT = int(os.getenv('DB_PORT', '5432'))
        self.DB_NAME = os.getenv('DB_NAME', 'netmonitor_db')
        self.DB_USER = os.getenv('DB_USER', 'netmonitor_user')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD', 'netmonitor_password')

        # SQLite Configuration
        self.SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', '/app/data/mcp_anomalies.db')
        self.SQLITE_JOURNAL_MODE = os.getenv('SQLITE_JOURNAL_MODE', 'WAL')
        self.SQLITE_SYNCHRONOUS = os.getenv('SQLITE_SYNCHRONOUS', 'NORMAL')
        self.SQLITE_CACHE_SIZE = os.getenv('SQLITE_CACHE_SIZE', '-2000')
        self.SQLITE_TEMP_STORE = os.getenv('SQLITE_TEMP_STORE', 'MEMORY')
        self.SQLITE_MMAP_SIZE = os.getenv('SQLITE_MMAP_SIZE', '30000000000')

        # Redis Configuration
        self.REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
        self.REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
        self.REDIS_DB = int(os.getenv('REDIS_DB', '0'))

        # Service Configuration
        self.SERVICE_HOST = os.getenv('SERVICE_HOST', '0.0.0.0')
        self.SERVICE_PORT = int(os.getenv('SERVICE_PORT', '5555'))
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.ANALYSIS_INTERVAL = int(os.getenv('ANALYSIS_INTERVAL', '300'))

    def get_db_config(self) -> Dict[str, Any]:
        """Get PostgreSQL database configuration."""
        return {
            'host': self.DB_HOST,
            'port': self.DB_PORT,
            'database': self.DB_NAME,
            'user': self.DB_USER,
            'password': self.DB_PASSWORD
        }

    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration."""
        return {
            'host': self.REDIS_HOST,
            'port': self.REDIS_PORT,
            'db': self.REDIS_DB
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for logging/debugging."""
        return {
            'db': self.get_db_config(),
            'sqlite': {
                'db_path': self.SQLITE_DB_PATH,
                'journal_mode': self.SQLITE_JOURNAL_MODE,
                'synchronous': self.SQLITE_SYNCHRONOUS,
                'cache_size': self.SQLITE_CACHE_SIZE,
                'temp_store': self.SQLITE_TEMP_STORE,
                'mmap_size': self.SQLITE_MMAP_SIZE
            },
            'redis': self.get_redis_config(),
            'service': {
                'host': self.SERVICE_HOST,
                'port': self.SERVICE_PORT,
                'log_level': self.LOG_LEVEL,
                'analysis_interval': self.ANALYSIS_INTERVAL
            }
        }

# Create a singleton settings instance
settings = Config() 