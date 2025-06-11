from flask import Flask, render_template, jsonify
from mcp_service.config import settings
from mcp_service.data_service import DataService

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Initialize data service
    data_service = DataService(settings)
    
    @app.route('/')
    def index():
        """Render the main page."""
        return render_template('index.html')
    
    @app.route('/api/health')
    def health():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0'
        })
    
    @app.route('/api/anomalies')
    def get_anomalies():
        """Get recent anomalies."""
        try:
            anomalies = data_service.get_recent_anomalies(limit=100)
            return jsonify(anomalies)
        except Exception as e:
            return jsonify({
                'error': str(e)
            }), 500
    
    return app 