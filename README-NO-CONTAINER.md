# MCP Service - No Container Setup

This guide provides instructions for running the MCP Service without Docker containers, suitable for development and low-performance devices.

## Overview

The no-container setup allows you to run all MCP Service components directly on your host system, providing:
- Lower resource usage compared to containers
- Easier debugging and development
- Better performance on low-end devices
- Direct access to system resources

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 10GB free space
- OS: Linux (Ubuntu 20.04+ recommended)

**Recommended Requirements:**
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 20GB+ free space
- OS: Linux (Ubuntu 22.04+)

### Required Software

1. **Python 3.8+**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   ```

2. **Node.js 16+**
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

3. **Redis**
   ```bash
   sudo apt install redis-server
   ```

4. **Prometheus** (optional)
   ```bash
   wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
   tar xvf prometheus-*.tar.gz
   sudo mv prometheus-* /opt/prometheus
   sudo ln -s /opt/prometheus/prometheus /usr/local/bin/prometheus
   ```

5. **Grafana** (optional)
   ```bash
   sudo apt-get install -y software-properties-common
   sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
   wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
   sudo apt update
   sudo apt install grafana
   ```

## Quick Start

### 1. Setup Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd mcp_service

# Run the setup script
./scripts/setup_dev_env.sh
```

### 2. Start All Services

```bash
# Start all services in background mode
./scripts/start_all.sh -b

# Or start in foreground mode (for debugging)
./scripts/start_all.sh
```

### 3. Verify Installation

```bash
# Check service health
./scripts/health_check.sh

# Check port availability
./scripts/check_ports.sh
```

### 4. Access Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **MCP Service**: http://localhost:5555
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001

## Low-Performance Device Setup

For devices with limited resources (2GB RAM, 2 CPU cores), use the optimized setup:

### 1. Run Optimization Script

```bash
# Analyze system and create optimized configurations
python3 scripts/optimize_for_low_performance.py
```

### 2. Start with Optimizations

```bash
# Start with low-performance optimizations
./scripts/start_optimized.sh
```

### 3. Monitor Resources

```bash
# Monitor system resources
./scripts/monitor_resources.sh
```

## Service Management

### Starting Services

```bash
# Start all services
./scripts/start_all.sh

# Start individual services
./scripts/start_backend.sh
./scripts/start_mcp_service.sh
./scripts/start_frontend.sh

# Start with custom ports
./scripts/start_all.sh --backend-port 5001 --mcp-port 5556
```

### Stopping Services

```bash
# Stop all services
./scripts/stop_all.sh

# Stop individual services (using Ctrl+C in foreground mode)
```

### Checking Service Status

```bash
# Comprehensive health check
./scripts/health_check.sh

# Check specific service
./scripts/health_check.sh http://localhost:5000 http://localhost:5555
```

## Configuration

### Environment Variables

The setup creates several environment files:

- `.env` - Standard configuration
- `.env.low_performance` - Optimized for low-performance devices

Key configuration options:

```bash
# Database Configuration
DB_HOST=192.168.10.14
DB_PORT=5432
DB_NAME=netmonitor_db
DB_USER=netmonitor_user
DB_PASSWORD=netmonitor_password

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=5555
LOG_LEVEL=INFO

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Resource Limits (for low-performance)
MAX_WORKERS=2
MEMORY_LIMIT=512
CPU_LIMIT=1
```

### Database Configuration

The system supports both PostgreSQL and SQLite:

**PostgreSQL (Production):**
- Configured to connect to external database
- Used for anomaly storage and analysis

**SQLite (Development/Low-performance):**
- Local database for development
- Optimized for low-resource environments

### Monitoring Configuration

**Prometheus:**
- Metrics collection endpoint: `/metrics`
- Scrape interval: 30s (standard) / 120s (low-performance)
- Data retention: 15 days (standard) / 3 days (low-performance)

**Grafana:**
- Default dashboard for MCP Service metrics
- Resource usage monitoring
- Anomaly detection visualization

## Development

### Project Structure

