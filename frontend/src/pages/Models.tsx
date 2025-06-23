import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Table, Badge, Button, Spinner, Alert, Modal, Form, Row, Col } from 'react-bootstrap';
import { FaInfoCircle, FaTrash, FaPlus, FaSync, FaExclamationTriangle, FaUpload } from 'react-icons/fa';
import { endpoints } from '../services/api';
import type { Model, ModelValidationSummary } from '../services/types';
import { toast } from 'react-hot-toast';
import { XMarkIcon } from '@heroicons/react/24/outline';
import ModelValidationSummaryComponent from '../components/models/ModelValidationSummary';

const Models: React.FC = () => {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState<string | null>(null);
  const [showInfoModal, setShowInfoModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [modelInfo, setModelInfo] = useState<Model | null>(null);
  const [showValidationSummary, setShowValidationSummary] = useState<ModelValidationSummary | null>(null);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['models'],
    queryFn: () => endpoints.listEnhancedModels(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const handleInfo = async (version: string) => {
    try {
      const modelInfo = data?.find(m => m.version === version);
      if (modelInfo) {
        setModelInfo(modelInfo);
        setShowInfoModal(true);
      }
    } catch (error) {
      console.error('Failed to get model info:', error);
      toast.error('Failed to get model info');
    }
  };

  const handleDelete = async (version: string) => {
    try {
      // For now, just show a message since delete endpoint might not exist
      toast.error('Delete functionality not implemented yet');
      setShowDeleteModal(null);
    } catch (error) {
      console.error('Failed to delete model:', error);
      toast.error('Failed to delete model');
    }
  };

  const handleDeploy = async (version: string) => {
    try {
      await endpoints.deployModelVersion(version);
      toast.success(`Model ${version} deployed successfully`);
      refetch();
    } catch (error) {
      console.error('Failed to deploy model:', error);
      toast.error('Failed to deploy model');
    }
  };

  const handleRollback = async (version: string) => {
    try {
      await endpoints.rollbackModel(version);
      toast.success(`Rolled back to model ${version}`);
      refetch();
    } catch (error) {
      console.error('Failed to rollback model:', error);
      toast.error('Failed to rollback model');
    }
  };

  const handleValidate = async (version: string) => {
    try {
      const result = await endpoints.validateModel(version);
      if (result.is_valid) {
        toast.success(`Model ${version} validation passed`);
      } else {
        toast.error(`Model ${version} validation failed: ${result.errors.join(', ')}`);
      }
    } catch (error) {
      console.error('Failed to validate model:', error);
      toast.error('Failed to validate model');
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      
      // Validate file type
      if (!file.name.endsWith('.zip')) {
        toast.error('Please select a ZIP file');
        return;
      }
      
      // Validate naming convention
      if (!file.name.match(/^model_.*_deployment\.zip$/)) {
        toast.error('File must follow naming convention: model_&lt;version&gt;_deployment.zip');
        return;
      }
      
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      console.log("No file selected");
      return;
    }
    
    console.log("Starting upload process...");
    console.log("Selected file:", selectedFile.name, selectedFile.size);
    
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      console.log("FormData created, calling importModelPackage...");
      console.log("API Base URL:", import.meta.env.VITE_API_BASE_URL);
      
      const result = await endpoints.importModelPackage(formData);
      
      console.log("Upload successful:", result);
      toast.success(`Model imported successfully: ${result.version}`);
      
      // Show validation summary if available
      if (result.validation_summary) {
        setShowValidationSummary(result.validation_summary);
      }
      
      setShowAddModal(false);
      setSelectedFile(null);
      refetch();
    } catch (error) {
      console.error("Upload failed:", error);
      console.error("Error details:", error.response?.data || error.message);
      toast.error('Failed to upload model package');
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

  const activeModels = data?.filter(m => m.status === 'deployed').length || 0;
  const totalModels = data?.length || 0;

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
              <h6 className="text-muted mb-2">Deployed Models</h6>
              <h3>{activeModels}</h3>
            </Card.Body>
          </Card>
        </div>
        <div className="col-md-4">
          <Card>
            <Card.Body>
              <h6 className="text-muted mb-2">Latest Update</h6>
              <h3>
                {data?.length > 0
                  ? new Date(Math.max(...data.map(m => new Date(m.created_at))))
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
                <th>Model Type</th>
                <th>Features</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((model) => (
                <tr key={model.version}>
                  <td>{model.version}</td>
                  <td>{new Date(model.created_at).toLocaleString()}</td>
                  <td>
                    <Badge
                      bg={
                        model.status === 'deployed' ? 'success' :
                        model.status === 'available' ? 'secondary' :
                        'danger'
                      }
                    >
                      {model.status}
                    </Badge>
                  </td>
                  <td>{model.metadata?.model_info?.model_type || 'Unknown'}</td>
                  <td>{model.metadata?.training_info?.feature_names?.length || 0}</td>
                  <td>
                    <div className="d-flex gap-2">
                      <Button
                        variant="info"
                        size="sm"
                        onClick={() => handleInfo(model.version)}
                        title="View Details"
                      >
                        <FaInfoCircle />
                      </Button>
                      <Button
                        variant="success"
                        size="sm"
                        onClick={() => handleDeploy(model.version)}
                        title="Deploy Model"
                        disabled={model.status === 'deployed'}
                      >
                        Deploy
                      </Button>
                      <Button
                        variant="warning"
                        size="sm"
                        onClick={() => handleRollback(model.version)}
                        title="Rollback to this version"
                        disabled={model.status === 'deployed'}
                      >
                        Rollback
                      </Button>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleValidate(model.version)}
                        title="Validate Model"
                      >
                        Validate
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => setShowDeleteModal(model.version)}
                        title="Delete Model"
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
              <Form.Label>Model Package (ZIP)</Form.Label>
              <Form.Control
                type="file"
                onChange={handleFileChange}
                accept=".zip"
                placeholder="Select model package ZIP file"
              />
              <Form.Text className="text-muted">
                File must follow naming convention: model_&lt;version&gt;_deployment.zip
              </Form.Text>
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
                        modelInfo.status === 'deployed' ? 'success' :
                        modelInfo.status === 'available' ? 'secondary' :
                        'danger'
                      }>
                        {modelInfo.status}
                      </Badge>
                    </td>
                  </tr>
                  <tr>
                    <th>Import Method</th>
                    <td>{modelInfo.import_method || 'Unknown'}</td>
                  </tr>
                  <tr>
                    <th>Path</th>
                    <td>{modelInfo.path}</td>
                  </tr>
                </tbody>
              </Table>

              {modelInfo.metadata && (
                <>
                  <h5 className="mt-4">Model Information</h5>
                  <Table striped bordered>
                    <tbody>
                      <tr>
                        <th>Model Type</th>
                        <td>{modelInfo.metadata.model_info?.model_type || 'Unknown'}</td>
                      </tr>
                      <tr>
                        <th>Description</th>
                        <td>{modelInfo.metadata.model_info?.description || 'No description'}</td>
                      </tr>
                      <tr>
                        <th>Features</th>
                        <td>{modelInfo.metadata.training_info?.feature_names?.length || 0}</td>
                      </tr>
                      <tr>
                        <th>Training Samples</th>
                        <td>{modelInfo.metadata.training_info?.n_samples || 'Unknown'}</td>
                      </tr>
                    </tbody>
                  </Table>

                  {modelInfo.metadata.evaluation_info?.basic_metrics && (
                    <>
                      <h5 className="mt-4">Performance Metrics</h5>
                      <Table striped bordered>
                        <tbody>
                          <tr>
                            <th>F1 Score</th>
                            <td>{(modelInfo.metadata.evaluation_info.basic_metrics.f1_score * 100).toFixed(1)}%</td>
                          </tr>
                          <tr>
                            <th>Precision</th>
                            <td>{(modelInfo.metadata.evaluation_info.basic_metrics.precision * 100).toFixed(1)}%</td>
                          </tr>
                          <tr>
                            <th>Recall</th>
                            <td>{(modelInfo.metadata.evaluation_info.basic_metrics.recall * 100).toFixed(1)}%</td>
                          </tr>
                          <tr>
                            <th>ROC AUC</th>
                            <td>{(modelInfo.metadata.evaluation_info.basic_metrics.roc_auc * 100).toFixed(1)}%</td>
                          </tr>
                        </tbody>
                      </Table>
                    </>
                  )}

                  {modelInfo.metadata.training_info?.feature_names && (
                    <>
                      <h5 className="mt-4">Feature Names</h5>
                      <ul>
                        {modelInfo.metadata.training_info.feature_names.map((feature, index) => (
                          <li key={index}>{feature}</li>
                        ))}
                      </ul>
                    </>
                  )}
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

      {/* Validation Summary Modal */}
      <Modal show={showValidationSummary !== null} onHide={() => setShowValidationSummary(null)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Model Import Validation Summary</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {showValidationSummary && (
            <ModelValidationSummaryComponent validationSummary={showValidationSummary} />
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowValidationSummary(null)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default Models;