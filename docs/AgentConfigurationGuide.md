# Agent Configuration Guide

## Overview

The Generic Agent Framework provides a configuration-driven approach to creating and managing anomaly detection agents. This guide explains how to add new agents, configure existing ones, and manage agent lifecycle through YAML configuration files.

## Table of Contents

1. [Agent Types](#agent-types)
2. [Configuration Schema](#configuration-schema)
3. [Adding New Agents](#adding-new-agents)
4. [Agent Management](#agent-management)
5. [Configuration Examples](#configuration-examples)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## Agent Types

The framework supports three types of agents:

### 1. ML-Based Agents (`agent_type: "ml_based"`)
- Use trained machine learning models for anomaly detection
- Require model files (`.pkl`, `.joblib`, etc.)
- Use FeatureExtractor and AnomalyClassifier components
- **Examples**: WiFiAgent, DNSAgent, SystemAgent

### 2. Rule-Based Agents (`agent_type: "rule_based"`)
- Use predefined rules and thresholds for detection
- No model files required (`model_path: null`)
- Simple pattern matching and filtering
- **Examples**: LogLevelAgent, ThresholdAgent

### 3. Hybrid Agents (`agent_type: "hybrid"`)
- Combine ML models with rule-based logic
- Fallback to rules when model unavailable
- Best of both approaches
- **Examples**: NetworkAgent

## Configuration Schema

### Required Fields

```yaml
agent_id: "unique_agent_identifier"    # Required: Unique identifier
name: "Agent Display Name"             # Required: Human-readable name
description: "Agent description"       # Required: Detailed description
agent_type: "ml_based"                 # Required: ml_based, rule_based, or hybrid
```

### Optional Fields

```yaml
process_filters: ["process1", "process2"]  # List of processes to monitor
model_path: "/path/to/model.pkl"           # Path to model file (null for rule-based)
capabilities: ["Capability 1", "Capability 2"]  # List of detection capabilities
```

### Analysis Rules

```yaml
analysis_rules:
  lookback_minutes: 5        # Minutes of historical data to analyze
  analysis_interval: 60      # Seconds between analysis cycles
  severity_mapping:          # Map anomaly types to severity levels (1-5)
    anomaly_type: 4
  # Agent-specific configuration follows...
```

## Adding New Agents

### Step 1: Create Configuration File

1. Navigate to the agents configuration directory:
   ```bash
   cd backend/app/config/agents/
   ```

2. Create a new YAML file with your agent name:
   ```bash
   touch my_custom_agent.yaml
   ```

### Step 2: Define Agent Configuration

```yaml
agent_id: "my_custom_agent"
name: "MyCustomAgent"
description: "Custom anomaly detection for specific use case"
agent_type: "ml_based"  # or "rule_based" or "hybrid"
process_filters: ["my_process", "another_process"]
model_path: "/app/models/my_custom_model.pkl"
capabilities: [
  "Custom anomaly detection",
  "Specific pattern recognition"
]
analysis_rules:
  lookback_minutes: 10
  analysis_interval: 120
  feature_extraction:
    custom_feature: true
    another_feature: true
  severity_mapping:
    custom_anomaly: 4
    critical_anomaly: 5
  thresholds:
    custom_threshold: 100
```

### Step 3: Restart the Backend

The system automatically discovers and creates agents from configuration files:

```bash
./scripts/start_backend.sh
```

### Step 4: Verify Agent Creation

Check the backend logs to confirm agent creation:
```
INFO: Creating ml_based agent: MyCustomAgent (my_custom_agent)
INFO: MyCustomAgent (my_custom_agent) created and started successfully
```

## Agent Management

### Viewing Agents

Agents are automatically listed in the Agent Management UI. You can also check via API:

```bash
curl http://localhost:5000/api/v1/agents
```

### Agent Lifecycle

1. **Discovery**: System scans `backend/app/config/agents/` for YAML files
2. **Creation**: Agents are instantiated based on configuration
3. **Registration**: Agents are registered with the AgentRegistry
4. **Startup**: Agents start monitoring and analysis cycles
5. **Runtime**: Agents run analysis cycles at configured intervals
6. **Shutdown**: Agents are stopped and unregistered on system shutdown

### Agent Status

Each agent maintains status information:
- **active**: Agent is running and performing analysis
- **analyzing**: Agent is currently running an analysis cycle
- **inactive**: Agent is stopped
- **error**: Agent encountered an error

## Configuration Examples

### ML-Based Agent (WiFiAgent)

```yaml
agent_id: "wifi_agent"
name: "WiFiAgent"
description: "WiFi anomaly detection using ML models"
agent_type: "ml_based"
process_filters: ["hostapd", "wpa_supplicant"]
model_path: "/app/models/wifi_anomaly_model.pkl"
capabilities: [
  "Authentication failure detection",
  "Deauthentication flood detection",
  "Beacon frame flood detection"
]
analysis_rules:
  lookback_minutes: 5
  analysis_interval: 60
  feature_extraction:
    auth_failures: true
    deauth_count: true
    beacon_count: true
  severity_mapping:
    auth_failure: 4
    deauth_flood: 5
    beacon_flood: 3
  thresholds:
    auth_failure_threshold: 5
    deauth_flood_threshold: 10
    beacon_flood_threshold: 100
```

### Rule-Based Agent (LogLevelAgent)

```yaml
agent_id: "log_level_agent"
name: "LogLevelAgent"
description: "Rule-based log level monitoring"
agent_type: "rule_based"
process_filters: []  # All processes
model_path: null  # No model required
capabilities: [
  "Error log level detection",
  "Critical log level detection",
  "Warning level monitoring"
]
analysis_rules:
  lookback_minutes: 5
  analysis_interval: 60
  target_levels: ["error", "critical", "warning"]
  severity_mapping:
    error: 4
    critical: 5
    warning: 3
  confidence: 1.0
  exclude_patterns: [
    ".*test.*",
    ".*debug.*"
  ]
  include_patterns: [
    ".*auth.*",
    ".*network.*",
    ".*system.*"
  ]
  alert_cooldown: 300
```

### Hybrid Agent (NetworkAgent)

```yaml
agent_id: "network_agent"
name: "NetworkAgent"
description: "Network traffic anomaly detection"
agent_type: "hybrid"
process_filters: ["iptables", "ufw", "firewalld", "netfilter"]
model_path: "/app/models/network_anomaly_model.pkl"
capabilities: [
  "Network traffic pattern analysis",
  "Firewall rule violation detection",
  "Port scanning detection"
]
analysis_rules:
  lookback_minutes: 20
  analysis_interval: 180
  feature_extraction:
    packet_count: true
    connection_count: true
    port_scanning: true
    traffic_patterns: true
  severity_mapping:
    traffic_anomaly: 4
    firewall_violation: 5
    port_scan: 4
  thresholds:
    packet_threshold: 10000
    connection_threshold: 1000
    port_scan_threshold: 100
  fallback_rules:
    enable_fallback: true
    rule_based_detection: true
```

## Best Practices

### 1. Naming Conventions
- Use descriptive `agent_id` values (e.g., `wifi_agent`, `dns_agent`)
- Use clear, descriptive names for `name` field
- Include detailed descriptions explaining the agent's purpose

### 2. Process Filtering
- Be specific with `process_filters` to reduce noise
- Use empty list `[]` to monitor all processes
- Consider performance impact of broad filters

### 3. Analysis Intervals
- Balance between responsiveness and system load
- Use shorter intervals (30-60 seconds) for critical monitoring
- Use longer intervals (300+ seconds) for resource-intensive analysis

### 4. Severity Mapping
- Use severity levels 1-5 consistently:
  - 1: Info/Low
  - 2: Minor
  - 3: Moderate
  - 4: High
  - 5: Critical

### 5. Model Management
- Place model files in `/app/models/` directory
- Use descriptive model names
- Ensure model files are accessible to the application

### 6. Configuration Validation
- Test configurations before deployment
- Use the test script to validate agent creation:
  ```bash
  cd backend && python3 test_generic_framework.py
  ```

## Troubleshooting

### Common Issues

#### 1. Agent Not Appearing in UI
**Symptoms**: Agent configuration exists but doesn't show in Agent Management
**Solutions**:
- Check YAML syntax for errors
- Verify file is in `backend/app/config/agents/` directory
- Restart backend service
- Check backend logs for configuration loading errors

#### 2. Agent Creation Fails
**Symptoms**: "Missing required configuration fields" error
**Solutions**:
- Ensure all required fields are present
- Check YAML indentation
- Verify `agent_type` is one of: `ml_based`, `rule_based`, `hybrid`

#### 3. Model Loading Errors
**Symptoms**: "Model file not found" warnings
**Solutions**:
- Verify model file path is correct
- Ensure model file exists and is accessible
- Check file permissions
- For ML-based agents, the system will use default models if files are missing

#### 4. Analysis Cycle Failures
**Symptoms**: Agents show "error" status
**Solutions**:
- Check data service connectivity
- Verify process filters match actual running processes
- Review analysis rules configuration
- Check backend logs for specific error messages

### Debugging Commands

#### Check Agent Configurations
```bash
cd backend && python3 test_generic_framework.py
```

#### View Backend Logs
```bash
tail -f backend/backend.log
```

#### Test Agent Creation
```bash
cd backend && python3 -c "
from app.mcp_service.components.agent_registry import agent_registry
configs = agent_registry.list_agent_configs()
for config in configs:
    print(f'{config[\"agent_id\"]}: {config[\"name\"]} ({config[\"agent_type\"]})')
"
```

### Getting Help

1. **Check the logs**: Backend logs contain detailed error messages
2. **Validate configuration**: Use the test script to verify configurations
3. **Review examples**: Refer to existing agent configurations as templates
4. **Check documentation**: Review this guide and the Generic Agent Framework documentation

## Advanced Configuration

### Custom Feature Extraction

For ML-based agents, you can configure custom feature extraction:

```yaml
analysis_rules:
  feature_extraction:
    custom_feature_1: true
    custom_feature_2: true
    feature_with_options:
      enabled: true
      threshold: 100
      window_size: 300
```

### Advanced Rule-Based Configuration

For rule-based agents, you can configure complex filtering:

```yaml
analysis_rules:
  target_levels: ["error", "critical"]
  exclude_patterns: [
    ".*test.*",
    ".*debug.*",
    ".*development.*"
  ]
  include_patterns: [
    ".*production.*",
    ".*critical.*"
  ]
  alert_cooldown: 300
  escalation_rules:
    error_critical: 10
    critical_critical: 5
```

### Hybrid Agent Fallback Configuration

For hybrid agents, configure fallback behavior:

```yaml
analysis_rules:
  fallback_rules:
    enable_fallback: true
    rule_based_detection: true
    fallback_threshold: 0.5
    ml_confidence_threshold: 0.8
```

This guide provides everything you need to configure and manage agents using the Generic Agent Framework. For additional support, refer to the main framework documentation or check the backend logs for specific error messages. 