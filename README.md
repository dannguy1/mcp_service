# WiFi Network Monitoring Service

A real-time WiFi network monitoring service that analyzes logs, detects anomalies, and generates alerts using machine learning.

## Features

- Real-time log analysis and anomaly detection
- Machine learning-based anomaly classification
- Automatic alert generation and management
- Resource monitoring and health checks
- Prometheus metrics integration
- Configurable thresholds and parameters
- Active device tracking

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Prometheus (optional, for metrics)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wifi-monitoring-service.git
cd wifi-monitoring-service
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

5. Initialize the database:
```bash
python init_db.py
```

## Configuration

The service is configured through environment variables and YAML configuration files:

- `.env`: Database credentials and sensitive information
- `config/agent_config.yaml`: Agent settings and thresholds
- `config/model_config.yaml`: Model parameters and paths

## Usage

### Running as a Service

1. Install the systemd service:
```bash
sudo cp systemd/wifi-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wifi-agent
sudo systemctl start wifi-agent
```

2. Check service status:
```bash
sudo systemctl status wifi-agent
```

### Running Manually

```bash
python cli.py --config config/agent_config.yaml
```

### Health Checks

The service exposes several endpoints for monitoring:

- `http://localhost:8080/health`: Service health status
- `http://localhost:8080/metrics`: Prometheus metrics
- `http://localhost:8080/status`: Service status and configuration

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

The project follows PEP 8 style guidelines. Use `black` for code formatting:

```bash
black .
```

## Project Structure

```
.
├── agents/              # Agent implementations
├── components/          # Core components
├── config/             # Configuration files
├── models/             # ML models and utilities
├── systemd/            # Service files
├── tests/              # Test suite
├── cli.py              # Command-line interface
├── data_service.py     # Database and cache service
├── init_db.py          # Database initialization
└── requirements.txt    # Python dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 