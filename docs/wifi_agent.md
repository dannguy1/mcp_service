# WiFi Anomaly Detection Agent

The WiFi agent is a core component of the MCP Service that monitors WiFi network logs, detects anomalies, and generates alerts. It uses machine learning models to identify potential issues in the network and provides real-time monitoring and alerting capabilities.

## Features

- Real-time WiFi log analysis
- Anomaly detection using machine learning
- Automatic alert generation
- Resource monitoring
- Prometheus metrics integration
- Configurable thresholds and parameters
- Active device tracking

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- Prometheus (optional, for metrics)

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Initialize the database:
   ```bash
   python init_db.py
   ```

## Configuration

The agent is configured using a YAML file (`config/agent_config.yaml`). Key configuration options include:

- `processing_interval`: Time between processing cycles (seconds)
- `batch_size`: Number of logs to process in each cycle
- `lookback_window`: Time window for historical analysis (minutes)
- `model_path`: Path to the anomaly detection model
- Database and Redis connection settings
- Alert thresholds
- Resource monitoring settings

## Usage

### Running as a Service

1. Copy the systemd service file:
   ```bash
   sudo cp systemd/wifi-agent.service /etc/systemd/system/
   ```

2. Edit the service file with your configuration:
   ```bash
   sudo nano /etc/systemd/system/wifi-agent.service
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl enable wifi-agent
   sudo systemctl start wifi-agent
   ```

### Running Manually

```bash
python cli.py --config config/agent_config.yaml --log-level INFO
```

## Monitoring

### Prometheus Metrics

The agent exposes the following metrics:

- `wifi_agent_logs_processed_total`: Total number of logs processed
- `wifi_agent_anomalies_detected_total`: Number of anomalies detected (by severity and type)
- `wifi_agent_alerts_generated_total`: Number of alerts generated (by severity)
- `wifi_agent_processing_duration_seconds`: Time spent processing logs
- `wifi_agent_active_devices`: Number of active WiFi devices

### Logs

Logs are written to the configured log file (default: `logs/wifi_agent.log`) and include:
- Agent startup and shutdown events
- Processing cycle information
- Anomaly detection results
- Alert generation details
- Error messages and exceptions

## Alert Types

The agent detects and classifies the following types of anomalies:

1. Signal Strength Anomalies
   - Weak signal strength
   - Signal strength fluctuations
   - Interference patterns

2. Performance Anomalies
   - High packet loss rates
   - Excessive retry counts
   - Low data rates

3. Channel Anomalies
   - Channel congestion
   - Channel switching issues
   - Co-channel interference

## Development

### Running Tests

```bash
./run_tests.py
```

### Code Structure

- `agents/wifi_agent.py`: Main agent implementation
- `components/`: Core components used by the agent
- `tests/unit/test_wifi_agent.py`: Unit tests
- `cli.py`: Command-line interface
- `config/agent_config.yaml`: Configuration file

## Troubleshooting

### Common Issues

1. Database Connection Issues
   - Verify PostgreSQL is running
   - Check database credentials
   - Ensure database schema is initialized

2. Redis Connection Issues
   - Verify Redis is running
   - Check Redis credentials
   - Ensure Redis is accessible

3. Model Loading Issues
   - Verify model file exists
   - Check model file permissions
   - Ensure model is compatible

### Logs and Debugging

- Check the agent's log file for detailed error messages
- Enable DEBUG logging level for more verbose output
- Monitor system resources using the resource monitor

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 