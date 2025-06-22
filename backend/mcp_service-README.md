# MCP Service - Environment Configuration Guide

## Overview
The MCP (Model Control Protocol) Service is a core component that manages WiFi anomaly detection agents, model management, and resource monitoring. It uses the same `.env` file as the main backend for configuration, ensuring consistency across all components.

## Architecture
- **`mcp_service.py`**: Main service that orchestrates WiFi agents and model management
- **`cli.py`**: Command-line interface for running individual agents
- **`start_mcp_service.sh`**: Shell script to start the MCP service with proper environment setup

## Environment Variable Configuration

### How It Works
1. **Single Source of Truth**: All MCP service configuration comes from the same `.env` file used by the main backend
2. **Automatic Loading**: Both Python code and shell scripts automatically load variables from `.env`
3. **Consistent Configuration**: No more YAML config files or duplicated settings

### Key Environment Variables

#### Core Service Configuration
```bash
ENVIRONMENT=development
LOG_LEVEL=info
ANALYSIS_INTERVAL=300
```

#### Agent Configuration
```bash
AGENT_PROCESSING_INTERVAL=60      # seconds between processing cycles
AGENT_BATCH_SIZE=1000             # number of logs to process in each cycle
AGENT_LOOKBACK_WINDOW=30          # minutes of historical data to consider
```

#### Threshold Configuration
```bash
THRESHOLD_SIGNAL_STRENGTH=-70     # dBm
THRESHOLD_PACKET_LOSS_RATE=0.1    # 10%
THRESHOLD_RETRY_RATE=0.2          # 20%
THRESHOLD_DATA_RATE=24            # Mbps
```

#### Resource Monitoring
```bash
RESOURCE_MONITORING_ENABLED=true
RESOURCE_CHECK_INTERVAL=60        # seconds
RESOURCE_THRESHOLD_CPU=80         # percentage
RESOURCE_THRESHOLD_MEMORY=85      # percentage
RESOURCE_THRESHOLD_DISK=90        # percentage
RESOURCE_THRESHOLD_NETWORK=1000000 # bytes per second
```

#### Database & Redis (shared with backend)
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=netmonitor_db
DB_USER=netmonitor_user
DB_PASSWORD=netmonitor_password

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## How to Use

### Starting the MCP Service
```bash
# Start the full MCP service (recommended)
./scripts/start_mcp_service.sh

# Or start in background
./scripts/start_mcp_service.sh &
```

### Using the CLI for Individual Agents
```bash
# Run WiFi agent with environment variables
cd backend
python3 app/core/cli.py --log-level DEBUG
```

### Environment Setup
1. **Copy the template** (if not already done):
   ```bash
   cp backend/example.env backend/.env
   ```

2. **Edit configuration**:
   ```bash
   # Edit backend/.env to customize settings
   nano backend/.env
   ```

3. **Start the service**:
   ```bash
   ./scripts/start_mcp_service.sh
   ```

## Configuration Migration

### From YAML to Environment Variables
The MCP service previously used YAML configuration files. These have been replaced with environment variables:

| Old YAML Setting | New Environment Variable |
|------------------|--------------------------|
| `processing_interval` | `AGENT_PROCESSING_INTERVAL` |
| `batch_size` | `AGENT_BATCH_SIZE` |
| `lookback_window` | `AGENT_LOOKBACK_WINDOW` |
| `thresholds.signal_strength` | `THRESHOLD_SIGNAL_STRENGTH` |
| `resource_monitoring.enabled` | `RESOURCE_MONITORING_ENABLED` |

### Benefits of Environment Variables
- **Single source of truth**: All config in one `.env` file
- **Easy deployment**: Different environments can use different `.env` files
- **Security**: Sensitive values can be managed separately
- **Consistency**: Same approach as the main backend

## Troubleshooting

### Common Issues
1. **Service won't start**: Check that `.env` file exists and is properly formatted
2. **Agent errors**: Verify database and Redis connection settings in `.env`
3. **Resource monitoring disabled**: Set `RESOURCE_MONITORING_ENABLED=true`

### Debug Mode
```bash
# Start with debug logging
LOG_LEVEL=DEBUG ./scripts/start_mcp_service.sh
```

### Checking Service Status
```bash
# Check if MCP service is running
ps aux | grep mcp_service

# Check logs
tail -f backend/backend.log
```

## Integration with Main Backend

The MCP service integrates seamlessly with the main backend:

- **Shared Configuration**: Uses the same `.env` file
- **Shared Database**: Connects to the same PostgreSQL database
- **Shared Redis**: Uses the same Redis instance for caching and status
- **Unified Logging**: All logs go to the same location

## Security Considerations

- **Never commit `.env` with real secrets** to version control
- **Use different `.env` files** for development, staging, and production
- **Rotate sensitive credentials** regularly
- **Monitor resource usage** to prevent service overload

---

For more details, see the main backend README and the code comments in the MCP service files. 