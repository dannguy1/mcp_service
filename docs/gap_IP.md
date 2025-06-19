# MCP Gap Remediation – Implementation Plan

This plan outlines actionable steps to address the gaps identified in the MCP codebase, mapped to responsible areas, deliverables, and suggested priorities.

---

## 1. Protocol Definition & Agent Interoperability

**Objective:**  
Formalize and document the MCP protocol for agent interaction.

---

### Implementation Details

#### 1.1. Define the `BaseAgent` Abstract Class

- Create a new file: `mcp/agents/base.py`.
- Use Python’s `abc` module to define an abstract base class called `BaseAgent`.
- The `BaseAgent` must specify the following abstract methods and properties:
    - `name: str` (property): Unique agent name.
    - `log_type: str` (property): The type of logs this agent processes (e.g., "wifi", "firewall").
    - `load_model(self, model_path: str) -> None`: Load a pre-trained model from disk.
    - `extract_features(self, log_entry: LogEntry) -> Features`: Convert a log entry to feature vector.
    - `infer(self, features: Features) -> InferenceResult`: Run inference on features.
    - `detect_anomaly(self, log_entry: LogEntry) -> Optional[Anomaly]`: Full pipeline: extract features, infer, and return anomaly if detected.
    - `get_supported_log_schema(self) -> Dict`: Return the expected log schema for this agent.
- All agents must inherit from `BaseAgent` and implement these methods.

#### 1.2. Define Data Contracts with Pydantic Models

- Create a new module: `mcp/models/`.
- Define the following Pydantic models:
    - `LogEntry`: Represents a single log entry (fields: timestamp, source, type, payload, etc.).
    - `Features`: Represents extracted features (fields: Dict[str, Any]).
    - `InferenceResult`: Represents model inference output (fields: score, label, etc.).
    - `Anomaly`: Represents an anomaly (fields: log_entry, agent_name, score, label, detected_at, etc.).
    - `ExportRecord`: Represents a record for export (fields: log_entry, anomaly, agent_name, etc.).
- All agent and service code must use these models for type safety and validation.

#### 1.3. Protocol Reference Documentation

- Create `docs/protocol_reference.md`.
- Document:
    - The purpose of the protocol.
    - The required interface (`BaseAgent`) and method signatures.
    - The structure and fields of each Pydantic model.
    - Example agent implementation.
    - Example log processing and anomaly detection flow.

#### 1.4. Protocol Compliance Tests

- In `tests/unit/agents/`, add tests that:
    - Ensure all agents inherit from `BaseAgent`.
    - Validate that required methods are implemented.
    - Check that agents correctly process logs and return expected data types.

#### 1.5. Versioning and Extensibility

- Add a `protocol_version` property to `BaseAgent`.
- Document how to extend the protocol for new log types or agent capabilities.

---

**Deliverables:**  
- `mcp/agents/base.py` (BaseAgent interface)
- `mcp/models/` (Pydantic models)
- `docs/protocol_reference.md`
- Unit tests for protocol compliance

**Priority:** High

**Objective:**  
Formalize and document the MCP protocol for agent interaction.

**Actions:**
- Define a `BaseAgent` abstract class (Python ABC) specifying required methods (log retrieval, feature extraction, inference, anomaly reporting).
- Create Pydantic models for all data contracts (logs, features, anomalies, export formats).
- Write a protocol reference guide for agent developers.
- Add protocol compliance checks/tests.

**Deliverables:**  
- `mcp/agents/base.py` (BaseAgent interface)
- `mcp/models/` (Pydantic models)
- `docs/protocol_reference.md`
- Unit tests for protocol compliance

**Priority:** High

---

## 2. Agent Plug-and-Play Architecture

**Objective:**  
Enable dynamic discovery and registration of agents, so new domain-specific agents can be integrated without modifying the core system.

---

### Implementation Details

#### 2.1. Implement Agent Registry

- Create a new file: `mcp/agents/registry.py`.
- Define an `AgentRegistry` class with the following responsibilities:
    - Maintain a mapping of agent names to agent classes.
    - Provide methods to register, unregister, and retrieve agents.
    - Support automatic discovery of agent classes in a specified directory (e.g., `mcp/agents/`).
    - Optionally, support registration via Python entry points for external agent packages.

**Example:**
```python
# filepath: mcp/agents/registry.py
import importlib
import pkgutil
from typing import Dict, Type
from .base import BaseAgent

class AgentRegistry:
    _agents: Dict[str, Type[BaseAgent]] = {}

    @classmethod
    def register(cls, agent_cls: Type[BaseAgent]):
        cls._agents[agent_cls.name] = agent_cls

    @classmethod
    def get_agent(cls, name: str) -> Type[BaseAgent]:
        return cls._agents[name]

    @classmethod
    def discover_agents(cls, package="mcp.agents"):
        for _, modname, _ in pkgutil.iter_modules([__path__[0]]):
            module = importlib.import_module(f"{package}.{modname}")
            for attr in dir(module):
                obj = getattr(module, attr)
                if isinstance(obj, type) and issubclass(obj, BaseAgent) and obj is not BaseAgent:
                    cls.register(obj)
```

