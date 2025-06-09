# Monitoring and Maintenance Guide

## Overview

This document provides comprehensive documentation for the monitoring and maintenance infrastructure of the MCP Service. The system includes Prometheus for metrics collection, Grafana for visualization, and automated maintenance scripts for system upkeep.

## Table of Contents

1. [Monitoring Setup](#monitoring-setup)
2. [Maintenance Procedures](#maintenance-procedures)
3. [Configuration Files](#configuration-files)
4. [Usage Guidelines](#usage-guidelines)
5. [Troubleshooting](#troubleshooting)

## Monitoring Setup

### Prerequisites

- Docker and Docker Compose installed
- Python 3.8 or higher
- Required Python packages (see requirements.txt)

### Directory Structure

```bash
monitoring/
├── prometheus/
│   ├── prometheus.yml
│   └── rules/
│       └── alerts.yml
└── grafana/
    ├── datasources/
    │   └── prometheus.yml
    └── dashboards/
        ├── system.json
        ├── service.json
        ├── model.json
        └── database.json
```

### Setup Instructions

1. Create required directories:
```bash
mkdir -p monitoring/prometheus/rules
mkdir -p monitoring/grafana/datasources
mkdir -p monitoring/grafana/dashboards
```

2. Run the monitoring setup script:
```bash
python scripts/setup_monitoring.py
```

3. Start the services:
```bash
docker-compose up -d
```

### Accessing Monitoring Interfaces

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000
  - Default credentials:
    - Username: admin (or GRAFANA_ADMIN_USER)
    - Password: admin (or GRAFANA_ADMIN_PASSWORD)

## Maintenance Procedures

### Automated Maintenance

The system includes automated maintenance tasks that run daily at 2 AM:

- Database backups
- Model and log file backups
- Log rotation and cleanup
- Database optimization
- Retention policy enforcement

### Manual Maintenance

To run maintenance tasks manually:

```bash
python scripts/maintenance.py
```

### Backup Locations

- Database backups: `backups/backup_YYYYMMDD_HHMMSS/database.sql`
- Model backups: `backups/backup_YYYYMMDD_HHMMSS/models/`
- Log backups: `backups/backup_YYYYMMDD_HHMMSS/logs/`

### Retention Policies

- Backups: 30 days
- Logs: 30 days
- Rotated logs: 10 files, 100MB each

## Configuration Files

### Monitoring Configuration

The monitoring configuration is defined in `config/monitoring_config.yaml`:

```yaml
prometheus:
  metrics:
    system:
      - name: cpu_usage_percent
        type: gauge
        threshold: 70
    service:
      - name: request_latency_seconds
        type: histogram
    model:
      - name: model_accuracy
        type: gauge
        threshold: 95
    database:
      - name: db_connection_pool_size
        type: gauge

  alerting:
    rules:
      - name: high_cpu_usage
        condition: "cpu_usage_percent > 70"
        duration: "5m"
        severity: warning
```

### Grafana Dashboards

The system includes four main dashboards:

1. **System Overview**
   - CPU Usage
   - Memory Usage
   - Disk Usage

2. **Service Performance**
   - Request Latency
   - Request Rate
   - Error Rate

3. **Model Performance**
   - Model Accuracy
   - False Positive Rate
   - False Negative Rate
   - Inference Latency

4. **Database Performance**
   - Query Latency
   - Connection Pool
   - Database Errors

## Usage Guidelines

### Adding New Metrics

1. Add metric definition to `config/monitoring_config.yaml`
2. Update Prometheus configuration
3. Create or update Grafana dashboard

### Creating Alerts

1. Define alert rule in `config/monitoring_config.yaml`
2. Add alert to Prometheus rules
3. Configure alert notifications in Grafana

### Backup Management

- Manual backups: Run `python scripts/maintenance.py`
- View backup history: Check `backups/` directory
- Restore from backup: Use provided restore scripts

## Troubleshooting

### Common Issues

1. **Prometheus Connection Issues**
   - Check if Prometheus container is running
   - Verify network connectivity
   - Check Prometheus logs

2. **Grafana Dashboard Issues**
   - Verify datasource configuration
   - Check dashboard JSON format
   - Clear browser cache

3. **Maintenance Script Errors**
   - Check log files
   - Verify permissions
   - Ensure sufficient disk space

### Log Files

- Application logs: `logs/app.log`
- Maintenance logs: `logs/maintenance.log`
- Monitoring setup logs: `logs/monitoring_setup.log`

### Monitoring Health Checks

1. Check Prometheus targets:
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

2. Check Grafana health:
   ```bash
   curl http://localhost:3000/api/health
   ```

3. Check Node Exporter metrics:
   ```bash
   curl http://localhost:9100/metrics
   ```

## Best Practices

1. **Monitoring**
   - Regularly review alert thresholds
   - Monitor system resource usage
   - Keep dashboards up to date

2. **Maintenance**
   - Schedule maintenance during low-traffic periods
   - Verify backups regularly
   - Monitor disk space usage

3. **Security**
   - Change default credentials
   - Use secure passwords
   - Restrict access to monitoring interfaces

## Support

For issues or questions:
1. Check the troubleshooting guide
2. Review log files
3. Contact system administrator

## Related Documents

- [Deployment Guide](deployment.md)
- [Configuration Guide](configuration.md)
- [API Documentation](api.md) 