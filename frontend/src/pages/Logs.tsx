import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, Table, Badge, Spinner, Alert, Form, Row, Col, Button, ButtonGroup, Pagination } from 'react-bootstrap';
import { FaExclamationTriangle, FaFilter, FaDownload, FaSync } from 'react-icons/fa';
import { endpoints } from '../services/api';
import type { Log } from '../services/types';

const Logs: React.FC = () => {
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    severity: [] as string[],
    programs: [] as string[],
    search: ''
  });

  const [pagination, setPagination] = useState({
    currentPage: 1,
    perPage: 25
  });

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['logs', filters, pagination],
    queryFn: () => endpoints.getLogs({ ...filters, page: pagination.currentPage, per_page: pagination.perPage }),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const handleFilterChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleSeverityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const options = e.target.options;
    const selectedValues = [];
    for (let i = 0; i < options.length; i++) {
      if (options[i].selected) {
        selectedValues.push(options[i].value);
      }
    }
    setFilters(prev => ({ ...prev, severity: selectedValues }));
  };

  const handleProgramChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const options = e.target.options;
    const selectedValues = [];
    for (let i = 0; i < options.length; i++) {
      if (options[i].selected) {
        selectedValues.push(options[i].value);
      }
    }
    setFilters(prev => ({ ...prev, programs: selectedValues }));
  };

  const handleExport = () => {
    // TODO: Implement export functionality
    console.log('Export logs');
  };

  const handleRefresh = () => {
    refetch();
  };

  const handlePageChange = (page: number) => {
    setPagination(prev => ({ ...prev, currentPage: page }));
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
        Error loading logs: {error instanceof Error ? error.message : 'Unknown error'}
      </Alert>
    );
  }

  if (!data?.logs) {
    return (
      <Alert variant="warning">
        <FaExclamationTriangle className="me-2" />
        No logs available
      </Alert>
    );
  }

  const totalPages = Math.ceil((data.total || 0) / pagination.perPage);

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>System Logs</h2>
        <ButtonGroup>
          <Button variant="outline-primary" onClick={handleRefresh}>
            <FaSync className="me-2" />
            Refresh
          </Button>
          <Button variant="outline-success" onClick={handleExport}>
            <FaDownload className="me-2" />
            Export
          </Button>
        </ButtonGroup>
      </div>

      <Card className="mb-4">
        <Card.Header>
          <FaFilter className="me-2" />
          Filters
        </Card.Header>
        <Card.Body>
          <Form>
            <Row>
              <Col md={3}>
                <Form.Group className="mb-3">
                  <Form.Label>Start Date</Form.Label>
                  <Form.Control
                    type="datetime-local"
                    name="startDate"
                    value={filters.startDate}
                    onChange={handleFilterChange}
                  />
                </Form.Group>
              </Col>
              <Col md={3}>
                <Form.Group className="mb-3">
                  <Form.Label>End Date</Form.Label>
                  <Form.Control
                    type="datetime-local"
                    name="endDate"
                    value={filters.endDate}
                    onChange={handleFilterChange}
                  />
                </Form.Group>
              </Col>
              <Col md={3}>
                <Form.Group className="mb-3">
                  <Form.Label>Level</Form.Label>
                  <Form.Select
                    multiple
                    name="severity"
                    value={filters.severity}
                    onChange={handleSeverityChange}
                  >
                    <option value="emergency">Emergency</option>
                    <option value="alert">Alert</option>
                    <option value="critical">Critical</option>
                    <option value="error">Error</option>
                    <option value="warning">Warning</option>
                    <option value="notice">Notice</option>
                    <option value="info">Info</option>
                    <option value="debug">Debug</option>
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={3}>
                <Form.Group className="mb-3">
                  <Form.Label>Process</Form.Label>
                  <Form.Select
                    multiple
                    name="programs"
                    value={filters.programs}
                    onChange={handleProgramChange}
                  >
                    {data.filters?.programs.map(program => (
                      <option key={program} value={program}>{program}</option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>
            <Row>
              <Col md={12}>
                <Form.Group className="mb-3">
                  <Form.Label>Search</Form.Label>
                  <Form.Control
                    type="text"
                    name="search"
                    value={filters.search}
                    onChange={handleFilterChange}
                    placeholder="Search in messages..."
                  />
                </Form.Group>
              </Col>
            </Row>
            <div className="d-flex justify-content-between align-items-center">
              <Pagination>
                <Pagination.First 
                  onClick={() => handlePageChange(1)}
                  disabled={pagination.currentPage === 1}
                />
                <Pagination.Prev 
                  onClick={() => handlePageChange(pagination.currentPage - 1)}
                  disabled={pagination.currentPage === 1}
                />
                <Pagination.Item active>{pagination.currentPage}</Pagination.Item>
                <Pagination.Next 
                  onClick={() => handlePageChange(pagination.currentPage + 1)}
                  disabled={pagination.currentPage === totalPages}
                />
                <Pagination.Last 
                  onClick={() => handlePageChange(totalPages)}
                  disabled={pagination.currentPage === totalPages}
                />
              </Pagination>
              <Button variant="primary" onClick={() => refetch()}>
                Apply Filters
              </Button>
            </div>
          </Form>
        </Card.Body>
      </Card>

      <Card>
        <Card.Body>
          <Table responsive hover>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Device</th>
                <th>Level</th>
                <th>Process</th>
                <th>Message</th>
                <th>AI Status</th>
              </tr>
            </thead>
            <tbody>
              {data.logs.map((log) => (
                <tr key={log.id}>
                  <td>{new Date(log.timestamp).toLocaleString()}</td>
                  <td>{log.device_ip}</td>
                  <td>
                    <Badge
                      bg={
                        log.log_level === 'ERROR' ? 'danger' :
                        log.log_level === 'WARNING' ? 'warning' :
                        log.log_level === 'INFO' ? 'info' : 'secondary'
                      }
                    >
                      {log.log_level}
                    </Badge>
                  </td>
                  <td>{log.process_name}</td>
                  <td>{log.message}</td>
                  <td>
                    <Badge
                      bg={log.pushed_to_ai ? 'success' : 'secondary'}
                    >
                      {log.pushed_to_ai ? 'Processed' : 'Pending'}
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

export default Logs; 