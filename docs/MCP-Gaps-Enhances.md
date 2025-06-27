### **MCP/OPMAS: Feature Work and Improvement Plan**

Date: June 26, 2025  
Location: Huntington Beach, California, United States  
**1\. Introduction**

The current design successfully addresses the core challenge of standardizing agent and model interactions for log analysis. The implementation plan for the Generic Agent Framework is clear and provides a solid migration path from legacy, hardcoded agents.

The following feature plan identifies critical capabilities needed to operationalize this framework, focusing on agent lifecycle management, real-time configuration, inter-agent collaboration, and proactive response mechanisms. The features are grouped into tiers based on priority.

**2\. Tier 1: Foundational Operational Capabilities**

These features are essential for making the Generic Agent Framework truly manageable and operational beyond a simple execution script.

**2.1. Feature: Agent Lifecycle Management Engine**

* **Current State:** The current design specifies that agents are dynamically created by the AgentRegistry. However, the actual process of starting, stopping, and monitoring these agents as OS processes or containers is handled by a main.py script with "hardcoded agent initialization and lifecycle management". The ModelManagement.md document describes a mature lifecycle for models, but a corresponding engine for agents is missing.  
* **Problem/Gap:** The system lacks a robust mechanism to manage the runtime state of agents. There is no clear way for an administrator to start or stop a specific agent without restarting the entire MCP service, and no automated way to handle agent crashes.  
* **Proposed Solution:**  
  1. **Introduce an Agent Controller / Process Manager:** A central service responsible for physically launching, stopping, and monitoring agent processes/containers.  
  2. **Define a Lifecycle API:** Implement the agent management API endpoints outlined in the implementation plan ("List available agent configurations", "Create agents from configuration") and expand them with POST /agents/{agent\_id}/start and POST /agents/{agent\_id}/stop.  
  3. **Containerize Agents:** Package each agent type as a Docker container. The Agent Controller would then interact with the Docker daemon or a container orchestrator (like Kubernetes) to manage the agent lifecycle. This simplifies dependency management and resource isolation.  
  4. **Implement Health Checks:** Agents should emit a periodic heartbeat (e.g., via Redis or NATS). The Agent Controller will monitor these heartbeats and automatically restart agents that fail, according to a defined policy (e.g., max retries).  
* **Benefit:** Provides essential operational control, enables high availability, and allows for managing individual agents without system-wide downtime.

**2.2. Feature: Dynamic Configuration Management API & UI**

* **Current State:** Agent configuration is driven by YAML files located in backend/app/config/agents/. The implementation plan includes a "Frontend updates" phase with an "Agent configuration interface", but the backend support is not detailed.  
* **Problem/Gap:** Modifying an agent's behavior (e.g., changing a threshold, updating a regex pattern in exclude\_patterns) requires editing a YAML file and restarting the agent or the entire service. This is inflexible and not suitable for non-developer users.  
* **Proposed Solution:**  
  1. **Database as Source of Truth:** While YAML files can define the *defaults* for an agent, the active configuration should be stored in a relational database (like the existing PostgreSQL).  
  2. **Implement Configuration API:** Create GET /agents/{agent\_id}/config and PUT /agents/{agent\_id}/config endpoints that allow reading and writing agent configurations to the database.  
  3. **Enable Hot-Reloading:** Design a mechanism for agents to fetch and apply updated configurations without restarting. This can be achieved via:  
     * A NATS control message that triggers a configuration refresh.  
     * The agent periodically checking the API for config updates.  
  4. **Build the UI:** Develop the frontend interface as planned, backed by the new configuration API, allowing users to view and edit agent parameters in real time.  
* **Benefit:** Allows for dynamic, real-time tuning of agent behavior by administrators through a UI, dramatically improving system flexibility and usability.

**3\. Tier 2: Enterprise Features & Closing the Loop**

These features build on the Tier 1 foundation to make the system more intelligent, proactive, and integrated into operational workflows.

**3.1. Feature: Inter-Agent Orchestration Engine**

* **Current State:** The current architecture describes agents that operate independently. Each agent retrieves logs, performs analysis, and stores anomalies. There is no mechanism for agents to share context or for their findings to be correlated.  
* **Problem/Gap:** The system cannot identify complex problems that manifest across multiple domains. For example, it cannot link a WiFiAgent finding of "deauthentication flood" to a NetworkAgent finding of "port scan" from a specific IP.  
* **Proposed Solution:**  
  1. **Introduce an Orchestrator Agent:** A special agent that subscribes to the findings of all other domain agents.  
  2. **Develop Correlation Rules:** Create a system (configurable via API/UI) to define rules that correlate findings. For example: IF (Finding A from WiFiAgent) AND (Finding B from SystemAgent) within (Time T) \-\> Create (High-Priority Correlated Finding C).  
  3. **Contextual Enrichment:** The Orchestrator can enrich findings with additional context from the DataService or other sources before making a final determination.  
