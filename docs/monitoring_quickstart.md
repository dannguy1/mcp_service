# Monitoring and Maintenance Quick Start Guide

## Quick Setup

### 1. Initial Setup (5 minutes)

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd mcp_service

# Create required directories
mkdir -p monitoring/prometheus/rules
mkdir -p monitoring/grafana/datasources
mkdir -p monitoring/grafana/dashboards

# Copy environment file and update credentials
cp .env.example .env
# Edit .env with your credentials
```

### 2. Start Services (2 minutes)

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 3. Access Monitoring Interfaces

- **Grafana**: http://localhost:3000
  - Username: admin
  - Password: admin (change this immediately)
- **Prometheus**: http://localhost:9090

## Essential Tasks

### 1. Change Default Passwords

```bash
# Update .env file
GRAFANA_ADMIN_USER=your_username
GRAFANA_ADMIN_PASSWORD=your_secure_password
```

### 2. Verify Monitoring Setup

```bash
# Run the setup script
python scripts/setup_monitoring.py

# Check setup logs
tail -f logs/monitoring_setup.log
```

### 3. Run Initial Maintenance

```bash
# Run maintenance tasks
python scripts/maintenance.py

# Check maintenance logs
tail -f logs/maintenance.log
```

## Key Dashboards

### 1. System Overview
- **Location**: Grafana → Dashboards → System Overview
- **Key Metrics**:
  - CPU Usage
  - Memory Usage
  - Disk Usage

### 2. Service Performance
- **Location**: Grafana → Dashboards → Service Performance
- **Key Metrics**:
  - Request Latency
  - Error Rate
  - Throughput

### 3. Model Performance
- **Location**: Grafana → Dashboards → Model Performance
- **Key Metrics**:
  - Model Accuracy
  - Inference Latency
  - False Positive/Negative Rates

## Common Tasks

### 1. Check System Health

```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs -f

# Check metrics
curl http://localhost:9090/api/v1/targets
```

### 2. Manual Backup

```bash
# Run backup
python scripts/maintenance.py

# Verify backup
ls -l backups/
```

### 3. View Recent Alerts

```bash
# Check Prometheus alerts
curl http://localhost:9090/api/v1/alerts

# Or visit Prometheus UI
# http://localhost:9090/alerts
```

## Troubleshooting Quick Reference

### 1. Service Not Starting

```bash
# Check logs
docker-compose logs <service-name>

# Restart service
docker-compose restart <service-name>
```

### 2. Metrics Not Showing

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check service health
curl http://localhost:8000/health
```

### 3. Grafana Dashboard Issues

```bash
# Check datasource
curl http://localhost:3000/api/datasources

# Restart Grafana
docker-compose restart grafana
```

## Daily Checklist

1. **Morning Check**
   - [ ] Review overnight alerts
   - [ ] Check system metrics
   - [ ] Verify backup completion

2. **During Day**
   - [ ] Monitor error rates
   - [ ] Check model performance
   - [ ] Review resource usage

3. **End of Day**
   - [ ] Review daily metrics
   - [ ] Check backup status
   - [ ] Verify alert thresholds

## Important Files

```
.
├── config/
│   └── monitoring_config.yaml    # Monitoring configuration
├── monitoring/
│   ├── prometheus/              # Prometheus config
│   └── grafana/                 # Grafana config
├── scripts/
│   ├── setup_monitoring.py      # Setup script
│   └── maintenance.py           # Maintenance script
└── docker-compose.yml           # Service definitions
```

## Quick Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Run maintenance
python scripts/maintenance.py

# Check service health
curl http://localhost:8000/health

# View metrics
curl http://localhost:9090/metrics
```

## Next Steps

1. **Customize Alerts**
   - Review `config/monitoring_config.yaml`
   - Adjust thresholds as needed
   - Add team-specific alerts

2. **Set Up Notifications**
   - Configure email/Slack notifications
   - Set up alert routing
   - Define escalation policies

3. **Create Custom Dashboards**
   - Clone existing dashboards
   - Add team-specific metrics
   - Share with team members

## Support

- **Documentation**: `docs/monitoring_and_maintenance.md`
- **Logs**: `logs/` directory
- **Issues**: GitHub repository issues

## Security Notes

1. **Immediate Actions**
   - Change default passwords
   - Restrict access to monitoring ports
   - Enable authentication

2. **Regular Tasks**
   - Rotate credentials
   - Review access logs
   - Update security patches

## Best Practices

1. **Monitoring**
   - Set up meaningful alerts
   - Regular threshold review
   - Document custom metrics

2. **Maintenance**
   - Schedule during off-hours
   - Verify backups
   - Monitor disk space

3. **Security**
   - Use strong passwords
   - Regular access review
   - Keep services updated 