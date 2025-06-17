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