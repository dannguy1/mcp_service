# MCP Service

A modular AI processing service designed to analyze OpenWRT network logs for anomaly detection within the Log Monitor framework.

## Table of Contents

1. [Getting Started](#getting-started)
2. [System Architecture](#system-architecture)
3. [User Interfaces](#user-interfaces)
4. [Configuration](#configuration)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Development](#development)
7. [Troubleshooting](#troubleshooting)
8. [Support](#support)
9. [Running Components Natively](#running-components-natively)

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/dannguy1/mcp_service.git
cd mcp_service
```

2. Set up virtual environment:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. Configure environment:
```bash
# Copy example environment file
cp example.env .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

4. Run the system:
```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or run manually
python scripts/run_web_ui.py
```

For detailed installation instructions, see [Deployment Guide](docs/Implementation/AnalyzerMCPServer-IP-Deployment.md).

## System Architecture

The MCP Service consists of several components:

- **Model Server**: Core service for anomaly detection
- **Database**: PostgreSQL for data storage
- **Cache**: Redis for performance optimization
- **Monitoring**: Prometheus and Grafana
- **Web UI**: Real-time monitoring interface

For detailed architecture information, see [Implementation Overview](docs/Implementation/AnalyzerMCPServer-IP-Overview.md).

## User Interfaces

### 1. MCP Service Web UI
- **URL**: http://localhost:8080
- **Purpose**: Real-time monitoring and management
- **Features**:
  - System status dashboard
  - Performance metrics
  - Anomaly detection results
  - Real-time charts

### 2. Grafana Dashboards
- **URL**: http://localhost:3000
- **Default Credentials**: admin/admin
- **Dashboards**:
  - System Overview
  - Service Performance
  - Model Performance
  - Database Performance

### 3. Prometheus UI
- **URL**: http://localhost:9090
- **Purpose**: Raw metrics and alert management

For detailed UI documentation, see [Monitoring Quick Start Guide](docs/monitoring_quickstart.md).

## Configuration

### Environment Variables
Key variables in `.env`:
```env
# Database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=mcp_service

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=your_secure_password

# Web UI
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=8080
```

### Configuration Files
- `config/monitoring_config.yaml`: Monitoring setup
- `config/server_config.yaml`: Server settings
- `config/data_source_config.yaml`: Data source configuration

For detailed configuration information, see [Server Implementation](docs/Implementation/AnalyzerMCPServer-IP-Server.md).

## Monitoring & Maintenance

### Automated Tasks
- Daily backups (2 AM)
- Log rotation
- Database optimization
- Performance monitoring

### Manual Maintenance
```bash
python scripts/maintenance.py
```

For detailed monitoring and maintenance information, see [Monitoring and Maintenance Guide](docs/monitoring_and_maintenance.md).

## Development

### Project Structure
```
mcp_service/
├── config/                 # Configuration files
├── docs/                   # Documentation
├── monitoring/            # Monitoring setup
├── scripts/               # Utility scripts
├── static/               # Web UI static files
├── templates/            # Web UI templates
├── tests/                # Test suite
└── utils/                # Utility modules
```

### Running Tests
```bash
# All tests
pytest

# Specific categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/
```

For development guidelines, see [Testing Implementation](docs/Implementation/AnalyzerMCPServer-IP-Testing.md).

## Troubleshooting

### Quick Checks

1. **Service Status**
```bash
docker-compose ps
docker-compose logs <service-name>
```

2. **Health Check**
```bash
curl http://localhost:8000/health
```

3. **Metrics**
```bash
curl http://localhost:9090/api/v1/targets
```

### Common Issues

1. **Service Not Starting**
   - Check logs: `docker-compose logs <service-name>`
   - Verify environment variables
   - Check port availability

2. **Metrics Not Showing**
   - Verify Prometheus targets
   - Check service health
   - Review network connectivity

3. **Web UI Issues**
   - Check web UI logs
   - Verify port configuration
   - Clear browser cache

For detailed troubleshooting, see [Monitoring and Maintenance Guide](docs/monitoring_and_maintenance.md).

## Support

### Documentation
- [API Documentation](docs/api_documentation.md)
- [Monitoring Guide](docs/monitoring_and_maintenance.md)
- [Quick Start Guide](docs/monitoring_quickstart.md)

### Getting Help
1. Check the troubleshooting guide
2. Review log files in `logs/`
3. Contact system administrator

## License

[Your License Here]

## Running Components Natively

While the system is designed to run in Docker containers, you can also run individual components natively for development and debugging purposes. The `scripts` directory contains several utility scripts for this purpose.

### Model Server

Run the FastAPI model server with:
```bash
python scripts/run_model_server.py [options]

Options:
  --config CONFIG     Path to server configuration file (default: config/server_config.yaml)
  --host HOST        Host to bind the server to (default: 0.0.0.0)
  --port PORT        Port to bind the server to (default: 8000)
  --workers WORKERS  Number of worker processes (default: 4)
  --reload          Enable auto-reload on code changes
  --debug           Enable debug logging
```

### Model Training

Train the anomaly detection model with:
```bash
python scripts/train_model.py [options]

Options:
  --config CONFIG     Path to model configuration file (default: config/model_config.yaml)
  --start-date DATE  Start date for training data (YYYY-MM-DD)
  --end-date DATE    End date for training data (YYYY-MM-DD)
  --debug           Enable debug logging
```

### Model Monitoring

Monitor model performance and drift with:
```bash
python scripts/monitor_model.py [options]

Options:
  --config CONFIG       Path to model configuration file (default: config/model_config.yaml)
  --model-version VER   Model version to monitor (default: latest)
  --interval SECONDS    Monitoring interval in seconds (default: 300)
  --debug              Enable debug logging
```

### Features

Each script provides:
- Automatic environment setup
- Configuration management
- Detailed logging (both console and file)
- Error handling and recovery
- Debug mode for troubleshooting

### Logs

Logs are stored in the `~/.mcp_service/logs` directory:
- `~/.mcp_service/logs/model_server.log`: Model server logs
- `~/.mcp_service/logs/training.log`: Model training logs
- `~/.mcp_service/logs/monitoring.log`: Model monitoring logs

The logs directory is automatically created in your home directory to avoid permission issues. Each script will create its own log file with appropriate permissions.

### Environment Setup

The scripts automatically:
1. Set up the Python path
2. Load environment variables from `.env`
3. Create necessary directories
4. Configure logging

### Debug Mode

Use the `--debug` flag to enable detailed logging and troubleshooting information. This is particularly useful during development and when investigating issues. 