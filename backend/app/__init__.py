from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from app.config.config import Config, config
from app.services.status_manager import ServiceStatusManager
import os
import redis
from sqlalchemy import text
import logging

socketio = SocketIO()
status_manager = None
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app)
    socketio.init_app(app)

    # Initialize Redis client
    redis_host = os.getenv('REDIS_HOST', 'redis')
    redis_port = int(os.getenv('REDIS_PORT', '6379'))
    redis_client = redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5
    )
    
    # Initialize status manager with Redis client
    global status_manager
    status_manager = ServiceStatusManager('backend', redis_client)
    
    # Start status updates
    def health_check():
        try:
            # Check Redis connection
            redis_client.ping()
            
            # Check database connection
            from app.db import get_db_connection
            with get_db_connection() as conn:
                conn.execute(text('SELECT 1'))
            
            return True
        except Exception as e:
            logger.error(f"Backend health check failed: {str(e)}")
            return False
    
    status_manager.start_status_updates(health_check)

    # Register blueprints
    from app.api.routes import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    @app.route("/api/v1/health")
    def health_check():
        return jsonify({"status": "healthy"})

    @app.teardown_appcontext
    def shutdown_status_manager(exception=None):
        if status_manager:
            status_manager.stop_status_updates()

    return app
