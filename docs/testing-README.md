# WiFi Anomaly Detection Testing Guide

This guide provides comprehensive information about testing the WiFi Anomaly Detection system, including test suites, configuration, and reporting.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Test Configuration](#test-configuration)
5. [Test Suites](#test-suites)
6. [Test Reports](#test-reports)
7. [Data Source Verification](#data-source-verification)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

Before running the tests, ensure you have:

1. Python 3.8+ installed
2. Required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Access to the model server (local or remote)
4. Sufficient disk space for test results (recommended: 1GB+)

## Test Structure

The test suite is organized as follows:

```
tests/
├── config/
│   └── test_config.yaml      # Test configuration
├── performance/
│   └── test_load.py         # Performance test suite
├── security/
│   └── test_api_security.py # Security test suite
├── utils/
│   ├── test_data_generator.py    # Test data generation
│   ├── report_generator.py       # Report generation
│   └── templates/
│       └── report_template.html  # HTML report template
└── run_tests.py             # Main test runner
```

## Running Tests

### Basic Usage

To run all test suites:

```bash
python tests/run_tests.py --base-url http://your-model-server:8000
```

Replace `http://your-model-server:8000` with your actual model server URL:
- Local server: `http://localhost:8000`
- Remote server: `http://192.168.10.8:8000`

### Command Line Options

```bash
python tests/run_tests.py --help
```

Available options:
- `--base-url`: URL of the model server to test
- `--output-dir`: Directory to save test results (default: "test_results")

### Example Commands

1. Test local server:
   ```bash
   python tests/run_tests.py --base-url http://localhost:8000
   ```

2. Test remote server with custom output directory:
   ```bash
   python tests/run_tests.py --base-url http://192.168.10.8:8000 --output-dir custom_results
   ```

## Test Configuration

The test configuration is managed in `tests/config/test_config.yaml`. Key settings include:

### Performance Test Settings
```yaml
performance:
  basic_load:
    requests: 1000
    concurrency: 50
  high_concurrency:
    requests: 5000
    concurrency: 200
  endurance:
    requests: 10000
    concurrency: 100
```

### Security Test Settings
```yaml
security:
  rate_limit:
    requests_per_minute: 100
    burst_limit: 150
  authentication:
    valid_api_key: "your-api-key-here"
```

### Test Metrics Thresholds
```yaml
metrics:
  performance:
    max_latency_ms: 500
    min_success_rate: 0.95
  security:
    min_auth_success_rate: 1.0
```

## Test Suites

### 1. Performance Tests
- Basic load testing
- High concurrency testing
- Endurance testing
- Mixed workload testing

Metrics collected:
- Response latency
- Throughput
- Success rate
- Error rate

### 2. Security Tests
- Authentication testing
- Rate limiting
- Input validation
- CORS testing
- SQL injection prevention
- XSS prevention

## Test Reports

Test results are saved in the specified output directory with the following structure:

```
test_results/
└── YYYYMMDD_HHMMSS/
    ├── performance/
    │   ├── metrics.json
    │   ├── latency_distribution.png
    │   └── throughput.png
    ├── security/
    │   └── security_results.json
    ├── test_results.json
    ├── test_results.csv
    └── test_report.html
```

### Report Types

1. **HTML Report**
   - Comprehensive test summary
   - Performance metrics and plots
   - Security test results
   - Detailed test status

2. **CSV Report**
   - Raw test data
   - Suitable for further analysis

3. **JSON Results**
   - Detailed test results
   - Machine-readable format

## Data Source Verification

Before running the model server, it's crucial to verify connectivity and data access with the external data source. The system includes a verification script to ensure all requirements are met.

### Configuration

The data source configuration is managed in `config/data_source_config.yaml`:

```yaml
database:
  host: "localhost"  # Replace with your data source host
  port: 5432        # Replace with your data source port
  name: "wifi_logs" # Replace with your database name
  user: "reader"    # Replace with your read-only user
  password: ""      # Replace with your password or use environment variable

query:
  batch_size: 1000
  max_retries: 3
  timeout: 30
  pool_size: 5

validation:
  required_columns:
    - timestamp
    - device_id
    - signal_strength
    - latency
    - packet_loss
    - connection_duration
```

### Running Verification

To verify data source connectivity:

```bash
# Basic verification
python scripts/verify_data_source.py

# With custom configuration
python scripts/verify_data_source.py --config custom_config.yaml

# With specific parameters
python scripts/verify_data_source.py --hours 48 --sample-size 2000
```

### Verification Steps

The script performs the following checks:

1. **Connection Verification**
   - Establishes connection to the database
   - Verifies credentials and permissions
   - Tests connection pool settings

2. **Schema Verification**
   - Checks for required tables
   - Validates column existence
   - Verifies data types
   - Ensures indexes are present

3. **Data Access Verification**
   - Confirms access to recent data
   - Verifies data freshness
   - Checks data volume
   - Validates data quality

4. **Performance Verification**
   - Tests query execution time
   - Measures data retrieval speed
   - Verifies connection pool performance
   - Checks resource utilization

### Expected Output

Successful verification will show:
```
INFO - Starting data source verification...
INFO - Successfully connected to the data source database
INFO - Database schema verification successful
INFO - Found X records
INFO - Data range: YYYY-MM-DD HH:MM:SS to YYYY-MM-DD HH:MM:SS
INFO - Query execution plan: [details]
INFO - All verification steps completed successfully
```

### Common Issues

1. **Connection Failures**
   - Check database host and port
   - Verify credentials
   - Ensure network connectivity
   - Check firewall settings

2. **Schema Issues**
   - Verify table names
   - Check column names and types
   - Ensure required indexes exist
   - Validate permissions

3. **Data Access Problems**
   - Check data freshness
   - Verify data volume
   - Ensure data quality
   - Validate permissions

4. **Performance Issues**
   - Check query execution time
   - Verify connection pool settings
   - Monitor resource usage
   - Optimize indexes if needed

### Best Practices

1. **Configuration**
   - Use environment variables for sensitive data
   - Keep configuration files in version control
   - Document all configuration options
   - Use separate configs for different environments

2. **Verification**
   - Run verification before starting the server
   - Schedule regular verification checks
   - Monitor verification results
   - Set up alerts for failures

3. **Security**
   - Use read-only database user
   - Implement connection pooling
   - Set appropriate timeouts
   - Monitor access patterns

4. **Maintenance**
   - Regularly update verification rules
   - Monitor data source changes
   - Update configuration as needed
   - Document any changes

### Integration with Testing

The data source verification can be integrated into the test suite:

```python
def test_data_source_verification():
    verifier = DataSourceVerifier("config/data_source_config.yaml")
    assert verifier.run_verification(), "Data source verification failed"
```

### Monitoring

The verification results can be monitored through:
- Log files
- Prometheus metrics
- Grafana dashboards
- Alert notifications

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify the model server is running
   - Check network connectivity
   - Validate the base URL format

2. **Authentication Failures**
   - Verify API key in test configuration
   - Check server authentication settings

3. **Performance Test Failures**
   - Check server resources
   - Verify rate limiting settings
   - Adjust concurrency settings if needed

### Debugging

1. Enable detailed logging:
   ```bash
   export PYTHONPATH=.  # Add project root to Python path
   python tests/run_tests.py --base-url http://localhost:8000
   ```

2. Check test results:
   ```bash
   cat test_results/YYYYMMDD_HHMMSS/test_results.json
   ```

3. View HTML report:
   ```bash
   open test_results/YYYYMMDD_HHMMSS/test_report.html
   ```

## Best Practices

1. **Test Environment**
   - Use a dedicated test environment
   - Avoid running tests in production
   - Monitor system resources during tests

2. **Test Data**
   - Use realistic test data
   - Include edge cases
   - Test with various data volumes

3. **Test Execution**
   - Run tests during off-peak hours
   - Monitor system impact
   - Save test results for comparison

4. **Maintenance**
   - Regularly update test data
   - Review and update thresholds
   - Clean up old test results

## Support

For issues or questions:
1. Check the troubleshooting guide
2. Review test logs
3. Contact the development team

## Contributing

To add new tests:
1. Follow the existing test structure
2. Update test configuration
3. Add appropriate documentation
4. Include test data generation
5. Update the test runner if needed 