```
mcp_service/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── core/           # Core MCP service
│   │   ├── services/       # Business logic
│   │   └── models/         # Data models
├── frontend/               # React frontend
├── scripts/                # Management scripts
├── data/                   # Data storage
│   ├── sqlite/            # SQLite databases
│   ├── redis/             # Redis configuration
│   └── prometheus/        # Prometheus data
└── logs/                  # Application logs
```

### Development Workflow

1. **Setup Development Environment:**
   ```bash
   ./scripts/setup_dev_env.sh
   ```

2. **Start Services:**
   ```bash
   ./scripts/start_all.sh
   ```

3. **Make Changes:**
   - Backend: Edit files in `backend/app/`
   - Frontend: Edit files in `frontend/src/`

4. **Test Changes:**
   ```bash
   ./scripts/health_check.sh
   ```

5. **Stop Services:**
   ```bash
   ./scripts/stop_all.sh
   ```

### Debugging

**Backend Debugging:**
```bash
# Start backend in debug mode
cd backend
source ../venv/bin/activate
uvicorn app.main:app --reload --log-level debug
```

**Frontend Debugging:**
```bash
# Start frontend in debug mode
cd frontend
npm run dev -- --debug
```

**Log Analysis:**
```bash
# View all logs
tail -f logs/*.log

# View specific service logs
tail -f backend.log
tail -f mcp_service.log
```

## Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Check what's using the port
sudo lsof -i :5000

# Kill the process
sudo kill -9 <PID>
```

**2. Permission Denied**
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Fix ownership
sudo chown -R $USER:$USER .
```

**3. Service Won't Start**
```bash
# Check logs
tail -f *.log

# Check system resources
./scripts/monitor_resources.sh

# Restart services
./scripts/stop_all.sh
./scripts/start_all.sh
```

**4. Database Connection Issues**
```bash
# Test database connection
python3 scripts/test_db_connection.py

# Check database configuration
cat .env | grep DB_
```

**5. Low Memory Issues**
```bash
# Check available memory
free -h

# Start with low-performance optimizations
./scripts/start_optimized.sh

# Monitor resource usage
./scripts/monitor_resources.sh
```

### Performance Optimization

**For Low-Performance Devices:**

1. **Reduce Worker Count:**
   ```bash
   export MAX_WORKERS=1
   ```

2. **Limit Memory Usage:**
   ```bash
   export MEMORY_LIMIT=256
   ```

3. **Increase Scrape Intervals:**
   ```bash
   export METRICS_INTERVAL=120
   ```

4. **Disable Frontend (if not needed):**
   ```bash
   export ENABLE_FRONTEND=false
   ```

### Maintenance

**Regular Cleanup:**
```bash
# Clean up temporary files
./scripts/cleanup.sh

# Rotate logs
sudo logrotate logs/logrotate.conf
```

**Database Maintenance:**
```bash
# SQLite optimization
python3 scripts/optimize_for_low_performance.py

# PostgreSQL maintenance (if using)
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "VACUUM ANALYZE;"
```

## Security Considerations

### Network Security

- Services bind to `localhost` by default
- Use firewall rules for external access
- Configure SSL/TLS for production

### Data Security

- Database credentials in environment files
- Regular backup of SQLite databases
- Secure Redis configuration

### Access Control

- Implement authentication for API endpoints
- Use environment variables for secrets
- Regular security updates

## Monitoring and Logging

### Log Files

- `backend.log` - Backend application logs
- `mcp_service.log` - MCP service logs
- `frontend.log` - Frontend development logs
- `redis.log` - Redis server logs
- `prometheus.log` - Prometheus logs
- `grafana.log` - Grafana logs

### Metrics

Key metrics available:
- Service health status
- Request/response times
- Error rates
- Resource usage (CPU, memory, disk)
- Database connection status

### Alerts

Configure alerts for:
- Service downtime
- High resource usage
- Database connection failures
- Error rate thresholds

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review log files for errors
3. Run health checks
4. Check system resources
5. Consult the main README.md

## Contributing

When contributing to the no-container setup:

1. Test on both standard and low-performance devices
2. Update documentation for new features
3. Ensure scripts work across different Linux distributions
4. Add appropriate error handling and logging
5. Test cleanup and recovery procedures 