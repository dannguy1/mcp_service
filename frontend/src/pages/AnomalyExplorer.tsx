import React from 'react';
import { Card, Table, Badge, Form, Row, Col } from 'react-bootstrap';
import { useQuery } from '@tanstack/react-query';
import { endpoints } from '../services/api';
import type { Anomaly } from '../services/types';

const AnomalyExplorer: React.FC = () => {
  const { data: anomalies, isLoading, error } = useQuery<Anomaly[]>({
    queryKey: ['anomalies'],
    queryFn: () => endpoints.getAnomalies(),
    refetchInterval: 30000 // Refresh every 30 seconds
  });

  const getSeverityColor = (severity: number) => {
    if (severity >= 8) return 'danger';
    if (severity >= 5) return 'warning';
    return 'info';
  };

  if (isLoading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="mt-3">Loading anomalies...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="mt-4">
        <Card.Body>
          <div className="alert alert-danger">
            Error loading anomalies: {error instanceof Error ? error.message : 'Unknown error'}
          </div>
        </Card.Body>
      </Card>
    );
  }

  return (
    <div className="anomaly-explorer">
      <h2 className="mb-4">Anomaly Explorer</h2>
      
      <Card className="mb-4">
        <Card.Header>
          <Row className="align-items-center">
            <Col>
              <h5 className="mb-0">Detected Anomalies</h5>
            </Col>
            <Col xs="auto">
              <Form.Select size="sm">
                <option value="all">All Types</option>
                <option value="network">Network</option>
                <option value="system">System</option>
                <option value="security">Security</option>
              </Form.Select>
            </Col>
          </Row>
        </Card.Header>
        <Card.Body>
          <Table hover responsive>
            <thead>
              <tr>
                <th>ID</th>
                <th>Timestamp</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Description</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {anomalies?.map((anomaly) => (
                <tr key={anomaly.id}>
                  <td>{anomaly.id}</td>
                  <td>{new Date(anomaly.timestamp).toLocaleString()}</td>
                  <td>{anomaly.type}</td>
                  <td>
                    <Badge bg={getSeverityColor(anomaly.severity)}>
                      {anomaly.severity}/10
                    </Badge>
                  </td>
                  <td>{anomaly.description}</td>
                  <td>
                    <Badge bg={anomaly.status === 'resolved' ? 'success' : 'warning'}>
                      {anomaly.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>
    </div>
  );
};

export default AnomalyExplorer;
