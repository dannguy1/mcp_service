# MCP Service API Documentation

## Overview

The MCP Service provides a RESTful API for model inference, monitoring, and management. This document details all available endpoints, their usage, and examples.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All API endpoints require authentication using an API key.

### Headers
```
X-API-Key: your_api_key
```

## Endpoints

### Model Inference

#### Predict Anomalies
```http
POST /predict
```

Analyzes WiFi logs for anomalies.

**Request Body:**
```json
{
    "timestamp": "2024-03-20T10:00:00Z",
    "signal_strength": -65,
    "latency": 25,
    "packet_loss": 0.1,
    "connection_duration": 3600,
    "client_count": 15,
    "error_count": 2
}
```

**Response:**
```json
{
    "anomaly_detected": true,
    "confidence": 0.95,
    "severity": "high",
    "description": "Unusual pattern in error rate and latency",
    "timestamp": "2024-03-20T10:00:00Z"
}
```

**Status Codes:**
- 200: Success
- 400: Invalid request
- 401: Unauthorized
- 500: Server error

### Model Management

#### Get Model Status
```http
GET /models/status
```

Returns the current model status and version information.

**Response:**
```json
{
    "model_version": "1.2.0",
    "last_updated": "2024-03-19T15:30:00Z",
    "status": "active",
    "performance": {
        "accuracy": 0.98,
        "false_positive_rate": 0.01,
        "false_negative_rate": 0.02
    }
}
```

#### Update Model
```http
POST /models/update
```

Updates the model with a new version.

**Request Body:**
```json
{
    "model_path": "/path/to/new/model",
    "version": "1.2.1",
    "description": "Updated model with improved accuracy"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Model updated successfully",
    "new_version": "1.2.1"
}
```

### Health and Monitoring

#### Health Check
```http
GET /health
```

Returns the health status of the service.

**Response:**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "uptime": "5d 12h 30m",
    "components": {
        "database": "healthy",
        "model": "healthy",
        "cache": "healthy"
    }
}
```

#### Metrics
```http
GET /metrics
```

Returns Prometheus-compatible metrics.

**Response:**
```
# HELP request_latency_seconds Request latency in seconds
# TYPE request_latency_seconds histogram
request_latency_seconds_bucket{le="0.1"} 100
request_latency_seconds_bucket{le="0.5"} 200
request_latency_seconds_bucket{le="1.0"} 250
request_latency_seconds_count 300
request_latency_seconds_sum 150.5

# HELP model_accuracy Model accuracy percentage
# TYPE model_accuracy gauge
model_accuracy 98.5
```

### Data Management

#### Export Logs
```http
POST /logs/export
```

Exports logs for model training.

**Request Body:**
```json
{
    "start_date": "2024-03-01T00:00:00Z",
    "end_date": "2024-03-20T00:00:00Z",
    "format": "csv"
}
```

**Response:**
```json
{
    "status": "success",
    "file_path": "/exports/logs_20240301_20240320.csv",
    "record_count": 10000
}
```

#### Get Statistics
```http
GET /stats
```

Returns statistical information about the data.

**Response:**
```json
{
    "total_records": 100000,
    "anomaly_count": 150,
    "average_latency": 25.5,
    "error_rate": 0.02,
    "time_range": {
        "start": "2024-03-01T00:00:00Z",
        "end": "2024-03-20T00:00:00Z"
    }
}
```

## Error Handling

### Error Response Format
```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable error message",
        "details": {
            "field": "Additional error details"
        }
    }
}
```

### Common Error Codes
- `INVALID_REQUEST`: Invalid request parameters
- `UNAUTHORIZED`: Missing or invalid API key
- `MODEL_ERROR`: Model inference error
- `DATABASE_ERROR`: Database operation error
- `INTERNAL_ERROR`: Internal server error

## Rate Limiting

- 100 requests per minute per API key
- Rate limit headers included in response:
  ```
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 95
  X-RateLimit-Reset: 1616236800
  ```

## Examples

### Python
```python
import requests
import json

API_KEY = "your_api_key"
BASE_URL = "http://localhost:8000/api/v1"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Predict anomalies
data = {
    "timestamp": "2024-03-20T10:00:00Z",
    "signal_strength": -65,
    "latency": 25,
    "packet_loss": 0.1,
    "connection_duration": 3600,
    "client_count": 15,
    "error_count": 2
}

response = requests.post(
    f"{BASE_URL}/predict",
    headers=headers,
    json=data
)

print(json.dumps(response.json(), indent=2))
```

### cURL
```bash
# Health check
curl -H "X-API-Key: your_api_key" http://localhost:8000/api/v1/health

# Predict anomalies
curl -X POST \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-03-20T10:00:00Z",
    "signal_strength": -65,
    "latency": 25,
    "packet_loss": 0.1,
    "connection_duration": 3600,
    "client_count": 15,
    "error_count": 2
  }' \
  http://localhost:8000/api/v1/predict
```

## Best Practices

1. **Error Handling**
   - Always check response status codes
   - Implement exponential backoff for retries
   - Handle rate limiting appropriately

2. **Security**
   - Keep API keys secure
   - Use HTTPS in production
   - Rotate API keys regularly

3. **Performance**
   - Implement client-side caching
   - Batch requests when possible
   - Monitor rate limits

## Versioning

- API version included in URL path
- Breaking changes will increment major version
- New features will increment minor version
- Bug fixes will increment patch version

## Support

For API support:
- Email: support@example.com
- Documentation: https://docs.example.com
- Status: https://status.example.com 