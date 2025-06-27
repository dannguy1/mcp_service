import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, Table, Badge, Spinner, Alert, Form, Row, Col, Button, ButtonGroup, Pagination } from 'react-bootstrap';
import { FaExclamationTriangle, FaFilter, FaDownload, FaSync, FaChartBar, FaHistory } from 'react-icons/fa';
import { endpoints } from '../services/api';
import type { Log } from '../services/types';
import TabbedLayout from '../components/common/TabbedLayout';
import type { TabItem } from '../components/common/types';

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

  const clearFilters = () => {
    setFilters({
      startDate: '',
      endDate: '',
      severity: [],
      programs: [],
      search: ''
    });
    setPagination(prev => ({ ...prev, currentPage: 1 }));
  };

  // Count active filters
  const activeFiltersCount = 
    filters.severity.length + 
    filters.programs.length + 
    (filters.startDate ? 1 : 0) + 
    (filters.endDate ? 1 : 0) + 
    (filters.search ? 1 : 0);

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

  // Log Viewer Tab Content
  const LogViewerContent = (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4>Log Viewer</h4>
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
        <Card.Header className="d-flex justify-content-between align-items-center">
          <div>
            <FaFilter className="me-2" />
            Filters
          </div>
          <Button 
            variant="outline-secondary" 
            size="sm" 
            onClick={clearFilters}
            disabled={activeFiltersCount === 0}
          >
            Clear Filters ({activeFiltersCount})
          </Button>
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
          </Form>
        </Card.Body>
      </Card>

      <Card>
        <Card.Body>
          <Table responsive hover>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Level</th>
                <th>Process</th>
                <th>Device</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {data.logs.map((log) => (
                <tr key={log.id}>
                  <td>{new Date(log.timestamp).toLocaleString()}</td>
                  <td>
                    <Badge
                      bg={
                        log.level === 'error' ? 'danger' :
                        log.level === 'warning' ? 'warning' :
                        log.level === 'info' ? 'info' :
                        'secondary'
                      }
                    >
                      {log.level}
                    </Badge>
                  </td>
                  <td>{log.process}</td>
                  <td>{log.device_id}</td>
                  <td>
                    <div className="text-truncate" style={{ maxWidth: '300px' }} title={log.message}>
                      {log.message}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>

          <div className="d-flex justify-content-between align-items-center mt-3">
            <div>
              Showing {((pagination.currentPage - 1) * pagination.perPage) + 1} to {Math.min(pagination.currentPage * pagination.perPage, data.total || 0)} of {data.total || 0} logs
            </div>
            <Pagination>
              <Pagination.First 
                onClick={() => handlePageChange(1)}
                disabled={pagination.currentPage === 1}
              />
              <Pagination.Prev 
                onClick={() => handlePageChange(pagination.currentPage - 1)}
                disabled={pagination.currentPage === 1}
              />
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const page = Math.max(1, Math.min(totalPages - 4, pagination.currentPage - 2)) + i;
                return (
                  <Pagination.Item
                    key={page}
                    active={page === pagination.currentPage}
                    onClick={() => handlePageChange(page)}
                  >
                    {page}
                  </Pagination.Item>
                );
              })}
              <Pagination.Next 
                onClick={() => handlePageChange(pagination.currentPage + 1)}
                disabled={pagination.currentPage === totalPages}
              />
              <Pagination.Last 
                onClick={() => handlePageChange(totalPages)}
                disabled={pagination.currentPage === totalPages}
              />
            </Pagination>
          </div>
        </Card.Body>
      </Card>
    </div>
  );

  // Log Analysis Tab Content
  const LogAnalysisContent = (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4>Log Analysis</h4>
        <Button variant="outline-primary" onClick={handleRefresh}>
          <FaSync className="me-2" />
          Refresh
        </Button>
      </div>

      <div className="row">
        <div className="col-md-3">
          <Card>
            <Card.Body>
              <h6 className="text-muted mb-2">Total Logs</h6>
              <h3>{data.total?.toLocaleString() || 0}</h3>
            </Card.Body>
          </Card>
        </div>
        <div className="col-md-3">
          <Card>
            <Card.Body>
              <h6 className="text-muted mb-2">Error Rate</h6>
              <h3>
                {data.total ? 
                  Math.round((data.logs.filter(log => log.level === 'error').length / data.total) * 100) : 0
                }%
              </h3>
            </Card.Body>
          </Card>
        </div>
        <div className="col-md-3">
          <Card>
            <Card.Body>
              <h6 className="text-muted mb-2">Warning Rate</h6>
              <h3>
                {data.total ? 
                  Math.round((data.logs.filter(log => log.level === 'warning').length / data.total) * 100) : 0
                }%
              </h3>
            </Card.Body>
          </Card>
        </div>
        <div className="col-md-3">
          <Card>
            <Card.Body>
              <h6 className="text-muted mb-2">Unique Processes</h6>
              <h3>{new Set(data.logs.map(log => log.process)).size}</h3>
            </Card.Body>
          </Card>
        </div>
      </div>

      <div className="row mt-4">
        <div className="col-md-6">
          <Card>
            <Card.Header>
              <h6 className="mb-0">Log Levels Distribution</h6>
            </Card.Header>
            <Card.Body>
              <div className="d-flex flex-column gap-2">
                {['error', 'warning', 'info', 'debug'].map(level => {
                  const count = data.logs.filter(log => log.level === level).length;
                  const percentage = data.total ? (count / data.total) * 100 : 0;
                  return (
                    <div key={level} className="d-flex justify-content-between align-items-center">
                      <span className="text-capitalize">{level}</span>
                      <div className="d-flex align-items-center gap-2">
                        <div className="progress flex-grow-1" style={{ width: '100px' }}>
                          <div 
                            className="progress-bar" 
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
        <div className="col-md-6">
          <Card>
            <Card.Header>
              <h6 className="mb-0">Top Processes</h6>
            </Card.Header>
            <Card.Body>
              <div className="d-flex flex-column gap-2">
                {Array.from(
                  data.logs.reduce((acc, log) => {
                    acc.set(log.process, (acc.get(log.process) || 0) + 1);
                    return acc;
                  }, new Map<string, number>())
                )
                .sort(([,a], [,b]) => b - a)
                .slice(0, 5)
                .map(([process, count]) => (
                  <div key={process} className="d-flex justify-content-between align-items-center">
                    <span className="text-truncate" style={{ maxWidth: '150px' }} title={process}>
                      {process}
                    </span>
                    <div className="d-flex align-items-center gap-2">
                      <div className="progress flex-grow-1" style={{ width: '100px' }}>
                        <div 
                          className="progress-bar" 
                          style={{ width: `${(count / data.total!) * 100}%` }}
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
      </div>
    </div>
  );

  // Export History Tab Content
  const ExportHistoryContent = (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4>Export History</h4>
        <Button variant="outline-primary" onClick={handleRefresh}>
          <FaSync className="me-2" />
          Refresh
        </Button>
      </div>

      <Alert variant="info">
        <FaHistory className="me-2" />
        Export history functionality will be implemented in a future update. This will show all log export operations and their status.
      </Alert>

      <Card>
        <Card.Body>
          <div className="text-center text-muted py-5">
            <FaHistory size={48} className="mb-3" />
            <h5>No Export History</h5>
            <p>Export history will appear here once log exports are performed.</p>
          </div>
        </Card.Body>
      </Card>
    </div>
  );

  const tabs: TabItem[] = [
    {
      key: 'viewer',
      title: 'Log Viewer',
      icon: <FaFilter />,
      content: LogViewerContent
    },
    {
      key: 'analysis',
      title: 'Log Analysis',
      icon: <FaChartBar />,
      content: LogAnalysisContent
    },
    {
      key: 'export',
      title: 'Export History',
      icon: <FaHistory />,
      content: ExportHistoryContent
    }
  ];

  return (
    <div className="container-fluid">
      <TabbedLayout title="System Logs" tabs={tabs} />
    </div>
  );
};

export default Logs; 