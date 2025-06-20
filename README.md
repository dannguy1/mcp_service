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

## Development Setup

### Prerequisites
- Docker and Docker Compose

### Development Environment

The project uses Docker Compose for development. All services (backend, frontend, Redis, Prometheus, and Grafana) are containerized.

1. Start all services:
```bash
docker compose up
```

This will start:
- Frontend on http://localhost:3000
- Backend API on http://localhost:8000
- Grafana on http://localhost:3001
- Prometheus on http://localhost:9090
- Redis on port 6379

The frontend container includes hot-reloading, so any changes to the frontend code will be immediately reflected in the browser.

### Manual Development (Alternative)

If you prefer to run services manually:

1. Start Redis:
```bash
./scripts/start_redis.sh
```

2. Start Backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask run --host=0.0.0.0 --port=5000
```

3. Start Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Documentation

- [Architecture](docs/architecture.md)
- [API Documentation](docs/api.md)
- [Development Guide](docs/development.md)
- [Deployment Guide](docs/deployment.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 