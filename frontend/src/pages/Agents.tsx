import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  Badge, 
  Table, 
  Modal, 
  Form,
  Alert,
  Spinner,
  OverlayTrigger,
  Tooltip,
  Nav,
  Tab,
  Row,
  Col
} from 'react-bootstrap';
import { 
  FaPlay, 
  FaStop, 
  FaSync, 
  FaCog, 
  FaTrash, 
  FaExclamationTriangle,
  FaCheckCircle,
  FaClock,
  FaTimesCircle,
  FaInfoCircle,
  FaList,
  FaSave,
  FaCheck,
  FaTimes,
  FaPlus,
  FaFileCode
} from 'react-icons/fa';
import { useAgents, useAgentDetailedInfo, useAgentsDetailedInfo } from '../hooks/useAgents';
import AgentDetailsModal from '../components/AgentDetailsModal';
import { endpoints } from '../services/api';
import type { Agent, AvailableModel, AgentConfig, AgentConfigValidationResponse, ConfigTemplates } from '../services/types';

const Agents: React.FC = () => {
  const {
    agents,
    availableModels,
    isLoading,
    setAgentModel,
    restartAgent,
    unregisterAgent,
    isSettingModel,
    isRestarting,
    isUnregistering
  } = useAgents();

  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState<Agent | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState<Agent | null>(null);
  const [showAllDetailsModal, setShowAllDetailsModal] = useState(false);

  // New state for configuration management
  const [activeTab, setActiveTab] = useState('agents');
  const [configAgent, setConfigAgent] = useState<Agent | null>(null);
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [originalConfig, setOriginalConfig] = useState<AgentConfig | null>(null);
  const [templates, setTemplates] = useState<ConfigTemplates | null>(null);
  const [isLoadingConfig, setIsLoadingConfig] = useState(false);
  const [isSavingConfig, setIsSavingConfig] = useState(false);
  const [isValidatingConfig, setIsValidatingConfig] = useState(false);
  const [validationResult, setValidationResult] = useState<AgentConfigValidationResponse | null>(null);
  const [showDeleteConfigModal, setShowDeleteConfigModal] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [configActiveTab, setConfigActiveTab] = useState('basic');
  const [configError, setConfigError] = useState<string | null>(null);
  const [configSuccess, setConfigSuccess] = useState<string | null>(null);

  // Hook for detailed agent information
  const { agentDetailedInfo, isLoading: isLoadingDetails, error: detailsError } = useAgentDetailedInfo(
    showDetailsModal?.id || ''
  );

  // Hook for all agents detailed information
  const { agentsDetailedInfo, isLoading: isLoadingAllDetails, error: allDetailsError } = useAgentsDetailedInfo(
    showAllDetailsModal ? agents.map(a => a.id) : undefined
  );

  // Load templates on component mount
  useEffect(() => {
    loadTemplates();
  }, []);

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
      setIsLoadingConfig(true);
      setConfigError(null);
      
      const configData = await endpoints.getAgentConfig(agent.id);
      setConfig(configData.config);
      setOriginalConfig(configData.config);
      setConfigAgent(agent);
      setValidationResult(null);
      setConfigActiveTab('basic');
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
        setConfigAgent(agent);
      } else {
        setConfigError('Failed to load agent configuration');
        console.error('Error loading agent config:', err);
      }
    } finally {
      setIsLoadingConfig(false);
    }
  };

  // Validate configuration
  const validateConfig = async () => {
    if (!config || !configAgent) return;

    try {
      setIsValidatingConfig(true);
      const result = await endpoints.validateAgentConfig(configAgent.id, config);
      setValidationResult(result);
      
      if (result.is_valid) {
        setConfigSuccess('Configuration is valid!');
        setTimeout(() => setConfigSuccess(null), 3000);
      }
    } catch (err) {
      setConfigError('Failed to validate configuration');
      console.error('Error validating config:', err);
    } finally {
      setIsValidatingConfig(false);
    }
  };

  // Save configuration
  const saveConfig = async () => {
    if (!config || !configAgent) return;

    try {
      setIsSavingConfig(true);
      setConfigError(null);
      
      await endpoints.saveAgentConfig(configAgent.id, config);
      setOriginalConfig(config);
      setConfigSuccess('Configuration saved successfully!');
      setTimeout(() => setConfigSuccess(null), 3000);
    } catch (err: any) {
      setConfigError(err.response?.data?.detail || 'Failed to save configuration');
      console.error('Error saving config:', err);
    } finally {
      setIsSavingConfig(false);
    }
  };

  // Delete configuration
  const deleteConfig = async () => {
    if (!configAgent) return;

    try {
      await endpoints.deleteAgentConfig(configAgent.id);
      setShowDeleteConfigModal(false);
      setConfigAgent(null);
      setConfig(null);
      setOriginalConfig(null);
      setConfigSuccess('Configuration deleted successfully!');
      setTimeout(() => setConfigSuccess(null), 3000);
    } catch (err: any) {
      setConfigError(err.response?.data?.detail || 'Failed to delete configuration');
      console.error('Error deleting config:', err);
    }
  };

  // Apply template
  const applyTemplate = (templateType: keyof ConfigTemplates) => {
    if (!templates || !configAgent) return;

    const template = templates[templateType];
    const newConfig: AgentConfig = {
      ...template,
      agent_id: configAgent.id,
      name: configAgent.name,
      description: configAgent.description || template.description,
      process_filters: configAgent.process_filters || template.process_filters,
      model_path: configAgent.model_path || template.model_path
    };

    setConfig(newConfig);
    setShowTemplateModal(false);
    setConfigSuccess(`Applied ${templateType} template`);
    setTimeout(() => setConfigSuccess(null), 3000);
  };

  // Reset to original configuration
  const resetConfig = () => {
    if (originalConfig) {
      setConfig(originalConfig);
      setValidationResult(null);
      setConfigError(null);
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

  const handleRestartAgent = (agent: Agent) => {
    restartAgent(agent.id);
  };

  const handleUnregisterAgent = (agent: Agent) => {
    unregisterAgent(agent.id);
    setShowDeleteModal(null);
  };

  const handleViewDetails = (agent: Agent) => {
    setShowDetailsModal(agent);
  };

  const handleCloseDetails = () => {
    setShowDetailsModal(null);
  };

  const handleViewAllDetails = () => {
    setShowAllDetailsModal(true);
  };

  const handleCloseAllDetails = () => {
    setShowAllDetailsModal(false);
  };

  const getStatusIcon = (agent: Agent) => {
    if (agent.is_running) {
      return <FaCheckCircle className="h-4 w-4 text-success" />;
    } else if (agent.status === 'error') {
      return <FaTimesCircle className="h-4 w-4 text-danger" />;
    } else {
      return <FaClock className="h-4 w-4 text-warning" />;
    }
  };

  const getStatusBadge = (agent: Agent) => {
    if (agent.is_running) {
      return <Badge bg="success">Running</Badge>;
    } else if (agent.status === 'error') {
      return <Badge bg="danger">Error</Badge>;
    } else {
      return <Badge bg="secondary">Stopped</Badge>;
    }
  };

  const formatLastRun = (lastRun: string | null) => {
    if (!lastRun) return 'Never';
    const date = new Date(lastRun);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return `${Math.floor(diffMins / 1440)}d ago`;
  };

  const getModelName = (modelPath: string | null) => {
    if (!modelPath) return 'No model assigned';
    
    // First try to find the model in availableModels
    const model = availableModels.find(m => m.path === modelPath);
    if (model) {
      return model.name;
    }
    
    // If not found, try to find by path basename (for zip files)
    const pathBasename = modelPath.split('/').pop() || modelPath;
    const modelByBasename = availableModels.find(m => {
      const mBasename = m.path.split('/').pop() || m.path;
      return mBasename === pathBasename;
    });
    if (modelByBasename) {
      return modelByBasename.name;
    }
    
    // If still not found, try to extract a meaningful name from the path
    if (pathBasename.endsWith('.zip')) {
      // For zip files, try to extract a more meaningful name
      const zipName = pathBasename.replace('.zip', '');
      if (zipName.startsWith('model_')) {
        // Convert model_tmpo3jl9ugx.zip to "Model tmpo3jl9ugx"
        const cleanName = zipName.replace('model_', '').replace('tmp', '');
        return `Model ${cleanName}`;
      }
      return zipName;
    }
    
    // Final fallback: use the basename or full path
    return pathBasename || modelPath;
  };

  if (isLoading) {
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
      <div className="d-flex justify-content-between align-items-center">
        <div>
          <h1 className="h3 mb-2">Agent Management</h1>
          <p className="text-muted">
            Manage agents, their configurations, and model associations
          </p>
        </div>
        <div className="d-flex gap-2">
          <Button
            variant="outline-info"
            size="sm"
            onClick={handleViewAllDetails}
            disabled={agents.length === 0}
          >
            <FaList className="me-1" />
            View All Details
          </Button>
          <Badge bg="outline-primary">
            {agents.filter(a => a.is_running).length} Running
          </Badge>
          <Badge bg="outline-secondary">
            {agents.length} Total
          </Badge>
        </div>
      </div>

      {/* Main Tabs */}
      <Tab.Container activeKey={activeTab} onSelect={(k) => setActiveTab(k || 'agents')}>
        <Nav variant="tabs" className="mb-3">
          <Nav.Item>
            <Nav.Link eventKey="agents">
              <FaList className="me-1" />
              Agents
            </Nav.Link>
          </Nav.Item>
          <Nav.Item>
            <Nav.Link eventKey="configuration">
              <FaCog className="me-1" />
              Configuration
            </Nav.Link>
          </Nav.Item>
        </Nav>

        <Tab.Content>
          {/* Agents Tab */}
          <Tab.Pane eventKey="agents">
            <Card>
              <Card.Header>
                <Card.Title className="mb-0">Registered Agents</Card.Title>
              </Card.Header>
              <Card.Body>
                {agents.length === 0 ? (
                  <div className="text-center py-5 text-muted">
                    <FaExclamationTriangle className="h-12 w-12 mx-auto mb-3 text-muted" />
                    <p>No agents registered</p>
                  </div>
                ) : (
                  <Table responsive>
                    <thead>
                      <tr>
                        <th>Agent</th>
                        <th>Status</th>
                        <th>Model</th>
                        <th>Last Run</th>
                        <th>Capabilities</th>
                        <th>Process Filters</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {agents.map((agent) => {
                        return (
                        <tr key={agent.id}>
                          <td>
                            <div className="d-flex align-items-center gap-3">
                              {getStatusIcon(agent)}
                              <div>
                                <div className="fw-medium">{agent.name}</div>
                                <div className="text-muted small">{agent.description}</div>
                              </div>
                            </div>
                          </td>
                          <td>
                            {getStatusBadge(agent)}
                          </td>
                          <td>
                            <div className="text-truncate" style={{ maxWidth: '200px' }}>
                              {getModelName(agent.model_path)}
                            </div>
                          </td>
                          <td>
                            {formatLastRun(agent.last_run)}
                          </td>
                          <td>
                            <div className="d-flex flex-wrap gap-1">
                              {(agent.capabilities || []).slice(0, 2).map((capability, index) => (
                                <Badge key={index} bg="secondary" className="small" style={{ color: 'white' }}>
                                  {capability}
                                </Badge>
                              ))}
                              {(agent.capabilities || []).length > 2 && (
                                <Badge bg="secondary" className="small" style={{ color: 'white' }}>
                                  +{(agent.capabilities || []).length - 2} more
                                </Badge>
                              )}
                              {(!agent.capabilities || agent.capabilities.length === 0) && (
                                <span className="text-muted small">None</span>
                              )}
                            </div>
                          </td>
                          <td>
                            <div className="d-flex flex-wrap gap-1">
                              {(agent.process_filters || []).slice(0, 2).map((filter, index) => (
                                <Badge key={index} bg="secondary" className="small" style={{ color: 'white' }}>
                                  {filter}
                                </Badge>
                              ))}
                              {(agent.process_filters || []).length > 2 && (
                                <Badge bg="secondary" className="small" style={{ color: 'white' }}>
                                  +{(agent.process_filters || []).length - 2} more
                                </Badge>
                              )}
                              {(!agent.process_filters || agent.process_filters.length === 0) && (
                                <span className="text-muted small">None</span>
                              )}
                            </div>
                          </td>
                          <td>
                            <div className="d-flex gap-2">
                              <OverlayTrigger
                                placement="top"
                                overlay={<Tooltip>Restart Agent</Tooltip>}
                              >
                                <Button
                                  size="sm"
                                  variant="outline-secondary"
                                  onClick={() => handleRestartAgent(agent)}
                                  disabled={isRestarting}
                                >
                                  <FaSync className="h-4 w-4" />
                                </Button>
                              </OverlayTrigger>
                              <OverlayTrigger
                                placement="top"
                                overlay={<Tooltip>Unregister Agent</Tooltip>}
                              >
                                <Button
                                  size="sm"
                                  variant="outline-danger"
                                  onClick={() => setShowDeleteModal(agent)}
                                  disabled={isUnregistering}
                                >
                                  <FaTrash className="h-4 w-4" />
                                </Button>
                              </OverlayTrigger>
                              <OverlayTrigger
                                placement="top"
                                overlay={<Tooltip>View Details</Tooltip>}
                              >
                                <Button
                                  size="sm"
                                  variant="outline-info"
                                  onClick={() => handleViewDetails(agent)}
                                >
                                  <FaInfoCircle className="h-4 w-4" />
                                </Button>
                              </OverlayTrigger>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                    </tbody>
                  </Table>
                )}
              </Card.Body>
            </Card>
          </Tab.Pane>

          {/* Configuration Tab */}
          <Tab.Pane eventKey="configuration">
            <Row>
              {/* Agent Selection */}
              <Col md={4}>
                <Card>
                  <Card.Header>
                    <Card.Title className="mb-0">Select Agent to Configure</Card.Title>
                  </Card.Header>
                  <Card.Body>
                    <Form.Group className="mb-3">
                      <Form.Label>Choose Agent</Form.Label>
                      <Form.Select
                        value={configAgent?.id || ''}
                        onChange={(e) => {
                          const agent = agents.find(a => a.id === e.target.value);
                          if (agent) {
                            loadAgentConfig(agent);
                          } else {
                            setConfigAgent(null);
                            setConfig(null);
                            setOriginalConfig(null);
                          }
                        }}
                      >
                        <option value="">Select an agent...</option>
                        {agents.map((agent) => (
                          <option key={agent.id} value={agent.id}>
                            {agent.name} ({agent.agent_type || 'unknown'})
                          </option>
                        ))}
                      </Form.Select>
                    </Form.Group>
                    
                    {configAgent && (
                      <div className="mt-3">
                        <h6>Selected Agent</h6>
                        <div className="d-flex align-items-center gap-2 mb-2">
                          {getStatusIcon(configAgent)}
                          <strong>{configAgent.name}</strong>
                        </div>
                        <p className="text-muted small mb-2">{configAgent.description}</p>
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
                        </div>
                      </div>
                    )}
                  </Card.Body>
                </Card>
              </Col>

              {/* Configuration Editor */}
              <Col md={8}>
                {configAgent && config ? (
                  <Card>
                    <Card.Header>
                      <div className="d-flex justify-content-between align-items-center">
                        <Card.Title className="mb-0">
                          Configure: {configAgent.name}
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
                            disabled={isValidatingConfig}
                          >
                            {isValidatingConfig ? (
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
                            disabled={isSavingConfig || !hasChanges()}
                          >
                            {isSavingConfig ? (
                              <Spinner animation="border" size="sm" />
                            ) : (
                              <FaSave className="me-1" />
                            )}
                            Save
                          </Button>
                          <Button
                            variant="outline-danger"
                            size="sm"
                            onClick={() => setShowDeleteConfigModal(true)}
                          >
                            <FaTrash className="me-1" />
                            Delete
                          </Button>
                        </div>
                      </div>
                    </Card.Header>
                    <Card.Body>
                      {/* Configuration Alerts */}
                      {configError && (
                        <Alert variant="danger" dismissible onClose={() => setConfigError(null)}>
                          <FaExclamationTriangle className="me-2" />
                          {configError}
                        </Alert>
                      )}

                      {configSuccess && (
                        <Alert variant="success" dismissible onClose={() => setConfigSuccess(null)}>
                          <FaCheck className="me-2" />
                          {configSuccess}
                        </Alert>
                      )}

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

                      {/* Configuration Form */}
                      <Tab.Container activeKey={configActiveTab} onSelect={(k) => setConfigActiveTab(k || 'basic')}>
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

                              {/* Add Model Assignment Section */}
                              <Form.Group className="mb-3">
                                <Form.Label>Assign Model</Form.Label>
                                <Form.Select
                                  value={config.model_path || ''}
                                  onChange={(e) => updateConfig('model_path', e.target.value || null)}
                                >
                                  <option value="">No model assigned</option>
                                  {availableModels.map((model) => (
                                    <option key={model.path} value={model.path}>
                                      {model.name} ({model.path})
                                    </option>
                                  ))}
                                </Form.Select>
                                <Form.Text className="text-muted">
                                  Select a model from available models or enter a custom path above
                                </Form.Text>
                              </Form.Group>

                              <Form.Group className="mb-3">
                                <Form.Label>
                                  Process Filters
                                  <Button
                                    variant="outline-primary"
                                    size="sm"
                                    className="ms-2"
                                    onClick={() => {
                                      const newFilters = [...config.process_filters, ''];
                                      updateConfig('process_filters', newFilters);
                                    }}
                                  >
                                    <FaPlus />
                                  </Button>
                                </Form.Label>
                                {config.process_filters.map((filter, index) => (
                                  <div key={index} className="d-flex gap-2 mb-2">
                                    <Form.Control
                                      type="text"
                                      value={filter}
                                      onChange={(e) => {
                                        const newFilters = [...config.process_filters];
                                        newFilters[index] = e.target.value;
                                        updateConfig('process_filters', newFilters);
                                      }}
                                      placeholder="process_name"
                                    />
                                    <Button
                                      variant="outline-danger"
                                      size="sm"
                                      onClick={() => {
                                        const newFilters = config.process_filters.filter((_, i) => i !== index);
                                        updateConfig('process_filters', newFilters);
                                      }}
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
                                    onClick={() => {
                                      const newCapabilities = [...config.capabilities, ''];
                                      updateConfig('capabilities', newCapabilities);
                                    }}
                                  >
                                    <FaPlus />
                                  </Button>
                                </Form.Label>
                                {config.capabilities.map((capability, index) => (
                                  <div key={index} className="d-flex gap-2 mb-2">
                                    <Form.Control
                                      type="text"
                                      value={capability}
                                      onChange={(e) => {
                                        const newCapabilities = [...config.capabilities];
                                        newCapabilities[index] = e.target.value;
                                        updateConfig('capabilities', newCapabilities);
                                      }}
                                      placeholder="Capability description"
                                    />
                                    <Button
                                      variant="outline-danger"
                                      size="sm"
                                      onClick={() => {
                                        const newCapabilities = config.capabilities.filter((_, i) => i !== index);
                                        updateConfig('capabilities', newCapabilities);
                                      }}
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
                                    onClick={() => {
                                      const newMapping = { ...config.analysis_rules.severity_mapping, 'new_anomaly': 3 };
                                      updateConfig('analysis_rules.severity_mapping', newMapping);
                                    }}
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
                                      onChange={(e) => {
                                        const newMapping = { ...config.analysis_rules.severity_mapping, [anomalyType]: parseInt(e.target.value) };
                                        updateConfig('analysis_rules.severity_mapping', newMapping);
                                      }}
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
                                      onClick={() => {
                                        const newMapping = { ...config.analysis_rules.severity_mapping };
                                        delete newMapping[anomalyType];
                                        updateConfig('analysis_rules.severity_mapping', newMapping);
                                      }}
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
          </Tab.Pane>
        </Tab.Content>
      </Tab.Container>

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
                      disabled={!configAgent}
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
                      disabled={!configAgent}
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
                      disabled={!configAgent}
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

      {/* Delete Configuration Modal */}
      <Modal show={showDeleteConfigModal} onHide={() => setShowDeleteConfigModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Delete Configuration</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>Are you sure you want to delete the configuration for <strong>{configAgent?.name}</strong>?</p>
          <p className="text-muted">This action cannot be undone.</p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteConfigModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={deleteConfig}>
            Delete Configuration
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal show={!!showDeleteModal} onHide={() => setShowDeleteModal(null)}>
        <Modal.Header closeButton>
          <Modal.Title>Unregister Agent</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to unregister {showDeleteModal?.name}? 
          This action cannot be undone.
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(null)}>
            Cancel
          </Button>
          <Button 
            variant="danger" 
            onClick={() => showDeleteModal && handleUnregisterAgent(showDeleteModal)}
            disabled={isUnregistering}
          >
            {isUnregistering ? 'Unregistering...' : 'Unregister'}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Agent Details Modal */}
      <AgentDetailsModal
        show={!!showDetailsModal}
        onHide={handleCloseDetails}
        agentDetailedInfo={agentDetailedInfo}
        isLoading={isLoadingDetails}
        error={detailsError}
      />

      {/* All Agents Details Modal */}
      <Modal show={showAllDetailsModal} onHide={handleCloseAllDetails} size="xl">
        <Modal.Header closeButton>
          <Modal.Title>
            <div className="d-flex align-items-center gap-2">
              <FaList />
              All Agents - Detailed Information
            </div>
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {isLoadingAllDetails ? (
            <div className="text-center py-5">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Loading...</span>
              </Spinner>
              <p className="mt-3">Loading all agents details...</p>
            </div>
          ) : allDetailsError ? (
            <Alert variant="danger">
              <FaExclamationTriangle className="me-2" />
              Failed to load agents details: {allDetailsError.message || 'Unknown error'}
            </Alert>
          ) : agentsDetailedInfo.length === 0 ? (
            <Alert variant="warning">
              <FaInfoCircle className="me-2" />
              No agents found
            </Alert>
          ) : (
            <div className="space-y-4">
              {agentsDetailedInfo.map((agentInfo) => (
                <Card key={agentInfo.id} className="mb-3">
                  <Card.Header>
                    <div className="d-flex justify-content-between align-items-center">
                      <h6 className="mb-0">{agentInfo.name}</h6>
                      <div className="d-flex gap-2">
                        <Badge bg={agentInfo.is_running ? "success" : "secondary"}>
                          {agentInfo.is_running ? "Running" : "Stopped"}
                        </Badge>
                        <Badge bg="outline-primary">{agentInfo.agent_type}</Badge>
                      </div>
                    </div>
                  </Card.Header>
                  <Card.Body>
                    <div className="row">
                      <div className="col-md-6">
                        <p><strong>Description:</strong> {agentInfo.description || 'No description'}</p>
                        <p><strong>Data Sources:</strong> {agentInfo.data_requirements.data_sources.length || 0}</p>
                        <p><strong>Export Format:</strong> {agentInfo.export_considerations.data_format}</p>
                        <p><strong>Data Volume:</strong> {agentInfo.export_considerations.data_volume_estimate}</p>
                      </div>
                      <div className="col-md-6">
                        <p><strong>Capabilities:</strong></p>
                        <div className="d-flex flex-wrap gap-1 mb-2">
                          {agentInfo.capabilities.slice(0, 3).map((capability, index) => (
                            <Badge key={index} bg="outline-primary" className="small">
                              {capability}
                            </Badge>
                          ))}
                          {agentInfo.capabilities.length > 3 && (
                            <Badge bg="outline-secondary" className="small">
                              +{agentInfo.capabilities.length - 3} more
                            </Badge>
                          )}
                        </div>
                        <p><strong>Required Fields:</strong> {agentInfo.export_considerations.required_fields.length}</p>
                        <p><strong>Preprocessing Steps:</strong> {agentInfo.export_considerations.preprocessing_steps.length}</p>
                      </div>
                    </div>
                    {agentInfo.performance_metrics && (
                      <div className="mt-3 pt-3 border-top">
                        <div className="row">
                          <div className="col-md-3">
                            <small className="text-muted">Analysis Cycles</small>
                            <div className="fw-bold">{agentInfo.performance_metrics.analysis_cycles}</div>
                          </div>
                          <div className="col-md-3">
                            <small className="text-muted">Anomalies Detected</small>
                            <div className="fw-bold">{agentInfo.performance_metrics.anomalies_detected}</div>
                          </div>
                          <div className="col-md-3">
                            <small className="text-muted">Success Rate</small>
                            <div className="fw-bold">
                              {agentInfo.performance_metrics.success_rate 
                                ? `${(agentInfo.performance_metrics.success_rate * 100).toFixed(1)}%`
                                : 'N/A'
                              }
                            </div>
                          </div>
                          <div className="col-md-3">
                            <small className="text-muted">Avg Cycle Time</small>
                            <div className="fw-bold">
                              {agentInfo.performance_metrics.average_cycle_time 
                                ? `${agentInfo.performance_metrics.average_cycle_time.toFixed(2)}s`
                                : 'N/A'
                              }
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </Card.Body>
                </Card>
              ))}
            </div>
          )}
        </Modal.Body>
      </Modal>
    </div>
  );
};

export default Agents; 