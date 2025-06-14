import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, Table, Badge, Button, Spinner, Alert, Modal, Form } from 'react-bootstrap';
import { FaPlay, FaStop, FaInfoCircle, FaTrash, FaPlus, FaSync, FaExclamationTriangle } from 'react-icons/fa';
import { endpoints } from '../services/api';
import type { Model } from '../services/types';
import { toast } from 'react-hot-toast';
import { XMarkIcon } from '@heroicons/react/24/outline';

const Models: React.FC = () => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState<string | null>(null);
  const [showInfoModal, setShowInfoModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [modelInfo, setModelInfo] = useState<Model | null>(null);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['models'],
    queryFn: () => endpoints.getModels(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const handleActivate = async (modelId: string) => {
    try {
      await endpoints.activateModel(modelId);
      refetch();
    } catch (error) {
      console.error('Failed to activate model:', error);
    }
  };

  const handleInfo = async (modelId: string) => {
    try {
      const info = await endpoints.getModelInfo(modelId);
      if (info.error) {
        console.error('Error in model info:', info.error);
        alert(info.error);
        return;
      }
      setModelInfo(info);
      setShowInfoModal(true);
    } catch (error) {
      console.error('Error fetching model info:', error);
      alert('Failed to fetch model information');
    }
  };

  const handleDeploy = async (modelId: string) => {
    try {
      await endpoints.deployModel(modelId);
      refetch();
    } catch (error) {
      console.error('Failed to deploy model:', error);
    }
  };

  const handleDelete = async (modelId: string) => {
    try {
      await endpoints.deleteModel(modelId);
      setShowDeleteModal(null);
      refetch();
    } catch (error) {
      console.error('Failed to delete model:', error);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    
    try {
      const formData = new FormData();
      formData.append('model', selectedFile);
      await endpoints.uploadModel(formData);
      setShowAddModal(false);
      setSelectedFile(null);
      refetch();
    } catch (error) {
      console.error('Failed to upload model:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '200px' }}>
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="danger">
        <FaExclamationTriangle className="me-2" />
        Error loading models: {error instanceof Error ? error.message : 'Unknown error'}
      </Alert>
    );
  }

  const activeModels = data?.models.filter(m => m.status === 'active').length || 0;
  const totalModels = data?.models.length || 0;

  return (
    <div className="container-fluid">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>AI Models</h2>
        <div className="d-flex gap-2">
          <Button variant="outline-primary" onClick={() => refetch()}>
            <FaSync className="me-2" />
            Refresh
          </Button>
          <Button variant="primary" onClick={() => setShowAddModal(true)}>
            <FaPlus className="me-2" />
            Add Model
          </Button>
        </div>
      </div>

      {/* Model Statistics */}
      <div className="row mb-4">
        <div className="col-md-4">
          <Card>
            <Card.Body>
              <h6 className="text-muted mb-2">Total Models</h6>
              <h3>{totalModels}</h3>
            </Card.Body>
          </Card>
        </div>
        <div className="col-md-4">
          <Card>
            <Card.Body>
              <h6 className="text-muted mb-2">Active Models</h6>
              <h3>{activeModels}</h3>
            </Card.Body>
          </Card>
        </div>
        <div className="col-md-4">
          <Card>
            <Card.Body>
              <h6 className="text-muted mb-2">Latest Update</h6>
              <h3>
                {data?.models.length > 0
                  ? new Date(Math.max(...data.models.map(m => new Date(m.created_at))))
                      .toLocaleDateString()
                  : 'N/A'}
              </h3>
            </Card.Body>
          </Card>
        </div>
      </div>

      {/* Models Table */}
      <Card>
        <Card.Body>
          <Table responsive hover>
            <thead>
              <tr>
                <th>Version</th>
                <th>Created At</th>
                <th>Status</th>
                <th>Accuracy</th>
                <th>False Positive Rate</th>
                <th>False Negative Rate</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data?.models.map((model) => (
                <tr key={model.id}>
                  <td>{model.version}</td>
                  <td>{new Date(model.created_at).toLocaleString()}</td>
                  <td>
                    <Badge
                      bg={
                        model.status === 'active' ? 'success' :
                        model.status === 'inactive' ? 'secondary' :
                        'danger'
                      }
                    >
                      {model.status}
                    </Badge>
                  </td>
                  <td>{(model.metrics.accuracy * 100).toFixed(1)}%</td>
                  <td>{(model.metrics.false_positive_rate * 100).toFixed(1)}%</td>
                  <td>{(model.metrics.false_negative_rate * 100).toFixed(1)}%</td>
                  <td>
                    <div className="d-flex gap-2">
                      <Button
                        variant={model.status === 'active' ? 'warning' : 'success'}
                        size="sm"
                        onClick={() => handleActivate(model.id)}
                      >
                        {model.status === 'active' ? <FaStop /> : <FaPlay />}
                      </Button>
                      <Button
                        variant="info"
                        size="sm"
                        onClick={() => handleInfo(model.id)}
                      >
                        <FaInfoCircle />
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => setShowDeleteModal(model.id)}
                      >
                        <FaTrash />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      {/* Add Model Modal */}
      <Modal show={showAddModal} onHide={() => setShowAddModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Add New Model</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Model File</Form.Label>
              <Form.Control
                type="file"
                onChange={handleFileChange}
                accept=".joblib,.pkl,.model"
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowAddModal(false)}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleUpload}
            disabled={!selectedFile}
          >
            Upload
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Model Info Modal */}
      <Modal show={showInfoModal} onHide={() => setShowInfoModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Model Information</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {modelInfo && (
            <div>
              <h5>Basic Information</h5>
              <Table striped bordered>
                <tbody>
                  <tr>
                    <th>ID</th>
                    <td>{modelInfo.id}</td>
                  </tr>
                  <tr>
                    <th>Version</th>
                    <td>{modelInfo.version}</td>
                  </tr>
                  <tr>
                    <th>Created At</th>
                    <td>{new Date(modelInfo.created_at).toLocaleString()}</td>
                  </tr>
                  <tr>
                    <th>Status</th>
                    <td>
                      <Badge bg={
                        modelInfo.status === 'active' ? 'success' :
                        modelInfo.status === 'inactive' ? 'secondary' :
                        'danger'
                      }>
                        {modelInfo.status}
                      </Badge>
                    </td>
                  </tr>
                </tbody>
              </Table>

              {modelInfo.metrics && (
                <>
                  <h5 className="mt-4">Metrics</h5>
                  <Table striped bordered>
                    <tbody>
                      <tr>
                        <th>Accuracy</th>
                        <td>{(modelInfo.metrics.accuracy * 100).toFixed(1)}%</td>
                      </tr>
                      <tr>
                        <th>False Positive Rate</th>
                        <td>{(modelInfo.metrics.false_positive_rate * 100).toFixed(1)}%</td>
                      </tr>
                      <tr>
                        <th>False Negative Rate</th>
                        <td>{(modelInfo.metrics.false_negative_rate * 100).toFixed(1)}%</td>
                      </tr>
                    </tbody>
                  </Table>
                </>
              )}

              {modelInfo.agent_info && Object.keys(modelInfo.agent_info).length > 0 && (
                <>
                  <h5 className="mt-4">Agent Information</h5>
                  <Table striped bordered>
                    <tbody>
                      <tr>
                        <th>Status</th>
                        <td>
                          <Badge bg={
                            modelInfo.agent_info.status === 'active' ? 'success' :
                            modelInfo.agent_info.status === 'inactive' ? 'secondary' :
                            'danger'
                          }>
                            {modelInfo.agent_info.status}
                          </Badge>
                        </td>
                      </tr>
                      <tr>
                        <th>Running</th>
                        <td>{modelInfo.agent_info.is_running ? 'Yes' : 'No'}</td>
                      </tr>
                      {modelInfo.agent_info.last_run && (
                        <tr>
                          <th>Last Run</th>
                          <td>{new Date(modelInfo.agent_info.last_run).toLocaleString()}</td>
                        </tr>
                      )}
                      {modelInfo.agent_info.description && (
                        <tr>
                          <th>Description</th>
                          <td>{modelInfo.agent_info.description}</td>
                        </tr>
                      )}
                      {modelInfo.agent_info.capabilities && modelInfo.agent_info.capabilities.length > 0 && (
                        <tr>
                          <th>Capabilities</th>
                          <td>
                            <ul className="mb-0">
                              {modelInfo.agent_info.capabilities.map((cap, index) => (
                                <li key={index}>{cap}</li>
                              ))}
                            </ul>
                          </td>
                        </tr>
                      )}
                      {modelInfo.agent_info.programs && modelInfo.agent_info.programs.length > 0 && (
                        <tr>
                          <th>Monitored Programs</th>
                          <td>
                            <ul className="mb-0">
                              {modelInfo.agent_info.programs.map((prog, index) => (
                                <li key={index}>{prog}</li>
                              ))}
                            </ul>
                          </td>
                        </tr>
                      )}
                      {modelInfo.agent_info.model_path && (
                        <tr>
                          <th>Model Path</th>
                          <td>{modelInfo.agent_info.model_path}</td>
                        </tr>
                      )}
                    </tbody>
                  </Table>
                </>
              )}
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowInfoModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal show={!!showDeleteModal} onHide={() => setShowDeleteModal(null)}>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Delete</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to delete this model? This action cannot be undone.
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(null)}>
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={() => showDeleteModal && handleDelete(showDeleteModal)}
          >
            Delete
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default Models;