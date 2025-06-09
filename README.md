# WiFi Anomaly Detection Model Server

A FastAPI-based server for serving WiFi anomaly detection models with monitoring and metrics.

## Features

- Model serving via REST API
- Real-time anomaly detection
- Model versioning and management
- Performance monitoring with Prometheus
- Visualization with Grafana
- Automatic model retraining
- Health checks and metrics
- Docker support

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- PostgreSQL 12+
- Redis 6+

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/your-org/mcp_service.git
cd mcp_service
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run with Docker Compose:
```bash
docker-compose up -d
```

The services will be available at:
- Model Server API: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/mcp_service)

## API Endpoints

- `GET /health`: Health check endpoint
- `POST /predict`: Make predictions
- `GET /models`: List available models
- `GET /models/{version}`: Get model information
- `POST /train`: Train a new model
- `GET /metrics`: Prometheus metrics

## Development

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
python run_tests.py
```

3. Run linters:
```bash
black .
flake8 .
isort .
mypy .
```

## Monitoring

The server exposes Prometheus metrics at `/metrics`. Key metrics include:

- `model_predictions_total`: Total number of predictions
- `model_anomalies_detected`: Number of anomalies detected
- `model_prediction_latency_seconds`: Prediction latency
- `model_feature_drift`: Feature drift metrics
- `model_data_quality`: Data quality metrics

## Deployment

See [deployment documentation](docs/deployment.md) for detailed instructions.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 