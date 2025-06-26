import React, { useState } from 'react';
import { 
  Card, 
  Button, 
  Badge, 
  Table, 
  Modal, 
  Form,
  Alert,
  Spinner
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
  FaTimesCircle
} from 'react-icons/fa';
import { useAgents } from '../hooks/useAgents';
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
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {agents.map((agent) => (
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
                        {agent.capabilities.slice(0, 2).map((capability, index) => (
                          <Badge key={index} bg="outline-secondary" className="small">
                            {capability}
                          </Badge>
                        ))}
                        {agent.capabilities.length > 2 && (
                          <Badge bg="outline-secondary" className="small">
                            +{agent.capabilities.length - 2} more
                          </Badge>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className="d-flex gap-2">
                        <Button
                          size="sm"
                          variant="outline-primary"
                          onClick={() => handleSetModel(agent)}
                          disabled={isSettingModel}
                        >
                          <FaCog className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline-secondary"
                          onClick={() => handleRestartAgent(agent)}
                          disabled={isRestarting}
                        >
                          <FaSync className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline-danger"
                          onClick={() => setShowDeleteModal(agent)}
                          disabled={isUnregistering}
                        >
                          <FaTrash className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
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
    </div>
  );
};

export default Agents; 