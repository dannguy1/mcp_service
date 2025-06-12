# Data Exporter Usage Guide

## Overview

The Data Exporter is a powerful tool for exporting data from the AnalyzerMCPServer for AI training purposes. It provides a robust API for exporting logs, anomalies, and IP data with features like data validation, transformation, compression, and status tracking.

## Features

1. **Data Types**
   - Log entries
   - Anomaly detection results
   - IP address records

2. **Export Options**
   - Date range filtering
   - Batch processing
   - Data validation
   - Data transformation
   - Compression support
   - Progress tracking

3. **Status Tracking**
   - Real-time progress updates
   - Export history
   - Error reporting
   - Performance metrics

## API Endpoints

### 1. Create Export

```http
POST /export
```

Request body:
```json
{
    "start_date": "2024-03-01T00:00:00Z",
    "end_date": "2024-03-15T23:59:59Z",
    "data_types": ["logs", "anomalies", "ips"],
    "batch_size": 1000,
    "include_metadata": true,
    "validation_level": "basic",
    "output_format": "json",
    "compression": false
}
```

Response:
```json
{
    "export_id": "550e8400-e29b-41d4-a716-446655440000",
    "data_version": "1.0.0",
    "export_config": {
        "start_date": "2024-03-01T00:00:00Z",
        "end_date": "2024-03-15T23:59:59Z",
        "data_types": ["logs", "anomalies", "ips"],
        "batch_size": 1000,
        "include_metadata": true,
        "validation_level": "basic",
        "output_format": "json",
        "compression": false
    },
    "record_count": 0,
    "file_size": 0,
    "status": "pending"
}
```

### 2. Get Export Status

```http
GET /export/{export_id}
```

Response:
```json
{
    "export_id": "550e8400-e29b-41d4-a716-446655440000",
    "data_version": "1.0.0",
    "export_config": {
        "start_date": "2024-03-01T00:00:00Z",
        "end_date": "2024-03-15T23:59:59Z",
        "data_types": ["logs", "anomalies", "ips"],
        "batch_size": 1000,
        "include_metadata": true,
        "validation_level": "basic",
        "output_format": "json",
        "compression": false
    },
    "record_count": 1500,
    "file_size": 1024000,
    "status": "completed"
}
```

### 3. List Exports

```http
GET /export?limit=100&offset=0
```

Response:
```json
[
    {
        "export_id": "550e8400-e29b-41d4-a716-446655440000",
        "data_version": "1.0.0",
        "export_config": {
            "start_date": "2024-03-01T00:00:00Z",
            "end_date": "2024-03-15T23:59:59Z",
            "data_types": ["logs", "anomalies", "ips"],
            "batch_size": 1000,
            "include_metadata": true,
            "validation_level": "basic",
            "output_format": "json",
            "compression": false
        },
        "record_count": 1500,
        "file_size": 1024000,
        "status": "completed"
    }
]
```

## Configuration Options

### 1. Data Types
- `logs`: Export log entries
- `anomalies`: Export anomaly detection results
- `ips`: Export IP address records

### 2. Validation Levels
- `basic`: Check required fields and basic format
- `strict`: Additional validation for data quality
- `custom`: Custom validation rules

### 3. Output Format
- `json`: Standard JSON format
- `json.gz`: Compressed JSON format

## Export Process

1. **Initialization**
   - Create export request with configuration
   - Generate unique export ID
   - Initialize status tracking

2. **Data Processing**
   - Fetch data in batches
   - Validate data according to rules
   - Transform data to standard format
   - Write to files with optional compression

3. **Status Updates**
   - Track progress per data type
   - Update record counts
   - Monitor file sizes
   - Handle errors gracefully

## Best Practices

1. **Performance Optimization**
   - Use appropriate batch size (default: 1000)
   - Enable compression for large exports
   - Monitor memory usage

2. **Error Handling**
   - Check export status regularly
   - Handle partial failures gracefully
   - Review error messages for troubleshooting

3. **Resource Management**
   - Clean up old exports periodically
   - Monitor disk space usage
   - Consider compression for storage efficiency

## Example Usage

### Python Client

```python
import requests
from datetime import datetime, timedelta

# Create export
response = requests.post(
    "http://localhost:8000/export",
    json={
        "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
        "end_date": datetime.utcnow().isoformat(),
        "data_types": ["logs", "anomalies"],
        "batch_size": 1000,
        "compression": True
    }
)
export_id = response.json()["export_id"]

# Monitor progress
while True:
    status = requests.get(f"http://localhost:8000/export/{export_id}").json()
    if status["status"] in ["completed", "failed"]:
        break
    time.sleep(5)
```

### Shell Script

```bash
#!/bin/bash

# Create export
EXPORT_ID=$(curl -s -X POST http://localhost:8000/export \
    -H "Content-Type: application/json" \
    -d '{
        "start_date": "2024-03-01T00:00:00Z",
        "end_date": "2024-03-15T23:59:59Z",
        "data_types": ["logs"],
        "compression": true
    }' | jq -r '.export_id')

# Monitor progress
while true; do
    STATUS=$(curl -s http://localhost:8000/export/$EXPORT_ID | jq -r '.status')
    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
        break
    fi
    sleep 5
done
```

## Troubleshooting

1. **Common Issues**
   - Export stuck in "pending" state
   - Memory errors during large exports
   - Compression failures
   - Database connection issues

2. **Solutions**
   - Check server logs for errors
   - Verify database connectivity
   - Reduce batch size for large exports
   - Ensure sufficient disk space

3. **Monitoring**
   - Track export progress
   - Monitor resource usage
   - Check error messages
   - Review export history

## Security Considerations

1. **Data Protection**
   - Secure API endpoints
   - Validate input data
   - Sanitize output files
   - Control access to exports

2. **Resource Security**
   - Limit export sizes
   - Control concurrent exports
   - Monitor disk usage
   - Implement cleanup policies

## Future Enhancements

1. **Planned Features**
   - Export scheduling
   - Custom data transformations
   - Advanced compression options
   - Export templates
   - Automated cleanup

2. **Integration Options**
   - Cloud storage support
   - External API integration
   - Custom validation rules
   - Advanced monitoring 