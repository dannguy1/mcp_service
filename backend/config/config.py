import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'

    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Service timing configuration
    ANALYSIS_INTERVAL = int(os.getenv('ANALYSIS_INTERVAL', '300'))  # 5 minutes in seconds
    STATUS_UPDATE_INTERVAL = int(os.getenv('STATUS_UPDATE_INTERVAL', '10'))  # 10 seconds
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '60'))  # 1 minute
    MODEL_UPDATE_INTERVAL = int(os.getenv('MODEL_UPDATE_INTERVAL', '86400').split('#')[0].strip())  # 24 hours

    # Model configuration
    model_dir = os.getenv('MODEL_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models'))

    # API configuration
    API_PREFIX = '/api/ui'
    
    # Redis configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # CORS configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # WebSocket configuration
    SOCKETIO_MESSAGE_QUEUE = os.getenv('SOCKETIO_MESSAGE_QUEUE', 'redis://localhost:6379/0')

    # Database configuration
    db = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'database': os.getenv('DB_NAME', 'mcp_service'),
        'min_connections': int(os.getenv('DB_MIN_CONNECTIONS', '5')),
        'max_connections': int(os.getenv('DB_MAX_CONNECTIONS', '20')),
        'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30'))
    }

    # Redis configuration for DataService
    redis = {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', '6379')),
        'db': int(os.getenv('REDIS_DB', '0')),
        'max_connections': int(os.getenv('REDIS_MAX_CONNECTIONS', '10')),
        'socket_timeout': int(os.getenv('REDIS_SOCKET_TIMEOUT', '5'))
    }

    # SQLite configuration
    sqlite = {
        'db_path': os.getenv('SQLITE_DB_PATH', 'mcp_service.db'),
        'synchronous': os.getenv('SQLITE_SYNCHRONOUS', 'NORMAL'),
        'cache_size': int(os.getenv('SQLITE_CACHE_SIZE', '-2000')),
        'temp_store': os.getenv('SQLITE_TEMP_STORE', 'MEMORY'),
        'mmap_size': int(os.getenv('SQLITE_MMAP_SIZE', '30000000000'))
    }

    # Log columns configuration
    log_columns = {
        'id': 'id',
        'timestamp': 'timestamp',
        'device_id': 'device_id',
        'program': 'program',
        'message': 'message',
        'severity': 'severity',
        'source': 'source'
    } 

# Create a singleton instance of the Config class
config = Config() 