# Model Server Deployment Guide

This guide provides instructions for deploying the WiFi Anomaly Detection Model Server in production.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Redis 6 or higher
- Prometheus (optional, for monitoring)
- Docker (optional, for containerized deployment)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/mcp_service.git
   cd mcp_service
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Configuration

1. Model Configuration (`config/model_config.yaml`):
   - Adjust model parameters
   - Configure feature engineering
   - Set training parameters
   - Configure model storage

2. Server Configuration (`config/server_config.yaml`):
   - Set server host and port
   - Configure worker processes
   - Set up monitoring
   - Configure security settings
   - Set database and Redis connections

## Database Setup

1. Create the database:
   ```sql
   CREATE DATABASE mcp_service;
   ```

2. Create the user:
   ```sql
   CREATE USER mcp_service WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE mcp_service TO mcp_service;
   ```

3. Initialize the database:
   ```bash
   python scripts/init_db.py
   ```

## Running the Server

### Development Mode

```bash
python scripts/run_model_server.py --reload
```

### Production Mode

1. Using systemd (recommended):
   ```bash
   sudo cp systemd/wifi-agent.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable wifi-agent
   sudo systemctl start wifi-agent
   ```

2. Using Docker:
   ```bash
   docker build -t mcp_service .
   docker run -d --name mcp_service \
     -p 8000:8000 \
     -v $(pwd)/models:/app/models \
     -v $(pwd)/config:/app/config \
     mcp_service
   ```

## Monitoring

### Prometheus Setup

1. Install Prometheus:
   ```bash
   # Follow Prometheus installation guide for your OS
   ```

2. Configure Prometheus to scrape metrics:
   ```yaml
   scrape_configs:
     - job_name: 'mcp_service'
       static_configs:
         - targets: ['localhost:8000']
   ```

### Grafana Dashboard

1. Install Grafana:
   ```bash
   # Follow Grafana installation guide for your OS
   ```

2. Import the provided dashboard:
   - Use the dashboard JSON from `monitoring/grafana_dashboard.json`
   - Configure the Prometheus data source

## Model Training

### Manual Training

```bash
python scripts/train_model.py \
  --config config/model_config.yaml \
  --days 30 \
  --model-dir models
```

### Automated Training

1. Set up a cron job for regular training:
   ```bash
   # Add to crontab
   0 0 * * * /path/to/venv/bin/python /path/to/scripts/train_model.py
   ```

2. Or use the training API endpoint:
   ```bash
   curl -X POST http://localhost:8000/train \
     -H "Content-Type: application/json" \
     -d '{"start_date": "2024-01-01", "end_date": "2024-01-31"}'
   ```

## Security Considerations

1. Enable authentication:
   - Set `security.authentication.enabled: true` in `server_config.yaml`
   - Generate and configure API tokens

2. Configure CORS:
   - Update `security.cors_origins` in `server_config.yaml`
   - Restrict to trusted domains

3. Set up rate limiting:
   - Adjust `security.rate_limit.requests_per_minute` in `server_config.yaml`

## Backup and Recovery

1. Database backups:
   ```bash
   pg_dump -U mcp_service mcp_service > backup.sql
   ```

2. Model backups:
   ```bash
   tar -czf models_backup.tar.gz models/
   ```

3. Configuration backups:
   ```bash
   tar -czf config_backup.tar.gz config/
   ```

## Troubleshooting

### Common Issues

1. Database Connection:
   - Check PostgreSQL service status
   - Verify connection parameters in `.env`
   - Check network connectivity

2. Model Loading:
   - Verify model files exist
   - Check model version compatibility
   - Review model loading logs

3. Performance Issues:
   - Monitor system resources
   - Check worker count
   - Review prediction latency metrics

### Logs

- Application logs: `logs/model_server.log`
- System logs: `journalctl -u wifi-agent`
- Docker logs: `docker logs mcp_service`

## Maintenance

1. Regular tasks:
   - Monitor model performance
   - Check for data drift
   - Review and clean up old model versions
   - Update dependencies

2. Backup schedule:
   - Daily database backups
   - Weekly model backups
   - Monthly configuration backups

## Support

For issues and support:
- Create an issue on GitHub
- Contact the development team
- Check the troubleshooting guide 