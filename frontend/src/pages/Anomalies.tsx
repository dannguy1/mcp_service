import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, Table, Badge, Spinner, Alert, Row, Col, Button } from 'react-bootstrap';
import { FaExclamationTriangle, FaChartBar, FaCogs, FaSync, FaEye, FaFilter } from 'react-icons/fa';
import { endpoints } from '../services/api';
import type { Anomaly } from '../services/types';
import TabbedLayout from '../components/common/TabbedLayout';
import type { TabItem } from '../components/common/types';

const Anomalies: React.FC = () => {
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null);

  const { data: anomalies, isLoading, error, refetch } = useQuery<Anomaly[]>({
    queryKey: ['anomalies'],
    queryFn: () => endpoints.getAnomalies(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

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

  // Detection Rules Tab Content
  const DetectionRulesContent = (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4>Detection Rules</h4>
        <Button variant="outline-primary" onClick={() => refetch()}>
          <FaSync className="me-2" />
          Refresh
        </Button>
      </div>

      <Alert variant="info">
        <FaCogs className="me-2" />
        Detection rules configuration will be implemented in a future update. This will allow you to configure and manage anomaly detection thresholds and rules.
      </Alert>

      <Card>
        <Card.Body>
          <div className="text-center text-muted py-5">
            <FaCogs size={48} className="mb-3" />
            <h5>No Detection Rules</h5>
            <p>Detection rules will appear here once they are configured.</p>
          </div>
        </Card.Body>
      </Card>
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
      key: 'rules',
      title: 'Detection Rules',
      icon: <FaCogs />,
      content: DetectionRulesContent
    }
  ];

  return (
    <div className="container-fluid">
      <TabbedLayout title="Detected Anomalies" tabs={tabs} />
    </div>
  );
};

export default Anomalies; 