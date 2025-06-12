import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, Table, Badge, Button, Spinner, Alert, Modal, Form } from 'react-bootstrap';
import { FaPlay, FaStop, FaInfoCircle, FaTrash, FaPlus, FaSync, FaExclamationTriangle } from 'react-icons/fa';
import { endpoints } from '../services/api';
import type { Model } from '../services/types';

const Models: React.FC = () => {
  const [showAddModal, setShowAddModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

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
    <div>
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
                        onClick={() => handleDeploy(model.id)}
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