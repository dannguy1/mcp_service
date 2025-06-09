# AnalyzerMCPServer Implementation Plan - Deployment

## Overview

This document details the deployment process and monitoring setup for the AnalyzerMCPServer, including environment setup, deployment steps, and maintenance procedures.

## 1. Environment Setup

### 1.1 System Requirements

- **Hardware**
  - Raspberry Pi 5 (4-8GB RAM)
  - Quad-core CPU
  - 32GB+ storage
  - Network connectivity

- **Software**
  - Docker 20.10+
  - Docker Compose 2.0+
  - Git
  - Python 3.9+

### 1.2 Project Structure
```
mcp_service/
├── agents/                 # Agent implementations
│   ├── __init__.py
│   ├── base_agent.py      # Base agent class
│   └── wifi_agent.py      # WiFi-specific agent
├── components/            # Core components
│   ├── __init__.py
│   ├── feature_extractor.py
│   ├── model_manager.py
│   └── anomaly_classifier.py
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── performance/      # Performance tests
├── docs/                 # Documentation
│   └── Implementation/   # Implementation plans
├── models/              # Model storage
├── mcp_service.py      # Main service
├── data_service.py     # Data access layer
├── config.py           # Configuration
├── init_db.py          # Database initialization
├── export_logs.py      # Log export utility
├── train_model.py      # Model training
├── deploy_model.py     # Model deployment
├── requirements.txt    # Dependencies
├── Dockerfile         # Container definition
├── docker-compose.yml # Service orchestration
└── .env.example       # Environment template
```

### 1.3 Environment Variables

The project uses component-specific environment files for better organization and security. Each component has its own `.env.example` file that should be copied to `.env` in the same directory.

Component-specific environment files:
```
mcp_service/
├── .env.example              # Main service configuration
├── agents/
│   ├── wifi_agent/
│   │   └── .env.example     # WiFi agent specific settings
│   └── base_agent/
│       └── .env.example     # Base agent settings
├── components/
│   ├── feature_extractor/
│   │   └── .env.example     # Feature extractor settings
│   ├── model_manager/
│   │   └── .env.example     # Model manager settings
│   └── anomaly_classifier/
│       └── .env.example     # Anomaly classifier settings
└── tests/
    └── .env.example         # Test configuration
```

Main service configuration (mcp_service/.env):
```ini
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=log_monitor
DB_USER=log_monitor
DB_PASSWORD=your_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=5555
LOG_LEVEL=INFO
ANALYSIS_INTERVAL=300

# Notification Configuration
NOTIFICATION_ENABLED=true
NOTIFICATION_URL=http://notification-service:8080/notify
NOTIFICATION_TOKEN=your_token

# SFTP Configuration
SFTP_HOST=model-server
SFTP_PORT=22
SFTP_USER=model-user
SFTP_PASSWORD=your_password
SFTP_REMOTE_PATH=/models/wifi
```

WiFi Agent configuration (mcp_service/agents/wifi_agent/.env):
```ini
# Agent Configuration
AGENT_ID=wifi_agent_1
AGENT_TYPE=wifi
ANALYSIS_INTERVAL=300
BATCH_SIZE=1000

# Model Configuration
MODEL_PATH=/app/models/wifi
MODEL_VERSION=1.0.0
```

Feature Extractor configuration (mcp_service/components/feature_extractor/.env):
```ini
# Feature Configuration
FEATURE_WINDOW_SIZE=1000
FEATURE_OVERLAP=0.5
MIN_FEATURES=10
```

Model Manager configuration (mcp_service/components/model_manager/.env):
```ini
# Model Configuration
MODEL_CACHE_SIZE=5
MODEL_UPDATE_INTERVAL=3600
MODEL_BACKUP_PATH=/app/models/backup
```

Anomaly Classifier configuration (mcp_service/components/anomaly_classifier/.env):
```ini
# Classification Configuration
SEVERITY_THRESHOLDS={"low": 0.3, "medium": 0.6, "high": 0.8}
CONFIDENCE_THRESHOLD=0.7
```

Test configuration (mcp_service/tests/.env):
```ini
# Test Configuration
TEST_DB_NAME=test_log_monitor
TEST_DB_USER=test_user
TEST_DB_PASSWORD=test_password
MOCK_REDIS=true
```

To set up the environment files:

```bash
# Clone repository
git clone https://github.com/your-org/analyzer-mcp.git
cd analyzer-mcp

# Create environment files for each component
for dir in $(find mcp_service -name ".env.example"); do
    cp "$dir" "${dir%.example}"
done

# Edit each .env file with appropriate values
```

## 2. Deployment Process

### 2.1 Initial Setup

```bash
# Clone repository
git clone https://github.com/your-org/analyzer-mcp.git
cd analyzer-mcp

# Create environment file
cp mcp_service/.env.example mcp_service/.env
# Edit .env with your configuration

# Build Docker images
docker-compose -f mcp_service/docker-compose.yml build

# Start services
docker-compose -f mcp_service/docker-compose.yml up -d

# Verify deployment
curl http://localhost:5555/health
```

### 2.2 Database Initialization

```bash
# Initialize database
docker-compose exec mcp_service python init_db.py

# Verify database setup
docker-compose exec postgres psql -U log_monitor -d log_monitor -c "\dt"
```

### 2.3 Model Deployment

```bash
# Deploy initial model
docker-compose exec mcp_service python deploy_model.py

# Verify model deployment
docker-compose exec mcp_service ls -l /app/models
```

