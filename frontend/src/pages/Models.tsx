import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Table, Badge, Button, Spinner, Alert, Modal, Form, Row, Col, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { FaInfoCircle, FaTrash, FaPlus, FaSync, FaExclamationTriangle, FaUpload, FaChartLine, FaHistory } from 'react-icons/fa';
import { endpoints } from '../services/api';
import type { Model, ModelValidationSummary, ModelValidationResult, ModelPerformanceMetrics, ModelTransferHistory } from '../services/types';
import { toast } from 'react-hot-toast';
import { XMarkIcon } from '@heroicons/react/24/outline';
import ModelValidationSummaryComponent from '../components/models/ModelValidationSummary';
import ModelValidationModal from '../components/models/ModelValidationModal';
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
  const [showValidationModal, setShowValidationModal] = useState(false);
  const [validationResult, setValidationResult] = useState<ModelValidationResult | null>(null);
  const [validatingModel, setValidatingModel] = useState<string | null>(null);
  const [modelInfoLoading, setModelInfoLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

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

  // Helper function to get model name from metadata
  const getModelName = (model: any): string => {
    if (model.metadata?.model_info?.model_name) {
      return model.metadata.model_info.model_name;
    }
    // Fallback to version if no model name is available
    return model.version;
  };

  // Helper function to get model name with version
  const getModelNameWithVersion = (model: any): string => {
    const modelName = getModelName(model);
    if (modelName === model.version) {
      return model.version;
    }
    return `${modelName} (${model.version})`;
  };

  const handleInfo = async (version: string) => {
    try {
      setModelInfoLoading(true);
      setShowInfoModal(true);
      
      // Fetch detailed model information from API
      const detailedInfo = await endpoints.getEnhancedModelInfo(version);
      setModelInfo(detailedInfo);
    } catch (error: any) {
      console.error('Failed to get model info:', error);
      toast.error('Failed to get model info');
      setShowInfoModal(false);
    } finally {
      setModelInfoLoading(false);
    }
  };

  const handleDelete = async (version: string) => {
    try {
      await endpoints.deleteModel(version);
      toast.success(`Model ${version} deleted successfully`);
      setShowDeleteModal(null);
      refetch();
    } catch (error: any) {
      console.error('Failed to delete model:', error);
      
      // Provide more specific error messages
      let errorMessage = 'Failed to delete model';
      
      if (error.response?.data) {
        const errorData = error.response.data;
        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast.error(errorMessage);
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
      setValidatingModel(version);
      setShowValidationModal(true);
      
      console.log('Starting validation for model:', version);
      const result = await endpoints.generateValidationReport(version);
      console.log('Validation result:', result);
      
      // Check the structure of the result
      let validationData;
      if (result.quality_validation) {
        // New structure with quality_validation wrapper
        validationData = result.quality_validation;
      } else if (result.validation_summary) {
        // Structure with validation_summary - construct ModelValidationResult
        validationData = {
          is_valid: result.validation_summary.is_valid,
          score: result.validation_summary.score,
          errors: result.errors || [],
          warnings: result.warnings || [],
          recommendations: result.recommendations || [],
          quality_metrics: result.quality_metrics || {},
          issues: result.issues || [],
          package_info: result.package_info,
          model_info: result.model_info,
          training_info: result.training_info,
          evaluation_info: result.evaluation_info,
          package_structure: result.package_structure,
          trainer_notes: result.trainer_notes
        };
      } else if (result.is_valid !== undefined) {
        // Direct ModelValidationResult structure
        validationData = result;
      } else {
        console.error('Unexpected validation result structure:', result);
        toast.error('Invalid validation result format');
        setShowValidationModal(false);
        return;
      }
      
      console.log('Extracted validation data:', validationData);
      setValidationResult(validationData);
      
      // Show a brief toast for immediate feedback
      if (validationData.is_valid) {
        toast.success(`Model ${version} validation completed`);
      } else {
        toast.error(`Model ${version} validation found issues`);
      }
    } catch (error) {
      console.error('Failed to validate model:', error);
      toast.error('Failed to validate model');
      setShowValidationModal(false);
    } finally {
      setValidatingModel(null);
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
      
      // Check for validation warnings
      if (result.validation_summary && result.validation_summary.warnings && result.validation_summary.warnings.length > 0) {
        // Show success message with warnings
        toast.success(`Model imported successfully: ${result.version}`, {
          duration: 5000
        });
        
        // Show warnings in a more detailed way
        const warningMessage = result.validation_summary.warnings.join('; ');
        toast(`Import completed with warnings: ${warningMessage}`, {
          duration: 8000,
          icon: '⚠️',
          style: {
            background: '#fff3cd',
            color: '#856404',
            border: '1px solid #ffeaa7'
          }
        });
        
        // Set validation summary for detailed view
        setShowValidationSummary(result.validation_summary);
      } else {
        // Clean success
        toast.success(`Model imported successfully: ${result.version}`);
      }
      
      setShowAddModal(false);
      setSelectedFile(null);
      refetch();
    } catch (error: any) {
      console.error("Upload failed:", error);
      console.error("Error details:", error.response?.data || error.message);
      
      // Provide more specific error messages
      let errorMessage = 'Failed to upload model package';
      
      if (error.response?.data) {
        const errorData = error.response.data;
        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      // Check if it's a validation error with warnings
      if (errorMessage.includes('validation') || errorMessage.includes('warning')) {
        toast(`Validation warning: ${errorMessage}`, {
          duration: 8000,
          icon: '⚠️',
          style: {
            background: '#fff3cd',
            color: '#856404',
            border: '1px solid #ffeaa7'
          }
        });
      } else {
        toast.error(errorMessage);
      }
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
                <th>Model Name</th>
                <th>Status</th>
                <th>Assigned Agents</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((model: any) => (
                <tr key={model.version}>
                  <td>
                    <div>
                      <strong>{getModelName(model)}</strong>
                      <div className="small text-muted">{model.version}</div>
                    </div>
                  </td>
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
                  <td>
                    {model.assigned_agents && model.assigned_agents.length > 0 ? (
                      <div>
                        <Badge bg="info" className="me-1">
                          {model.agent_count || model.assigned_agents.length} agent(s)
                        </Badge>
                        <div className="small text-muted mt-1">
                          {model.assigned_agents.slice(0, 2).map((agent: any) => (
                            <div key={agent.agent_id} className="d-flex align-items-center">
                              <Badge 
                                bg={agent.status === 'running' ? 'success' : 'secondary'} 
                                size="sm"
                                className="me-1"
                              >
                                {agent.status}
                              </Badge>
                              {agent.agent_name}
                            </div>
                          ))}
                          {model.assigned_agents.length > 2 && (
                            <div className="text-muted">
                              +{model.assigned_agents.length - 2} more...
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      <span className="text-muted">No agents assigned</span>
                    )}
                  </td>
                  <td>{new Date(model.created_at).toLocaleDateString()}</td>
                  <td>
                    <div className="d-flex gap-1">
                      <OverlayTrigger
                        placement="top"
                        overlay={<Tooltip>View Model Info</Tooltip>}
                      >
                        <Button
                          size="sm"
                          variant="outline-info"
                          onClick={() => handleInfo(model.version)}
                        >
                          <FaInfoCircle />
                        </Button>
                      </OverlayTrigger>
                      <OverlayTrigger
                        placement="top"
                        overlay={<Tooltip>Deploy Model</Tooltip>}
                      >
                        <Button
                          size="sm"
                          variant="outline-success"
                          onClick={() => handleDeploy(model.version)}
                          disabled={model.status === 'deployed'}
                        >
                          Deploy
                        </Button>
                      </OverlayTrigger>
                      <OverlayTrigger
                        placement="top"
                        overlay={<Tooltip>Rollback to This Model</Tooltip>}
                      >
                        <Button
                          size="sm"
                          variant="outline-warning"
                          onClick={() => handleRollback(model.version)}
                          disabled={model.status !== 'deployed'}
                        >
                          Rollback
                        </Button>
                      </OverlayTrigger>
                      <OverlayTrigger
                        placement="top"
                        overlay={<Tooltip>Validate Model</Tooltip>}
                      >
                        <Button
                          size="sm"
                          variant="outline-primary"
                          onClick={() => handleValidate(model.version)}
                        >
                          Validate
                        </Button>
                      </OverlayTrigger>
                      <OverlayTrigger
                        placement="top"
                        overlay={
                          <Tooltip>
                            {model.assigned_agents && model.assigned_agents.length > 0
                              ? 'Cannot delete: model is assigned to one or more agents'
                              : 'Delete Model'}
                          </Tooltip>
                        }
                      >
                        <span>
                          <Button
                            size="sm"
                            variant="outline-danger"
                            onClick={() => setShowDeleteModal(model.version)}
                            disabled={model.assigned_agents && model.assigned_agents.length > 0}
                            style={(model.assigned_agents && model.assigned_agents.length > 0) ? { pointerEvents: 'none' } : {}}
                          >
                            <FaTrash />
                          </Button>
                        </span>
                      </OverlayTrigger>
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
                <h6 className="mb-0">
                  {(() => {
                    const model = data?.find((m: any) => m.version === performance.model_version);
                    return model ? getModelName(model) : `Model ${performance.model_version}`;
                  })()}
                </h6>
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
      <Modal show={showInfoModal} onHide={() => setShowInfoModal(false)} size="xl">
        <Modal.Header closeButton>
                          <Modal.Title>Model Information - {modelInfo?.metadata?.model_info?.model_name || modelInfo?.version}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {modelInfoLoading ? (
            <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '200px' }}>
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Loading model information...</span>
              </Spinner>
            </div>
          ) : modelInfo ? (
            <div>
              {/* Basic Info Section */}
              <div className="mb-4">
                <h5 className="border-bottom pb-2">Basic Information</h5>
                <div className="row">
                  <div className="col-md-6">
                    <p><strong>Version:</strong> {modelInfo.version}</p>
                    {((modelInfo as any).metadata?.model_info?.name || (modelInfo as any).metadata?.model_info?.model_name) ? (
                      <p><strong>Name:</strong> {(modelInfo as any).metadata.model_info.name || (modelInfo as any).metadata.model_info.model_name}</p>
                    ) : (
                      <p><strong>Name:</strong> <span className="text-muted">Not specified</span></p>
                    )}
                    {(modelInfo as any).metadata?.model_info?.training_id && (
                      <p><strong>Training ID:</strong> <code className="small">{(modelInfo as any).metadata.model_info.training_id}</code></p>
                    )}
                    <p><strong>Status:</strong> 
                      <Badge 
                        bg={(modelInfo as any).status === 'deployed' ? 'success' : 'secondary'} 
                        className="ms-2"
                      >
                        {(modelInfo as any).status}
                      </Badge>
                    </p>
                    <p><strong>Created:</strong> {new Date(modelInfo.created_at).toLocaleString()}</p>
                    {(modelInfo as any).last_updated && (
                      <p><strong>Last Updated:</strong> {new Date((modelInfo as any).last_updated).toLocaleString()}</p>
                    )}
                  </div>
                  <div className="col-md-6">
                    <p><strong>Import Method:</strong> {(modelInfo as any).import_method || 'Unknown'}</p>
                    <p><strong>Model Path:</strong> <code className="small">{(modelInfo as any).path}</code></p>
                  </div>
                </div>
              </div>

              {/* Agent Assignment Section */}
              {(modelInfo as any).assigned_agents && (modelInfo as any).assigned_agents.length > 0 ? (
                <div className="mb-4">
                  <h5 className="border-bottom pb-2">Assigned Agents</h5>
                  <div className="row">
                    <div className="col-12">
                      <p><strong>Total Agents:</strong> <Badge bg="info">{(modelInfo as any).agent_count || (modelInfo as any).assigned_agents.length}</Badge></p>
                      <div className="table-responsive">
                        <Table striped bordered size="sm">
                          <thead>
                            <tr>
                              <th>Agent Name</th>
                              <th>Type</th>
                              <th>Status</th>
                              <th>Capabilities</th>
                            </tr>
                          </thead>
                          <tbody>
                            {(modelInfo as any).assigned_agents.map((agent: any) => (
                              <tr key={agent.agent_id}>
                                <td>
                                  <strong>{agent.agent_name}</strong>
                                  <br />
                                  <small className="text-muted">ID: {agent.agent_id}</small>
                                </td>
                                <td>
                                  <Badge bg="secondary" size="sm">
                                    {agent.agent_type}
                                  </Badge>
                                </td>
                                <td>
                                  <Badge 
                                    bg={agent.status === 'running' ? 'success' : 
                                        agent.status === 'configured' ? 'info' : 'secondary'} 
                                    size="sm"
                                  >
                                    {agent.status}
                                  </Badge>
                                </td>
                                <td>
                                  <div className="small">
                                    {agent.capabilities.slice(0, 3).map((capability: string, index: number) => (
                                      <Badge key={index} bg="light" text="dark" size="sm" className="me-1 mb-1">
                                        {capability}
                                      </Badge>
                                    ))}
                                    {agent.capabilities.length > 3 && (
                                      <Badge bg="light" text="dark" size="sm">
                                        +{agent.capabilities.length - 3} more
                                      </Badge>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </Table>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="mb-4">
                  <h5 className="border-bottom pb-2">Assigned Agents</h5>
                  <Alert variant="info">
                    <FaInfoCircle className="me-2" />
                    No agents are currently assigned to this model.
                  </Alert>
                </div>
              )}

              {/* Model Metadata Section */}
              {(modelInfo as any).metadata && (
                <div className="mb-4">
                  <h5 className="border-bottom pb-2">Model Details</h5>
                  
                  {/* Model Info */}
                  {(modelInfo as any).metadata.model_info && (
                    <div className="mb-3">
                      <h6>Model Information</h6>
                      <div className="row">
                        <div className="col-md-6">
                          <p><strong>Model Name:</strong> {(modelInfo as any).metadata.model_info.model_name || 'N/A'}</p>
                          <p><strong>Model Type:</strong> {(modelInfo as any).metadata.model_info.model_type}</p>
                          <p><strong>Description:</strong> {(modelInfo as any).metadata.model_info.description || 'No description available'}</p>
                        </div>
                        <div className="col-md-6">
                          <p><strong>Version:</strong> {(modelInfo as any).metadata.model_info.version}</p>
                          <p><strong>Created At:</strong> {new Date((modelInfo as any).metadata.model_info.created_at).toLocaleString()}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Training Information */}
                  {(modelInfo as any).metadata.training_info && (
                    <div className="mb-3">
                      <h6>Training Information</h6>
                      <div className="row">
                        <div className="col-md-6">
                          <p><strong>Training Samples:</strong> {(modelInfo as any).metadata.training_info.n_samples?.toLocaleString()}</p>
                          <p><strong>Number of Features:</strong> {(modelInfo as any).metadata.training_info.n_features}</p>
                          {(modelInfo as any).metadata.training_info.training_date && (
                            <p><strong>Training Date:</strong> {new Date((modelInfo as any).metadata.training_info.training_date).toLocaleString()}</p>
                          )}
                        </div>
                        <div className="col-md-6">
                          <p><strong>Feature Names:</strong></p>
                          <div className="small">
                            {(modelInfo as any).metadata.training_info.feature_names?.map((feature: string, index: number) => (
                              <Badge key={index} bg="light" text="dark" className="me-1 mb-1">
                                {feature}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Evaluation Information */}
                  {(modelInfo as any).metadata.evaluation_info && (
                    <div className="mb-3">
                      <h6>Evaluation Metrics</h6>
                      <div className="row">
                        <div className="col-md-6">
                          <p><strong>F1 Score:</strong> {((modelInfo as any).metadata.evaluation_info.basic_metrics?.f1_score * 100).toFixed(1)}%</p>
                          <p><strong>Precision:</strong> {((modelInfo as any).metadata.evaluation_info.basic_metrics?.precision * 100).toFixed(1)}%</p>
                          <p><strong>Recall:</strong> {((modelInfo as any).metadata.evaluation_info.basic_metrics?.recall * 100).toFixed(1)}%</p>
                        </div>
                        <div className="col-md-6">
                          <p><strong>ROC AUC:</strong> {((modelInfo as any).metadata.evaluation_info.basic_metrics?.roc_auc * 100).toFixed(1)}%</p>
                          {(modelInfo as any).metadata.evaluation_info.basic_metrics?.accuracy && (
                            <p><strong>Accuracy:</strong> {((modelInfo as any).metadata.evaluation_info.basic_metrics.accuracy * 100).toFixed(1)}%</p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Deployment Information */}
                  {(modelInfo as any).metadata.deployment_info && (
                    <div className="mb-3">
                      <h6>Deployment Information</h6>
                      <div className="row">
                        <div className="col-md-6">
                          <p><strong>Deployment Status:</strong> 
                            <Badge 
                              bg={(modelInfo as any).metadata.deployment_info.status === 'deployed' ? 'success' : 'secondary'} 
                              className="ms-2"
                            >
                              {(modelInfo as any).metadata.deployment_info.status}
                            </Badge>
                          </p>
                          {(modelInfo as any).metadata.deployment_info.deployed_at && (
                            <p><strong>Deployed At:</strong> {new Date((modelInfo as any).metadata.deployment_info.deployed_at).toLocaleString()}</p>
                          )}
                        </div>
                        <div className="col-md-6">
                          {(modelInfo as any).metadata.deployment_info.deployed_by && (
                            <p><strong>Deployed By:</strong> {(modelInfo as any).metadata.deployment_info.deployed_by}</p>
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Performance Metrics Section */}
              {performanceData && performanceData.find((p: any) => p.model_version === modelInfo.version) && (
                <div className="mb-4">
                  <h5 className="border-bottom pb-2">Performance Metrics</h5>
                  {(() => {
                    const performance = performanceData.find((p: any) => p.model_version === modelInfo.version);
                    if (!performance) return null;
                    
                    return (
                      <div className="row">
                        <div className="col-md-6">
                          <p><strong>Total Inferences:</strong> {performance.total_inferences.toLocaleString()}</p>
                          <p><strong>Average Inference Time:</strong> {(performance.performance_metrics.avg_inference_time * 1000).toFixed(2)}ms</p>
                          <p><strong>Min Inference Time:</strong> {(performance.performance_metrics.min_inference_time * 1000).toFixed(2)}ms</p>
                        </div>
                        <div className="col-md-6">
                          <p><strong>Max Inference Time:</strong> {(performance.performance_metrics.max_inference_time * 1000).toFixed(2)}ms</p>
                          <p><strong>Average Anomaly Score:</strong> {performance.performance_metrics.avg_anomaly_score.toFixed(3)}</p>
                          <p><strong>Anomaly Rate:</strong> {(performance.performance_metrics.anomaly_rate * 100).toFixed(2)}%</p>
                          <p><strong>Total Anomalies:</strong> {performance.performance_metrics.total_anomalies.toLocaleString()}</p>
                        </div>
                        {performance.last_updated && (
                          <div className="col-12 mt-2">
                            <small className="text-muted">
                              <strong>Last Updated:</strong> {new Date(performance.last_updated).toLocaleString()}
                            </small>
                          </div>
                        )}
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Model Quality Assessment */}
              {(modelInfo as any).metadata?.evaluation_info?.basic_metrics && (
                <div className="mb-4">
                  <h5 className="border-bottom pb-2">Quality Assessment</h5>
                  {(() => {
                    const metrics = (modelInfo as any).metadata.evaluation_info.basic_metrics;
                    const assessments = [];
                    
                    // F1 Score assessment
                    if (metrics.f1_score >= 0.9) {
                      assessments.push({ metric: 'F1 Score', status: 'Excellent', color: 'success', value: `${(metrics.f1_score * 100).toFixed(1)}%` });
                    } else if (metrics.f1_score >= 0.7) {
                      assessments.push({ metric: 'F1 Score', status: 'Good', color: 'info', value: `${(metrics.f1_score * 100).toFixed(1)}%` });
                    } else if (metrics.f1_score >= 0.5) {
                      assessments.push({ metric: 'F1 Score', status: 'Fair', color: 'warning', value: `${(metrics.f1_score * 100).toFixed(1)}%` });
                    } else {
                      assessments.push({ metric: 'F1 Score', status: 'Poor', color: 'danger', value: `${(metrics.f1_score * 100).toFixed(1)}%` });
                    }
                    
                    // ROC AUC assessment
                    if (metrics.roc_auc >= 0.9) {
                      assessments.push({ metric: 'ROC AUC', status: 'Excellent', color: 'success', value: `${(metrics.roc_auc * 100).toFixed(1)}%` });
                    } else if (metrics.roc_auc >= 0.8) {
                      assessments.push({ metric: 'ROC AUC', status: 'Good', color: 'info', value: `${(metrics.roc_auc * 100).toFixed(1)}%` });
                    } else if (metrics.roc_auc >= 0.6) {
                      assessments.push({ metric: 'ROC AUC', status: 'Fair', color: 'warning', value: `${(metrics.roc_auc * 100).toFixed(1)}%` });
                    } else {
                      assessments.push({ metric: 'ROC AUC', status: 'Poor', color: 'danger', value: `${(metrics.roc_auc * 100).toFixed(1)}%` });
                    }
                    
                    return (
                      <div className="row">
                        {assessments.map((assessment, index) => (
                          <div key={index} className="col-md-6 mb-2">
                            <div className="d-flex justify-content-between align-items-center">
                              <span><strong>{assessment.metric}:</strong></span>
                              <div>
                                <Badge bg={assessment.color} className="me-2">{assessment.status}</Badge>
                                <span>{assessment.value}</span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    );
                  })()}
                </div>
              )}

              {/* Recommendations Section */}
              {(modelInfo as any).metadata?.evaluation_info?.basic_metrics && (
                <div className="mb-4">
                  <h5 className="border-bottom pb-2">Recommendations</h5>
                  {(() => {
                    const metrics = (modelInfo as any).metadata.evaluation_info.basic_metrics;
                    const recommendations = [];
                    
                    if (metrics.f1_score < 0.7) {
                      recommendations.push("Consider retraining with more data or different parameters to improve F1 score");
                    }
                    if (metrics.roc_auc < 0.8) {
                      recommendations.push("Feature engineering or model tuning may improve ROC AUC performance");
                    }
                    if (metrics.precision < 0.8) {
                      recommendations.push("High false positive rate detected - consider adjusting classification threshold");
                    }
                    if (metrics.recall < 0.8) {
                      recommendations.push("Low recall indicates missed anomalies - consider model retraining");
                    }
                    
                    if (recommendations.length === 0) {
                      recommendations.push("Model performance is within acceptable ranges");
                    }
                    
                    return (
                      <ul className="list-group">
                        {recommendations.map((rec, index) => (
                          <li key={index} className="list-group-item">
                            <FaInfoCircle className="me-2 text-info" />
                            {rec}
                          </li>
                        ))}
                      </ul>
                    );
                  })()}
                </div>
              )}
            </div>
          ) : null}
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
            <ModelValidationSummaryComponent validationSummary={showValidationSummary} />
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowValidationSummary(null)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Model Validation Modal */}
      <ModelValidationModal
        show={showValidationModal}
        onHide={() => {
          setShowValidationModal(false);
          setValidationResult(null);
        }}
        validationResult={validationResult}
        modelVersion={validatingModel || ''}
        isLoading={!!validatingModel}
      />
    </div>
  );
};

export default Models;