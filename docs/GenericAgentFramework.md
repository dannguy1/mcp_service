# Generic Agent Framework Implementation Plan

## Current State Analysis

### Existing Architecture Overview
The current codebase already has a solid foundation that aligns well with the generic framework goals:

#### 1. Base Infrastructure
- **BaseAgent Class** (`backend/app/mcp_service/agents/base_agent.py`): Well-defined abstract base class with common lifecycle methods and required interfaces.
- **AgentRegistry** (`backend/app/mcp_service/components/agent_registry.py`): Manages agent registration, instantiation, and status updates (integrated with Redis).
- **ModelManager** (`backend/app/mcp_service/components/model_manager.py`): Handles model loading, versioning, and assignment using a singleton pattern.
- **DataService** (`backend/app/mcp_service/data_service.py`): Provides database access and log retrieval.

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
- **YAML configs** for agents:
  - `backend/app/config/agent_config.yaml`: WiFi agent settings
  - `backend/app/config/agent_log_level.yaml`: Log level agent settings
- **Configuration loading** is partially implemented in AgentRegistry, but not yet fully unified or validated.

#### 4. Main Application Integration
- **main.py** (`backend/app/main.py`): Currently uses hardcoded agent initialization and lifecycle management.
- **Background analysis cycles** reference specific agent classes.
- **API endpoints** exist for agent management, but are not yet fully configuration-driven.

### Key Strengths to Leverage
1. **Solid BaseAgent abstraction** with proper lifecycle management.
2. **Comprehensive ModelManager** with Redis integration.
3. **Existing agent patterns** that demonstrate both ML-based and rule-based approaches.
4. **Redis status management** already implemented.
5. **Partial configuration loading** in AgentRegistry.

### Areas for Enhancement
1. **Full configuration-driven agent creation** (remove hardcoded agent instantiation in main.py).
2. **Dynamic agent type selection** based on configuration schema.
3. **Unified configuration schema** for all agents, with validation.
4. **Enhanced AgentRegistry** for dynamic agent instantiation and config validation.
5. **Generic agent classes** to replace hardcoded implementations and support new agent types.

---

## Updated Framework Overview

The Generic Agent Framework will evolve the current system to a fully configuration-driven, extensible agent management platform. The following updates reflect the current codebase and the enhancements required for full generic agent support.

### 1. Core Components

#### GenericAgent Class
- **Status:** Not yet implemented as a single class, but the codebase has clear separation between ML-based and rule-based agents.
- **Action:** Implement a `GenericAgent` class that can be initialized from configuration, delegating to ML-based or rule-based logic as needed.

#### Specialized Agent Classes
- **MLBasedAgent** and **RuleBasedAgent**: These should be refactored from the current WiFiAgent and LogLevelAgent, respectively, to accept configuration and support generic instantiation.

#### Agent Configuration Schema
- **Status:** Multiple YAML files exist, but schemas are not unified or validated.
- **Action:** Define a unified schema (YAML/JSONSchema) for all agent configs and implement validation in AgentRegistry.

#### AgentRegistry
- **Status:** Exists and manages agent registration/status, but agent instantiation is still partially hardcoded.
- **Action:** Refactor to support dynamic agent creation from configuration, and maintain a registry of active agents.

---

### 2. Implementation Steps

#### Phase 1: Core Framework Refactor
1. **Implement GenericAgent and Specialized Classes**
   - Create `GenericAgent`, `MLBasedAgent`, and `RuleBasedAgent` classes in `backend/app/mcp_service/agents/`.
   - Refactor WiFiAgent and LogLevelAgent to inherit from these and support config-driven initialization.

2. **Unify Configuration Schema**
   - Move all agent configs to `backend/app/config/agents/`.
   - Define and document a unified schema for agent configuration.
   - Implement schema validation in AgentRegistry.

3. **Enhance AgentRegistry**
   - Refactor to load all agent configs at startup.
   - Support dynamic agent instantiation based on config.
   - Maintain backward compatibility with existing agent status management.

4. **Update main.py**
   - Remove hardcoded agent instantiation.
   - Instantiate agents dynamically from AgentRegistry using loaded configs.

#### Phase 2: Model Management Integration
1. **Dynamic Model Assignment**
   - Ensure ModelManager supports loading models as specified in agent configs.
   - On agent instantiation, assign the correct model based on config.

2. **Model Validation**
   - On agent startup, validate that the assigned model matches the agent's expected features/capabilities.

#### Phase 3: API and UI Updates
1. **Agent Management API**
   - Add endpoints to list, create, and manage agents based on configuration.
   - Support runtime agent reloads and status queries.

2. **Frontend Updates**
   - Update UI to display agent configurations, status, and allow management actions.

#### Phase 4: Testing and Migration
1. **Unit and Integration Tests**
   - Test agent instantiation, configuration validation, and model assignment.
   - Ensure backward compatibility with existing agents.

2. **Migration**
   - Gradually migrate existing agents to the new framework.
   - Deprecate legacy agent classes once migration is complete.

---

## Example Unified Agent Configuration

```yaml
agent_id: "wifi_agent"
name: "WiFiAgent"
description: "WiFi anomaly detection using ML models"
agent_type: "ml_based"  # ml_based, rule_based, hybrid
process_filters: ["hostapd", "wpa_supplicant"]
model_path: "/app/models/wifi_anomaly_model.pkl"
capabilities:
  - "Authentication failure detection"
  - "Deauthentication flood detection"
  - "Beacon frame flood detection"
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

---

## File Structure

```
backend/app/mcp_service/agents/
├── __init__.py
├── base_agent.py
├── generic_agent.py         # New: configuration-driven agent
├── ml_based_agent.py        # New/refactored
├── rule_based_agent.py      # New/refactored
├── hybrid_agent.py          # Optional/future
└── legacy/
    ├── wifi_agent.py        # To be deprecated
    └── log_level_agent.py   # To be deprecated

backend/app/config/agents/
├── wifi_agent.yaml
├── dns_agent.yaml
├── system_agent.yaml
├── log_level_agent.yaml
└── network_agent.yaml

backend/app/mcp_service/components/
├── agent_registry.py        # Enhanced for config-driven agents
├── model_manager.py
└── configuration_manager.py # New (optional)
```

---

## Testing Strategy

- **Unit Tests:** For agent instantiation, config validation, and model assignment.
- **Integration Tests:** For end-to-end agent lifecycle and anomaly detection.
- **Migration Tests:** Ensure legacy agents produce the same results as new generic agents.

---

## Timeline

- **Week 1:** Core framework refactor and config schema.
- **Week 2:** Model management integration and migration of existing agents.
- **Week 3:** API/UI updates and testing.
- **Week 4:** Documentation and deployment.

---

## Backward Compatibility

- Maintain legacy agent support during migration.
- Ensure API endpoints and Redis status updates remain compatible.
- Gradually deprecate old agent classes after successful migration.

---

## Summary

The codebase is well-positioned for a generic, configuration-driven agent framework. The main enhancements required are:
- Implementing a unified configuration schema and validation.
- Refactoring agent instantiation to be fully config-driven.
- Creating generic agent classes for ML-based and rule-based logic.
- Updating the registry, API, and UI for dynamic agent management.

This will enable scalable, maintainable, and flexible agent deployment in MCP.