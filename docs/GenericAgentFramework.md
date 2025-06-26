# Generic Agent Framework Implementation Plan

## Current State Analysis

### Existing Architecture Overview
The current codebase already has a solid foundation that aligns well with the generic framework goals:

#### 1. Base Infrastructure
- **BaseAgent Class** (`backend/app/mcp_service/agents/base_agent.py`): Well-defined abstract base class with common lifecycle methods
- **AgentRegistry** (`backend/app/mcp_service/components/agent_registry.py`): Basic agent management with Redis status updates
- **ModelManager** (`backend/app/mcp_service/components/model_manager.py`): Comprehensive model management with singleton pattern
- **DataService** (`backend/app/mcp_service/data_service.py`): Database access and log retrieval

#### 2. Current Agent Implementations
- **WiFiAgent** (`backend/app/mcp_service/agents/wifi_agent.py`): ML-based agent using:
  - FeatureExtractor for log processing
  - AnomalyClassifier for detection
  - ModelManager integration
  - Redis status updates
- **LogLevelAgent** (`backend/app/mcp_service/agents/log_level_agent.py`): Rule-based agent for:
  - Log level monitoring (error, critical)
  - Simple pattern matching
  - Direct anomaly generation

#### 3. Configuration Structure
- **Basic YAML configs** exist but are not fully utilized:
  - `backend/app/config/agent_config.yaml`: WiFi agent settings
  - `backend/app/config/agent_log_level.yaml`: Log level agent settings
- **Configuration loading** is partially implemented in AgentRegistry

#### 4. Main Application Integration
- **main.py** (`backend/app/main.py`): Hardcoded agent initialization and lifecycle management
- **Background analysis cycles** with fixed agent references
- **API endpoints** for agent management

### Key Strengths to Leverage
1. **Solid BaseAgent abstraction** with proper lifecycle management
2. **Comprehensive ModelManager** with Redis integration
3. **Existing agent patterns** that demonstrate both ML-based and rule-based approaches
4. **Redis status management** already implemented
5. **Configuration loading** partially implemented

### Areas for Enhancement
1. **Configuration-driven agent creation** instead of hardcoded initialization
2. **Dynamic agent type selection** based on configuration
3. **Unified configuration schema** across all agents
4. **Enhanced AgentRegistry** with configuration validation
5. **Generic agent classes** that can replace hardcoded implementations

## Overview

The Generic Agent Framework will replace the current hardcoded agent implementations (WiFiAgent, LogLevelAgent) with a configuration-driven system that can create specialized agents dynamically. This approach provides:

- **Scalability**: Easy to add new agent types without code changes
- **Maintainability**: Single codebase for all agent logic
- **Flexibility**: Configuration-driven agent behavior
- **Model Assignment**: Dynamic model-agent associations

## Architecture

### 1. Core Components

#### GenericAgent Class
```python
class GenericAgent(BaseAgent):
    def __init__(self, config, data_service, model_manager=None):
        # Configuration-driven initialization
        self.agent_name = config.get('name', 'GenericAgent')
        self.target_processes = config.get('process_filters', [])
        self.model_path = config.get('model_path')
        self.agent_type = config.get('agent_type', 'ml_based')  # ml_based, rule_based
        self.analysis_rules = config.get('analysis_rules', {})
        # ... other configurable parameters
```

#### Agent Configuration Schema
```yaml
# Example: wifi_agent_config.yaml
agent_id: "wifi_agent"
name: "WiFiAgent"
description: "WiFi anomaly detection agent"
agent_type: "ml_based"  # ml_based, rule_based, hybrid
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
  severity_mapping:
    auth_failure: 4
    deauth_flood: 5
    beacon_flood: 3
```

### 2. Agent Types

#### A. ML-Based Agents (like current WiFiAgent)
- Use trained models for anomaly detection
- Require model files
- Use FeatureExtractor and AnomalyClassifier
- Example: WiFiAgent, DNSAgent, NetworkAgent

#### B. Rule-Based Agents (like current LogLevelAgent)
- Use predefined rules and thresholds
- No model required
- Simple pattern matching and filtering
- Example: LogLevelAgent, ThresholdAgent

#### C. Hybrid Agents
- Combine ML models with rule-based logic
- Fallback to rules when model unavailable
- Example: AdaptiveAgent

### 3. Configuration Management