* **Benefit:** Elevates the system from a collection of simple detectors to an intelligent analysis platform capable of identifying complex, high-impact events and reducing alert noise.

**3.2. Feature: Proactive Action & Response Framework**

* **Current State:** The system is focused on detection and storage of anomalies in Redis/SQLite. The data flow ends with storage and export; it does not "close the loop" by taking action.  
* **Problem/Gap:** The system is purely passive. It can tell you something is wrong but cannot do anything about it. The "P" in OPMAS (Proactive) is not yet realized.  
* **Proposed Solution:**  
  1. **Introduce an Action Executor Service:** A secure, sandboxed service that can perform actions on external systems (e.g., connect to an OpenWRT device via SSH to run a command).  
  2. **Define Action Playbooks:** Allow administrators to define simple "playbooks" linked to specific findings (especially correlated findings from the Orchestrator). For example: ON (Finding C) \-\> EXECUTE (Action 'block-ip' on 'Action Executor' with parameters from Finding).  
  3. **API for Actions:** The Orchestrator would use an internal API to command the Action Executor.  
* **Benefit:** Transforms OPMAS into a truly proactive system that can perform preventive measures or automated remediation, directly addressing its core mission.

**3.3. Feature: Real-time Alerting & Notification Engine**

* **Current State:** The architecture diagram vaguely mentions "Notification Systems" as an external component, but no internal mechanism for generating or routing alerts is described.  
* **Problem/Gap:** There is no way to immediately notify an administrator when a critical anomaly is detected. They would have to be actively watching the UI or database.  
* **Proposed Solution:**  
  1. **Introduce a Notification Service:** A service that subscribes to all agent findings.  
  2. **Configurable Alerting Rules:** Create a UI and API for administrators to define alerting rules. For example:  
     * IF (Finding Severity \>= 4\) AND (Agent Name \== 'SecurityAgent') \-\> SEND (Email to security-team@example.com).  
     * IF (Finding Type \== 'CorrelatedFindingC') \-\> SEND (Webhook to PagerDuty).  
  3. **Integrations:** Build out-of-the-box integrations for common notification channels like email, Slack, and webhooks.  
* **Benefit:** Ensures that critical events are immediately brought to the attention of the appropriate personnel, enabling timely manual intervention.

**4\. Tier 3: Architectural Enhancements**

These are longer-term improvements that would enhance the performance, scalability, and power of the core architecture.

**4.1. Feature: Transition to a Streaming Data Architecture**

* **Current State:** The workflow is primarily batch-based. Agents query the PostgreSQL database for recent logs on an interval (analysis\_interval).  
* **Problem/Gap:** This polling-based approach introduces latency between when a log event occurs and when it is analyzed. It can also put a periodic, spiky load on the PostgreSQL database.  
* **Proposed Solution:**  
  1. **Introduce a Message Bus:** Implement a high-throughput message bus like NATS or Kafka between the Log Collector and the agents.  
  2. **Update Log Ingestion:** The Log Collector would now publish logs directly to the message bus instead of writing to PostgreSQL.  
  3. **Update Agents:** Agents would become real-time consumers, subscribing to log streams from the message bus instead of polling the database. PostgreSQL could still be used for long-term archival.  
* **Benefit:** Enables near real-time anomaly detection, reduces latency significantly, and provides a more scalable and resilient data ingestion pipeline.

**5\. Summary Roadmap**

| Tier | Feature | Description |
| :---- | :---- | :---- |
| **1** | **Agent Lifecycle Management Engine** | Provides the core operational ability to start, stop, and monitor agents as independent processes or containers. |
| **1** | **Dynamic Configuration API & UI** | Allows real-time management of agent rules and parameters via a UI, without requiring service restarts. |
| **2** | **Inter-Agent Orchestration Engine** | Correlates findings from multiple agents to detect complex, multi-domain events and reduce alert noise. |
| **2** | **Proactive Action & Response Framework** | Closes the loop by enabling the system to execute predefined actions in response to specific findings. |
| **2** | **Real-time Alerting & Notification Engine** | Pushes critical alerts to external systems like email, Slack, or PagerDuty for immediate notification. |
| **3** | **Transition to Streaming Architecture** | Re-architects the data flow from batch-polling to a real-time stream for lower latency and better scalability. |

