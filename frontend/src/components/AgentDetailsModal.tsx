import React from 'react';
import { 
  Modal, 
  Card, 
  Badge, 
  Table, 
  ListGroup, 
  Accordion,
  Spinner,
  Alert
} from 'react-bootstrap';
import { 
  FaDatabase, 
  FaDownload, 
  FaCog, 
  FaChartLine, 
  FaInfoCircle,
  FaClock,
  FaCheckCircle,
  FaExclamationTriangle
} from 'react-icons/fa';
import type { AgentDetailedInfo } from '../services/types';

interface AgentDetailsModalProps {
  show: boolean;
  onHide: () => void;
  agentDetailedInfo: AgentDetailedInfo | null;
  isLoading: boolean;
  error: any;
}

const AgentDetailsModal: React.FC<AgentDetailsModalProps> = ({
  show,
  onHide,
  agentDetailedInfo,
  isLoading,
  error
}) => {
  if (isLoading) {
    return (
      <Modal show={show} onHide={onHide} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Agent Details</Modal.Title>
        </Modal.Header>
        <Modal.Body className="text-center py-5">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Loading...</span>
          </Spinner>
          <p className="mt-3">Loading agent details...</p>
        </Modal.Body>
      </Modal>
    );
  }

  if (error) {
    return (
      <Modal show={show} onHide={onHide} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Agent Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Alert variant="danger">
            <FaExclamationTriangle className="me-2" />
            Failed to load agent details: {error.message || 'Unknown error'}
          </Alert>
        </Modal.Body>
      </Modal>
    );
  }

  if (!agentDetailedInfo) {
    return (
      <Modal show={show} onHide={onHide} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Agent Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Alert variant="warning">
            <FaInfoCircle className="me-2" />
            No agent details available
          </Alert>
        </Modal.Body>
      </Modal>
    );
  }

  const { 
    name, 
    description, 
    agent_type, 
    status, 
    is_running, 
    capabilities,
    data_requirements,
    export_considerations,
    configuration,
    model_info,
    performance_metrics
  } = agentDetailedInfo;

  const getStatusBadge = () => {
    if (is_running) {
      return <Badge bg="success">Running</Badge>;
    } else if (status === 'error') {
      return <Badge bg="danger">Error</Badge>;
    } else if (status === 'configured') {
      return <Badge bg="info">Configured</Badge>;
    } else {
      return <Badge bg="secondary">Stopped</Badge>;
    }
  };

  const getAgentTypeBadge = () => {
    const typeColors: Record<string, string> = {
      'ml_based': 'primary',
      'rule_based': 'info',
      'hybrid': 'warning',
      'unknown': 'secondary'
    };
    return <Badge bg={typeColors[agent_type] || 'secondary'}>{agent_type}</Badge>;
  };

  return (
    <Modal show={show} onHide={onHide} size="xl">
      <Modal.Header closeButton>
        <Modal.Title>
          <div className="d-flex align-items-center gap-2">
            <FaInfoCircle />
            {name} - Agent Details
          </div>
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <div className="row">
          {/* Basic Information */}
          <div className="col-12 mb-4">
            <Card>
              <Card.Header>
                <h5 className="mb-0">Basic Information</h5>
              </Card.Header>
              <Card.Body>
                <div className="row">
                  <div className="col-md-6">
                    <p><strong>Name:</strong> {name}</p>
                    <p><strong>Description:</strong> {description || 'No description'}</p>
                    <p><strong>Type:</strong> {getAgentTypeBadge()}</p>
                  </div>
                  <div className="col-md-6">
                    <p><strong>Status:</strong> {getStatusBadge()}</p>
                    <p><strong>Capabilities:</strong></p>
                    <div className="d-flex flex-wrap gap-1">
                      {capabilities.map((capability, index) => (
                        <Badge key={index} bg="primary" className="small" style={{ color: 'white' }}>
                          {capability}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </Card.Body>
            </Card>
          </div>

          {/* Data Requirements */}
          <div className="col-md-6 mb-4">
            <Card>
              <Card.Header>
                <h6 className="mb-0">
                  <FaDatabase className="me-2" />
                  Data Requirements
                </h6>
              </Card.Header>
              <Card.Body>
                <ListGroup variant="flush">
                  <ListGroup.Item>
                    <strong>Data Sources:</strong>
                    {data_requirements.data_sources.length > 0 ? (
                      <div className="mt-1">
                        {data_requirements.data_sources.map((source, index) => (
                          <Badge key={index} bg="secondary" className="me-1" style={{ color: 'white' }}>
                            {source}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <span className="text-muted ms-2">None specified</span>
                    )}
                  </ListGroup.Item>
                  <ListGroup.Item>
                    <strong>Process Filters:</strong>
                    {data_requirements.process_filters.length > 0 ? (
                      <div className="mt-1">
                        {data_requirements.process_filters.map((filter, index) => (
                          <Badge key={index} bg="info" className="me-1" style={{ color: 'white' }}>
                            {filter}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <span className="text-muted ms-2">All processes</span>
                    )}
                  </ListGroup.Item>
                  <ListGroup.Item>
                    <strong>Lookback Period:</strong>
                    <span className="ms-2">
                      {data_requirements.lookback_period || 'Not specified'}
                    </span>
                  </ListGroup.Item>
                  <ListGroup.Item>
                    <strong>Sampling Frequency:</strong>
                    <span className="ms-2">
                      {data_requirements.sampling_frequency || 'Not specified'}
                    </span>
                  </ListGroup.Item>
                </ListGroup>
              </Card.Body>
            </Card>
          </div>

          {/* Export Considerations */}
          <div className="col-md-6 mb-4">
            <Card>
              <Card.Header>
                <h6 className="mb-0">
                  <FaDownload className="me-2" />
                  Export Considerations
                </h6>
              </Card.Header>
              <Card.Body>
                <ListGroup variant="flush">
                  <ListGroup.Item>
                    <strong>Data Format:</strong>
                    <Badge bg="success" className="ms-2" style={{ color: 'white' }}>
                      {export_considerations.data_format}
                    </Badge>
                  </ListGroup.Item>
                  <ListGroup.Item>
                    <strong>Data Volume:</strong>
                    <span className="ms-2">{export_considerations.data_volume_estimate}</span>
                  </ListGroup.Item>
                  <ListGroup.Item>
                    <strong>Required Fields:</strong>
                    {export_considerations.required_fields.length > 0 ? (
                      <div className="mt-1">
                        {export_considerations.required_fields.slice(0, 3).map((field, index) => (
                          <Badge key={index} bg="warning" className="me-1" style={{ color: 'black' }}>
                            {field}
                          </Badge>
                        ))}
                        {export_considerations.required_fields.length > 3 && (
                          <Badge bg="secondary" style={{ color: 'white' }}>
                            +{export_considerations.required_fields.length - 3} more
                          </Badge>
                        )}
                      </div>
                    ) : (
                      <span className="text-muted ms-2">None specified</span>
                    )}
                  </ListGroup.Item>
                  <ListGroup.Item>
                    <strong>Preprocessing Steps:</strong>
                    {export_considerations.preprocessing_steps.length > 0 ? (
                      <div className="mt-1">
                        {export_considerations.preprocessing_steps.slice(0, 2).map((step, index) => (
                          <Badge key={index} bg="info" className="me-1" style={{ color: 'white' }}>
                            {step}
                          </Badge>
                        ))}
                        {export_considerations.preprocessing_steps.length > 2 && (
                          <Badge bg="secondary" style={{ color: 'white' }}>
                            +{export_considerations.preprocessing_steps.length - 2} more
                          </Badge>
                        )}
                      </div>
                    ) : (
                      <span className="text-muted ms-2">None specified</span>
                    )}
                  </ListGroup.Item>
                </ListGroup>
              </Card.Body>
            </Card>
          </div>

          {/* Configuration */}
          <div className="col-md-6 mb-4">
            <Card>
              <Card.Header>
                <h6 className="mb-0">
                  <FaCog className="me-2" />
                  Configuration
                </h6>
              </Card.Header>
              <Card.Body>
                <ListGroup variant="flush">
                  <ListGroup.Item>
                    <strong>Enabled:</strong>
                    <Badge bg={configuration.enabled ? "success" : "danger"} className="ms-2">
                      {configuration.enabled ? "Yes" : "No"}
                    </Badge>
                  </ListGroup.Item>
                  <ListGroup.Item>
                    <strong>Priority:</strong>
                    <Badge bg="primary" className="ms-2" style={{ color: 'white' }}>
                      {configuration.priority}
                    </Badge>
                  </ListGroup.Item>
                  <ListGroup.Item>
                    <strong>Model Path:</strong>
                    <span className="ms-2 text-truncate d-inline-block" style={{ maxWidth: '200px' }}>
                      {configuration.model_path || 'No model assigned'}
                    </span>
                  </ListGroup.Item>
                  <ListGroup.Item>
                    <strong>Analysis Rules:</strong>
                    <span className="ms-2">
                      {Object.keys(configuration.analysis_rules).length} rules configured
                    </span>
                  </ListGroup.Item>
                </ListGroup>
              </Card.Body>
            </Card>
          </div>

          {/* Performance Metrics */}
          <div className="col-md-6 mb-4">
            <Card>
              <Card.Header>
                <h6 className="mb-0">
                  <FaChartLine className="me-2" />
                  Performance Metrics
                </h6>
              </Card.Header>
              <Card.Body>
                {performance_metrics ? (
                  <ListGroup variant="flush">
                    <ListGroup.Item>
                      <strong>Analysis Cycles:</strong>
                      <span className="ms-2">{performance_metrics.analysis_cycles}</span>
                    </ListGroup.Item>
                    <ListGroup.Item>
                      <strong>Anomalies Detected:</strong>
                      <span className="ms-2">{performance_metrics.anomalies_detected}</span>
                    </ListGroup.Item>
                    <ListGroup.Item>
                      <strong>Average Cycle Time:</strong>
                      <span className="ms-2">
                        {performance_metrics.average_cycle_time 
                          ? `${performance_metrics.average_cycle_time.toFixed(2)}s`
                          : 'Not available'
                        }
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item>
                      <strong>Success Rate:</strong>
                      <span className="ms-2">
                        {performance_metrics.success_rate 
                          ? `${(performance_metrics.success_rate * 100).toFixed(1)}%`
                          : 'Not available'
                        }
                      </span>
                    </ListGroup.Item>
                    <ListGroup.Item>
                      <strong>Last Analysis:</strong>
                      <span className="ms-2">
                        {performance_metrics.last_analysis_time 
                          ? new Date(performance_metrics.last_analysis_time).toLocaleString()
                          : 'Never'
                        }
                      </span>
                    </ListGroup.Item>
                  </ListGroup>
                ) : (
                  <p className="text-muted">No performance metrics available</p>
                )}
              </Card.Body>
            </Card>
          </div>

          {/* Model Information */}
          {model_info && (
            <div className="col-12 mb-4">
              <Card>
                <Card.Header>
                  <h6 className="mb-0">
                    <FaCog className="me-2" />
                    Model Information
                  </h6>
                </Card.Header>
                <Card.Body>
                  <Table striped bordered size="sm">
                    <tbody>
                      <tr>
                        <td><strong>Model Path</strong></td>
                        <td>{model_info.path}</td>
                      </tr>
                      <tr>
                        <td><strong>Assigned</strong></td>
                        <td>
                          <Badge bg={model_info.assigned ? "success" : "danger"}>
                            {model_info.assigned ? "Yes" : "No"}
                          </Badge>
                        </td>
                      </tr>
                      <tr>
                        <td><strong>Type</strong></td>
                        <td>{model_info.type}</td>
                      </tr>
                    </tbody>
                  </Table>
                </Card.Body>
              </Card>
            </div>
          )}

          {/* Training Data Requirements */}
          <div className="col-12">
            <Card>
              <Card.Header>
                <h6 className="mb-0">
                  <FaDownload className="me-2" />
                  Training Data Requirements
                </h6>
              </Card.Header>
              <Card.Body>
                <div className="row">
                  <div className="col-md-6">
                    <h6>Required Data:</h6>
                    <ListGroup>
                      {export_considerations.training_data_requirements.map((requirement, index) => (
                        <ListGroup.Item key={index} className="d-flex align-items-center">
                          <FaCheckCircle className="text-success me-2" />
                          {requirement}
                        </ListGroup.Item>
                      ))}
                    </ListGroup>
                  </div>
                  <div className="col-md-6">
                    <h6>Preprocessing Steps:</h6>
                    <ListGroup>
                      {export_considerations.preprocessing_steps.map((step, index) => (
                        <ListGroup.Item key={index} className="d-flex align-items-center">
                          <FaCog className="text-primary me-2" />
                          {step}
                        </ListGroup.Item>
                      ))}
                    </ListGroup>
                  </div>
                </div>
              </Card.Body>
            </Card>
          </div>
        </div>
      </Modal.Body>
    </Modal>
  );
};

export default AgentDetailsModal; 