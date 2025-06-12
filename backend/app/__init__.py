from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from app.config.config import Config, settings
from app.services.status_manager import ServiceStatusManager

socketio = SocketIO()
status_manager = None

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app)
    socketio.init_app(app)

    # Initialize status manager with backend_service name
    global status_manager
    status_manager = ServiceStatusManager('backend_service')
    
    # Start status updates
    def health_check():
        return True  # Add your health check logic here
    
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
