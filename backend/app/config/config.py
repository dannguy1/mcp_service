import os
from typing import Dict, Any

class Config:
    def __init__(self):
        # Database Configuration (PostgreSQL - Read Only)
        self.db = {
            'host': os.getenv('DB_HOST', '192.168.10.14'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'netmonitor_db'),
            'user': os.getenv('DB_USER', 'netmonitor_user'),
            'password': os.getenv('DB_PASSWORD', 'netmonitor_password'),
            'min_connections': int(os.getenv('DB_MIN_CONNECTIONS', '5')),
            'max_connections': int(os.getenv('DB_MAX_CONNECTIONS', '20')),
            'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30'))
        }

        # SQLite Configuration
        self.sqlite = {
            'db_path': os.getenv('SQLITE_DB_PATH', '/app/data/mcp_anomalies.db'),
            'journal_mode': os.getenv('SQLITE_JOURNAL_MODE', 'WAL'),
            'synchronous': os.getenv('SQLITE_SYNCHRONOUS', 'NORMAL'),
            'cache_size': int(os.getenv('SQLITE_CACHE_SIZE', '-2000')),
            'temp_store': os.getenv('SQLITE_TEMP_STORE', 'MEMORY'),
            'mmap_size': int(os.getenv('SQLITE_MMAP_SIZE', '30000000000'))
        }

        # Redis Configuration
        self.redis = {
            'host': os.getenv('REDIS_HOST', 'redis'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'db': int(os.getenv('REDIS_DB', '0')),
            'max_connections': int(os.getenv('REDIS_MAX_CONNECTIONS', '10')),
            'socket_timeout': int(os.getenv('REDIS_SOCKET_TIMEOUT', '5'))
        }

        # Service Configuration
        self.SERVICE_HOST = os.getenv('SERVICE_HOST', '0.0.0.0')
        self.SERVICE_PORT = int(os.getenv('SERVICE_PORT', '5555'))
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.ANALYSIS_INTERVAL = int(os.getenv('ANALYSIS_INTERVAL', '300'))

        # SocketIO Configuration
        self.SOCKETIO_MESSAGE_QUEUE = os.getenv('SOCKETIO_MESSAGE_QUEUE', f'redis://{self.redis["host"]}:{self.redis["port"]}/{self.redis["db"]}')
        self.API_PREFIX = os.getenv('API_PREFIX', '/api/v1')

        # Log columns configuration
        self.log_columns = {
            'id': 'id',
            'timestamp': 'timestamp',
            'device_id': 'device_id',
            'program': 'program',
            'message': 'message',
            'severity': 'severity',
            'source': 'source'
        }

        # Model directory configuration
        self.model_dir = os.getenv('MODEL_DIR', '/app/models')

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for logging/debugging."""
        return {
            'db': self.db,
            'sqlite': self.sqlite,
            'redis': self.redis,
            'service': {
                'host': self.SERVICE_HOST,
                'port': self.SERVICE_PORT,
                'log_level': self.LOG_LEVEL,
                'analysis_interval': self.ANALYSIS_INTERVAL
            }
        }

# Create a singleton config instance
config = Config() 