from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import json
import os
import psutil

bp = Blueprint('api', __name__)

def get_system_status():
    """Get system status information"""
    return {
        'status': 'healthy',
        'uptime': '1d 2h 3m',
        'version': '1.0.0',
        'metrics': {
            'cpu_usage': 45.2,
            'memory_usage': 62.8,
            'response_time': 120
        }
    }

def get_recent_anomalies():
    """Get recent anomalies from SQLite database"""
    # TODO: Implement actual database query
    return []

def get_filtered_logs():
    """Get filtered logs from PostgreSQL"""
    # TODO: Implement actual database query
    return []

def get_model_list():
    """Get list of available models"""
    models_dir = '/app/models'
    models = []
    
    if os.path.exists(models_dir):
        for model_dir in os.listdir(models_dir):
            metadata_path = os.path.join(models_dir, model_dir, 'metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    models.append({
                        'id': model_dir,
                        'name': f"Model {model_dir}",
                        'is_active': os.path.exists(os.path.join(models_dir, f"{model_dir}_active")),
                        'metadata': metadata
                    })
    
    return models

def get_uptime():
    """Get system uptime in human readable format"""
    uptime_seconds = psutil.boot_time()
    uptime = datetime.now() - datetime.fromtimestamp(uptime_seconds)
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

@bp.route('/server/stats')
def get_server_stats():
    """Get server statistics"""
    try:
        # CPU Information
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        try:
            # Try to get CPU temperature if available
            temps = psutil.sensors_temperatures()
            cpu_temp = next(iter(temps.values()))[0].current if temps else 0
        except:
            cpu_temp = 0

        # Memory Information
        memory = psutil.virtual_memory()
        
        # Disk Information
        disk = psutil.disk_usage('/')

        return jsonify({
            "cpu": {
                "usage": cpu_percent,
                "cores": cpu_count,
                "temperature": cpu_temp
            },
            "memory": {
                "total": memory.total,
                "used": memory.used,
                "free": memory.available
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free
            },
            "uptime": get_uptime()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/anomalies')
def get_anomalies():
    """Get anomalies"""
    try:
        # Mock data for now
        anomalies = [
            {
                "id": 1,
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                "type": "network",
                "severity": 8,
                "description": "Unusual network traffic pattern detected",
                "status": "active"
            },
            {
                "id": 2,
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "type": "system",
                "severity": 6,
                "description": "High CPU usage detected",
                "status": "resolved"
            },
            {
                "id": 3,
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "type": "security",
                "severity": 9,
                "description": "Multiple failed login attempts",
                "status": "active"
            }
        ]
        return jsonify(anomalies)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/dashboard')
def get_dashboard_data():
    """Aggregate data for dashboard display"""
    return jsonify({
        'system_status': get_system_status(),
        'recent_anomalies': get_recent_anomalies(),
        'performance_metrics': get_system_status()['metrics']
    })

@bp.route('/logs')
def get_logs():
    """Get filtered log entries"""
    filters = request.args.to_dict()
    return jsonify({
        'logs': get_filtered_logs(),
        'total': 0,
        'filters': {
            'severity': ['info', 'warning', 'error'],
            'programs': ['hostapd', 'wpa_supplicant']
        }
    })

@bp.route('/models')
def get_models():
    """Get model information"""
    return jsonify({
        'models': get_model_list(),
        'active_model': next((m for m in get_model_list() if m['is_active']), None),
        'metadata': {}
    })

@bp.route('/models/<model_id>/activate', methods=['POST'])
def activate_model(model_id):
    """Activate a specific model version"""
    # TODO: Implement model activation
    return jsonify({'status': 'success', 'message': f'Model {model_id} activated'})

@bp.route('/models/<model_id>/deploy', methods=['POST'])
def deploy_model(model_id):
    """Deploy a model to the service"""
    # TODO: Implement model deployment
    return jsonify({'status': 'success', 'message': f'Model {model_id} deployed'})
