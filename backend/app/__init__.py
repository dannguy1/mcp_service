from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from app.config.config import Config

socketio = SocketIO()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app)
    socketio.init_app(app)

    # Register blueprints
    from app.api.routes import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    @app.route("/api/v1/health")
    def health_check():
        return jsonify({"status": "healthy"})

    return app
