import React, { useState } from 'react';
import { Card, Table, Button, Badge, Form, Modal } from 'react-bootstrap';
import { FaUpload, FaTrash, FaPlay, FaStop, FaInfoCircle } from 'react-icons/fa';

interface Model {
  id: string;
  name: string;
  type: string;
  version: string;
  status: 'active' | 'inactive' | 'error';
  lastUpdated: string;
  accuracy: number;
}

const Models: React.FC = () => {
  const [models, setModels] = useState<Model[]>([
    {
      id: '1',
      name: 'WiFi Classifier',
      type: 'Classification',
      version: '1.0.0',
      status: 'active',
      lastUpdated: '2024-03-15',
      accuracy: 0.95
    },
    {
      id: '2',
      name: 'Anomaly Detector',
      type: 'Anomaly Detection',
      version: '2.1.0',
      status: 'inactive',
      lastUpdated: '2024-03-14',
      accuracy: 0.89
    }
  ]);

  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  const handleStatusToggle = (modelId: string) => {
    setModels(models.map(model => 
      model.id === modelId 
        ? { ...model, status: model.status === 'active' ? 'inactive' : 'active' }
        : model
    ));
  };

  const handleDelete = (modelId: string) => {
    if (window.confirm('Are you sure you want to delete this model?')) {
      setModels(models.filter(model => model.id !== modelId));
    }
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      active: 'success',
      inactive: 'secondary',
      error: 'danger'
    };
    return <Badge bg={variants[status as keyof typeof variants]}>{status}</Badge>;
  };

  return (
    <div className="models-page">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Models</h2>
        <Button variant="primary" onClick={() => setShowUploadModal(true)}>
          <FaUpload className="me-2" />
          Upload New Model
        </Button>
      </div>

      <Card>
        <Card.Body>
          <Table responsive hover>
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Version</th>
                <th>Status</th>
                <th>Last Updated</th>
                <th>Accuracy</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {models.map(model => (
                <tr key={model.id}>
                  <td>{model.name}</td>
                  <td>{model.type}</td>
                  <td>{model.version}</td>
                  <td>{getStatusBadge(model.status)}</td>
                  <td>{model.lastUpdated}</td>
                  <td>{(model.accuracy * 100).toFixed(1)}%</td>
                  <td>
                    <Button
                      variant={model.status === 'active' ? 'warning' : 'success'}
                      size="sm"
                      className="me-2"
                      onClick={() => handleStatusToggle(model.id)}
                    >
                      {model.status === 'active' ? <FaStop /> : <FaPlay />}
                    </Button>
                    <Button
                      variant="info"
                      size="sm"
                      className="me-2"
                      onClick={() => {
                        setSelectedModel(model);
                        setShowDetailsModal(true);
                      }}
                    >
                      <FaInfoCircle />
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleDelete(model.id)}
                    >
                      <FaTrash />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      {/* Upload Modal */}
      <Modal show={showUploadModal} onHide={() => setShowUploadModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Upload New Model</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Model Name</Form.Label>
              <Form.Control type="text" placeholder="Enter model name" />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Model Type</Form.Label>
              <Form.Select>
                <option>Classification</option>
                <option>Anomaly Detection</option>
                <option>Regression</option>
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Model File</Form.Label>
              <Form.Control type="file" />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Version</Form.Label>
              <Form.Control type="text" placeholder="e.g., 1.0.0" />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowUploadModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={() => setShowUploadModal(false)}>
            Upload
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Details Modal */}
      <Modal show={showDetailsModal} onHide={() => setShowDetailsModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Model Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedModel && (
            <div>
              <h5>{selectedModel.name}</h5>
              <p><strong>Type:</strong> {selectedModel.type}</p>
              <p><strong>Version:</strong> {selectedModel.version}</p>
              <p><strong>Status:</strong> {getStatusBadge(selectedModel.status)}</p>
              <p><strong>Last Updated:</strong> {selectedModel.lastUpdated}</p>
              <p><strong>Accuracy:</strong> {(selectedModel.accuracy * 100).toFixed(1)}%</p>
              <hr />
              <h6>Model Metrics</h6>
              <p><strong>Training Time:</strong> 2.5 hours</p>
              <p><strong>Dataset Size:</strong> 10,000 samples</p>
              <p><strong>Features:</strong> 50</p>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDetailsModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default Models;