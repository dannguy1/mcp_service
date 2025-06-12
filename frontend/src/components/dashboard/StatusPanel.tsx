import React from "react";
import { Card, Row, Col } from "react-bootstrap";
import type { SystemStatus } from "../../services/types";

interface StatusPanelProps {
  data: SystemStatus;
}

const StatusPanel: React.FC<StatusPanelProps> = ({ data }) => {
  if (!data) {
    return (
      <Card className="mb-4">
        <Card.Body>
          <div className="text-center">Loading...</div>
        </Card.Body>
      </Card>
    );
  }

  const metrics = [
    { name: "CPU Usage", value: `${data.metrics.cpu_usage}%`, color: "#8884d8" },
    { name: "Memory Usage", value: `${data.metrics.memory_usage}%`, color: "#82ca9d" },
    { name: "Response Time", value: `${data.metrics.response_time}ms`, color: "#ffc658" },
  ];

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'connected':
        return 'success';
      case 'disconnected':
        return 'danger';
      case 'error':
        return 'warning';
      default:
        return 'secondary';
    }
  };

  return (
    <>
      <Card className="mb-4">
        <Card.Header>System Status</Card.Header>
        <Card.Body>
          <Row>
            <Col md={4}>
              <div className="text-center">
                <h5>Status</h5>
                <span className={`badge bg-${data.status === "healthy" ? "success" : "danger"}`}>
                  {data.status}
                </span>
              </div>
            </Col>
            <Col md={4}>
              <div className="text-center">
                <h5>Uptime</h5>
                <p>{data.uptime}</p>
              </div>
            </Col>
            <Col md={4}>
              <div className="text-center">
                <h5>Version</h5>
                <p>{data.version}</p>
              </div>
            </Col>
          </Row>
          <Row className="mt-4">
            {metrics.map((metric) => (
              <Col md={4} key={metric.name}>
                <Card>
                  <Card.Body>
                    <h6>{metric.name}</h6>
                    <p className="h4">{metric.value}</p>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>
        </Card.Body>
      </Card>

      <Card className="mb-4">
        <Card.Header>Service Status</Card.Header>
        <Card.Body>
          <Row>
            <Col md={6}>
              <Card className="mb-3">
                <Card.Header className="bg-white text-dark">
                  <h5 className="mb-0">MCP Service</h5>
                </Card.Header>
                <Card.Body>
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <span>Status:</span>
                    <span className={`badge bg-${getStatusColor(data.connections?.mcp_service?.status || 'disconnected')}`}>
                      {data.connections?.mcp_service?.status || 'disconnected'}
                    </span>
                  </div>
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <span>Last Check:</span>
                    <span>{data.connections?.mcp_service?.last_check || 'Never'}</span>
                  </div>
                  {data.connections?.mcp_service?.error && (
                    <div className="text-danger mt-2">
                      <small>{data.connections.mcp_service.error}</small>
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Col>
            <Col md={6}>
              <Card className="mb-3">
                <Card.Header className="bg-white text-dark">
                  <h5 className="mb-0">Backend Service</h5>
                </Card.Header>
                <Card.Body>
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <span>Status:</span>
                    <span className={`badge bg-${getStatusColor(data.connections?.backend_service?.status || 'disconnected')}`}>
                      {data.connections?.backend_service?.status || 'disconnected'}
                    </span>
                  </div>
                  <div className="d-flex justify-content-between align-items-center mb-2">
                    <span>Last Check:</span>
                    <span>{data.connections?.backend_service?.last_check || 'Never'}</span>
                  </div>
                  {data.connections?.backend_service?.error && (
                    <div className="text-danger mt-2">
                      <small>{data.connections.backend_service.error}</small>
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      <Card className="mb-4">
        <Card.Header>Connection Status</Card.Header>
        <Card.Body>
          <Row>
            <Col md={3}>
              <div className="text-center">
                <h5>Data Source</h5>
                <span className={`badge bg-${getStatusColor(data.connections?.data_source?.status || 'disconnected')}`}>
                  {data.connections?.data_source?.status || 'disconnected'}
                </span>
                {data.connections?.data_source?.error && (
                  <small className="d-block text-danger mt-1">{data.connections.data_source.error}</small>
                )}
              </div>
            </Col>
            <Col md={3}>
              <div className="text-center">
                <h5>Database</h5>
                <span className={`badge bg-${getStatusColor(data.connections?.database?.status || 'disconnected')}`}>
                  {data.connections?.database?.status || 'disconnected'}
                </span>
                {data.connections?.database?.error && (
                  <small className="d-block text-danger mt-1">{data.connections.database.error}</small>
                )}
              </div>
            </Col>
            <Col md={3}>
              <div className="text-center">
                <h5>Model Service</h5>
                <span className={`badge bg-${getStatusColor(data.connections?.model_service?.status || 'disconnected')}`}>
                  {data.connections?.model_service?.status || 'disconnected'}
                </span>
                {data.connections?.model_service?.error && (
                  <small className="d-block text-danger mt-1">{data.connections.model_service.error}</small>
                )}
              </div>
            </Col>
            <Col md={3}>
              <div className="text-center">
                <h5>Redis</h5>
                <span className={`badge bg-${getStatusColor(data.connections?.redis?.status || 'disconnected')}`}>
                  {data.connections?.redis?.status || 'disconnected'}
                </span>
                {data.connections?.redis?.error && (
                  <small className="d-block text-danger mt-1">{data.connections.redis.error}</small>
                )}
              </div>
            </Col>
          </Row>
        </Card.Body>
      </Card>
    </>
  );
};

export default StatusPanel;
