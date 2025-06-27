import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def parse_int_with_comment(value, default):
    """Parse an integer value that may contain a comment."""
    if not value:
        return default
    # Split on '#' and take the first part, then strip whitespace
    clean_value = value.split('#')[0].strip()
    try:
        return int(clean_value)
    except ValueError:
        return default

class Config:
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'

    # Logging configuration
    log_level = os.getenv('LOG_LEVEL', 'info')
    LOG_LEVEL = log_level.upper()

    # Service timing configuration
    ANALYSIS_INTERVAL = parse_int_with_comment(os.getenv('ANALYSIS_INTERVAL'), 60)  # seconds
    STATUS_UPDATE_INTERVAL = parse_int_with_comment(os.getenv('STATUS_UPDATE_INTERVAL'), 10)  # 10 seconds
    HEALTH_CHECK_INTERVAL = parse_int_with_comment(os.getenv('HEALTH_CHECK_INTERVAL'), 60)  # 1 minute
    MODEL_UPDATE_INTERVAL = parse_int_with_comment(os.getenv('MODEL_UPDATE_INTERVAL'), 86400)  # 24 hours

    # Base paths
    base_dir = Path(__file__).parent.parent
    model_dir = os.path.join(base_dir, 'models')
    
    # API configuration
    api_prefix = '/api/ui'
    api_host = os.getenv('API_HOST', '0.0.0.0')
    api_port = int(os.getenv('API_PORT', '5000'))
    
    # Redis configuration
    redis_host = os.getenv('REDIS_HOST', 'redis')
    redis_port = int(os.getenv('REDIS_PORT', '6379'))
    
    # CORS configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # WebSocket configuration
    SOCKETIO_MESSAGE_QUEUE = os.getenv('SOCKETIO_MESSAGE_QUEUE', 'redis://localhost:6379/0')

    # Database configuration
    database_url = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    
    # Log field mappings
    log_field_mappings = {
        'timestamp': 'timestamp',
        'level': 'level',
        'program': 'program',
        'message': 'message',
        'device_id': 'device_id',
        'device_ip': 'device_ip',
        'severity': 'severity',
        'source': 'source'
    }

    # Model configuration
    model_version = os.getenv('MODEL_VERSION', '1.0.0')
    model_threshold = float(os.getenv('MODEL_THRESHOLD', '0.8'))
    
    # Feature extraction configuration
    feature_window = parse_int_with_comment(os.getenv('FEATURE_WINDOW'), 300)  # 5 minutes
    min_samples = parse_int_with_comment(os.getenv('MIN_SAMPLES'), 10)
    
    # Anomaly detection configuration
    anomaly_threshold = float(os.getenv('ANOMALY_THRESHOLD', '0.95'))
    max_anomalies = parse_int_with_comment(os.getenv('MAX_ANOMALIES'), 100)

# Create a singleton instance of the Config class
config = Config() 