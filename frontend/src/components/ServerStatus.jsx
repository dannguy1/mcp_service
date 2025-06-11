import { useState, useEffect } from 'react';
import { Card, Table, Badge, Spinner, Alert } from 'react-bootstrap';
import { FaServer, FaCheckCircle, FaTimesCircle, FaExclamationTriangle } from 'react-icons/fa';
import { fetchServerStatus } from '../services/api';

function ServerStatus() {
  const [serverStatus, setServerStatus] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await fetchServerStatus();
        setServerStatus(data);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="spinner-container">
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
        {error}
      </Alert>
    );
  }

  const getStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case 'healthy':
        return <Badge bg="success"><FaCheckCircle className="me-1" /> Healthy</Badge>;
      case 'unhealthy':
        return <Badge bg="danger"><FaTimesCircle className="me-1" /> Unhealthy</Badge>;
      default:
        return <Badge bg="warning"><FaExclamationTriangle className="me-1" /> Unknown</Badge>;
    }
  };

  return (
    <div className="server-status-container">
      <h1 className="mb-4">Server Status</h1>

      {/* Overview Card */}
      <Card className="dashboard-card mb-4">
        <Card.Header>
          <FaServer className="me-2" />
          Server Overview
        </Card.Header>
        <Card.Body>
          <Row>
            <Col md={4}>
              <div className="status-item">
                <h6>Overall Status</h6>
                {getStatusBadge(serverStatus?.status)}
              </div>
            </Col>
            <Col md={4}>
              <div className="status-item">
                <h6>Uptime</h6>
                <Badge bg="info">{serverStatus?.uptime || '0s'}</Badge>
              </div>
            </Col>
            <Col md={4}>
              <div className="status-item">
                <h6>Version</h6>
                <Badge bg="secondary">{serverStatus?.version || 'unknown'}</Badge>
              </div>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Detailed Status Table */}
      <Card className="dashboard-card">
        <Card.Header>Detailed Status</Card.Header>
        <Card.Body>
          <Table responsive hover>
            <thead>
              <tr>
                <th>Component</th>
                <th>Status</th>
                <th>Message</th>
                <th>Last Check</th>
              </tr>
            </thead>
            <tbody>
              {serverStatus?.components?.map((component, index) => (
                <tr key={index}>
                  <td>{component.name}</td>
                  <td>{getStatusBadge(component.status)}</td>
                  <td>{component.message || 'No message available'}</td>
                  <td>{component.last_check || 'Unknown'}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      {/* System Information */}
      <Card className="dashboard-card mt-4">
        <Card.Header>System Information</Card.Header>
        <Card.Body>
          <Row>
            <Col md={6}>
              <h6>Server Details</h6>
              <ul className="list-unstyled">
                <li><strong>Hostname:</strong> {serverStatus?.hostname || 'Unknown'}</li>
                <li><strong>Platform:</strong> {serverStatus?.platform || 'Unknown'}</li>
                <li><strong>Python Version:</strong> {serverStatus?.python_version || 'Unknown'}</li>
              </ul>
            </Col>
            <Col md={6}>
              <h6>Resource Usage</h6>
              <ul className="list-unstyled">
                <li><strong>CPU Usage:</strong> {serverStatus?.cpu_usage || 'Unknown'}</li>
                <li><strong>Memory Usage:</strong> {serverStatus?.memory_usage || 'Unknown'}</li>
                <li><strong>Disk Usage:</strong> {serverStatus?.disk_usage || 'Unknown'}</li>
              </ul>
            </Col>
          </Row>
        </Card.Body>
      </Card>
    </div>
  );
}

export default ServerStatus; 