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
  Tooltip
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
  FaList
} from 'react-icons/fa';
import { useAgents, useAgentDetailedInfo, useAgentsDetailedInfo } from '../hooks/useAgents';
import AgentDetailsModal from '../components/AgentDetailsModal';
import type { Agent, AvailableModel } from '../services/types';

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
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [isModelDialogOpen, setIsModelDialogOpen] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState<Agent | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState<Agent | null>(null);
  const [showAllDetailsModal, setShowAllDetailsModal] = useState(false);

  // Hook for detailed agent information
  const { agentDetailedInfo, isLoading: isLoadingDetails, error: detailsError } = useAgentDetailedInfo(
    showDetailsModal?.id || ''
  );

  // Hook for all agents detailed information
  const { agentsDetailedInfo, isLoading: isLoadingAllDetails, error: allDetailsError } = useAgentsDetailedInfo(
    showAllDetailsModal ? agents.map(a => a.id) : undefined
  );

  const handleSetModel = (agent: Agent) => {
    setSelectedAgent(agent);
    setSelectedModel(agent.model_path || '');
    setIsModelDialogOpen(true);
  };

  const handleConfirmSetModel = () => {
    if (selectedAgent && selectedModel) {
      setAgentModel(selectedAgent.id, selectedModel);
      setIsModelDialogOpen(false);
      setSelectedAgent(null);
      setSelectedModel('');
    }
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
    const model = availableModels.find(m => m.path === modelPath);
    return model ? model.name : modelPath.split('/').pop() || modelPath;
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
            Manage agents and their model associations
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
                          overlay={<Tooltip>Assign Model</Tooltip>}
                        >
                          <Button
                            size="sm"
                            variant="outline-primary"
                            onClick={() => handleSetModel(agent)}
                            disabled={isSettingModel}
                          >
                            <FaCog className="h-4 w-4" />
                          </Button>
                        </OverlayTrigger>
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

      {/* Model Assignment Modal */}
      <Modal show={isModelDialogOpen} onHide={() => setIsModelDialogOpen(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Assign Model to {selectedAgent?.name}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group>
              <Form.Label>Select Model</Form.Label>
              <Form.Select 
                value={selectedModel} 
                onChange={(e) => setSelectedModel(e.target.value)}
              >
                <option value="">No model</option>
                {availableModels.map((model) => (
                  <option key={model.path} value={model.path}>
                    {model.name}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setIsModelDialogOpen(false)}>
            Cancel
          </Button>
          <Button 
            variant="primary" 
            onClick={handleConfirmSetModel}
            disabled={!selectedModel || isSettingModel}
          >
            {isSettingModel ? 'Updating...' : 'Update Model'}
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