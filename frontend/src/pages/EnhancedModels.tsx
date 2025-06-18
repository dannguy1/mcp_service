/**
 * Enhanced Models Component
 * 
 * This component provides model management functionality for the MCP service.
 * 
 * Architectural Note: Training service functionality has been intentionally excluded
 * from this component to maintain proper separation of concerns. The training service
 * may be deployed on a separate server and should have its own independent UI.
 * This design prevents unnecessary coupling and architectural assumptions about
 * service co-location.
 */

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Card, 
  Table, 
  Badge, 
  Button, 
  Spinner, 
  Alert, 
  Modal, 
  Form, 
  Row, 
  Col,
  ProgressBar,
  ListGroup,
  Accordion,
  Tabs,
  Tab
} from 'react-bootstrap';
import { 
  FaInfoCircle, 
  FaTrash, 
  FaPlus, 
  FaSync, 
  FaExclamationTriangle,
  FaDownload,
  FaUpload,
  FaCheck,
  FaTimes,
  FaChartLine,
  FaCog,
  FaHistory,
  FaShieldAlt,
  FaRocket,
  FaUndo
} from 'react-icons/fa';
import { endpoints } from '../services/api';
import type { 
  ModelValidationResult,
  ModelPerformanceMetrics,
  ModelDriftResult,
  ModelTransferHistory
} from '../services/types';
import { toast } from 'react-hot-toast';

