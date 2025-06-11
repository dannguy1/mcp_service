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
├── docker-compose.yml     # Production compose file
└── docker-compose.dev.yml # Development compose file
```

## Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker and Docker Compose
- Redis

### Local Development

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

### Docker Development

```bash
docker compose -f docker-compose.dev.yml up
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

## Deployment

1. Build the containers:
```bash
docker compose build
```

2. Start the services:
```bash
docker compose up -d
```

## Documentation

- [Architecture](docs/architecture.md)
- [API Documentation](docs/api.md)
- [Development Guide](docs/development.md)
- [Deployment Guide](docs/deployment.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 