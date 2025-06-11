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

  return (
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
  );
};

export default StatusPanel;