#### 2.2. Agent Self-Registration

- In each agent implementation (e.g., `wifi_agent.py`), add code to self-register with the registry upon import:
```python
# filepath: mcp/agents/wifi_agent.py
from .base import BaseAgent
from .registry import AgentRegistry

class WifiAgent(BaseAgent):
    name = "wifi"
    # ...implement required methods...

AgentRegistry.register(WifiAgent)
```

#### 2.3. Dynamic Agent Loading

- In the main service or wherever agents are needed:
    - Use `AgentRegistry.discover_agents()` at startup to auto-register all agents in the agents directory.
    - Retrieve and instantiate agents by name as needed.

#### 2.4. Plugin Support (Optional/Advanced)

- For external agent packages, use Python entry points (e.g., via `setup.py` or `pyproject.toml`) to allow third-party agents to register themselves.
- Document the entry point group (e.g., `mcp.agents`) and provide an example.

#### 2.5. Documentation

- In `docs/agent_development.md`, document:
    - How to implement a new agent.
    - How to register an agent with the registry.
    - How to package an agent for external/plugin use.
    - How dynamic discovery works.

#### 2.6. Tests

- In `tests/unit/agents/`, add tests to:
    - Ensure agents are registered and discoverable.
    - Validate dynamic loading and instantiation.
    - Test error handling for duplicate or missing agent names.

---

**Deliverables:**  
- `mcp/agents/registry.py` (AgentRegistry implementation)
- Updated agent modules with self-registration
- Dynamic discovery logic in service startup
- `docs/agent_development.md`
- Unit tests for registry and dynamic loading

**Priority:** High

**Objective:**  
Enable dynamic discovery and registration of agents.

**Actions:**
- Implement an agent registry or plugin loader (e.g., using Python entry points or dynamic imports).
- Refactor agent loading to use the registry.
- Document agent packaging and registration process.

**Deliverables:**  
- `mcp/agents/registry.py`
- Updated agent loading logic in main service
- `docs/agent_development.md`

**Priority:** High

---



**Objective:**  
Abstract log access and improve robustness.

**Actions:**
- Refactor `DataService` for schema abstraction and error handling.
- Add configuration for log source schemas (YAML/JSON).
- Implement connection pooling and retry logic.
- Add support for schema evolution.

**Deliverables:**  
- `mcp/services/data_service.py` (refactored)
- Config files for log schemas
- Unit tests for error handling and schema changes

**Priority:** High

---




**Objective:**  
Abstract log access, support multiple schemas, and improve robustness and configurability of log extraction.

---

### Implementation Details

#### 3.1. Refactor DataService for Schema Abstraction

- Refactor or create `mcp/services/data_service.py` to:
    - Provide a unified interface for log retrieval, anomaly storage, and cache access.
    - Accept log schema definitions at runtime (e.g., via configuration files).
    - Support multiple log types and schemas (e.g., Wi-Fi, firewall, DNS).
    - Use Pydantic models (from protocol section) for log validation and parsing.

**Example:**
```python
# filepath: mcp/services/data_service.py
from typing import List, Type
from mcp.models import LogEntry

class DataService:
    def __init__(self, pg_config, sqlite_config, redis_config, log_schemas: dict):
        # Initialize DB connections and cache
        self.log_schemas = log_schemas

    def get_logs(self, log_type: str, start_time=None, end_time=None) -> List[LogEntry]:
        # Use self.log_schemas[log_type] to parse/validate logs
        # Query PostgreSQL for logs of the given type and time range
        # Return as list of LogEntry Pydantic models
        pass

    def store_anomaly(self, anomaly):
        # Store anomaly in SQLite
        pass

    # ...other methods...
```

#### 3.2. Log Schema Configuration

- Create a directory `mcp/config/log_schemas/` with YAML or JSON files describing each supported log schema.
    - Example: `wifi.yaml`, `firewall.yaml`
- Each schema file should define:
    - Field names and types
    - Required/optional fields
    - Any transformations or mappings needed

#### 3.3. Error Handling and Connection Pooling

- Use robust error handling for all DB and cache operations.
- Implement connection pooling for PostgreSQL (e.g., using `psycopg2.pool` or SQLAlchemy).
- Add retry logic for transient errors (e.g., using `tenacity`).

#### 3.4. Support for Schema Evolution

- Allow schema files to be updated without code changes.
- Validate logs against the current schema version.
- Log warnings or errors for schema mismatches.

