import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Table, Badge, Button, Spinner, Alert, Modal, Form, Row, Col } from 'react-bootstrap';
import { FaInfoCircle, FaTrash, FaPlus, FaSync, FaExclamationTriangle, FaUpload, FaChartLine, FaHistory } from 'react-icons/fa';
import { endpoints } from '../services/api';
import type { Model, ModelValidationSummary, ModelPerformanceMetrics, ModelTransferHistory } from '../services/types';
import { toast } from 'react-hot-toast';
import { XMarkIcon } from '@heroicons/react/24/outline';
import ModelValidationSummaryComponent from '../components/models/ModelValidationSummary';
import TabbedLayout from '../components/common/TabbedLayout';
import type { TabItem } from '../components/common/types';

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

  const { data: performanceData } = useQuery({
    queryKey: ['modelPerformance'],
    queryFn: () => endpoints.getAllModelPerformance(),
    refetchInterval: 60000, // Refresh every minute
  });

  const { data: transferHistory } = useQuery({
    queryKey: ['transferHistory'],
    queryFn: () => endpoints.getTransferHistory(),
    refetchInterval: 300000, // Refresh every 5 minutes
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
        toast.error('File must follow naming convention: model_<version>_deployment.zip');
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

  // Model List Tab Content
  const ModelListContent = (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
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
              <h6 className="text-muted mb-2">Success Rate</h6>
              <h3>{totalModels > 0 ? Math.round((activeModels / totalModels) * 100) : 0}%</h3>
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
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((model) => (
                <tr key={model.version}>
                  <td>{model.version}</td>
                  <td>
                    <Badge
                      bg={
                        model.status === 'deployed' ? 'success' :
                        model.status === 'active' ? 'primary' :
                        model.status === 'inactive' ? 'secondary' :
                        'danger'
                      }
                    >
                      {model.status}
                    </Badge>
                  </td>
                  <td>{new Date(model.created_at).toLocaleDateString()}</td>
                  <td>
                    <div className="d-flex gap-1">
                      <Button
                        size="sm"
                        variant="outline-info"
                        onClick={() => handleInfo(model.version)}
                      >
                        <FaInfoCircle />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline-success"
                        onClick={() => handleDeploy(model.version)}
                        disabled={model.status === 'deployed'}
                      >
                        Deploy
                      </Button>
                      <Button
                        size="sm"
                        variant="outline-warning"
                        onClick={() => handleRollback(model.version)}
                        disabled={model.status !== 'deployed'}
                      >
                        Rollback
                      </Button>
                      <Button
                        size="sm"
                        variant="outline-primary"
                        onClick={() => handleValidate(model.version)}
                      >
                        Validate
                      </Button>
                      <Button
                        size="sm"
                        variant="outline-danger"
                        onClick={() => setShowDeleteModal(model.version)}
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
    </div>
  );

  // Model Performance Tab Content
  const ModelPerformanceContent = (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4>Model Performance Metrics</h4>
        <Button variant="outline-primary" onClick={() => queryClient.invalidateQueries(['modelPerformance'])}>
          <FaSync className="me-2" />
          Refresh
        </Button>
      </div>

      {performanceData && performanceData.length > 0 ? (
        <div className="row">
          {performanceData.map((performance) => (
            <div key={performance.model_version} className="col-md-6 mb-4">
              <Card>
                <Card.Header>
                  <h6 className="mb-0">Model {performance.model_version}</h6>
                </Card.Header>
                <Card.Body>
                  <div className="row">
                    <div className="col-6">
                      <small className="text-muted">Total Inferences</small>
                      <div className="h5 mb-0">{performance.total_inferences.toLocaleString()}</div>
                    </div>
                    <div className="col-6">
                      <small className="text-muted">Anomaly Rate</small>
                      <div className="h5 mb-0">{(performance.performance_metrics.anomaly_rate * 100).toFixed(2)}%</div>
                    </div>
                  </div>
                  <div className="row mt-3">
                    <div className="col-6">
                      <small className="text-muted">Avg Inference Time</small>
                      <div className="h5 mb-0">{performance.performance_metrics.avg_inference_time.toFixed(2)}ms</div>
                    </div>
                    <div className="col-6">
                      <small className="text-muted">Total Anomalies</small>
                      <div className="h5 mb-0">{performance.performance_metrics.total_anomalies}</div>
                    </div>
                  </div>
                  <div className="mt-3">
                    <small className="text-muted">Last Updated: {new Date(performance.last_updated).toLocaleString()}</small>
                  </div>
                </Card.Body>
              </Card>
            </div>
          ))}
        </div>
      ) : (
        <Alert variant="info">
          No performance data available. Models need to be deployed and used to generate performance metrics.
        </Alert>
      )}
    </div>
  );

  // Transfer History Tab Content
  const TransferHistoryContent = (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4>Model Transfer History</h4>
        <Button variant="outline-primary" onClick={() => queryClient.invalidateQueries(['transferHistory'])}>
          <FaSync className="me-2" />
          Refresh
        </Button>
      </div>

      {transferHistory && transferHistory.length > 0 ? (
        <Card>
          <Card.Body>
            <Table responsive hover>
              <thead>
                <tr>
                  <th>Transfer ID</th>
                  <th>Original Path</th>
                  <th>Local Path</th>
                  <th>Transferred At</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {transferHistory.map((transfer) => (
                  <tr key={transfer.transfer_id}>
                    <td>{transfer.transfer_id}</td>
                    <td>{transfer.original_path}</td>
                    <td>{transfer.local_path}</td>
                    <td>{new Date(transfer.transferred_at).toLocaleString()}</td>
                    <td>
                      <Badge
                        bg={transfer.status === 'completed' ? 'success' : 'warning'}
                      >
                        {transfer.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Card.Body>
        </Card>
      ) : (
        <Alert variant="info">
          No transfer history available. Model transfers will appear here once they occur.
        </Alert>
      )}
    </div>
  );

  const tabs: TabItem[] = [
    {
      key: 'list',
      title: 'Model List',
      icon: <FaPlus />,
      content: ModelListContent
    },
    {
      key: 'performance',
      title: 'Performance',
      icon: <FaChartLine />,
      content: ModelPerformanceContent
    },
    {
      key: 'history',
      title: 'Transfer History',
      icon: <FaHistory />,
      content: TransferHistoryContent
    }
  ];

  return (
    <div className="container-fluid">
      <TabbedLayout title="AI Models" tabs={tabs} />

      {/* Add Model Modal */}
      <Modal show={showAddModal} onHide={() => setShowAddModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Add New Model</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Model Package (ZIP file)</Form.Label>
              <Form.Control
                type="file"
                accept=".zip"
                onChange={handleFileChange}
              />
              <Form.Text className="text-muted">
                Select a model package file. Must follow naming convention: model_&lt;version&gt;_deployment.zip
              </Form.Text>
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowAddModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleUpload} disabled={!selectedFile}>
            <FaUpload className="me-2" />
            Upload Model
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
              <h5>Version: {modelInfo.version}</h5>
              <p><strong>Status:</strong> {modelInfo.status}</p>
              <p><strong>Created:</strong> {new Date(modelInfo.created_at).toLocaleString()}</p>
              {modelInfo.metrics && (
                <div>
                  <h6>Metrics:</h6>
                  <ul>
                    <li>Accuracy: {modelInfo.metrics.accuracy}%</li>
                    <li>False Positive Rate: {modelInfo.metrics.false_positive_rate}%</li>
                    <li>False Negative Rate: {modelInfo.metrics.false_negative_rate}%</li>
                  </ul>
                </div>
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
          <Modal.Title>Delete Model</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to delete model {showDeleteModal}? This action cannot be undone.
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDeleteModal(null)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={() => showDeleteModal && handleDelete(showDeleteModal)}>
            Delete
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Validation Summary Modal */}
      <Modal show={!!showValidationSummary} onHide={() => setShowValidationSummary(null)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Model Validation Summary</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {showValidationSummary && (
            <ModelValidationSummaryComponent summary={showValidationSummary} />
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