# MCP Service

A Modular, Extensible AI Processing Service for network log analysis.

## Project Structure

```
.
├── backend/                 # Backend service
│   ├── app/                # Application code
│   │   ├── api/           # API endpoints
│   │   ├── agents/        # Analysis agents
│   │   ├── components/    # Shared components
│   │   ├── models/        # Model storage
│   │   ├── monitoring/    # Monitoring components
│   │   ├── scripts/       # Utility scripts
│   │   ├── services/      # Core services
│   │   └── utils/         # Utility functions
│   ├── tests/             # Test files
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend container config
├── frontend/               # Frontend application
│   ├── src/               # Source code
│   ├── public/            # Static assets
│   └── Dockerfile         # Frontend container config
├── docs/                   # Documentation
├── scripts/               # Project-wide scripts
└── docker-compose.yml     # Docker compose file
```

## Quick Start

### 1. Initial Setup
```bash
# Install system dependencies and Python environment
./scripts/setup_dev_env.sh
```

### 2. Start Services
```bash
# Start all services (development mode)
./scripts/start_dev.sh

# Or start optimized for low-performance devices
./scripts/start_optimized.sh
```

### 3. Access Applications
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Documentation**: http://localhost:5000/api/v1/docs
- **Health Check**: http://localhost:5000/api/v1/health

## Enhanced Startup Process

The development startup script (`start_dev.sh`) has been enhanced with the following improvements:

### Health Checks
- **Backend Health Check**: Waits for the backend API to be fully ready before starting the frontend
- **Frontend Health Check**: Verifies the frontend is accessible before completing startup
- **Service Dependencies**: Checks Redis and Node.js availability before starting services

### Port Management
- **Port Availability**: Checks if required ports (5000, 3000) are available before starting services
- **Process Cleanup**: Automatically stops existing processes using required ports
- **Background Mode**: Runs backend in background mode for better process management

### Error Handling
- **Graceful Failures**: Provides clear error messages and cleanup on startup failures
- **Dependency Checks**: Verifies all required dependencies are installed
- **Fallback Options**: Provides alternatives when optional dependencies (like curl) are missing

### Testing Startup
You can test the startup improvements:
```bash
# Run startup tests
./scripts/test_startup.sh
```

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Redis (installed via setup script)
- PostgreSQL client (installed via setup script)

### Environment Configuration

#### Backend Environment
Create `.env.low_performance` in the project root for optimized settings:
```env
# Database Configuration
SQLITE_DB_PATH=./backend/app/data/mcp_anomalies.db
REDIS_HOST=localhost
REDIS_PORT=6379

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=5555
LOG_LEVEL=WARNING

# Resource Limits
MAX_WORKERS=1
MEMORY_LIMIT=512

# Enable frontend
ENABLE_FRONTEND=true
```

#### Frontend Environment
The frontend uses environment variables for API configuration:
```env
# API Configuration
VITE_API_BASE_URL=http://localhost:5000/api/v1

# Feature Flags
VITE_ENABLE_WEBSOCKETS=true
VITE_ENABLE_ANALYTICS=true
```

### CORS Configuration

The backend is configured to allow CORS requests from multiple origins:
- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://192.168.10.8:3000`
- `http://192.168.10.10:3000`
- `http://192.168.10.149:3000`

You can customize this by setting the `FRONTEND_URL` environment variable.

### Manual Development

If you prefer to run services manually:

1. **Start Redis** (system service):
```bash
sudo systemctl start redis-server
```

2. **Start Backend**:
```bash
cd backend
source ../venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

3. **Start Frontend**:
```bash
cd frontend
npm install
npm run dev
```

## Service Management

### Start Services
```bash
# Development mode
./scripts/start_dev.sh

# Optimized mode (low-performance devices)
./scripts/start_optimized.sh
```

### Stop Services
```bash
# Stop application services only
./scripts/stop_all.sh

# Stop Redis (if needed)
sudo systemctl stop redis-server
```

### Verify Data Source
```bash
# Run data source verification
./scripts/run_verify_data_source.sh
```

## Testing

### Backend Tests
```bash
cd backend
source ../venv/bin/activate
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Troubleshooting

### Startup Issues

#### Multiple Startup Attempts Required
If the UI doesn't come up on the first try:
1. **Check the startup logs** for specific error messages
2. **Verify dependencies** are installed:
   ```bash
   ./scripts/test_startup.sh
   ```
3. **Check port availability**:
   ```bash
   lsof -i :5000  # Check backend port
   lsof -i :3000  # Check frontend port
   ```
4. **Restart Redis** if needed:
   ```bash
   sudo systemctl restart redis-server
   ```

#### Backend Health Check Failures
If the backend health check fails:
1. **Check backend logs**:
   ```bash
   tail -f backend/backend.log
   ```
2. **Verify database connection**:
   ```bash
   ./scripts/run_verify_data_source.sh
   ```
3. **Check Redis connection**:
   ```bash
   redis-cli ping
   ```

#### Frontend Health Check Failures
If the frontend health check fails:
1. **Check frontend logs** in the terminal where `npm run dev` is running
2. **Verify Node.js installation**:
   ```bash
   node --version
   npm --version
   ```
3. **Reinstall dependencies**:
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

### CORS Issues
If you encounter CORS errors:
1. Ensure the frontend URL is in the backend's CORS allowlist
2. Check that `VITE_API_BASE_URL` is correctly set in frontend/.env
3. Verify the backend is running on the expected port

### Redis Connection Issues
```bash
# Check Redis status
sudo systemctl status redis-server

# Test Redis connection
redis-cli ping
```

### API Connection Issues
```bash
# Test backend health
curl http://localhost:5000/api/v1/health

# Check API documentation
curl http://localhost:5000/api/v1/docs
```

## Documentation

- [Architecture](docs/architecture.md)
- [API Documentation](docs/api.md)
- [Development Guide](docs/development.md)
- [Deployment Guide](docs/deployment.md)
- [Troubleshooting](docs/troubleshooting.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 