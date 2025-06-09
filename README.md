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

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- Git

### Quick Installation

1. Clone and setup:
```bash
git clone <repository-url>
cd mcp_service
cp .env.example .env
# Edit .env with your configuration
pip install -r requirements.txt
```

2. Start the system:
```bash
docker-compose up -d
```

3. Verify services:
```bash
docker-compose ps
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