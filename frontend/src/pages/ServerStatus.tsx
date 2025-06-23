import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, Row, Col, ProgressBar, Table, Badge, Spinner, Alert } from 'react-bootstrap';
import { FaServer, FaMemory, FaHdd, FaCogs, FaExclamationTriangle, FaChartLine, FaList, FaDesktop } from 'react-icons/fa';
import { endpoints } from '../services/api';
import type { ServerStatus } from '../services/types';
import TabbedLayout from '../components/common/TabbedLayout';
import type { TabItem } from '../components/common/types';

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

  // System Metrics Tab Content
  const SystemMetricsContent = (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4>System Metrics</h4>
        <Badge
          bg={status?.status === 'healthy' ? 'success' : 'danger'}
          className="fs-6"
        >
          {status?.status.toUpperCase()}
        </Badge>
      </div>

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
                <FaHdd className="text-primary me-2" size={24} />
                <h5 className="mb-0">Disk Usage</h5>
              </div>
              <ProgressBar
                now={status?.metrics.disk_usage || 0}
                label={`${status?.metrics.disk_usage || 0}%`}
                variant={status?.metrics.disk_usage > 80 ? 'danger' : status?.metrics.disk_usage > 60 ? 'warning' : 'success'}
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
      </Row>

      <Row>
        <Col md={6}>
          <Card>
            <Card.Header>
              <h6 className="mb-0">System Information</h6>
            </Card.Header>
            <Card.Body>
              <div className="row">
                <div className="col-6">
                  <small className="text-muted">Uptime</small>
                  <div className="h6 mb-2">{status?.uptime || 'N/A'}</div>
                </div>
                <div className="col-6">
                  <small className="text-muted">Load Average</small>
                  <div className="h6 mb-2">{status?.load_average || 'N/A'}</div>
                </div>
                <div className="col-6">
                  <small className="text-muted">Total Memory</small>
                  <div className="h6 mb-2">{status?.total_memory || 'N/A'}</div>
                </div>
                <div className="col-6">
                  <small className="text-muted">Available Memory</small>
                  <div className="h6 mb-2">{status?.available_memory || 'N/A'}</div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Header>
              <h6 className="mb-0">Network Information</h6>
            </Card.Header>
            <Card.Body>
              <div className="row">
                <div className="col-6">
                  <small className="text-muted">Network Interfaces</small>
                  <div className="h6 mb-2">{status?.network_interfaces || 'N/A'}</div>
                </div>
                <div className="col-6">
                  <small className="text-muted">Active Connections</small>
                  <div className="h6 mb-2">{status?.active_connections || 'N/A'}</div>
                </div>
                <div className="col-6">
                  <small className="text-muted">Bytes Received</small>
                  <div className="h6 mb-2">{status?.bytes_received || 'N/A'}</div>
                </div>
                <div className="col-6">
                  <small className="text-muted">Bytes Sent</small>
                  <div className="h6 mb-2">{status?.bytes_sent || 'N/A'}</div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );

  // Component Status Tab Content
  const ComponentStatusContent = (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4>Component Status</h4>
        <Badge
          bg={Object.values(status?.components || {}).every(c => c === 'healthy') ? 'success' : 'warning'}
          className="fs-6"
        >
          {Object.values(status?.components || {}).every(c => c === 'healthy') ? 'ALL HEALTHY' : 'ISSUES DETECTED'}
        </Badge>
      </div>

      <Row>
        {Object.entries(status?.components || {}).map(([component, componentStatus]) => (
          <Col md={4} key={component} className="mb-3">
            <Card>
              <Card.Body>
                <div className="d-flex align-items-center justify-content-between mb-3">
                  <h6 className="mb-0 text-capitalize">{component.replace('_', ' ')}</h6>
                  <Badge
                    bg={componentStatus === 'healthy' ? 'success' : 'danger'}
                  >
                    {componentStatus.toUpperCase()}
                  </Badge>
                </div>
                <div className="d-flex align-items-center">
                  <div className={`me-2 ${componentStatus === 'healthy' ? 'text-success' : 'text-danger'}`}>
                    <FaCogs size={20} />
                  </div>
                  <div>
                    <small className="text-muted">Status</small>
                    <div className="h6 mb-0">{componentStatus}</div>
                  </div>
                </div>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>

      <Card className="mt-4">
        <Card.Header>
          <h6 className="mb-0">Component Health Summary</h6>
        </Card.Header>
        <Card.Body>
          <div className="row">
            <div className="col-md-3">
              <div className="text-center">
                <h4 className="text-success">{Object.values(status?.components || {}).filter(c => c === 'healthy').length}</h4>
                <small className="text-muted">Healthy</small>
              </div>
            </div>
            <div className="col-md-3">
              <div className="text-center">
                <h4 className="text-danger">{Object.values(status?.components || {}).filter(c => c !== 'healthy').length}</h4>
                <small className="text-muted">Unhealthy</small>
              </div>
            </div>
            <div className="col-md-3">
              <div className="text-center">
                <h4>{Object.keys(status?.components || {}).length}</h4>
                <small className="text-muted">Total</small>
              </div>
            </div>
            <div className="col-md-3">
              <div className="text-center">
                <h4 className="text-success">
                  {Object.keys(status?.components || {}).length > 0 ? 
                    Math.round((Object.values(status?.components || {}).filter(c => c === 'healthy').length / Object.keys(status?.components || {}).length) * 100) : 0
                  }%
                </h4>
                <small className="text-muted">Health Rate</small>
              </div>
            </div>
          </div>
        </Card.Body>
      </Card>
    </div>
  );

  // Service Status Tab Content
  const ServiceStatusContent = (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h4>Service Status</h4>
        <div className="d-flex gap-2">
          <Badge bg="success" className="fs-6">
            {status?.services.filter(s => s.status === 'running').length} Running
          </Badge>
          <Badge bg="secondary" className="fs-6">
            {status?.services.filter(s => s.status === 'stopped').length} Stopped
          </Badge>
        </div>
      </div>

      <Card>
        <Card.Body>
          <Table responsive hover>
            <thead>
              <tr>
                <th>Service</th>
                <th>Status</th>
                <th>Uptime</th>
                <th>Memory Usage</th>
                <th>CPU Usage</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {status?.services.map((service) => (
                <tr key={service.name}>
                  <td>
                    <div className="d-flex align-items-center">
                      <FaDesktop className="me-2 text-primary" />
                      {service.name}
                    </div>
                  </td>
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
                    <div className="d-flex align-items-center">
                      <ProgressBar
                        now={service.memoryUsage}
                        label={`${service.memoryUsage}%`}
                        variant={service.memoryUsage > 80 ? 'danger' : service.memoryUsage > 60 ? 'warning' : 'success'}
                        style={{ width: '100px' }}
                      />
                    </div>
                  </td>
                  <td>
                    <div className="d-flex align-items-center">
                      <ProgressBar
                        now={service.cpuUsage || 0}
                        label={`${service.cpuUsage || 0}%`}
                        variant={(service.cpuUsage || 0) > 80 ? 'danger' : (service.cpuUsage || 0) > 60 ? 'warning' : 'success'}
                        style={{ width: '100px' }}
                      />
                    </div>
                  </td>
                  <td>
                    <div className="btn-group btn-group-sm">
                      <button className="btn btn-outline-success" title="Start">
                        ▶
                      </button>
                      <button className="btn btn-outline-warning" title="Restart">
                        🔄
                      </button>
                      <button className="btn btn-outline-danger" title="Stop">
                        ⏹
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      <Row className="mt-4">
        <Col md={6}>
          <Card>
            <Card.Header>
              <h6 className="mb-0">Service Performance Summary</h6>
            </Card.Header>
            <Card.Body>
              <div className="row">
                <div className="col-6">
                  <small className="text-muted">Total Services</small>
                  <div className="h5 mb-0">{status?.services.length || 0}</div>
                </div>
                <div className="col-6">
                  <small className="text-muted">Running Services</small>
                  <div className="h5 mb-0 text-success">{status?.services.filter(s => s.status === 'running').length || 0}</div>
                </div>
                <div className="col-6">
                  <small className="text-muted">Avg Memory Usage</small>
                  <div className="h5 mb-0">
                    {status?.services.length ? 
                      Math.round(status.services.reduce((sum, s) => sum + s.memoryUsage, 0) / status.services.length) : 0
                    }%
                  </div>
                </div>
                <div className="col-6">
                  <small className="text-muted">Avg CPU Usage</small>
                  <div className="h5 mb-0">
                    {status?.services.length ? 
                      Math.round(status.services.reduce((sum, s) => sum + (s.cpuUsage || 0), 0) / status.services.length) : 0
                    }%
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Header>
              <h6 className="mb-0">Service Health</h6>
            </Card.Header>
            <Card.Body>
              <div className="d-flex flex-column gap-2">
                {['running', 'stopped', 'error'].map(statusType => {
                  const count = status?.services.filter(s => s.status === statusType).length || 0;
                  const percentage = status?.services.length ? (count / status.services.length) * 100 : 0;
                  return (
                    <div key={statusType} className="d-flex justify-content-between align-items-center">
                      <span className="text-capitalize">{statusType}</span>
                      <div className="d-flex align-items-center gap-2">
                        <div className="progress flex-grow-1" style={{ width: '100px' }}>
                          <div 
                            className={`progress-bar bg-${statusType === 'running' ? 'success' : statusType === 'stopped' ? 'secondary' : 'danger'}`}
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
        </Col>
      </Row>
    </div>
  );

  const tabs: TabItem[] = [
    {
      key: 'metrics',
      title: 'System Metrics',
      icon: <FaChartLine />,
      content: SystemMetricsContent
    },
    {
      key: 'components',
      title: 'Component Status',
      icon: <FaList />,
      content: ComponentStatusContent
    },
    {
      key: 'services',
      title: 'Service Status',
      icon: <FaDesktop />,
      content: ServiceStatusContent
    }
  ];

  return (
    <div className="container-fluid">
      <TabbedLayout title="Server Status" tabs={tabs} />
    </div>
  );
};

export default ServerStatusPage;