#### Agent Configuration Files
```
backend/app/config/agents/
├── wifi_agent.yaml
├── dns_agent.yaml
├── system_agent.yaml
├── log_level_agent.yaml
└── network_agent.yaml
```

#### Agent Registry Enhancement
```python
class AgentRegistry:
    def __init__(self):
        self.agent_configs = {}
        self.agents = {}
        self._load_agent_configs()
    
    def _load_agent_configs(self):
        """Load all agent configurations from config/agents/"""
        config_dir = Path("backend/app/config/agents")
        for config_file in config_dir.glob("*.yaml"):
            agent_id = config_file.stem
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                self.agent_configs[agent_id] = config
    
    def create_agent(self, agent_id: str, data_service, model_manager=None):
        """Create agent instance from configuration"""
        if agent_id not in self.agent_configs:
            raise ValueError(f"Agent configuration not found: {agent_id}")
        
        config = self.agent_configs[agent_id]
        agent_type = config.get('agent_type', 'ml_based')
        
        if agent_type == 'ml_based':
            return MLBasedAgent(config, data_service, model_manager)
        elif agent_type == 'rule_based':
            return RuleBasedAgent(config, data_service)
        elif agent_type == 'hybrid':
            return HybridAgent(config, data_service, model_manager)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
```

### 4. Implementation Steps

#### Phase 1: Core Framework (Week 1)
1. **Create GenericAgent base class**
   - Extend existing BaseAgent with configuration-driven initialization
   - Add common agent lifecycle methods
   - Maintain compatibility with existing status management

2. **Create specialized agent classes**
   - `MLBasedAgent`: For model-based detection (based on current WiFiAgent)
   - `RuleBasedAgent`: For rule-based detection (based on current LogLevelAgent)
   - `HybridAgent`: For combined approaches

3. **Enhance AgentRegistry**
   - Extend existing AgentRegistry with configuration loading
   - Add dynamic agent creation from configuration
   - Maintain existing Redis status updates

#### Phase 2: Configuration System (Week 2)
1. **Create configuration schema**
   - YAML-based agent definitions
   - Validation rules
   - Default values

2. **Migrate existing agents**
   - Convert WiFiAgent configuration to new schema
   - Convert LogLevelAgent configuration to new schema
   - Test backward compatibility

#### Phase 3: Model Management Integration (Week 3)
1. **Dynamic model assignment**
   - Model-agent association via configuration
   - Runtime model loading
   - Model validation and fallback

2. **Model registry enhancement**
   - Model metadata for agent compatibility
   - Automatic model discovery
   - Model versioning

#### Phase 4: UI/API Updates (Week 4)
1. **Agent management API**
   - List available agent configurations
   - Create agents from configuration
   - Assign models to agents

2. **Frontend updates**
   - Agent configuration interface
   - Model assignment UI
   - Agent status monitoring

### 5. Configuration Examples

#### WiFi Agent Configuration (Based on Current Implementation)
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

#### DNS Agent Configuration
```yaml
agent_id: "dns_agent"
name: "DNSAgent"
description: "DNS query anomaly detection"
agent_type: "ml_based"
process_filters: ["named", "dnsmasq", "systemd-resolved"]
model_path: "/app/models/dns_anomaly_model.pkl"
capabilities: [
  "DNS amplification detection",
  "Query flood detection",
  "Suspicious domain detection"
]
analysis_rules:
  lookback_minutes: 10
  analysis_interval: 120
  feature_extraction:
    query_count: true
    response_time: true
    domain_patterns: true
    query_types: true
  severity_mapping:
    dns_amplification: 5
    query_flood: 4
    suspicious_domain: 3
  thresholds:
    query_flood_threshold: 1000
    response_time_threshold: 5000
    amplification_ratio_threshold: 10
```

#### System Agent Configuration
```yaml
agent_id: "system_agent"
name: "SystemAgent"
description: "System-level anomaly detection"
agent_type: "ml_based"
process_filters: ["systemd", "cron", "sshd", "sudo"]
model_path: "/app/models/system_anomaly_model.pkl"
capabilities: [
  "System resource anomaly detection",
  "Authentication failure detection",
  "Process behavior analysis"
]
analysis_rules:
  lookback_minutes: 15
  analysis_interval: 300
  feature_extraction:
    cpu_usage: true
    memory_usage: true
    disk_io: true
    network_connections: true
    failed_logins: true
  severity_mapping:
    resource_anomaly: 4
    auth_failure: 3
    process_anomaly: 5
  thresholds:
    cpu_threshold: 90
    memory_threshold: 85
    failed_login_threshold: 5
```

