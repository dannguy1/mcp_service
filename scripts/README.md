# Scripts Directory

This directory contains the essential scripts for running the MCP service environment.

## Scripts Overview

### Main Script
- **`start_all.sh`** - Complete startup script that runs all services in the correct order

### Individual Service Scripts
- **`start_redis.sh`** - Start Redis server (required for caching and sessions)
- **`start_backend.sh`** - Start the FastAPI backend server
- **`start_mcp_service.sh`** - Start the MCP service (WiFi anomaly detection)
- **`start_frontend.sh`** - Start the React frontend development server

## Quick Start

### Start Everything (Recommended)
```bash
# Start all services in foreground mode
./scripts/start_all.sh

# Start all services in background mode
./scripts/start_all.sh -b

# Start without frontend (API-only mode)
./scripts/start_all.sh --skip-frontend

# Start without MCP service (UI-only mode)
./scripts/start_all.sh --skip-mcp
```

### Start Individual Services
```bash
# Start Redis
./scripts/start_redis.sh

# Start Backend
./scripts/start_backend.sh

# Start MCP Service
./scripts/start_mcp_service.sh

# Start Frontend
./scripts/start_frontend.sh
```

## Automatic Environment Setup

All scripts automatically handle environment setup:

- **Backend/MCP**: Creates Python virtual environment and installs dependencies if needed
- **Frontend**: Installs Node.js dependencies if needed
- **Environment Variables**: Loads from `.env` files automatically

No manual setup required - just run the scripts!

## Service Ports

- **Redis**: 6379
- **Backend API**: 5000
- **Frontend**: 3000
- **MCP Service**: Internal (no external port)

## Background Mode

All scripts support background mode with the `-b` or `--background` flag:

```bash
# Start individual service in background
./scripts/start_backend.sh -b

# Start all services in background
./scripts/start_all.sh -b
```

When running in background mode:
- Services write logs to `.log` files
- PIDs are saved to `.pid` files
- Instructions for stopping services are displayed

## Stopping Services

### Background Services
```bash
# Stop by PID file
kill $(cat backend.pid)
kill $(cat frontend.pid)
kill $(cat mcp_service.pid)

# Stop Redis
redis-cli shutdown
```

### All Services (if started with start_all.sh)
Press `Ctrl+C` to stop all services gracefully.

## Logs

When running in background mode, logs are written to:
- `backend.log` - Backend API logs
- `frontend.log` - Frontend development server logs
- `mcp_service.log` - MCP service logs

View logs with:
```bash
tail -f backend.log
tail -f frontend.log
tail -f mcp_service.log
```

## Environment Variables

All scripts automatically load environment variables from:
1. `.env` file in the project root
2. `backend/.env` file
3. `frontend/.env` file

See the individual service READMEs for configuration details:
- `backend/backend-README.md`
- `backend/mcp_service-README.md`
- `frontend/frontend-README.md`

## Troubleshooting

### Port Already in Use
If a port is already in use, the script will warn you. Stop the conflicting service:
```bash
# Find what's using a port
lsof -i :5000

# Kill the process
kill <PID>
```

### Service Won't Start
1. Check that all dependencies are installed
2. Verify environment variables are set correctly
3. Check the log files for error messages
4. Ensure Redis is running (required for backend and MCP service)

### Redis Not Found
Install Redis if not already installed:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis
```

## Development Workflow

1. **Start**: Use `./scripts/start_all.sh` for development
2. **Develop**: Make changes and see live updates
3. **Stop**: Press `Ctrl+C` to stop all services

## Removed Scripts

The following scripts were removed to keep the project clean:
- `setup_monitoring.py` - Prometheus/Grafana setup (not needed)
- `run_model_server.py` - Redundant with backend
- `run_web_ui.py` - Redundant with frontend
- `monitor_model.py` - Monitoring related
- `maintenance.py` - Maintenance scripts
- `train_model.py` - Training scripts
- `verify_data_source.py` - Data source verification
- `test_db_connection.py` - Testing script
- `start_dev.sh` - Replaced by `start_all.sh`
- `setup_dev_env.sh` - Redundant (setup is automatic in individual scripts)

These scripts can be restored from git history if needed for specific use cases. 