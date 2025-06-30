import React from 'react';
import { Modal, Badge, Alert, Table, ProgressBar, Row, Col, Card, Button } from 'react-bootstrap';
import { FaCheckCircle, FaExclamationTriangle, FaInfoCircle, FaTimesCircle, FaDownload, FaCopy } from 'react-icons/fa';
import type { ModelValidationResult } from '../../services/types';
import { toast } from 'react-hot-toast';

interface ModelValidationModalProps {
  show: boolean;
  onHide: () => void;
  validationResult: ModelValidationResult | null;
  modelVersion: string;
  isLoading?: boolean;
}

const ModelValidationModal: React.FC<ModelValidationModalProps> = ({
  show,
  onHide,
  validationResult,
  modelVersion,
  isLoading = false
}) => {
  if (!validationResult) {
    return (
      <Modal show={show} onHide={onHide} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Model Validation</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="text-center py-4">
            <FaInfoCircle className="h-4 w-4 text-muted mb-3" />
            <p>No validation data available</p>
          </div>
        </Modal.Body>
      </Modal>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'danger';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 0.8) return 'Excellent';
    if (score >= 0.6) return 'Good';
    if (score >= 0.4) return 'Fair';
    return 'Poor';
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return <FaTimesCircle className="text-danger" />;
      case 'warning':
        return <FaExclamationTriangle className="text-warning" />;
      case 'info':
        return <FaInfoCircle className="text-info" />;
      default:
        return <FaInfoCircle className="text-muted" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'error':
        return <Badge bg="danger">Error</Badge>;
      case 'warning':
        return <Badge bg="warning" text="dark">Warning</Badge>;
      case 'info':
        return <Badge bg="info">Info</Badge>;
      default:
        return <Badge bg="secondary">Unknown</Badge>;
    }
  };

  const generateValidationReport = () => {
    const report = {
      report_generated_at: new Date().toISOString(),
      model_version: modelVersion,
      executive_summary: {
        package_name: validationResult.package_info?.package_identifier?.name || 'Unknown',
        package_version: validationResult.package_info?.package_identifier?.version || modelVersion,
        algorithm: validationResult.package_info?.model_details?.algorithm || 'Unknown',
        framework: validationResult.package_info?.model_details?.framework || 'Unknown',
        validation_status: validationResult.is_valid ? 'PASSED' : 'FAILED',
        overall_score: validationResult.score,
        score_label: getScoreLabel(validationResult.score),
        critical_issues: validationResult.errors.length,
        warnings: validationResult.warnings.length,
        recommendations: validationResult.recommendations.length
      },
      validation_summary: {
        is_valid: validationResult.is_valid,
        overall_score: validationResult.score,
        score_label: getScoreLabel(validationResult.score),
        error_count: validationResult.errors.length,
        warning_count: validationResult.warnings.length,
        recommendation_count: validationResult.recommendations.length
      },
      quality_metrics: validationResult.quality_metrics || {},
      issues: validationResult.issues || [],
      errors: validationResult.errors,
      warnings: validationResult.warnings,
      recommendations: validationResult.recommendations,
      next_steps: validationResult.is_valid ? [
        "Model is ready for deployment",
        "Monitor model performance in production",
        "Set up automated retraining if needed"
      ] : [
        "Address validation errors before deployment",
        "Consider retraining the model",
        "Review and fix configuration issues",
        "Validate against a larger test dataset"
      ]
    };
    return report;
  };

  const exportToFile = () => {
    try {
      const report = generateValidationReport();
      const reportJson = JSON.stringify(report, null, 2);
      const blob = new Blob([reportJson], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Create a more descriptive filename
      const packageName = validationResult.package_info?.package_identifier?.name || 'unknown';
      const packageVersion = validationResult.package_info?.package_identifier?.version || modelVersion;
      const algorithm = validationResult.package_info?.model_details?.algorithm || 'unknown';
      const date = new Date().toISOString().split('T')[0];
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0] + '_' + new Date().toISOString().split('T')[1].split('.')[0].replace(/:/g, '-');
      
      a.download = `validation_report_${packageName}_${packageVersion}_${algorithm}_${timestamp}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success('Validation report exported successfully');
    } catch (error) {
      console.error('Error exporting report:', error);
      toast.error('Failed to export validation report');
    }
  };

  const copyToClipboard = async () => {
    try {
      const report = generateValidationReport();
      const reportText = JSON.stringify(report, null, 2);
      await navigator.clipboard.writeText(reportText);
      toast.success('Validation report copied to clipboard');
    } catch (error) {
      console.error('Error copying to clipboard:', error);
      toast.error('Failed to copy validation report');
    }
  };

  return (
    <Modal show={show} onHide={onHide} size="xl">
      <Modal.Header closeButton>
        <Modal.Title>
          <div className="d-flex align-items-center gap-2">
            <FaCheckCircle className="text-primary" />
            Model Validation Results
          </div>
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {isLoading ? (
          <div className="text-center py-4">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
            <p className="mt-2">Validating model...</p>
          </div>
        ) : (
          <div>
            {/* Export Actions */}
            <div className="d-flex justify-content-end mb-3">
              <div className="d-flex gap-2">
                <Button
                  variant="outline-secondary"
                  size="sm"
                  onClick={copyToClipboard}
                  title="Copy validation report to clipboard"
                >
                  <FaCopy className="me-1" />
                  Copy Report
                </Button>
                <Button
                  variant="outline-primary"
                  size="sm"
                  onClick={exportToFile}
                  title="Download validation report as JSON file"
                >
                  <FaDownload className="me-1" />
                  Export Report
                </Button>
              </div>
            </div>

            {/* Package Information */}
            {validationResult.package_info && (
              <Card className="mb-4 border-primary">
                <Card.Header className="bg-primary text-white">
                  <h6 className="mb-0">Model Package Information</h6>
                </Card.Header>
                <Card.Body>
                  <Row>
                    <Col md={6}>
                      <h6>Package Identifier</h6>
                      <ul className="list-unstyled">
                        <li><strong>Name:</strong> {validationResult.package_info.package_identifier.name || 'Not specified'}</li>
                        <li><strong>Version:</strong> {validationResult.package_info.package_identifier.version || 'Not specified'}</li>
                        <li><strong>Type:</strong> {validationResult.package_info.package_identifier.type || 'Not specified'}</li>
                        <li><strong>Description:</strong> {validationResult.package_info.package_identifier.description || 'Not specified'}</li>
                        {validationResult.package_info.package_identifier.author && (
                          <li><strong>Author:</strong> {validationResult.package_info.package_identifier.author}</li>
                        )}
                        {validationResult.package_info.package_identifier.organization && (
                          <li><strong>Organization:</strong> {validationResult.package_info.package_identifier.organization}</li>
                        )}
                      </ul>
                    </Col>
                    <Col md={6}>
                      <h6>Model Details</h6>
                      <ul className="list-unstyled">
                        <li><strong>Algorithm:</strong> {validationResult.package_info.model_details.algorithm || 'Unknown'}</li>
                        <li><strong>Framework:</strong> {validationResult.package_info.model_details.framework || 'Unknown'}</li>
                        <li><strong>Framework Version:</strong> {validationResult.package_info.model_details.framework_version || 'Unknown'}</li>
                        <li><strong>Model Type:</strong> {validationResult.package_info.model_details.model_type || 'Not specified'}</li>
                      </ul>
                    </Col>
                  </Row>
                  
                  <Row className="mt-3">
                    <Col md={6}>
                      <h6>Source Information</h6>
                      <ul className="list-unstyled">
                        <li><strong>Training Source:</strong> {validationResult.package_info.source_information.training_source || 'Not specified'}</li>
                        <li><strong>Training ID:</strong> {validationResult.package_info.source_information.training_id || 'Not specified'}</li>
                        <li><strong>Original Path:</strong> <code className="small">{validationResult.package_info.source_information.original_path || 'Not specified'}</code></li>
                        <li><strong>Import Timestamp:</strong> {validationResult.package_info.source_information.import_timestamp || 'Not specified'}</li>
                      </ul>
                    </Col>
                    <Col md={6}>
                      <h6>Creation Information</h6>
                      <ul className="list-unstyled">
                        <li><strong>Created At:</strong> {validationResult.package_info.creation_info.created_at || 'Not specified'}</li>
                        <li><strong>Created By:</strong> {validationResult.package_info.creation_info.created_by || 'Not specified'}</li>
                        <li><strong>Training Duration:</strong> {validationResult.package_info.creation_info.training_duration ? `${validationResult.package_info.creation_info.training_duration}s` : 'Not specified'}</li>
                        <li><strong>Last Modified:</strong> {validationResult.package_info.creation_info.last_modified || 'Not specified'}</li>
                      </ul>
                    </Col>
                  </Row>
                  
                  {validationResult.package_info.deployment_info.environment_dependencies.length > 0 && (
                    <div className="mt-3">
                      <h6>Environment Dependencies</h6>
                      <div className="bg-light p-2 rounded">
                        <code className="small">
                          {validationResult.package_info.deployment_info.environment_dependencies.join(', ')}
                        </code>
                      </div>
                    </div>
                  )}
                </Card.Body>
              </Card>
            )}

            {/* Header Summary */}
            <Row className="mb-4">
              <Col md={6}>
                <Card>
                  <Card.Body>
                    <h6 className="text-muted mb-2">Model Version</h6>
                    <h5>{modelVersion}</h5>
                  </Card.Body>
                </Card>
              </Col>
              <Col md={6}>
                <Card>
                  <Card.Body>
                    <h6 className="text-muted mb-2">Overall Score</h6>
                    <div className="d-flex align-items-center gap-2">
                      <h5 className={`text-${getScoreColor(validationResult.score)}`}>
                        {(validationResult.score * 100).toFixed(1)}%
                      </h5>
                      <Badge bg={getScoreColor(validationResult.score)}>
                        {getScoreLabel(validationResult.score)}
                      </Badge>
                    </div>
                    <ProgressBar 
                      now={validationResult.score * 100} 
                      variant={getScoreColor(validationResult.score)}
                      className="mt-2"
                    />
                  </Card.Body>
                </Card>
              </Col>
            </Row>

            {/* Validation Status */}
            <Alert variant={validationResult.is_valid ? 'success' : 'danger'} className="mb-4">
              <div className="d-flex align-items-center gap-2">
                {validationResult.is_valid ? (
                  <FaCheckCircle />
                ) : (
                  <FaTimesCircle />
                )}
                <strong>
                  {validationResult.is_valid ? 'Validation Passed' : 'Validation Failed'}
                </strong>
              </div>
              <p className="mb-0 mt-2">
                {validationResult.is_valid 
                  ? 'This model meets the minimum quality requirements and is ready for deployment.'
                  : 'This model has issues that should be addressed before deployment.'
                }
              </p>
            </Alert>

            {/* Quality Metrics */}
            {validationResult.quality_metrics && (
              <Card className="mb-4">
                <Card.Header>
                  <h6 className="mb-0">Quality Metrics</h6>
                </Card.Header>
                <Card.Body>
                  <Row>
                    <Col md={2}>
                      <div className="text-center">
                        <h6 className="text-muted">F1 Score</h6>
                        <h4 className={`text-${validationResult.quality_metrics.f1_score >= 0.5 ? 'success' : 'danger'}`}>
                          {validationResult.quality_metrics.f1_score.toFixed(3)}
                        </h4>
                        <small className="text-muted">Threshold: 0.5</small>
                      </div>
                    </Col>
                    <Col md={2}>
                      <div className="text-center">
                        <h6 className="text-muted">ROC AUC</h6>
                        <h4 className={`text-${validationResult.quality_metrics.roc_auc >= 0.6 ? 'success' : 'danger'}`}>
                          {validationResult.quality_metrics.roc_auc.toFixed(3)}
                        </h4>
                        <small className="text-muted">Threshold: 0.6</small>
                      </div>
                    </Col>
                    <Col md={2}>
                      <div className="text-center">
                        <h6 className="text-muted">Precision</h6>
                        <h4 className="text-primary">
                          {validationResult.quality_metrics.precision.toFixed(3)}
                        </h4>
                      </div>
                    </Col>
                    <Col md={2}>
                      <div className="text-center">
                        <h6 className="text-muted">Recall</h6>
                        <h4 className="text-primary">
                          {validationResult.quality_metrics.recall.toFixed(3)}
                        </h4>
                      </div>
                    </Col>
                    <Col md={2}>
                      <div className="text-center">
                        <h6 className="text-muted">Accuracy</h6>
                        <h4 className="text-primary">
                          {validationResult.quality_metrics.accuracy.toFixed(3)}
                        </h4>
                      </div>
                    </Col>
                  </Row>
                </Card.Body>
              </Card>
            )}

            {/* Issues List */}
            {validationResult.issues && validationResult.issues.length > 0 && (
              <Card className="mb-4">
                <Card.Header>
                  <h6 className="mb-0">Issues Found</h6>
                </Card.Header>
                <Card.Body>
                  <Table responsive>
                    <thead>
                      <tr>
                        <th>Severity</th>
                        <th>Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {validationResult.issues.map((issue, index) => (
                        <tr key={index}>
                          <td>
                            <div className="d-flex align-items-center gap-2">
                              {getSeverityIcon(issue.severity)}
                              {getSeverityBadge(issue.severity)}
                            </div>
                          </td>
                          <td>{issue.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </Card.Body>
              </Card>
            )}

            {/* Errors */}
            {validationResult.errors && validationResult.errors.length > 0 && (
              <Card className="mb-4 border-danger">
                <Card.Header className="bg-danger text-white">
                  <h6 className="mb-0">
                    <FaTimesCircle className="me-2" />
                    Errors ({validationResult.errors.length})
                  </h6>
                </Card.Header>
                <Card.Body>
                  <ul className="list-unstyled mb-0">
                    {validationResult.errors.map((error, index) => (
                      <li key={index} className="mb-2">
                        <FaTimesCircle className="text-danger me-2" />
                        {error}
                      </li>
                    ))}
                  </ul>
                </Card.Body>
              </Card>
            )}

            {/* Warnings */}
            {validationResult.warnings && validationResult.warnings.length > 0 && (
              <Card className="mb-4 border-warning">
                <Card.Header className="bg-warning text-dark">
                  <h6 className="mb-0">
                    <FaExclamationTriangle className="me-2" />
                    Warnings ({validationResult.warnings.length})
                  </h6>
                </Card.Header>
                <Card.Body>
                  <ul className="list-unstyled mb-0">
                    {validationResult.warnings.map((warning, index) => (
                      <li key={index} className="mb-2">
                        <FaExclamationTriangle className="text-warning me-2" />
                        {warning}
                      </li>
                    ))}
                  </ul>
                </Card.Body>
              </Card>
            )}

            {/* Recommendations */}
            {validationResult.recommendations && validationResult.recommendations.length > 0 && (
              <Card className="mb-4 border-info">
                <Card.Header className="bg-info text-white">
                  <h6 className="mb-0">
                    <FaInfoCircle className="me-2" />
                    Recommendations ({validationResult.recommendations.length})
                  </h6>
                </Card.Header>
                <Card.Body>
                  <ul className="list-unstyled mb-0">
                    {validationResult.recommendations.map((recommendation, index) => (
                      <li key={index} className="mb-2">
                        <FaInfoCircle className="text-info me-2" />
                        {recommendation}
                      </li>
                    ))}
                  </ul>
                </Card.Body>
              </Card>
            )}

            {/* Package Structure */}
            {validationResult.package_structure && (
              <Card className="mb-4 border-info">
                <Card.Header className="bg-info text-white">
                  <h6 className="mb-0">Package Structure</h6>
                </Card.Header>
                <Card.Body>
                  <Row>
                    <Col md={6}>
                      <h6>Required Files</h6>
                      <ul className="list-unstyled">
                        {Object.entries(validationResult.package_structure.required_files).map(([file, exists]) => (
                          <li key={file} className="mb-1">
                            {exists ? (
                              <FaCheckCircle className="text-success me-2" />
                            ) : (
                              <FaTimesCircle className="text-danger me-2" />
                            )}
                            {file}
                          </li>
                        ))}
                      </ul>
                    </Col>
                    <Col md={6}>
                      <h6>Optional Files</h6>
                      <ul className="list-unstyled">
                        {Object.entries(validationResult.package_structure.optional_files).map(([file, exists]) => (
                          <li key={file} className="mb-1">
                            {exists ? (
                              <FaCheckCircle className="text-success me-2" />
                            ) : (
                              <FaInfoCircle className="text-muted me-2" />
                            )}
                            {file}
                          </li>
                        ))}
                      </ul>
                    </Col>
                  </Row>
                  <div className="mt-3">
                    <small className="text-muted">
                      Total package size: {(validationResult.package_structure.total_package_size / 1024).toFixed(1)} KB
                    </small>
                  </div>
                </Card.Body>
              </Card>
            )}

            {/* Trainer Notes */}
            {validationResult.trainer_notes && (
              <Card className="mb-4 border-warning">
                <Card.Header className="bg-warning text-dark">
                  <h6 className="mb-0">Notes for Model Trainer</h6>
                </Card.Header>
                <Card.Body>
                  {validationResult.trainer_notes.critical_issues.length > 0 && (
                    <div className="mb-3">
                      <h6 className="text-danger">Critical Issues</h6>
                      <ul className="list-unstyled">
                        {validationResult.trainer_notes.critical_issues.map((issue, index) => (
                          <li key={index} className="mb-1">
                            <FaTimesCircle className="text-danger me-2" />
                            {issue}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {validationResult.trainer_notes.quality_concerns.length > 0 && (
                    <div className="mb-3">
                      <h6 className="text-warning">Quality Concerns</h6>
                      <ul className="list-unstyled">
                        {validationResult.trainer_notes.quality_concerns.map((concern, index) => (
                          <li key={index} className="mb-1">
                            <FaExclamationTriangle className="text-warning me-2" />
                            {concern}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {validationResult.trainer_notes.missing_components.length > 0 && (
                    <div className="mb-3">
                      <h6 className="text-info">Missing Components</h6>
                      <ul className="list-unstyled">
                        {validationResult.trainer_notes.missing_components.map((component, index) => (
                          <li key={index} className="mb-1">
                            <FaInfoCircle className="text-info me-2" />
                            {component}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {validationResult.trainer_notes.improvement_suggestions.length > 0 && (
                    <div className="mb-3">
                      <h6 className="text-primary">Improvement Suggestions</h6>
                      <ul className="list-unstyled">
                        {validationResult.trainer_notes.improvement_suggestions.map((suggestion, index) => (
                          <li key={index} className="mb-1">
                            <FaInfoCircle className="text-primary me-2" />
                            {suggestion}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {validationResult.trainer_notes.priority_actions.length > 0 && (
                    <div>
                      <h6 className="text-dark">Priority Actions</h6>
                      <ul className="list-unstyled">
                        {validationResult.trainer_notes.priority_actions.map((action, index) => (
                          <li key={index} className="mb-1">
                            <FaCheckCircle className="text-success me-2" />
                            {action}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </Card.Body>
              </Card>
            )}

            {/* Next Steps */}
            <Card className="border-primary">
              <Card.Header className="bg-primary text-white">
                <h6 className="mb-0">Next Steps</h6>
              </Card.Header>
              <Card.Body>
                {validationResult.is_valid ? (
                  <div>
                    <p className="text-success mb-2">
                      <FaCheckCircle className="me-2" />
                      This model is ready for deployment.
                    </p>
                    <ul className="list-unstyled">
                      <li>• Deploy the model to production</li>
                      <li>• Monitor model performance in production</li>
                      <li>• Set up automated retraining if needed</li>
                    </ul>
                  </div>
                ) : (
                  <div>
                    <p className="text-danger mb-2">
                      <FaTimesCircle className="me-2" />
                      Address the following issues before deployment:
                    </p>
                    <ul className="list-unstyled">
                      <li>• Review and fix validation errors</li>
                      <li>• Consider retraining the model with better data</li>
                      <li>• Adjust model parameters if necessary</li>
                      <li>• Validate against a larger test dataset</li>
                    </ul>
                  </div>
                )}
              </Card.Body>
            </Card>
          </div>
        )}
      </Modal.Body>
    </Modal>
  );
};

export default ModelValidationModal; 