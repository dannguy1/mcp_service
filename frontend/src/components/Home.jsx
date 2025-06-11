import { useState, useEffect } from 'react';
import { Card, Row, Col, Badge, Spinner, Alert } from 'react-bootstrap';
import { FaServer, FaDatabase, FaClock, FaExclamationTriangle, FaChartLine } from 'react-icons/fa';
import { fetchHealthStatus } from '../services/api';

function Home() {
  const [healthStatus, setHealthStatus] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await fetchHealthStatus();
        setHealthStatus(data);
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
      <div className="loading-spinner">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="danger" className="mt-3">
        <Alert.Heading>
          <FaExclamationTriangle className="me-2" />
          Error
        </Alert.Heading>
        <p>{error}</p>
      </Alert>
    );
  }

  return (
    <div className="home-container">
      <h2 className="mb-4">System Overview</h2>
      
      {/* Status Cards */}
      <Row className="g-4 mb-4">
        <Col md={6} lg={3}>
          <Card className="dashboard-card h-100">
            <Card.Header className="bg-white text-dark">
              <h5 className="mb-0">
                <FaServer className="me-2" />
                Server Status
              </h5>
            </Card.Header>
            <Card.Body>
              <div className="d-flex align-items-center">
                <Badge bg={healthStatus?.server?.status === 'healthy' ? 'success' : 'danger'} className="me-2">
                  {healthStatus?.server?.status || 'unknown'}
                </Badge>
                <small className="text-muted">
                  {healthStatus?.server?.message || 'No status available'}
                </small>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={6} lg={3}>
          <Card className="dashboard-card h-100">
            <Card.Header className="bg-white text-dark">
              <h5 className="mb-0">
                <FaDatabase className="me-2" />
                Database Status
              </h5>
            </Card.Header>
            <Card.Body>
              <div className="d-flex align-items-center">
                <Badge bg={healthStatus?.database?.status === 'healthy' ? 'success' : 'danger'} className="me-2">
                  {healthStatus?.database?.status || 'unknown'}
                </Badge>
                <small className="text-muted">
                  {healthStatus?.database?.message || 'No status available'}
                </small>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={6} lg={3}>
          <Card className="dashboard-card h-100">
            <Card.Header className="bg-white text-dark">
              <h5 className="mb-0">
                <FaClock className="me-2" />
                Uptime
              </h5>
            </Card.Header>
            <Card.Body>
              <div className="d-flex align-items-center">
                <Badge bg="info" className="me-2">
                  {healthStatus?.uptime || '0s'}
                </Badge>
                <small className="text-muted">System running time</small>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={6} lg={3}>
          <Card className="dashboard-card h-100">
            <Card.Header className="bg-white text-dark">
              <h5 className="mb-0">
                <FaChartLine className="me-2" />
                Version
              </h5>
            </Card.Header>
            <Card.Body>
              <div className="d-flex align-items-center">
                <Badge bg="secondary" className="me-2">
                  {healthStatus?.version || 'unknown'}
                </Badge>
                <small className="text-muted">Current version</small>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* System Details */}
      <Card className="dashboard-card">
        <Card.Header className="bg-white text-dark">
          <h5 className="mb-0">System Details</h5>
        </Card.Header>
        <Card.Body>
          <Row>
            <Col md={6}>
              <h6 className="mb-3">Server Information</h6>
              <ul className="list-unstyled">
                <li className="mb-2">
                  <strong>Status:</strong>{' '}
                  <Badge bg={healthStatus?.server?.status === 'healthy' ? 'success' : 'danger'}>
                    {healthStatus?.server?.status || 'unknown'}
                  </Badge>
                </li>
                <li className="mb-2">
                  <strong>Message:</strong>{' '}
                  <span className="text-muted">{healthStatus?.server?.message || 'No message available'}</span>
                </li>
              </ul>
            </Col>
            <Col md={6}>
              <h6 className="mb-3">Database Information</h6>
              <ul className="list-unstyled">
                <li className="mb-2">
                  <strong>Status:</strong>{' '}
                  <Badge bg={healthStatus?.database?.status === 'healthy' ? 'success' : 'danger'}>
                    {healthStatus?.database?.status || 'unknown'}
                  </Badge>
                </li>
                <li className="mb-2">
                  <strong>Message:</strong>{' '}
                  <span className="text-muted">{healthStatus?.database?.message || 'No message available'}</span>
                </li>
              </ul>
            </Col>
          </Row>
        </Card.Body>
      </Card>
    </div>
  );
}

export default Home; 