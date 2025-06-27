# Agent Information Endpoints

This document describes the new agent information endpoints that provide detailed information about agents, including their data requirements and export considerations for training.

## Overview

The agent information endpoints help you understand:
- What data each agent requires
- How to export agent-specific data for training
- Agent capabilities and configuration
- Performance metrics and model associations

## Endpoints

### 1. Get Detailed Information for All Agents

**Endpoint:** `GET /api/v1/agents/detailed-info`

**Description:** Get comprehensive information about all agents or specific selected agents.

**Query Parameters:**
- `agent_ids` (optional): Comma-separated list of agent IDs to get detailed info for. If not provided, returns info for all agents.

**Example Request:**
```bash
# Get info for all agents
curl -X GET "http://localhost:5000/api/v1/agents/detailed-info"

# Get info for specific agents
curl -X GET "http://localhost:5000/api/v1/agents/detailed-info?agent_ids=wifi_agent,log_level_agent"
```

**Response Structure:**
```json
[
  {
    "id": "wifi_agent",
    "name": "WiFi Anomaly Detection Agent",
    "description": "Detects anomalies in WiFi network behavior",
    "agent_type": "ml_based",
    "status": "active",
    "is_running": true,
    "capabilities": ["wifi_anomaly_detection", "signal_analysis"],
    "data_requirements": {
      "data_sources": ["wifi_logs", "network_metrics"],
      "process_filters": ["wpa_supplicant", "hostapd"],
      "feature_requirements": ["signal_strength", "latency", "packet_loss"],
      "lookback_period": "5 minutes",
      "sampling_frequency": "60 seconds"
    },
    "export_considerations": {
      "exportable_features": ["wifi_anomaly_detection", "signal_analysis"],
      "data_format": "json",
      "required_fields": ["signal_strength", "latency", "packet_loss"],
      "data_volume_estimate": "~5 minutes of data every 60 seconds",
      "training_data_requirements": [
        "Labeled anomaly data",
        "Feature vectors",
        "Timestamp information",
        "Context metadata"
      ],
      "preprocessing_steps": [
        "Feature normalization",
        "Missing value handling",
        "Outlier detection",
        "Data validation"
      ]
    },
    "configuration": {
      "agent_type": "ml_based",
      "analysis_rules": {
        "lookback_minutes": 5,
        "analysis_interval": 60
      },
      "severity_mapping": {
        "low": 1,
        "medium": 2,
        "high": 3
      },
      "model_path": "/path/to/wifi_model.joblib",
      "enabled": true,
      "priority": "normal"
    },
    "model_info": {
      "path": "/path/to/wifi_model.joblib",
      "assigned": true,
      "type": "IsolationForest"
    },
    "performance_metrics": {
      "analysis_cycles": 150,
      "anomalies_detected": 12,
      "average_cycle_time": 2.5,
      "last_analysis_time": "2024-01-15T10:30:00Z",
      "success_rate": 0.98
    }
  }
]
```

### 2. Get Detailed Information for a Specific Agent

**Endpoint:** `GET /api/v1/agents/{agent_id}/detailed`

**Description:** Get comprehensive information about a specific agent.

**Path Parameters:**
- `agent_id`: The ID of the agent to get detailed information for

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/v1/agents/wifi_agent/detailed"
```

**Response Structure:** Same as the array element in the previous endpoint.

## Data Requirements

The `data_requirements` section provides information about:

- **data_sources**: What data sources the agent monitors
- **process_filters**: Which processes the agent filters for
- **feature_requirements**: What features the agent needs
- **lookback_period**: How far back the agent looks for data
- **sampling_frequency**: How often the agent analyzes data

## Export Considerations

The `export_considerations` section helps with training data preparation:

- **exportable_features**: What features can be exported
- **data_format**: Recommended format for exported data
- **required_fields**: Fields that must be included in exports
- **data_volume_estimate**: Estimated volume of data generated
- **training_data_requirements**: What's needed for training
- **preprocessing_steps**: Steps needed to prepare data for training

## Agent Types and Their Export Considerations

### ML-Based Agents
- **Training Requirements**: Labeled anomaly data, feature vectors, timestamps
- **Preprocessing**: Feature normalization, missing value handling, outlier detection
- **Data Format**: JSON with feature vectors and labels

### Rule-Based Agents
- **Training Requirements**: Rule condition data, threshold values, historical patterns
- **Preprocessing**: Rule validation, threshold calibration, pattern extraction
- **Data Format**: JSON with rule conditions and outcomes

### Hybrid Agents
- **Training Requirements**: Combination of ML and rule-based requirements
- **Preprocessing**: Both ML and rule-based preprocessing steps
- **Data Format**: JSON with both feature vectors and rule conditions

## Usage Examples

### 1. Planning Data Export for Training

```python
import requests

# Get detailed info for agents you want to export data from
response = requests.get("http://localhost:5000/api/v1/agents/detailed-info?agent_ids=wifi_agent,log_level_agent")
agents_info = response.json()

for agent in agents_info:
    print(f"Agent: {agent['name']}")
    print(f"Data Sources: {agent['data_requirements']['data_sources']}")
    print(f"Required Fields: {agent['export_considerations']['required_fields']}")
    print(f"Data Volume: {agent['export_considerations']['data_volume_estimate']}")
    print(f"Preprocessing Steps: {agent['export_considerations']['preprocessing_steps']}")
    print("---")
```

### 2. Checking Agent Capabilities

```python
# Get detailed info for a specific agent
response = requests.get("http://localhost:5000/api/v1/agents/wifi_agent/detailed")
agent_info = response.json()

print(f"Agent Type: {agent_info['agent_type']}")
print(f"Capabilities: {agent_info['capabilities']}")
print(f"Model: {agent_info['model_info']['path'] if agent_info['model_info'] else 'None'}")
print(f"Performance: {agent_info['performance_metrics']['success_rate']}% success rate")
```

### 3. Monitoring Agent Performance

```python
# Get performance metrics for all agents
response = requests.get("http://localhost:5000/api/v1/agents/detailed-info")
agents_info = response.json()

for agent in agents_info:
    metrics = agent['performance_metrics']
    print(f"{agent['name']}: {metrics['analysis_cycles']} cycles, {metrics['anomalies_detected']} anomalies")
```

## Testing

You can test the endpoints using the provided test script:

```bash
cd backend
python test_agent_info_endpoints.py
```

This will test:
- Getting detailed info for all agents
- Getting detailed info for specific agents
- Error handling for non-existent agents
- Data requirements extraction
- Export considerations generation

## Error Handling

The endpoints handle various error conditions:

- **404 Not Found**: When an agent ID doesn't exist
- **500 Internal Server Error**: When there's a server-side error
- **Warning Logs**: When some requested agents are not found (for bulk requests)

## Integration with Export System

These endpoints work well with the existing export system:

1. Use the detailed info to understand what data to export
2. Use the export considerations to format the data correctly
3. Use the data requirements to filter the right data sources
4. Use the preprocessing steps to prepare the data for training

## Future Enhancements

Potential future enhancements:
- Real-time performance metrics updates
- Agent comparison functionality
- Export template generation based on agent requirements
- Integration with model training pipelines 