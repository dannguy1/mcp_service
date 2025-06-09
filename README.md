# MCP Service

A service for monitoring and analyzing WiFi logs using machine learning.

## Data Source Configuration

The service connects to a PostgreSQL database for log data. Configure the data source in one of these locations:

1. **Primary Configuration** (`config/data_source_config.yaml`):
```yaml
database:
  url: "postgresql://netmonitor_user:netmonitor_password@192.168.10.14:5432/netmonitor_db"
  pool_size: 5
  max_overflow: 10
  timeout: 30
```

2. **Environment Variable**:
```bash
export DATABASE_URL="postgresql://netmonitor_user:netmonitor_password@192.168.10.14:5432/netmonitor_db"
```

### Required Database Schema

The service expects the following tables:

1. **log_entries** (Required):
   - `device_id` (character varying)
   - `message` (text)
   - `raw_message` (text)
   - `timestamp` (timestamp without time zone)

2. **anomaly_records** (Optional):
   - `device_id` (character varying)
   - `anomaly_type` (character varying)
   - `severity` (integer)
   - `details` (jsonb)
   - `timestamp` (timestamp without time zone)

## Verifying Data Source

To verify the data source configuration and connectivity:

1. **Run the Verification Script**:
```bash
python3 scripts/verify_data_source.py
```

This script will:
- Test database connectivity
- Verify schema and required tables
- Check data access and quality
- Test query performance
- Generate a test report

2. **Check Test Results**:
The verification script creates a `test_results` directory containing:
- `log_entries_sample.csv`: Sample of log entries
- `log_patterns.json`: Analyzed patterns
- `mock_anomaly.json`: Generated mock anomaly

3. **View Logs**:
- Check `test_data_access.log` for detailed verification results
- Look for any warnings or errors in the verification process

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mcp_service
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the data source (see above)

4. Verify the setup:
```bash
python3 scripts/verify_data_source.py
```

## Usage

1. Start the service:
```bash
python mcp_service.py
```

2. Monitor logs:
```bash
tail -f logs/mcp_service.log
```

## Development

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
python run_tests.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 