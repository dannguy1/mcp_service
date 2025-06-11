import React from "react";
import { Card, Row, Col, Spinner, Alert } from "react-bootstrap";
import { useQuery } from "@tanstack/react-query";
import { endpoints } from "../services/api";
import type { ServerStats } from "../services/types";

const ServerStatus: React.FC = () => {
  const { data: stats, isLoading, error } = useQuery<ServerStats>({
    queryKey: ["serverStats"],
    queryFn: () => endpoints.getServerStats(),
    refetchInterval: 30000,
  });

  if (isLoading) {
    return (
      <div className="text-center py-5">
        <Spinner animation="border" role="status" variant="primary" />
        <p className="mt-3">Loading server stats...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="danger" className="mt-4">
        <Alert.Heading>Error Loading Server Stats</Alert.Heading>
        <p>
          {error instanceof Error
            ? error.message
            : "Failed to load server statistics. Please try again later."}
        </p>
      </Alert>
    );
  }

  if (!stats) {
    return (
      <Alert variant="warning" className="mt-4">
        <Alert.Heading>No Data Available</Alert.Heading>
        <p>Server statistics are not currently available.</p>
      </Alert>
    );
  }

  return (
    <div>
      <h2 className="mb-4">Server Status</h2>
      <Row>
        <Col md={4}>
          <Card className="mb-4">
            <Card.Header>CPU Usage</Card.Header>
            <Card.Body>
              <p>
                <strong>Usage:</strong> {stats.cpu.usage.toFixed(1)}%
              </p>
              <p>
                <strong>Cores:</strong> {stats.cpu.cores}
              </p>
              {stats.cpu.temperature > 0 && (
                <p>
                  <strong>Temperature:</strong> {stats.cpu.temperature.toFixed(1)}°C
                </p>
              )}
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card className="mb-4">
            <Card.Header>Memory Usage</Card.Header>
            <Card.Body>
              <p>
                <strong>Total:</strong> {(stats.memory.total / (1024 * 1024 * 1024)).toFixed(2)} GB
              </p>
              <p>
                <strong>Used:</strong> {(stats.memory.used / (1024 * 1024 * 1024)).toFixed(2)} GB
              </p>
              <p>
                <strong>Free:</strong> {(stats.memory.free / (1024 * 1024 * 1024)).toFixed(2)} GB
              </p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={4}>
          <Card className="mb-4">
            <Card.Header>Disk Usage</Card.Header>
            <Card.Body>
              <p>
                <strong>Total:</strong> {(stats.disk.total / (1024 * 1024 * 1024)).toFixed(2)} GB
              </p>
              <p>
                <strong>Used:</strong> {(stats.disk.used / (1024 * 1024 * 1024)).toFixed(2)} GB
              </p>
              <p>
                <strong>Free:</strong> {(stats.disk.free / (1024 * 1024 * 1024)).toFixed(2)} GB
              </p>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      <Card>
        <Card.Header>System Uptime</Card.Header>
        <Card.Body>
          <p>
            <strong>Uptime:</strong> {stats.uptime}
          </p>
        </Card.Body>
      </Card>
    </div>
  );
};

export default ServerStatus;