#### 3.5. Configuration Management

- Accept DB and schema configuration via environment variables or config files.
- Document all configuration options in `docs/deployment.md`.

#### 3.6. Tests

- In `tests/unit/services/`, add tests for:
    - Log retrieval with different schemas
    - Error handling and retries
    - Schema validation and evolution

---

**Deliverables:**  
- Refactored `mcp/services/data_service.py`
- `mcp/config/log_schemas/` with example schema files
- Connection pooling and retry logic
- Configuration documentation in `docs/deployment.md`
- Unit tests for DataService

**Priority:**


**Objective:**  
Complete and document all API endpoints.

**Actions:**
- Implement missing endpoints (agent management, export status, configuration).
- Ensure OpenAPI schema is accurate and complete.
- Add API usage examples to documentation.

**Deliverables:**  
- `mcp/api/endpoints/`
- Updated OpenAPI docs
- `docs/api_usage.md`

**Priority:** High

---

## 3. Log Extraction & DataService

**Objective:**  
Abstract log access, support multiple schemas, and improve robustness and configurability of log extraction.

---

### Implementation Details

#### 3.1. Refactor DataService for Schema Abstraction

- Refactor or create `mcp/services/data_service.py` to:
    - Provide a unified interface for log retrieval, anomaly storage, and cache access.
    - Accept log schema definitions at runtime (e.g., via configuration files).
    - Support multiple log types and schemas (e.g., Wi-Fi, firewall, DNS).
    - Use Pydantic models (from protocol section) for log validation and parsing.

#### 3.2. Log Schema Configuration

- Create a directory `mcp/config/log_schemas/` with YAML or JSON files describing each supported log schema.
    - Example: `wifi.yaml`, `firewall.yaml`
- Each schema file should define:
    - Field names and types
    - Required/optional fields
    - Any transformations or mappings needed

#### 3.3. Error Handling and Connection Pooling

- Use robust error handling for all DB and cache operations.
- Implement connection pooling for PostgreSQL (e.g., using `psycopg2.pool` or SQLAlchemy).
- Add retry logic for transient errors (e.g., using `tenacity`).

#### 3.4. Support for Schema Evolution

- Allow schema files to be updated without code changes.
- Validate logs against the current schema version.
- Log warnings or errors for schema mismatches.

#### 3.5. Configuration Management

- Accept DB and schema configuration via environment variables or config files.
- Document all configuration options in `docs/deployment.md`.

#### 3.6. Tests

- In `tests/unit/services/`, add tests for:
    - Log retrieval with different schemas
    - Error handling and retries
    - Schema validation and evolution

---

**Deliverables:**  
- Refactored `mcp/services/data_service.py`
- `mcp/config/log_schemas/` with example schema files
- Connection pooling and retry logic
- Configuration documentation in `docs/deployment.md`
- Unit tests for DataService

**Priority:** High

---

## 4. Model Loading & Inference

**Objective:**  
Robust model management, versioning, and deployment for agent inference.

---

### Implementation Details

#### 4.1. ModelManager Enhancements

- Refactor or create `mcp/models/model_manager.py` to:
    - Support loading models from disk by agent name and version.
    - Validate model files (e.g., checksum, schema, metadata).
    - Provide methods for listing available models and versions.
    - Expose a method for agents to request a specific model version.

#### 4.2. Model Versioning

- Define a model directory structure:  
  `models/{agent_name}/{version}/model.bin` (or similar)
- Store metadata (e.g., version, date, checksum) in a `metadata.json` file alongside each model.

#### 4.3. Model Deployment/Update Workflow

- Document the process for deploying new models:
    - How to upload/replace model files.
    - How to trigger reload (manual or via API).
    - How to roll back to previous versions.

#### 4.4. Automated Model Update Endpoint or Watcher

- Implement a FastAPI endpoint or background watcher to detect new/updated models and reload them as needed.
- Log model load events and errors.

#### 4.5. Tests

- In `tests/unit/models/`, add tests for:
    - Model loading, validation, and version selection.
    - Error handling for missing/corrupt models.

---

**Deliverables:**  
- Enhanced `mcp/models/model_manager.py`
- Model directory structure and metadata format
- Model deployment/update documentation in `docs/model_deployment.md`
- API endpoint or watcher for model updates
- Unit tests for model management

**Priority:** Medium

---

## 5. Anomaly Storage & Export

**Objective:**  
Enhance export flexibility, filtering, batch processing, and status tracking.

---

### Implementation Details

#### 5.1. Flexible Export Filters

- Update or create `mcp/export/exporter.py` to:
    - Accept filter parameters (date range, agent, anomaly type, etc.) for export jobs.
    - Validate and apply filters using Pydantic models.

#### 5.2. Batch Export Processing

