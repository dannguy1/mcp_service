# Modular AI Processing Service

A modular, extensible AI processing service for analyzing OpenWRT network logs and detecting anomalies. The service operates independently from the log collector, fetches logs from a PostgreSQL database, and stores anomalies in a local SQLite database.

## Features

- **Modular Architecture**: Plug-and-play agent system for different types of analysis
- **Efficient Resource Usage**: Optimized for Raspberry Pi 5 (4-8GB RAM)
- **Local Storage**: SQLite database for anomaly storage
- **Remote Operation**: Support for remote PostgreSQL database access
- **Health Monitoring**: Resource usage monitoring and health check endpoint
- **Extensible**: Easy to add new analysis agents

## Components

- **DataService**: Centralized data access layer for PostgreSQL and SQLite
- **BaseAgent**: Abstract base class for all analysis agents
- **WiFiAgent**: Agent for WiFi anomaly detection
- **FeatureExtractor**: Extracts features from logs
- **ModelManager**: Manages ML models
- **AnomalyClassifier**: Classifies anomalies using ML models
- **ResourceMonitor**: Monitors system resources

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mcp_service.git
   cd mcp_service
   ```

2. Create a virtual environment:
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

4. Initialize the SQLite database:
   ```bash
   python -m mcp_service.init_local_db
   ```

## Configuration

The service is configured using environment variables:

```ini
# Database Configuration (PostgreSQL - Read Only)
DB_HOST=192.168.10.14
DB_PORT=5432
DB_NAME=netmonitor_db
DB_USER=netmonitor_user
DB_PASSWORD=netmonitor_password

# SQLite Configuration
SQLITE_DB_PATH=/app/data/mcp_anomalies.db
SQLITE_JOURNAL_MODE=WAL
SQLITE_SYNCHRONOUS=NORMAL
SQLITE_CACHE_SIZE=-2000
SQLITE_TEMP_STORE=MEMORY
SQLITE_MMAP_SIZE=30000000000

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=5555
LOG_LEVEL=INFO
ANALYSIS_INTERVAL=300
```

## Usage

1. Start the service:
   ```bash
   python -m mcp_service.mcp_service
   ```

2. The service will:
   - Connect to PostgreSQL and SQLite databases
   - Start the WiFi agent
   - Begin monitoring logs for anomalies
   - Expose health check endpoint at `/health`
   - Expose anomalies API at `/api/v1/anomalies`

## API Endpoints

### Health Check
```
GET /health
```
Returns the health status of the service and its components.

### Get Anomalies
```
GET /api/v1/anomalies?limit=100&offset=0&agent_name=WiFiAgent&status=new&resolution_status=open
```
Returns a list of anomalies with optional filtering.

### Update Anomaly Status
```
POST /api/v1/anomalies/{anomaly_id}/status
{
    "status": "acknowledged",
    "resolution_status": "resolved",
    "resolution_notes": "Fixed by restarting the access point"
}
```
Updates the status and resolution of an anomaly.

## Development

### Adding a New Agent

1. Create a new agent class that inherits from `BaseAgent`:
   ```python
   from mcp_service.agents.base_agent import BaseAgent

   class NewAgent(BaseAgent):
       def __init__(self, config, data_service):
           super().__init__(config, data_service)
           # Initialize agent-specific components

       async def start(self):
           # Start agent-specific components
           pass

       async def stop(self):
           # Stop agent-specific components
           pass

       async def run_analysis_cycle(self):
           # Implement analysis logic
           pass
   ```

2. Add the agent to the main service:
   ```python
   from mcp_service.agents.new_agent import NewAgent

   class MCPService:
       def __init__(self):
           # ...
           self.new_agent = NewAgent(self.config, self.data_service)
   ```

### Running Tests

```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 