#### Log Level Agent Configuration (Based on Current Implementation)
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
  confidence: 1.0  # High confidence for rule-based detection
  exclude_patterns: [
    ".*test.*",
    ".*debug.*"
  ]
  include_patterns: [
    ".*auth.*",
    ".*network.*",
    ".*system.*"
  ]
```

#### Network Agent Configuration
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

#### Threshold Agent Configuration
```yaml
agent_id: "threshold_agent"
name: "ThresholdAgent"
description: "Simple threshold-based monitoring"
agent_type: "rule_based"
process_filters: ["nginx", "apache2", "mysql", "postgresql"]
model_path: null
capabilities: [
  "High CPU usage detection",
  "Memory usage monitoring",
  "Disk space monitoring"
]
analysis_rules:
  lookback_minutes: 5
  analysis_interval: 60
  thresholds:
    cpu_usage: 80
    memory_usage: 85
    disk_usage: 90
  severity_mapping:
    cpu_high: 3
    memory_high: 3
    disk_full: 4
  alert_cooldown: 300  # 5 minutes between alerts
  escalation_rules:
    cpu_critical: 95
    memory_critical: 95
    disk_critical: 98
```

### 6. Migration Strategy

#### Step 1: Create Generic Framework
- Implement GenericAgent, MLBasedAgent, RuleBasedAgent
- Create configuration loading system
- Test with simple configurations

#### Step 2: Migrate Existing Agents
- Create configurations for WiFiAgent and LogLevelAgent
- Test that new framework produces same behavior
- Update main.py to use new framework

#### Step 3: Add New Agent Types
- Create configurations for DNSAgent, SystemAgent, etc.
- Test model assignment and agent creation
- Validate end-to-end functionality

#### Step 4: Update UI/API
- Enhance agent management endpoints
- Update frontend for configuration-driven agents
- Add model assignment interface

### 7. Benefits

1. **Scalability**: Add new agents by creating YAML configs
2. **Maintainability**: Single codebase for all agent logic
3. **Flexibility**: Easy to modify agent behavior via configuration
4. **Model Management**: Dynamic model-agent associations
5. **Testing**: Easy to test different configurations
6. **Deployment**: Configuration-driven deployment

### 8. File Structure

```
backend/app/mcp_service/agents/
├── __init__.py
├── base_agent.py (existing)
├── generic_agent.py (new)
├── ml_based_agent.py (new)
├── rule_based_agent.py (new)
├── hybrid_agent.py (new)
└── legacy/
    ├── wifi_agent.py (deprecated)
    └── log_level_agent.py (deprecated)

backend/app/config/agents/
├── wifi_agent.yaml
├── dns_agent.yaml
├── system_agent.yaml
├── log_level_agent.yaml
└── network_agent.yaml

backend/app/mcp_service/components/
├── agent_registry.py (enhanced)
├── model_manager.py (enhanced)
└── configuration_manager.py (new)
```

### 9. Testing Strategy

1. **Unit Tests**: Test each agent type independently
2. **Integration Tests**: Test agent creation from configuration
3. **End-to-End Tests**: Test complete agent lifecycle
4. **Configuration Tests**: Validate configuration schemas
5. **Migration Tests**: Ensure backward compatibility

### 10. Timeline

- **Week 1**: Core framework implementation
- **Week 2**: Configuration system and migration
- **Week 3**: Model management integration
- **Week 4**: UI/API updates and testing
- **Week 5**: Documentation and deployment

### 11. Backward Compatibility Considerations

#### Maintaining Existing Functionality
- Current agents (WiFiAgent, LogLevelAgent) continue to work during migration
- Existing API endpoints remain functional
- Redis status updates maintain current format
- ModelManager integration preserved

#### Gradual Migration Path
1. **Phase 1**: Add new generic framework alongside existing agents
2. **Phase 2**: Migrate one agent at a time to new framework
3. **Phase 3**: Update main.py to use generic framework
4. **Phase 4**: Deprecate old agent implementations

#### Configuration Migration
- Convert existing YAML configs to new schema
- Maintain current parameter names where possible
- Add validation for new required fields
- Provide migration scripts for existing deployments

This framework will provide a solid foundation for scalable, configuration-driven agent management while maintaining backward compatibility with existing implementations. 