- Implement batch processing for large exports to avoid memory issues.
- Stream data to export files in chunks.

#### 5.3. Export Status/Progress Tracking

- Use Redis to track export job status and progress.
- Assign unique IDs to export jobs.
- Provide methods to query status by job ID.

#### 5.4. Export History/Audit Log

- Store metadata about each export (job ID, filters, user, timestamp, status) in a SQLite or Redis table.
- Provide API endpoints to list export history and details.

#### 5.5. API Endpoints

- Add or update FastAPI endpoints for:
    - Starting an export job
    - Checking export status/progress
    - Listing export history
    - Downloading export files

#### 5.6. Tests

- In `tests/unit/export/` and `tests/integration/`, add tests for:
    - Export filtering and batching
    - Status tracking and history
    - API endpoints

---

**Deliverables:**  
- Enhanced `mcp/export/exporter.py`
- Export status tracking in Redis
- Export history/audit log
- FastAPI endpoints for export management
- Unit and integration tests for export

**Priority:** Medium

---

## 6. FastAPI Web Server & API

**Objective:**  
Complete and document all API endpoints for management, export, and health monitoring.

---

### Implementation Details

#### 6.1. Implement Missing Endpoints

- Add endpoints for:
    - Agent management (list, enable/disable, reload)
    - Export management (start, status, history, download)
    - Configuration (get/set runtime config)
    - Health and readiness checks

#### 6.2. OpenAPI Schema

- Ensure all endpoints are fully documented with FastAPI’s OpenAPI support.
- Use Pydantic models for request/response schemas.

#### 6.3. API Usage Documentation

- In `docs/api_usage.md`, provide:
    - Example requests and responses for each endpoint
    - Authentication/authorization details (if any)
    - Error codes and troubleshooting

#### 6.4. Tests

- In `tests/integration/api/`, add tests for:
    - All API endpoints (success and error cases)
    - OpenAPI schema validation

---

**Deliverables:**  
- Complete API endpoints in `mcp/api/endpoints/`
- Accurate OpenAPI schema
- API usage documentation in `docs/api_usage.md`
- Integration tests for API

**Priority:**
## 7. Notification System

**Objective:**  
Make notifications pluggable and configurable.

**Actions:**
- Refactor notification logic to support multiple backends (email, Slack, etc.).
- Add configuration for notification channels.
- Document notification setup.

**Deliverables:**  
- `mcp/notifications/`
- Notification config files
- `docs/notifications.md`

**Priority:** Medium

---

## 8. Configuration & Deployment

**Objective:**  
Improve deployment and configuration experience.

**Actions:**
- Expand deployment and configuration documentation.
- Provide setup scripts for local development and production.
- Add sample `.env` and config files.

**Deliverables:**  
- `docs/deployment.md`
- `scripts/setup_dev.sh`, `scripts/setup_prod.sh`
- Sample config files

**Priority:** Medium

---

## 9. Testing & Validation

**Objective:**  
Increase test coverage and reliability.

**Actions:**
- Add unit tests for all new/refactored modules.
- Implement integration tests for end-to-end flows (log extraction, agent inference, export).
- Add protocol compliance and export tests.

**Deliverables:**  
- `tests/unit/`
- `tests/integration/`
- Test coverage reports

**Priority:** High

---

## 10. Documentation

**Objective:**  
Provide comprehensive developer and user documentation.

**Actions:**
- Write protocol reference and agent development guide.
- Add API usage and deployment examples.
- Maintain a changelog and roadmap.

**Deliverables:**  
- `docs/protocol_reference.md`
- `docs/agent_development.md`
- `docs/api_usage.md`
- `docs/CHANGELOG.md`, `docs/ROADMAP.md`

**Priority:** High

---

# Implementation Timeline & Ownership

| Task Area                | Priority | Suggested Owner | Target Completion |
|--------------------------|----------|-----------------|------------------|
| Protocol Definition      | High     | Core Dev Lead   | Week 1           |
| Agent Plug-and-Play      | High     | Core Dev        | Week 1           |
| Log Extraction/DataSvc   | High     | Backend Dev     | Week 2           |
| Model Loading/Inference  | Medium   | ML Engineer     | Week 2           |
| Anomaly Storage/Export   | Medium   | Backend Dev     | Week 3           |
| FastAPI API              | High     | API Dev         | Week 2           |
| Notification System      | Medium   | Backend Dev     | Week 3           |
| Config/Deployment        | Medium   | DevOps          | Week 3           |
| Testing                  | High     | QA/All Devs     | Ongoing          |
| Documentation            | High     | All/Tech Writer | Ongoing          |

---

# Tracking & Review

- Review progress weekly in team meetings.
- Update this plan and the gap analysis as issues are resolved.
- Use GitHub issues/boards to track deliverables.