## 3. Monitoring Setup

### 3.1 Logging Configuration

```python
# mcp_service/components/logging_config.py
import logging
import logging.handlers
import os

def setup_logging(log_level=logging.INFO):
    """Configure logging."""
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                'logs/mcp_service.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        ]
    )
```

### 3.2 Prometheus Metrics

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Service metrics
ANALYSIS_CYCLES = Counter(
    'analysis_cycles_total',
    'Total number of analysis cycles',
    ['agent']
)

ANALYSIS_DURATION = Histogram(
    'analysis_duration_seconds',
    'Time spent on analysis',
    ['agent']
)

ANOMALIES_DETECTED = Counter(
    'anomalies_detected_total',
    'Total number of anomalies detected',
    ['agent', 'severity']
)

MODEL_VERSION = Gauge(
    'model_version',
    'Current model version',
    ['agent']
)

RESOURCE_USAGE = Gauge(
    'resource_usage',
    'System resource usage',
    ['resource', 'type']
)
```

### 3.3 Health Check Endpoint

```python
# health_check.py
from aiohttp import web
import psutil
import logging

async def health_check(request):
    """Health check endpoint."""
    try:
        # Check system resources
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        # Check service status
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'resources': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used': memory.used,
                'memory_total': memory.total
            },
            'agents': [
                {
                    'name': agent.name,
                    'status': 'running' if agent.running else 'stopped',
                    'last_analysis': agent.last_analysis.isoformat() if agent.last_analysis else None
                }
                for agent in request.app['agents']
            ]
        }
        
        return web.json_response(status)
        
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}")
        return web.json_response(
            {'status': 'unhealthy', 'error': str(e)},
            status=500
        )
```

## 4. Maintenance Procedures

### 4.1 Backup Procedures

```bash
# Backup database
docker-compose -f mcp_service/docker-compose.yml exec postgres pg_dump -U log_monitor -d log_monitor > backup.sql

# Backup models
tar -czf models_backup.tar.gz mcp_service/models

# Backup logs
tar -czf logs_backup.tar.gz mcp_service/logs
```

### 4.2 Update Procedures

```bash
# Update code
git pull origin main

# Rebuild and restart services
docker-compose down
docker-compose build
docker-compose up -d

# Verify update
curl http://localhost:5555/health
```

### 4.3 Monitoring Procedures

```bash
# Check service logs
docker-compose logs -f mcp_service

# Check resource usage
docker stats

# Check Prometheus metrics
curl http://localhost:9090/metrics
```

## 5. Troubleshooting

### 5.1 Common Issues

1. **Database Connection Issues**
   ```bash
   # Check database status
   docker-compose ps postgres
   
   # Check database logs
   docker-compose logs postgres
   
   # Test connection
   docker-compose exec postgres psql -U log_monitor -d log_monitor -c "\l"
   ```

2. **Redis Connection Issues**
   ```bash
   # Check Redis status
   docker-compose ps redis
   
   # Check Redis logs
   docker-compose logs redis
   
   # Test connection
   docker-compose exec redis redis-cli ping
   ```

3. **Model Loading Issues**
   ```bash
   # Check model files
   docker-compose exec mcp_service ls -l /app/models
   
   # Check model logs
   docker-compose logs mcp_service | grep "model"
   ```

### 5.2 Performance Issues

1. **High CPU Usage**
   ```bash
   # Check CPU usage
   docker stats
   
   # Check process details
   docker-compose exec mcp_service ps aux
   
   # Adjust analysis interval
   # Edit .env file and increase ANALYSIS_INTERVAL
   ```

2. **High Memory Usage**
   ```bash
   # Check memory usage
   docker stats
   
   # Check memory details
   docker-compose exec mcp_service free -m
   
   # Adjust Redis memory limit
   # Edit docker-compose.yml and add memory limit
   ```

3. **Slow Analysis**
   ```bash
   # Check analysis duration
   curl http://localhost:9090/metrics | grep analysis_duration
   
   # Check database performance
   docker-compose exec postgres psql -U log_monitor -d log_monitor -c "EXPLAIN ANALYZE SELECT * FROM wifi_logs;"
   ```

## 6. Security Considerations

### 6.1 Access Control

1. **Database Security**
   ```bash
   # Change default passwords
   docker-compose exec postgres psql -U postgres -c "ALTER USER log_monitor WITH PASSWORD 'new_password';"
   
   # Restrict database access
   # Edit postgresql.conf and pg_hba.conf
   ```

2. **Redis Security**
   ```bash
   # Enable Redis authentication
   # Edit redis.conf and set requirepass
   
   # Restrict Redis access
   # Edit redis.conf and set bind
   ```

3. **Service Security**
   ```bash
   # Use HTTPS
   # Edit nginx configuration
   
   # Enable authentication
   # Add authentication middleware
   ```

### 6.2 Monitoring Security

1. **Prometheus Security**
   ```bash
   # Enable basic auth
   # Edit prometheus.yml
   
   # Use HTTPS
   # Configure TLS certificates
   ```

2. **Log Security**
   ```bash
   # Rotate logs
   # Configure logrotate
   
   # Secure log storage
   # Set proper permissions
   ```

## Next Steps

1. Review the [Documentation Guide](AnalyzerMCPServer-IP-Docs.md) for documentation templates
2. Check the [Training Implementation](AnalyzerMCPServer-IP-Training.md) for model management
3. Follow the [Testing Implementation](AnalyzerMCPServer-IP-Testing.md) for testing procedures 