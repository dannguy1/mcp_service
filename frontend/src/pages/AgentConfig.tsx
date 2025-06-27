import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Form,
  Alert,
  Spinner,
  Modal,
  Badge,
  Row,
  Col,
  Nav,
  Tab,
  Accordion,
  ListGroup,
  OverlayTrigger,
  Tooltip
} from 'react-bootstrap';
import {
  FaSave,
  FaCheck,
  FaTimes,
  FaPlus,
  FaTrash,
  FaCopy,
  FaDownload,
  FaUpload,
  FaEye,
  FaEdit,
  FaCog,
  FaExclamationTriangle,
  FaInfoCircle,
  FaQuestionCircle,
  FaFileCode,
  FaHistory
} from 'react-icons/fa';
import { endpoints } from '../services/api';
import type { Agent, AgentConfig, AgentConfigValidationResponse, ConfigTemplates } from '../services/types';

const AgentConfig: React.FC = () => {
  // State management
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [originalConfig, setOriginalConfig] = useState<AgentConfig | null>(null);
  const [templates, setTemplates] = useState<ConfigTemplates | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<AgentConfigValidationResponse | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [activeTab, setActiveTab] = useState('basic');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Load agents and templates on component mount
  useEffect(() => {
    loadAgents();
    loadTemplates();
  }, []);

  // Load agents list
  const loadAgents = async () => {
    try {
      setIsLoading(true);
      const agentsData = await endpoints.listAgents();
      setAgents(agentsData);
    } catch (err) {
      setError('Failed to load agents');
      console.error('Error loading agents:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Load configuration templates
  const loadTemplates = async () => {
    try {
      const templatesData = await endpoints.getConfigTemplates();
      setTemplates(templatesData);
    } catch (err) {
      console.error('Error loading templates:', err);
    }
  };

  // Load agent configuration
  const loadAgentConfig = async (agent: Agent) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const configData = await endpoints.getAgentConfig(agent.id);
      setConfig(configData.config);
      setOriginalConfig(configData.config);
      setSelectedAgent(agent);
      setValidationResult(null);
      setActiveTab('basic');
    } catch (err: any) {
      if (err.response?.status === 404) {
        // Agent has no configuration, create a new one
        const newConfig: AgentConfig = {
          agent_id: agent.id,
          name: agent.name,
          description: agent.description || '',
          agent_type: 'ml_based',
          process_filters: agent.process_filters || [],
          model_path: agent.model_path,
          capabilities: agent.capabilities || [],
          analysis_rules: {
            lookback_minutes: 5,
            analysis_interval: 60,
            severity_mapping: {}
          }
        };
        setConfig(newConfig);
        setOriginalConfig(newConfig);
        setSelectedAgent(agent);
      } else {
        setError('Failed to load agent configuration');
        console.error('Error loading agent config:', err);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Validate configuration
  const validateConfig = async () => {
    if (!config || !selectedAgent) return;

    try {
      setIsValidating(true);
      const result = await endpoints.validateAgentConfig(selectedAgent.id, config);
      setValidationResult(result);
      
      if (result.is_valid) {
        setSuccess('Configuration is valid!');
        setTimeout(() => setSuccess(null), 3000);
      }
    } catch (err) {
      setError('Failed to validate configuration');
      console.error('Error validating config:', err);
    } finally {
      setIsValidating(false);
    }
  };

  // Save configuration
  const saveConfig = async () => {
    if (!config || !selectedAgent) return;

    try {
      setIsSaving(true);
      setError(null);
      
      await endpoints.saveAgentConfig(selectedAgent.id, config);
      setOriginalConfig(config);
      setSuccess('Configuration saved successfully!');
      setTimeout(() => setSuccess(null), 3000);
      
      // Reload agents to get updated data
      await loadAgents();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save configuration');
      console.error('Error saving config:', err);
    } finally {
      setIsSaving(false);
    }
  };

  // Delete configuration
  const deleteConfig = async () => {
    if (!selectedAgent) return;

    try {
      await endpoints.deleteAgentConfig(selectedAgent.id);
      setShowDeleteModal(false);
      setSelectedAgent(null);
      setConfig(null);
      setOriginalConfig(null);
      setSuccess('Configuration deleted successfully!');
      setTimeout(() => setSuccess(null), 3000);
      
      // Reload agents
      await loadAgents();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete configuration');
      console.error('Error deleting config:', err);
    }
  };

  // Apply template
  const applyTemplate = (templateType: keyof ConfigTemplates) => {
    if (!templates || !selectedAgent) return;

    const template = templates[templateType];
    const newConfig: AgentConfig = {
      ...template,
      agent_id: selectedAgent.id,
      name: selectedAgent.name,
      description: selectedAgent.description || template.description,
      process_filters: selectedAgent.process_filters || template.process_filters,
      model_path: selectedAgent.model_path || template.model_path
    };

    setConfig(newConfig);
    setShowTemplateModal(false);
    setSuccess(`Applied ${templateType} template`);
    setTimeout(() => setSuccess(null), 3000);
  };

  // Reset to original configuration
  const resetConfig = () => {
    if (originalConfig) {
      setConfig(originalConfig);
      setValidationResult(null);
      setError(null);
    }
  };

  // Check if configuration has changes
  const hasChanges = () => {
    if (!config || !originalConfig) return false;
    return JSON.stringify(config) !== JSON.stringify(originalConfig);
  };

  // Update configuration field
  const updateConfig = (path: string, value: any) => {
    if (!config) return;

    const pathParts = path.split('.');
    const newConfig = { ...config };
    let current: any = newConfig;

    for (let i = 0; i < pathParts.length - 1; i++) {
      if (!current[pathParts[i]]) {
        current[pathParts[i]] = {};
      }
      current = current[pathParts[i]];
    }

    current[pathParts[pathParts.length - 1]] = value;
    setConfig(newConfig);
    setValidationResult(null);
  };

  // Add capability
  const addCapability = () => {
    if (!config) return;
    const newCapabilities = [...config.capabilities, ''];
    updateConfig('capabilities', newCapabilities);
  };

  // Update capability
  const updateCapability = (index: number, value: string) => {
    if (!config) return;
    const newCapabilities = [...config.capabilities];
    newCapabilities[index] = value;
    updateConfig('capabilities', newCapabilities);
  };

  // Remove capability
  const removeCapability = (index: number) => {
    if (!config) return;
    const newCapabilities = config.capabilities.filter((_, i) => i !== index);
    updateConfig('capabilities', newCapabilities);
  };

  // Add process filter
  const addProcessFilter = () => {
    if (!config) return;
    const newFilters = [...config.process_filters, ''];
    updateConfig('process_filters', newFilters);
  };

  // Update process filter
  const updateProcessFilter = (index: number, value: string) => {
    if (!config) return;
    const newFilters = [...config.process_filters];
    newFilters[index] = value;
    updateConfig('process_filters', newFilters);
  };

  // Remove process filter
  const removeProcessFilter = (index: number) => {
    if (!config) return;
    const newFilters = config.process_filters.filter((_, i) => i !== index);
    updateConfig('process_filters', newFilters);
  };

  // Add severity mapping
  const addSeverityMapping = () => {
    if (!config?.analysis_rules?.severity_mapping) return;
    const newMapping = { ...config.analysis_rules.severity_mapping, 'new_anomaly': 3 };
    updateConfig('analysis_rules.severity_mapping', newMapping);
  };

  // Update severity mapping
  const updateSeverityMapping = (anomalyType: string, severity: number) => {
    if (!config?.analysis_rules?.severity_mapping) return;
    const newMapping = { ...config.analysis_rules.severity_mapping, [anomalyType]: severity };
    updateConfig('analysis_rules.severity_mapping', newMapping);
  };

  // Remove severity mapping
  const removeSeverityMapping = (anomalyType: string) => {
    if (!config?.analysis_rules?.severity_mapping) return;
    const newMapping = { ...config.analysis_rules.severity_mapping };
    delete newMapping[anomalyType];
    updateConfig('analysis_rules.severity_mapping', newMapping);
  };

  if (isLoading && !selectedAgent) {
    return (
      <div className="d-flex justify-content-center align-items-center h-100">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center">
        <div>
          <h1 className="h3 mb-2">Agent Configuration</h1>
          <p className="text-muted">
            Manage agent configurations and settings
          </p>
        </div>
        <div className="d-flex gap-2">
          <Button
            variant="outline-info"
            size="sm"
            onClick={() => setShowTemplateModal(true)}
            disabled={!templates}
          >
            <FaFileCode className="me-1" />
            Templates
          </Button>
          <Button
            variant="outline-secondary"
            size="sm"
            onClick={() => setShowHistoryModal(true)}
          >
            <FaHistory className="me-1" />
            History
          </Button>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          <FaExclamationTriangle className="me-2" />
          {error}
        </Alert>
      )}

      {success && (
        <Alert variant="success" dismissible onClose={() => setSuccess(null)}>
          <FaCheck className="me-2" />
          {success}
        </Alert>
      )}

      <Row>
        {/* Agent Selection */}
        <Col md={4}>
          <Card>
            <Card.Header>
              <Card.Title className="mb-0">Select Agent</Card.Title>
            </Card.Header>
            <Card.Body>
              <ListGroup>
                {agents.map((agent) => (
                  <ListGroup.Item
                    key={agent.id}
                    action
                    active={selectedAgent?.id === agent.id}
                    onClick={() => loadAgentConfig(agent)}
                    className="d-flex justify-content-between align-items-center"
                  >
                    <div>
                      <strong>{agent.name}</strong>
                      <br />
                      <small className="text-muted">{agent.description}</small>
                    </div>
                    <Badge bg={agent.is_running ? 'success' : 'secondary'}>
                      {agent.is_running ? 'Running' : 'Stopped'}
                    </Badge>
                  </ListGroup.Item>
                ))}
              </ListGroup>
            </Card.Body>
          </Card>
        </Col>

        {/* Configuration Editor */}
        <Col md={8}>
          {selectedAgent && config ? (
            <Card>
              <Card.Header>
                <div className="d-flex justify-content-between align-items-center">
                  <Card.Title className="mb-0">
                    Configure: {selectedAgent.name}
                  </Card.Title>
                  <div className="d-flex gap-2">
                    <Button
                      variant="outline-warning"
                      size="sm"
                      onClick={resetConfig}
                      disabled={!hasChanges()}
                    >
                      <FaTimes className="me-1" />
                      Reset
                    </Button>
                    <Button
                      variant="outline-info"
                      size="sm"
                      onClick={validateConfig}
                      disabled={isValidating}
                    >
                      {isValidating ? (
                        <Spinner animation="border" size="sm" />
                      ) : (
                        <FaCheck className="me-1" />
                      )}
                      Validate
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={saveConfig}
                      disabled={isSaving || !hasChanges()}
                    >
                      {isSaving ? (
                        <Spinner animation="border" size="sm" />
                      ) : (
                        <FaSave className="me-1" />
                      )}
                      Save
                    </Button>
                    <Button
                      variant="outline-danger"
                      size="sm"
                      onClick={() => setShowDeleteModal(true)}
                    >
                      <FaTrash className="me-1" />
                      Delete
                    </Button>
                  </div>
                </div>
              </Card.Header>
              <Card.Body>
                {/* Validation Results */}
                {validationResult && (
                  <Alert variant={validationResult.is_valid ? 'success' : 'warning'} className="mb-3">
                    <div className="d-flex align-items-center">
                      {validationResult.is_valid ? (
                        <FaCheck className="me-2" />
                      ) : (
                        <FaExclamationTriangle className="me-2" />
                      )}
                      <strong>
                        {validationResult.is_valid ? 'Configuration is valid' : 'Configuration has issues'}
                      </strong>
                    </div>
                    {validationResult.errors.length > 0 && (
                      <div className="mt-2">
                        <strong>Errors:</strong>
                        <ul className="mb-0">
                          {validationResult.errors.map((error, index) => (
                            <li key={index}>{error}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {validationResult.warnings.length > 0 && (
                      <div className="mt-2">
                        <strong>Warnings:</strong>
                        <ul className="mb-0">
                          {validationResult.warnings.map((warning, index) => (
                            <li key={index}>{warning}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </Alert>
                )}

                {/* Configuration Tabs */}
                <Tab.Container activeKey={activeTab} onSelect={(k) => setActiveTab(k || 'basic')}>
                  <Nav variant="tabs" className="mb-3">
                    <Nav.Item>
                      <Nav.Link eventKey="basic">Basic Settings</Nav.Link>
                    </Nav.Item>
                    <Nav.Item>
                      <Nav.Link eventKey="analysis">Analysis Rules</Nav.Link>
                    </Nav.Item>
                    <Nav.Item>
                      <Nav.Link eventKey="advanced">Advanced</Nav.Link>
                    </Nav.Item>
                  </Nav>

                  <Tab.Content>
                    {/* Basic Settings Tab */}
                    <Tab.Pane eventKey="basic">
                      <Form>
                        <Row>
                          <Col md={6}>
                            <Form.Group className="mb-3">
                              <Form.Label>Agent ID</Form.Label>
                              <Form.Control
                                type="text"
                                value={config.agent_id}
                                onChange={(e) => updateConfig('agent_id', e.target.value)}
                                disabled
                              />
                              <Form.Text className="text-muted">
                                Unique identifier for the agent
                              </Form.Text>
                            </Form.Group>
                          </Col>
                          <Col md={6}>
                            <Form.Group className="mb-3">
                              <Form.Label>Agent Type</Form.Label>
                              <Form.Select
                                value={config.agent_type}
                                onChange={(e) => updateConfig('agent_type', e.target.value)}
                              >
                                <option value="ml_based">ML-Based</option>
                                <option value="rule_based">Rule-Based</option>
                                <option value="hybrid">Hybrid</option>
                              </Form.Select>
                              <Form.Text className="text-muted">
                                Type of anomaly detection approach
                              </Form.Text>
                            </Form.Group>
                          </Col>
                        </Row>

                        <Form.Group className="mb-3">
                          <Form.Label>Name</Form.Label>
                          <Form.Control
                            type="text"
                            value={config.name}
                            onChange={(e) => updateConfig('name', e.target.value)}
                          />
                        </Form.Group>

                        <Form.Group className="mb-3">
                          <Form.Label>Description</Form.Label>
                          <Form.Control
                            as="textarea"
                            rows={3}
                            value={config.description}
                            onChange={(e) => updateConfig('description', e.target.value)}
                          />
                        </Form.Group>

                        <Form.Group className="mb-3">
                          <Form.Label>Model Path</Form.Label>
                          <Form.Control
                            type="text"
                            value={config.model_path || ''}
                            onChange={(e) => updateConfig('model_path', e.target.value || null)}
                            placeholder="/app/models/example_model.pkl"
                          />
                          <Form.Text className="text-muted">
                            Path to the model file (optional for rule-based agents)
                          </Form.Text>
                        </Form.Group>

                        <Form.Group className="mb-3">
                          <Form.Label>
                            Process Filters
                            <Button
                              variant="outline-primary"
                              size="sm"
                              className="ms-2"
                              onClick={addProcessFilter}
                            >
                              <FaPlus />
                            </Button>
                          </Form.Label>
                          {config.process_filters.map((filter, index) => (
                            <div key={index} className="d-flex gap-2 mb-2">
                              <Form.Control
                                type="text"
                                value={filter}
                                onChange={(e) => updateProcessFilter(index, e.target.value)}
                                placeholder="process_name"
                              />
                              <Button
                                variant="outline-danger"
                                size="sm"
                                onClick={() => removeProcessFilter(index)}
                              >
                                <FaTrash />
                              </Button>
                            </div>
                          ))}
                          {config.process_filters.length === 0 && (
                            <Form.Text className="text-muted">
                              No process filters specified (monitors all processes)
                            </Form.Text>
                          )}
                        </Form.Group>

                        <Form.Group className="mb-3">
                          <Form.Label>
                            Capabilities
                            <Button
                              variant="outline-primary"
                              size="sm"
                              className="ms-2"
                              onClick={addCapability}
                            >
                              <FaPlus />
                            </Button>
                          </Form.Label>
                          {config.capabilities.map((capability, index) => (
                            <div key={index} className="d-flex gap-2 mb-2">
                              <Form.Control
                                type="text"
                                value={capability}
                                onChange={(e) => updateCapability(index, e.target.value)}
                                placeholder="Capability description"
                              />
                              <Button
                                variant="outline-danger"
                                size="sm"
                                onClick={() => removeCapability(index)}
                              >
                                <FaTrash />
                              </Button>
                            </div>
                          ))}
                        </Form.Group>
                      </Form>
                    </Tab.Pane>

                    {/* Analysis Rules Tab */}
                    <Tab.Pane eventKey="analysis">
                      <Form>
                        <Row>
                          <Col md={6}>
                            <Form.Group className="mb-3">
                              <Form.Label>Lookback Minutes</Form.Label>
                              <Form.Control
                                type="number"
                                min="1"
                                max="1440"
                                value={config.analysis_rules.lookback_minutes || 5}
                                onChange={(e) => updateConfig('analysis_rules.lookback_minutes', parseInt(e.target.value))}
                              />
                              <Form.Text className="text-muted">
                                Minutes of historical data to analyze
                              </Form.Text>
                            </Form.Group>
                          </Col>
                          <Col md={6}>
                            <Form.Group className="mb-3">
                              <Form.Label>Analysis Interval (seconds)</Form.Label>
                              <Form.Control
                                type="number"
                                min="30"
                                max="3600"
                                value={config.analysis_rules.analysis_interval || 60}
                                onChange={(e) => updateConfig('analysis_rules.analysis_interval', parseInt(e.target.value))}
                              />
                              <Form.Text className="text-muted">
                                Seconds between analysis cycles
                              </Form.Text>
                            </Form.Group>
                          </Col>
                        </Row>

                        <Form.Group className="mb-3">
                          <Form.Label>
                            Severity Mapping
                            <Button
                              variant="outline-primary"
                              size="sm"
                              className="ms-2"
                              onClick={addSeverityMapping}
                            >
                              <FaPlus />
                            </Button>
                          </Form.Label>
                          {Object.entries(config.analysis_rules.severity_mapping || {}).map(([anomalyType, severity]) => (
                            <div key={anomalyType} className="d-flex gap-2 mb-2">
                              <Form.Control
                                type="text"
                                value={anomalyType}
                                placeholder="Anomaly type"
                                disabled
                              />
                              <Form.Select
                                value={severity as number}
                                onChange={(e) => updateSeverityMapping(anomalyType, parseInt(e.target.value))}
                                style={{ width: '100px' }}
                              >
                                <option value={1}>1 - Info</option>
                                <option value={2}>2 - Minor</option>
                                <option value={3}>3 - Moderate</option>
                                <option value={4}>4 - High</option>
                                <option value={5}>5 - Critical</option>
                              </Form.Select>
                              <Button
                                variant="outline-danger"
                                size="sm"
                                onClick={() => removeSeverityMapping(anomalyType)}
                              >
                                <FaTrash />
                              </Button>
                            </div>
                          ))}
                        </Form.Group>

                        {/* Agent-type specific fields */}
                        {config.agent_type === 'rule_based' && (
                          <>
                            <Form.Group className="mb-3">
                              <Form.Label>Target Log Levels</Form.Label>
                              <Form.Control
                                type="text"
                                value={(config.analysis_rules.target_levels || []).join(', ')}
                                onChange={(e) => updateConfig('analysis_rules.target_levels', e.target.value.split(',').map(s => s.trim()))}
                                placeholder="error, critical, warning"
                              />
                              <Form.Text className="text-muted">
                                Comma-separated list of log levels to monitor
                              </Form.Text>
                            </Form.Group>

                            <Form.Group className="mb-3">
                              <Form.Label>Exclude Patterns</Form.Label>
                              <Form.Control
                                type="text"
                                value={(config.analysis_rules.exclude_patterns || []).join(', ')}
                                onChange={(e) => updateConfig('analysis_rules.exclude_patterns', e.target.value.split(',').map(s => s.trim()))}
                                placeholder=".*test.*, .*debug.*"
                              />
                              <Form.Text className="text-muted">
                                Regex patterns to exclude from analysis
                              </Form.Text>
                            </Form.Group>

                            <Form.Group className="mb-3">
                              <Form.Label>Include Patterns</Form.Label>
                              <Form.Control
                                type="text"
                                value={(config.analysis_rules.include_patterns || []).join(', ')}
                                onChange={(e) => updateConfig('analysis_rules.include_patterns', e.target.value.split(',').map(s => s.trim()))}
                                placeholder=".*production.*, .*critical.*"
                              />
                              <Form.Text className="text-muted">
                                Regex patterns to include in analysis
                              </Form.Text>
                            </Form.Group>

                            <Form.Group className="mb-3">
                              <Form.Label>Alert Cooldown (seconds)</Form.Label>
                              <Form.Control
                                type="number"
                                min="0"
                                value={config.analysis_rules.alert_cooldown || 300}
                                onChange={(e) => updateConfig('analysis_rules.alert_cooldown', parseInt(e.target.value))}
                              />
                              <Form.Text className="text-muted">
                                Minimum time between alerts for the same issue
                              </Form.Text>
                            </Form.Group>
                          </>
                        )}

                        {config.agent_type === 'ml_based' && (
                          <>
                            <Form.Group className="mb-3">
                              <Form.Label>Feature Extraction</Form.Label>
                              <Form.Control
                                as="textarea"
                                rows={3}
                                value={JSON.stringify(config.analysis_rules.feature_extraction || {}, null, 2)}
                                onChange={(e) => {
                                  try {
                                    const parsed = JSON.parse(e.target.value);
                                    updateConfig('analysis_rules.feature_extraction', parsed);
                                  } catch (err) {
                                    // Invalid JSON, ignore
                                  }
                                }}
                                placeholder='{"feature1": true, "feature2": true}'
                              />
                              <Form.Text className="text-muted">
                                JSON object defining which features to extract
                              </Form.Text>
                            </Form.Group>

                            <Form.Group className="mb-3">
                              <Form.Label>Thresholds</Form.Label>
                              <Form.Control
                                as="textarea"
                                rows={3}
                                value={JSON.stringify(config.analysis_rules.thresholds || {}, null, 2)}
                                onChange={(e) => {
                                  try {
                                    const parsed = JSON.parse(e.target.value);
                                    updateConfig('analysis_rules.thresholds', parsed);
                                  } catch (err) {
                                    // Invalid JSON, ignore
                                  }
                                }}
                                placeholder='{"threshold1": 100, "threshold2": 50}'
                              />
                              <Form.Text className="text-muted">
                                JSON object defining detection thresholds
                              </Form.Text>
                            </Form.Group>
                          </>
                        )}

                        {config.agent_type === 'hybrid' && (
                          <>
                            <Form.Group className="mb-3">
                              <Form.Label>Fallback Rules</Form.Label>
                              <Form.Control
                                as="textarea"
                                rows={3}
                                value={JSON.stringify(config.analysis_rules.fallback_rules || {}, null, 2)}
                                onChange={(e) => {
                                  try {
                                    const parsed = JSON.parse(e.target.value);
                                    updateConfig('analysis_rules.fallback_rules', parsed);
                                  } catch (err) {
                                    // Invalid JSON, ignore
                                  }
                                }}
                                placeholder='{"enable_fallback": true, "rule_based_detection": true}'
                              />
                              <Form.Text className="text-muted">
                                JSON object defining fallback behavior
                              </Form.Text>
                            </Form.Group>
                          </>
                        )}
                      </Form>
                    </Tab.Pane>

                    {/* Advanced Tab */}
                    <Tab.Pane eventKey="advanced">
                      <Form>
                        <Form.Group className="mb-3">
                          <Form.Label>Raw Configuration (JSON)</Form.Label>
                          <Form.Control
                            as="textarea"
                            rows={15}
                            value={JSON.stringify(config, null, 2)}
                            onChange={(e) => {
                              try {
                                const parsed = JSON.parse(e.target.value);
                                setConfig(parsed);
                              } catch (err) {
                                // Invalid JSON, ignore
                              }
                            }}
                          />
                          <Form.Text className="text-muted">
                            Edit the complete configuration as JSON
                          </Form.Text>
                        </Form.Group>
                      </Form>
                    </Tab.Pane>
                  </Tab.Content>
                </Tab.Container>
              </Card.Body>
            </Card>
          ) : (
            <Card>
              <Card.Body className="text-center py-5">
                <FaCog className="h-12 w-12 mx-auto mb-3 text-muted" />
                <p className="text-muted">Select an agent to configure</p>
              </Card.Body>
            </Card>
          )}
        </Col>
      </Row>

      {/* Template Modal */}
      <Modal show={showTemplateModal} onHide={() => setShowTemplateModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Configuration Templates</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {templates ? (
            <Row>
              <Col md={4}>
                <Card>
                  <Card.Header>
                    <Card.Title className="mb-0">ML-Based Agent</Card.Title>
                  </Card.Header>
                  <Card.Body>
                    <p className="text-muted">{templates.ml_based.description}</p>
                    <Button
                      variant="primary"
                      onClick={() => applyTemplate('ml_based')}
                      disabled={!selectedAgent}
                    >
                      Apply Template
                    </Button>
                  </Card.Body>
                </Card>
              </Col>
              <Col md={4}>
                <Card>
                  <Card.Header>
                    <Card.Title className="mb-0">Rule-Based Agent</Card.Title>
                  </Card.Header>
                  <Card.Body>
                    <p className="text-muted">{templates.rule_based.description}</p>
                    <Button
                      variant="primary"
                      onClick={() => applyTemplate('rule_based')}
                      disabled={!selectedAgent}
                    >
                      Apply Template
                    </Button>
                  </Card.Body>
                </Card>
              </Col>
              <Col md={4}>
                <Card>
                  <Card.Header>
                    <Card.Title className="mb-0">Hybrid Agent</Card.Title>
                  </Card.Header>
                  <Card.Body>
                    <p className="text-muted">{templates.hybrid.description}</p>
                    <Button
                      variant="primary"
                      onClick={() => applyTemplate('hybrid')}
                      disabled={!selectedAgent}
                    >
                      Apply Template
                    </Button>
                  </Card.Body>
                </Card>
              </Col>
            </Row>
          ) : (
            <div className="text-center">
              <Spinner animation="border" />
              <p className="mt-2">Loading templates...</p>
            </div>
          )}
        </Modal.Body>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal show={showDeleteModal} onHide={() => setShowDeleteModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Delete Configuration</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Are you sure you want to delete the configuration for <strong>{selectedAgent?.name}</strong>?</p>
          <p className="text-muted">This action cannot be undone.</p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={deleteConfig}>
            Delete Configuration
          </Button>
        </Modal.Footer>
      </Modal>

      {/* History Modal */}
      <Modal show={showHistoryModal} onHide={() => setShowHistoryModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Configuration History</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p className="text-muted">Configuration history feature coming soon...</p>
        </Modal.Body>
      </Modal>
    </div>
  );
};

export default AgentConfig; 