const EnhancedModels: React.FC = () => {
  const queryClient = useQueryClient();
  
  // State management
  const [showValidationModal, setShowValidationModal] = useState<string | null>(null);
  const [showPerformanceModal, setShowPerformanceModal] = useState<string | null>(null);
  const [showTransferHistoryModal, setShowTransferHistoryModal] = useState(false);
  const [validationResult, setValidationResult] = useState<ModelValidationResult | null>(null);
  const [performanceData, setPerformanceData] = useState<ModelPerformanceMetrics | null>(null);
  const [driftData, setDriftData] = useState<ModelDriftResult | null>(null);
  const [activeTab, setActiveTab] = useState('models');

  // Queries
  const { data: models, isLoading: modelsLoading, error: modelsError } = useQuery({
    queryKey: ['enhanced-models'],
    queryFn: () => endpoints.listEnhancedModels(),
    refetchInterval: 30000,
  });

  const { data: basicModels, isLoading: basicModelsLoading, error: basicModelsError } = useQuery({
    queryKey: ['basic-models'],
    queryFn: () => endpoints.getModels(),
    refetchInterval: 30000,
  });

  const { data: transferHistory } = useQuery({
    queryKey: ['transfer-history'],
    queryFn: () => endpoints.getTransferHistory(),
    refetchInterval: 60000,
  });

  const { data: allPerformance } = useQuery({
    queryKey: ['all-model-performance'],
    queryFn: () => endpoints.getAllModelPerformance(),
    refetchInterval: 30000,
  });

  // Mutations
  const deployMutation = useMutation({
    mutationFn: (version: string) => endpoints.deployModelVersion(version),
    onSuccess: () => {
      toast.success('Model deployed successfully');
      queryClient.invalidateQueries({ queryKey: ['enhanced-models'] });
    },
    onError: (error) => {
      toast.error(`Failed to deploy model: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const rollbackMutation = useMutation({
    mutationFn: (version: string) => endpoints.rollbackModel(version),
    onSuccess: () => {
      toast.success('Model rolled back successfully');
      queryClient.invalidateQueries({ queryKey: ['enhanced-models'] });
    },
    onError: (error) => {
      toast.error(`Failed to rollback model: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const validateMutation = useMutation({
    mutationFn: (version: string) => endpoints.validateModel(version),
    onSuccess: (data) => {
      setValidationResult(data);
      setShowValidationModal('validation');
    },
    onError: (error) => {
      toast.error(`Failed to validate model: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  const checkDriftMutation = useMutation({
    mutationFn: (version: string) => endpoints.checkModelDrift(version),
    onSuccess: (data) => {
      setDriftData(data);
      setShowPerformanceModal('drift');
    },
    onError: (error) => {
      toast.error(`Failed to check model drift: ${error instanceof Error ? error.message : 'Unknown error'}`);
    },
  });

  // Handlers
  const handleValidateModel = (version: string) => {
    validateMutation.mutate(version);
  };

  const handleDeployModel = (version: string) => {
    deployMutation.mutate(version);
  };

  const handleRollbackModel = (version: string) => {
    rollbackMutation.mutate(version);
  };

  const handleCheckDrift = (version: string) => {
    checkDriftMutation.mutate(version);
  };

  const handleViewPerformance = async (version: string) => {
    try {
      const performance = await endpoints.getModelPerformance(version);
      setPerformanceData(performance);
      setShowPerformanceModal('performance');
    } catch (error) {
      toast.error(`Failed to fetch performance data: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  if (modelsLoading || basicModelsLoading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '200px' }}>
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </div>
    );
  }

  if (modelsError || basicModelsError) {
    return (
      <Alert variant="danger">
        <FaExclamationTriangle className="me-2" />
        Error loading model data: {modelsError instanceof Error ? modelsError.message : 'Unknown error'}
      </Alert>
    );
  }

  return (
    <div className="container-fluid">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Model Management</h2>
        <div className="d-flex gap-2">
          <Button 
            variant="outline-primary" 
            onClick={() => {
              queryClient.invalidateQueries({ queryKey: ['enhanced-models'] });
              queryClient.invalidateQueries({ queryKey: ['basic-models'] });
            }}
            disabled={modelsLoading || basicModelsLoading}
          >
            <FaSync className="me-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs activeKey={activeTab} onSelect={(k) => setActiveTab(k || 'models')} className="mb-4">
        <Tab eventKey="models" title="Local Models">
          <Card>
            <Card.Body>
              <Table responsive hover>
                <thead>
                  <tr>
                    <th>Model ID</th>
                    <th>Version</th>
                    <th>Status</th>
                    <th>Accuracy</th>
                    <th>False Positive Rate</th>
                    <th>False Negative Rate</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {basicModels?.models?.map((model) => (
                    <tr key={model.id}>
                      <td>{model.id}</td>
                      <td>{model.version}</td>
                      <td>
                        <Badge bg={model.status === 'active' ? 'success' : 'secondary'}>
                          {model.status}
                        </Badge>
                      </td>
                      <td>{(model.metrics.accuracy * 100).toFixed(1)}%</td>
                      <td>{(model.metrics.false_positive_rate * 100).toFixed(1)}%</td>
                      <td>{(model.metrics.false_negative_rate * 100).toFixed(1)}%</td>
                      <td>
                        <div className="d-flex gap-2">
                          <Button
                            variant="success"
                            size="sm"
                            onClick={() => handleDeployModel(model.version)}
                            disabled={deployMutation.isPending}
                            title="Deploy this model version"
                          >
                            <FaRocket />
                          </Button>
                          <Button
                            variant="warning"
                            size="sm"
                            onClick={() => handleRollbackModel(model.version)}
                            disabled={rollbackMutation.isPending}
                            title="Rollback to this version"
                          >
                            <FaUndo />
                          </Button>
                          <Button
                            variant="info"
                            size="sm"
                            onClick={() => handleValidateModel(model.version)}
                            disabled={validateMutation.isPending}
                            title="Validate model quality and performance"
                          >
                            <FaShieldAlt />
                          </Button>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleCheckDrift(model.version)}
                            disabled={checkDriftMutation.isPending}
                            title="Check for model drift and performance degradation"
                          >
                            <FaExclamationTriangle />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Tab>

        <Tab eventKey="performance" title="Performance">
          <Row>
            {allPerformance?.map((perf) => (
              <Col key={perf.model_version} md={6} lg={4} className="mb-3">
                <Card>
                  <Card.Header>
                    <strong>Model {perf.model_version}</strong>
                  </Card.Header>
                  <Card.Body>
                    <div className="mb-2">
                      <small className="text-muted">Total Inferences</small>
                      <div>{perf.total_inferences.toLocaleString()}</div>
                    </div>
                    <div className="mb-2">
                      <small className="text-muted">Avg Inference Time</small>
                      <div>{(perf.performance_metrics.avg_inference_time * 1000).toFixed(2)}ms</div>
                    </div>
                    <div className="mb-2">
                      <small className="text-muted">Anomaly Rate</small>
                      <div>{(perf.performance_metrics.anomaly_rate * 100).toFixed(2)}%</div>
                    </div>
                    <Button
                      variant="outline-primary"
                      size="sm"
                      onClick={() => handleViewPerformance(perf.model_version)}
                    >
                      View Details
                    </Button>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>
        </Tab>
      </Tabs>

      {/* Validation Modal */}
      <Modal show={showValidationModal === 'validation'} onHide={() => setShowValidationModal(null)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Model Validation Results</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {validationResult && (
            <div>
              <Alert variant={validationResult.is_valid ? 'success' : 'danger'}>
                <strong>Validation Status:</strong> {validationResult.is_valid ? 'PASSED' : 'FAILED'}
              </Alert>
              
              <h5>Quality Metrics</h5>
              <Table striped bordered>
                <tbody>
                  <tr>
                    <th>Accuracy</th>
                    <td>{(validationResult.quality_metrics.accuracy * 100).toFixed(1)}%</td>
                  </tr>
                  <tr>
                    <th>Precision</th>
                    <td>{(validationResult.quality_metrics.precision * 100).toFixed(1)}%</td>
                  </tr>
                  <tr>
                    <th>Recall</th>
                    <td>{(validationResult.quality_metrics.recall * 100).toFixed(1)}%</td>
                  </tr>
                  <tr>
                    <th>F1 Score</th>
                    <td>{(validationResult.quality_metrics.f1_score * 100).toFixed(1)}%</td>
                  </tr>
                </tbody>
              </Table>

              {validationResult.issues && validationResult.issues.length > 0 && (
                <>
                  <h5>Issues Found</h5>
                  <ListGroup>
                    {validationResult.issues.map((issue, index) => (
                      <ListGroup.Item key={index} variant="warning">
                        <strong>{issue.severity}:</strong> {issue.description}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </>
              )}

              {validationResult.recommendations && validationResult.recommendations.length > 0 && (
                <>
                  <h5>Recommendations</h5>
                  <ListGroup>
                    {validationResult.recommendations.map((rec, index) => (
                      <ListGroup.Item key={index} variant="info">
                        {rec}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </>
              )}
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowValidationModal(null)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Performance Modal */}
      <Modal show={showPerformanceModal !== null} onHide={() => setShowPerformanceModal(null)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            {showPerformanceModal === 'performance' ? 'Model Performance Details' : 'Model Drift Analysis'}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {showPerformanceModal === 'performance' && performanceData && (
            <div>
              <h5>Performance Metrics</h5>
              <Table striped bordered>
                <tbody>
                  <tr>
                    <th>Total Inferences</th>
                    <td>{performanceData.total_inferences.toLocaleString()}</td>
                  </tr>
                  <tr>
                    <th>Average Inference Time</th>
                    <td>{(performanceData.performance_metrics.avg_inference_time * 1000).toFixed(2)}ms</td>
                  </tr>
                  <tr>
                    <th>Anomaly Rate</th>
                    <td>{(performanceData.performance_metrics.anomaly_rate * 100).toFixed(2)}%</td>
                  </tr>
                  <tr>
                    <th>Throughput</th>
                    <td>{performanceData.performance_metrics.throughput.toFixed(2)} inferences/sec</td>
                  </tr>
                </tbody>
              </Table>

              {performanceData.trends && (
                <>
                  <h5>Performance Trends</h5>
                  <Row>
                    <Col md={6}>
                      <Card>
                        <Card.Body>
                          <h6>Inference Time Trend</h6>
                          <div className="text-center">
                            <span className={`badge ${performanceData.trends.inference_time_trend === 'improving' ? 'bg-success' : 'bg-warning'}`}>
                              {performanceData.trends.inference_time_trend}
                            </span>
                          </div>
                        </Card.Body>
                      </Card>
                    </Col>
                    <Col md={6}>
                      <Card>
                        <Card.Body>
                          <h6>Accuracy Trend</h6>
                          <div className="text-center">
                            <span className={`badge ${performanceData.trends.accuracy_trend === 'improving' ? 'bg-success' : 'bg-warning'}`}>
                              {performanceData.trends.accuracy_trend}
                            </span>
                          </div>
                        </Card.Body>
                      </Card>
                    </Col>
                  </Row>
                </>
              )}
            </div>
          )}

          {showPerformanceModal === 'drift' && driftData && (
            <div>
              <Alert variant={driftData.drift_detected ? 'warning' : 'success'}>
                <strong>Drift Status:</strong> {driftData.drift_detected ? 'DRIFT DETECTED' : 'NO DRIFT DETECTED'}
              </Alert>

              <h5>Drift Metrics</h5>
              <Table striped bordered>
                <tbody>
                  <tr>
                    <th>Feature Drift Score</th>
                    <td>{(driftData.drift_metrics.feature_drift_score * 100).toFixed(2)}%</td>
                  </tr>
                  <tr>
                    <th>Prediction Drift Score</th>
                    <td>{(driftData.drift_metrics.prediction_drift_score * 100).toFixed(2)}%</td>
                  </tr>
                  <tr>
                    <th>Data Quality Score</th>
                    <td>{(driftData.drift_metrics.data_quality_score * 100).toFixed(2)}%</td>
                  </tr>
                </tbody>
              </Table>

              {driftData.recommendations && driftData.recommendations.length > 0 && (
                <>
                  <h5>Recommendations</h5>
                  <ListGroup>
                    {driftData.recommendations.map((rec, index) => (
                      <ListGroup.Item key={index} variant="info">
                        {rec}
                      </ListGroup.Item>
                    ))}
                  </ListGroup>
                </>
              )}
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowPerformanceModal(null)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default EnhancedModels; 