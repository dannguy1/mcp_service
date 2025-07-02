import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Table, Badge, Spinner, Alert, Row, Col, Button, Form, Modal } from 'react-bootstrap';
import { FaExclamationTriangle, FaChartBar, FaCogs, FaSync, FaEye, FaFilter, FaPlay, FaHistory, FaFlask } from 'react-icons/fa';
import { endpoints } from '../services/api';
import type { Anomaly, Agent, AnomalyTestRequest, AnomalyTestResponse } from '../services/types';
import TabbedLayout from '../components/common/TabbedLayout';
import type { TabItem } from '../components/common/types';
import { useAgents } from '../hooks/useAgents';
import { toast } from 'react-hot-toast';

const Anomalies: React.FC = () => {
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null);
  const [showTestModal, setShowTestModal] = useState(false);
  const [testForm, setTestForm] = useState<AnomalyTestRequest>({
    agent_id: '',
    days_back: 7
  });
  const [testResults, setTestResults] = useState<AnomalyTestResponse | null>(null);

  const { data: anomalies, isLoading, error, refetch } = useQuery<Anomaly[]>({
    queryKey: ['anomalies'],
    queryFn: () => endpoints.getAnomalies(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { agents, isLoading: isLoadingAgents } = useAgents();
  const queryClient = useQueryClient();

  // Anomaly test mutation
  const runAnomalyTestMutation = useMutation({
    mutationFn: (testRequest: AnomalyTestRequest) => endpoints.runAnomalyTest(testRequest),
    onSuccess: (data: AnomalyTestResponse) => {
      setTestResults(data);
      toast.success(`Anomaly test completed! Found ${data.anomalies_detected} anomalies.`);
    },
    onError: (error: any) => {
      toast.error(`Anomaly test failed: ${error.message || 'Unknown error'}`);
    }
  });

  const handleTestSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    runAnomalyTestMutation.mutate(testForm);
  };

  const handleTestFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setTestForm(prev => ({
      ...prev,
      [name]: name === 'days_back' ? parseInt(value) : value
    }));
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
        Error loading anomalies: {error instanceof Error ? error.message : 'Unknown error'}
      </Alert>
    );
  }

  // Anomaly List Tab Content
  const AnomalyListContent = (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4>Anomaly List</h4>
        <Button variant="outline-primary" onClick={() => refetch()}>
          <FaSync className="me-2" />
          Refresh
        </Button>
      </div>

      <Card>
        <Card.Body>
          <Table responsive hover>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Description</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {anomalies?.map((anomaly) => (
                <tr key={anomaly.id}>
                  <td>{new Date(anomaly.timestamp).toLocaleString()}</td>
                  <td>
                    <Badge bg="primary">{anomaly.type}</Badge>
                  </td>
                  <td>
                    <Badge
                      bg={
                        anomaly.severity >= 8 ? 'danger' :
                        anomaly.severity >= 5 ? 'warning' :
                        anomaly.severity >= 3 ? 'info' : 'success'
                      }
                    >
                      {anomaly.severity}/10
                    </Badge>
                  </td>
                  <td>
                    <div className="text-truncate" style={{ maxWidth: '300px' }} title={anomaly.description}>
                      {anomaly.description}
                    </div>
                  </td>
                  <td>
                    <Badge
                      bg={anomaly.status === 'resolved' ? 'success' : 'warning'}
                    >
                      {anomaly.status.toUpperCase()}
                    </Badge>
                  </td>
                  <td>
                    <Button
                      size="sm"
                      variant="outline-info"
                      onClick={() => setSelectedAnomaly(anomaly)}
                    >
                      <FaEye />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      {/* Anomaly Detail Modal */}
      {selectedAnomaly && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Anomaly Details</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setSelectedAnomaly(null)}
                />
              </div>
              <div className="modal-body">
                <div className="row">
                  <div className="col-md-6">
                    <p><strong>ID:</strong> {selectedAnomaly.id}</p>
                    <p><strong>Type:</strong> {selectedAnomaly.type}</p>
                    <p><strong>Severity:</strong> {selectedAnomaly.severity}/10</p>
                    <p><strong>Status:</strong> {selectedAnomaly.status}</p>
                  </div>
                  <div className="col-md-6">
                    <p><strong>Timestamp:</strong> {new Date(selectedAnomaly.timestamp).toLocaleString()}</p>
                    <p><strong>Device:</strong> {selectedAnomaly.device_id || 'N/A'}</p>
                    <p><strong>Model:</strong> {selectedAnomaly.model_version || 'N/A'}</p>
                  </div>
                </div>
                <div className="mt-3">
                  <p><strong>Description:</strong></p>
                  <p>{selectedAnomaly.description}</p>
                </div>
                {selectedAnomaly.details && (
                  <div className="mt-3">
                    <p><strong>Details:</strong></p>
                    <pre className="bg-light p-3 rounded">{JSON.stringify(selectedAnomaly.details, null, 2)}</pre>
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <Button variant="secondary" onClick={() => setSelectedAnomaly(null)}>
                  Close
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  // Anomaly Analysis Tab Content
  const AnomalyAnalysisContent = (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4>Anomaly Analysis</h4>
        <Button variant="outline-primary" onClick={() => refetch()}>
          <FaSync className="me-2" />
          Refresh
        </Button>
      </div>

      <div className="row">
        <div className="col-md-3">
          <Card>
            <Card.Body>
              <h6 className="text-muted mb-2">Total Anomalies</h6>
              <h3>{anomalies?.length || 0}</h3>
            </Card.Body>
          </Card>
        </div>
        <div className="col-md-3">
          <Card>
            <Card.Body>
              <h6 className="text-muted mb-2">High Severity</h6>
              <h3 className="text-danger">
                {anomalies?.filter(a => a.severity >= 8).length || 0}
              </h3>
            </Card.Body>
          </Card>
        </div>
        <div className="col-md-3">
          <Card>
            <Card.Body>
              <h6 className="text-muted mb-2">Resolved</h6>
              <h3 className="text-success">
                {anomalies?.filter(a => a.status === 'resolved').length || 0}
              </h3>
            </Card.Body>
          </Card>
        </div>
        <div className="col-md-3">
          <Card>
            <Card.Body>
              <h6 className="text-muted mb-2">Resolution Rate</h6>
              <h3>
                {anomalies?.length ? 
                  Math.round((anomalies.filter(a => a.status === 'resolved').length / anomalies.length) * 100) : 0
                }%
              </h3>
            </Card.Body>
          </Card>
        </div>
      </div>

      <div className="row mt-4">
        <div className="col-md-6">
          <Card>
            <Card.Header>
              <h6 className="mb-0">Anomaly Types Distribution</h6>
            </Card.Header>
            <Card.Body>
              <div className="d-flex flex-column gap-2">
                {Array.from(
                  anomalies?.reduce((acc, anomaly) => {
                    acc.set(anomaly.type, (acc.get(anomaly.type) || 0) + 1);
                    return acc;
                  }, new Map<string, number>()) || []
                )
                .sort(([,a], [,b]) => b - a)
                .map(([type, count]) => (
                  <div key={type} className="d-flex justify-content-between align-items-center">
                    <span>{type}</span>
                    <div className="d-flex align-items-center gap-2">
                      <div className="progress flex-grow-1" style={{ width: '100px' }}>
                        <div 
                          className="progress-bar" 
                          style={{ width: `${(count / (anomalies?.length || 1)) * 100}%` }}
                        />
                      </div>
                      <small>{count}</small>
                    </div>
                  </div>
                ))}
              </div>
            </Card.Body>
          </Card>
        </div>
        <div className="col-md-6">
          <Card>
            <Card.Header>
              <h6 className="mb-0">Severity Distribution</h6>
            </Card.Header>
            <Card.Body>
              <div className="d-flex flex-column gap-2">
                {[
                  { label: 'Critical (8-10)', range: [8, 10], color: 'danger' },
                  { label: 'High (5-7)', range: [5, 7], color: 'warning' },
                  { label: 'Medium (3-4)', range: [3, 4], color: 'info' },
                  { label: 'Low (1-2)', range: [1, 2], color: 'success' }
                ].map(({ label, range, color }) => {
                  const count = anomalies?.filter(a => a.severity >= range[0] && a.severity <= range[1]).length || 0;
                  const percentage = anomalies?.length ? (count / anomalies.length) * 100 : 0;
                  return (
                    <div key={label} className="d-flex justify-content-between align-items-center">
                      <span>{label}</span>
                      <div className="d-flex align-items-center gap-2">
                        <div className="progress flex-grow-1" style={{ width: '100px' }}>
                          <div 
                            className={`progress-bar bg-${color}`}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                        <small>{count}</small>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card.Body>
          </Card>
        </div>
      </div>
    </div>
  );

  // Anomaly Test Tab Content
  const AnomalyTestContent = (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4>Anomaly Test</h4>
        <Button variant="primary" onClick={() => setShowTestModal(true)}>
          <FaPlay className="me-2" />
          Run Test
        </Button>
      </div>

      <Alert variant="info">
        <FaFlask className="me-2" />
        Run anomaly detection tests on historical data to validate agent performance and model accuracy.
      </Alert>

      <Card>
        <Card.Body>
          <div className="text-center text-muted py-5">
            <FaHistory size={48} className="mb-3" />
            <h5>No Tests Run</h5>
            <p>Click "Run Test" to start an anomaly detection test on historical data.</p>
          </div>
        </Card.Body>
      </Card>

      {/* Test Results */}
      {testResults && (
        <Card className="mt-4">
          <Card.Header>
            <h6 className="mb-0">Test Results</h6>
          </Card.Header>
          <Card.Body>
            <div className="row">
              <div className="col-md-3">
                <h6 className="text-muted">Agent</h6>
                <p>{testResults.agent_name}</p>
              </div>
                              <div className="col-md-3">
                  <h6 className="text-muted">Status</h6>
                  <Badge bg={
                    testResults.status === 'completed' ? 'success' : 
                    testResults.status === 'completed_with_errors' ? 'warning' : 
                    'danger'
                  }>
                    {testResults.status.replace('_', ' ')}
                  </Badge>
                </div>
              <div className="col-md-3">
                <h6 className="text-muted">Logs Processed</h6>
                <p>{testResults.logs_processed.toLocaleString()}</p>
              </div>
              <div className="col-md-3">
                <h6 className="text-muted">Anomalies Found</h6>
                <p className="text-danger fw-bold">{testResults.anomalies_detected}</p>
              </div>
            </div>
            <div className="row mt-3">
              <div className="col-md-6">
                <h6 className="text-muted">Time Range</h6>
                <p>{new Date(testResults.start_time).toLocaleDateString()} - {new Date(testResults.end_time).toLocaleDateString()}</p>
              </div>
              <div className="col-md-6">
                <h6 className="text-muted">Test Duration</h6>
                <p>{testResults.test_duration.toFixed(2)} seconds</p>
              </div>
            </div>
            
            {testResults.errors && testResults.errors.length > 0 && (
              <div className="mt-3">
                <h6 className="text-danger">Errors Encountered</h6>
                <Alert variant="danger">
                  <ul className="mb-0">
                    {testResults.errors.map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                </Alert>
              </div>
            )}
            
            {testResults.results.length > 0 && (
              <div className="mt-4">
                <h6>Detected Anomalies</h6>
                <Table striped bordered size="sm">
                  <thead>
                    <tr>
                      <th>Timestamp</th>
                      <th>Type</th>
                      <th>Severity</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {testResults.results.slice(0, 10).map((result, index) => (
                      <tr key={index}>
                        <td>{new Date(result.timestamp).toLocaleString()}</td>
                        <td>
                          <Badge bg="primary">{result.type}</Badge>
                        </td>
                        <td>
                          <Badge
                            bg={
                              result.severity >= 8 ? 'danger' :
                              result.severity >= 5 ? 'warning' :
                              result.severity >= 3 ? 'info' : 'success'
                            }
                          >
                            {result.severity}/10
                          </Badge>
                        </td>
                        <td>
                          <div className="text-truncate" style={{ maxWidth: '200px' }} title={result.description}>
                            {result.description}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
                {testResults.results.length > 10 && (
                  <p className="text-muted text-center mt-2">
                    Showing first 10 of {testResults.results.length} anomalies
                  </p>
                )}
              </div>
            )}
          </Card.Body>
        </Card>
      )}
    </div>
  );

  const tabs: TabItem[] = [
    {
      key: 'list',
      title: 'Anomaly List',
      icon: <FaEye />,
      content: AnomalyListContent
    },
    {
      key: 'analysis',
      title: 'Anomaly Analysis',
      icon: <FaChartBar />,
      content: AnomalyAnalysisContent
    },
    {
      key: 'test',
      title: 'Anomaly Test',
      icon: <FaFlask />,
      content: AnomalyTestContent
    }
  ];

  return (
    <div className="container-fluid">
      <TabbedLayout title="Detected Anomalies" tabs={tabs} />
      
      {/* Anomaly Test Modal */}
      <Modal show={showTestModal} onHide={() => setShowTestModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Run Anomaly Test</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleTestSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Select Agent</Form.Label>
              <Form.Select
                name="agent_id"
                value={testForm.agent_id}
                onChange={handleTestFormChange}
                required
              >
                <option value="">Choose an agent...</option>
                {agents.map(agent => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name} ({agent.id})
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
            
            <Form.Group className="mb-3">
              <Form.Label>Time Range</Form.Label>
              <div className="row">
                <div className="col-md-6">
                  <Form.Label className="small">Days Back</Form.Label>
                  <Form.Select
                    name="days_back"
                    value={testForm.days_back}
                    onChange={handleTestFormChange}
                  >
                    <option value={1}>1 day</option>
                    <option value={3}>3 days</option>
                    <option value={7}>7 days</option>
                    <option value={14}>14 days</option>
                    <option value={30}>30 days</option>
                  </Form.Select>
                </div>
                <div className="col-md-6">
                  <Form.Label className="small">Or Custom Range</Form.Label>
                  <div className="d-flex gap-2">
                    <Form.Control
                      type="date"
                      name="start_date"
                      value={testForm.start_date || ''}
                      onChange={handleTestFormChange}
                      placeholder="Start date"
                    />
                    <Form.Control
                      type="date"
                      name="end_date"
                      value={testForm.end_date || ''}
                      onChange={handleTestFormChange}
                      placeholder="End date"
                    />
                  </div>
                </div>
              </div>
              <Form.Text className="text-muted">
                Use "Days Back" for a quick test, or specify custom start/end dates for precise control.
              </Form.Text>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowTestModal(false)}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              type="submit"
              disabled={runAnomalyTestMutation.isPending || !testForm.agent_id}
            >
              {runAnomalyTestMutation.isPending ? (
                <>
                  <Spinner animation="border" size="sm" className="me-2" />
                  Running Test...
                </>
              ) : (
                <>
                  <FaPlay className="me-2" />
                  Run Test
                </>
              )}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </div>
  );
};

export default Anomalies; 