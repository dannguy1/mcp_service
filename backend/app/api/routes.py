from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import json
import os
import psutil
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from app.db import get_db_connection

bp = Blueprint('api', __name__)

def get_system_status():
    """Get system status information"""
    # Initialize all services with default status
    services = {
        'database': {
            'status': 'disconnected',
            'last_check': datetime.now().isoformat(),
            'error': None
        },
        'redis': {
            'status': 'disconnected',
            'last_check': datetime.now().isoformat(),
            'error': None
        },
        'model_service': {
            'status': 'disconnected',
            'last_check': datetime.now().isoformat(),
            'error': None
        },
        'data_source': {
            'status': 'disconnected',
            'last_check': datetime.now().isoformat(),
            'error': None
        },
        'backend_service': {
            'status': 'disconnected',
            'last_check': datetime.now().isoformat(),
            'error': None
        },
        'mcp_service': {
            'status': 'disconnected',
            'last_check': datetime.now().isoformat(),
            'error': None
        }
    }
    
    # Check database connection
    try:
        with get_db_connection() as conn:
            conn.execute(text('SELECT 1'))
            services['database']['status'] = 'connected'
    except Exception as e:
        services['database']['status'] = 'error'
        services['database']['error'] = str(e)

    # Check Redis connection and get service statuses
    try:
        import redis
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        r = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        
        # Test Redis connection
        r.ping()
        services['redis']['status'] = 'connected'
        
        # Get service statuses from Redis
        for service in ['model_service', 'data_source', 'backend', 'mcp_service', 'database']:
            status_key = f'mcp:{service}:status'
            error_key = f'mcp:{service}:error'
            last_check_key = f'mcp:{service}:last_check'
            
            status = r.get(status_key)
            if status:
                # Map 'backend' to 'backend_service' for frontend compatibility
                service_key = 'backend_service' if service == 'backend' else service
                services[service_key]['status'] = status
                services[service_key]['error'] = r.get(error_key)
                last_check = r.get(last_check_key)
                if last_check:
                    services[service_key]['last_check'] = last_check
                
    except redis.AuthenticationError as e:
        services['redis']['status'] = 'error'
        services['redis']['error'] = "Redis authentication failed. Please check credentials."
    except redis.ConnectionError as e:
        services['redis']['status'] = 'error'
        services['redis']['error'] = "Could not connect to Redis server."
    except Exception as e:
        services['redis']['status'] = 'error'
        services['redis']['error'] = str(e)

    # Calculate overall system status
    system_status = 'healthy'
    if any(service['status'] == 'error' for service in services.values()):
        system_status = 'unhealthy'

    return {
        'status': system_status,
        'uptime': get_uptime(),
        'version': '1.0.0',
        'metrics': {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'response_time': 120
        },
        'connections': services
    }

def get_recent_anomalies():
    """Get recent anomalies from SQLite database"""
    # TODO: Implement actual database query
    return []

def get_filtered_logs():
    """Get filtered logs from PostgreSQL with pagination"""
    try:
        # Get filter parameters
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        severity = request.args.get('severity')
        program = request.args.get('program')
        search = request.args.get('search')
        
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 25))
        offset = (page - 1) * per_page

        print(f"Fetching logs with filters: start_date={start_date}, end_date={end_date}, severity={severity}, program={program}, page={page}, per_page={per_page}")

        # Build the base query
        query = """
            SELECT 
                id,
                device_id,
                device_ip,
                timestamp,
                log_level,
                process_name,
                message,
                raw_message,
                structured_data,
                pushed_to_ai,
                pushed_at,
                push_attempts,
                last_push_error
            FROM log_entries
            WHERE 1=1
        """
        count_query = "SELECT COUNT(*) FROM log_entries WHERE 1=1"
        params = {}

        # Add filters
        if start_date:
            query += " AND timestamp >= :start_date"
            count_query += " AND timestamp >= :start_date"
            params['start_date'] = start_date
        if end_date:
            query += " AND timestamp <= :end_date"
            count_query += " AND timestamp <= :end_date"
            params['end_date'] = end_date
        if severity:
            query += " AND log_level = :severity"
            count_query += " AND log_level = :severity"
            params['severity'] = severity
        if program:
            query += " AND process_name = :program"
            count_query += " AND process_name = :program"
            params['program'] = program
        if search:
            query += " AND (message ILIKE :search OR raw_message ILIKE :search)"
            count_query += " AND (message ILIKE :search OR raw_message ILIKE :search)"
            params['search'] = f'%{search}%'

        # Add ordering and pagination
        query += " ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
        params['limit'] = per_page
        params['offset'] = offset

        print(f"Executing query: {query}")
        print(f"With params: {params}")

        # Execute queries
        with get_db_connection() as conn:
            # Get total count
            total_count = conn.execute(text(count_query), params).scalar()
            print(f"Total count: {total_count}")
            
            # Get paginated results
            result = conn.execute(text(query), params)
            logs = []
            for row in result:
                log_entry = {
                    'id': row.id,
                    'device_id': row.device_id,
                    'device_ip': row.device_ip,
                    'timestamp': row.timestamp.isoformat(),
                    'level': row.log_level,
                    'program': row.process_name,
                    'message': row.message,
                    'raw_message': row.raw_message,
                    'structured_data': row.structured_data,
                    'pushed_to_ai': row.pushed_to_ai,
                    'pushed_at': row.pushed_at.isoformat() if row.pushed_at else None,
                    'push_attempts': row.push_attempts,
                    'last_push_error': row.last_push_error
                }
                logs.append(log_entry)

        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        
        response = {
            'logs': logs,
            'pagination': {
                'total': total_count,
                'per_page': per_page,
                'current_page': page,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1
            }
        }
        
        print(f"Returning response with {len(logs)} logs")
        print(f"Response structure: {response.keys()}")
        return response
    except Exception as e:
        print(f"Error fetching logs: {str(e)}")
        return {
            'logs': [],
            'pagination': {
                'total': 0,
                'per_page': per_page,
                'current_page': page,
                'total_pages': 0,
                'has_next': False,
                'has_prev': False
            }
        }

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
    try:
        logs = get_filtered_logs()
        
        # Get unique programs for filter options
        with get_db_connection() as conn:
            programs = conn.execute(text("SELECT DISTINCT process_name FROM log_entries WHERE process_name IS NOT NULL ORDER BY process_name")).fetchall()
            programs = [p[0] for p in programs]

        return jsonify({
            'logs': logs,
            'total': len(logs),
            'filters': {
                'severity': ['emergency', 'alert', 'critical', 'error', 'warning', 'notice', 'info', 'debug'],
                'programs': programs
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
