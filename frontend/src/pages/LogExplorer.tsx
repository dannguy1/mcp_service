import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, Form, Table } from "react-bootstrap";
import { endpoints } from "../services/api";
import * as Types from "../services/types";

const LogExplorer: React.FC = () => {
  const [filters, setFilters] = useState({
    severity: [],
    programs: [],
    startDate: "",
    endDate: ""
  });

  const { data, isLoading, error } = useQuery<Types.LogsResponse>({
    queryKey: ["logs", filters],
    queryFn: () => endpoints.getLogs(filters)
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading logs</div>;
  if (!data) return null;

  // Ensure we have the logs array from the nested structure
  const logs = data.logs?.logs || [];
  const total = data.logs?.pagination?.total || 0;
  const availablePrograms = data.filters?.programs || [];

  return (
    <div>
      <h2 className="mb-4">Log Explorer</h2>
      
      <Card className="mb-4">
        <Card.Header>Filters</Card.Header>
        <Card.Body>
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Severity</Form.Label>
              <Form.Select
                multiple
                value={filters.severity}
                onChange={(e) => {
                  const values = Array.from(e.target.selectedOptions, option => option.value);
                  setFilters(prev => ({ ...prev, severity: values }));
                }}
              >
                <option value="error">Error</option>
                <option value="warning">Warning</option>
                <option value="info">Info</option>
                <option value="debug">Debug</option>
              </Form.Select>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Programs</Form.Label>
              <Form.Select
                multiple
                value={filters.programs}
                onChange={(e) => {
                  const values = Array.from(e.target.selectedOptions, option => option.value);
                  setFilters(prev => ({ ...prev, programs: values }));
                }}
              >
                {availablePrograms.map(program => (
                  <option key={program} value={program}>{program}</option>
                ))}
              </Form.Select>
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Date Range</Form.Label>
              <div className="d-flex gap-2">
                <Form.Control
                  type="datetime-local"
                  value={filters.startDate}
                  onChange={(e) => setFilters(prev => ({ ...prev, startDate: e.target.value }))}
                />
                <Form.Control
                  type="datetime-local"
                  value={filters.endDate}
                  onChange={(e) => setFilters(prev => ({ ...prev, endDate: e.target.value }))}
                />
              </div>
            </Form.Group>
          </Form>
        </Card.Body>
      </Card>

      <Card>
        <Card.Header>Logs ({total})</Card.Header>
        <Card.Body>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Level</th>
                <th>Program</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log: Types.LogEntry) => (
                <tr key={log.id}>
                  <td>{new Date(log.timestamp).toLocaleString()}</td>
                  <td>
                    <span className={`badge bg-${log.level === "error" ? "danger" : log.level === "warning" ? "warning" : "info"}`}>
                      {log.level}
                    </span>
                  </td>
                  <td>{log.program}</td>
                  <td>{log.message}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>
    </div>
  );
};

export default LogExplorer;