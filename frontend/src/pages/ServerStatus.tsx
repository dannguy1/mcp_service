import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, Row, Col, ProgressBar, Table, Badge, Spinner, Alert } from 'react-bootstrap';
import { FaServer, FaMemory, FaHdd, FaCogs, FaExclamationTriangle } from 'react-icons/fa';
import { endpoints } from '../services/api';
import type { ServerStatus } from '../services/types';

const ServerStatusPage: React.FC = () => {
  const { data: status, isLoading, error } = useQuery<ServerStatus>({
    queryKey: ['serverStatus'],
    queryFn: () => endpoints.getServerStatus(),
    refetchInterval: 5000, // Refresh every 5 seconds
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
        Error loading server status: {error instanceof Error ? error.message : 'Unknown error'}
      </Alert>
    );
  }

  return (
    <div>
      <h2 className="mb-4">Server Status</h2>
      
      {/* System Metrics */}
      <Row className="mb-4">
        <Col md={3}>
          <Card className="h-100">
            <Card.Body>
              <div className="d-flex align-items-center mb-3">
                <FaServer className="text-primary me-2" size={24} />
                <h5 className="mb-0">CPU Usage</h5>
              </div>
              <ProgressBar
                now={status?.metrics.cpu_usage || 0}
                label={`${status?.metrics.cpu_usage || 0}%`}
                variant={status?.metrics.cpu_usage > 80 ? 'danger' : status?.metrics.cpu_usage > 60 ? 'warning' : 'success'}
              />
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="h-100">
            <Card.Body>
              <div className="d-flex align-items-center mb-3">
                <FaMemory className="text-primary me-2" size={24} />
                <h5 className="mb-0">Memory Usage</h5>
              </div>
              <ProgressBar
                now={status?.metrics.memory_usage || 0}
                label={`${status?.metrics.memory_usage || 0}%`}
                variant={status?.metrics.memory_usage > 80 ? 'danger' : status?.metrics.memory_usage > 60 ? 'warning' : 'success'}
              />
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="h-100">
            <Card.Body>
              <div className="d-flex align-items-center mb-3">
                <FaCogs className="text-primary me-2" size={24} />
                <h5 className="mb-0">Response Time</h5>
              </div>
              <h3 className="mb-0">
                {status?.metrics.response_time}ms
              </h3>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="h-100">
            <Card.Body>
              <div className="d-flex align-items-center mb-3">
                <FaCogs className="text-primary me-2" size={24} />
                <h5 className="mb-0">System Status</h5>
              </div>
              <Badge
                bg={status?.status === 'healthy' ? 'success' : 'danger'}
                className="fs-6"
              >
                {status?.status.toUpperCase()}
              </Badge>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Component Status */}
      <Card className="mb-4">
        <Card.Body>
          <h5 className="mb-3">Component Status</h5>
          <Row>
            {Object.entries(status?.components || {}).map(([component, status]) => (
              <Col md={4} key={component}>
                <div className="d-flex align-items-center mb-2">
                  <Badge
                    bg={status === 'healthy' ? 'success' : 'danger'}
                    className="me-2"
                  >
                    {status.toUpperCase()}
                  </Badge>
                  <span className="text-capitalize">{component}</span>
                </div>
              </Col>
            ))}
          </Row>
        </Card.Body>
      </Card>

      {/* Services Table */}
      <Card>
        <Card.Body>
          <h5 className="mb-3">Service Status</h5>
          <Table responsive hover>
            <thead>
              <tr>
                <th>Service</th>
                <th>Status</th>
                <th>Uptime</th>
                <th>Memory Usage</th>
              </tr>
            </thead>
            <tbody>
              {status?.services.map((service) => (
                <tr key={service.name}>
                  <td>{service.name}</td>
                  <td>
                    <Badge
                      bg={
                        service.status === 'running' ? 'success' :
                        service.status === 'stopped' ? 'secondary' :
                        'danger'
                      }
                    >
                      {service.status}
                    </Badge>
                  </td>
                  <td>{service.uptime}</td>
                  <td>
                    <ProgressBar
                      now={service.memoryUsage}
                      label={`${service.memoryUsage}%`}
                      variant={service.memoryUsage > 80 ? 'danger' : service.memoryUsage > 60 ? 'warning' : 'success'}
                      style={{ width: '100px' }}
                    />
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

export default ServerStatusPage;
