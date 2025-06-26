import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Badge, Table, Spinner, Alert, ProgressBar } from 'react-bootstrap';
import { FaChartLine, FaEye, FaClock, FaExclamationTriangle, FaCheckCircle, FaServer } from 'react-icons/fa';
import { useQuery } from '@tanstack/react-query';
import { endpoints } from '../services/api';
import type { Agent } from '../services/types';

interface AnalysisStats {
  agent: Agent;
  analysis_stats: {
    analysis_cycles: number;
    logs_processed: number;
    features_extracted: number;
    anomalies_detected: number;
    total_cycle_duration: number;
    avg_cycle_duration: number;
    last_cycle_timestamp: string;
    feature_totals: {
      auth_failures: number;
      deauth_count: number;
      beacon_count: number;
      unique_mac_count: number;
      unique_ssid_count: number;
    };
    anomaly_type_counts: Record<string, number>;
    anomaly_severity_counts: Record<string, number>;
  };
}

interface AnalysisOverview {
  total_agents: number;
  active_agents: number;
  total_analysis_cycles: number;
  total_logs_processed: number;
  total_features_extracted: number;
  total_anomalies_detected: number;
  agent_stats: AnalysisStats[];
}

const AnalysisStats: React.FC = () => {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  // Fetch analysis overview
  const { data: overview, isLoading: overviewLoading, error: overviewError } = useQuery<AnalysisOverview>({
    queryKey: ['analysis-overview'],
    queryFn: () => endpoints.getAnalysisOverview(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch specific agent stats
  const { data: agentStats, isLoading: agentStatsLoading, error: agentStatsError } = useQuery<AnalysisStats>({
    queryKey: ['agent-stats', selectedAgent],
    queryFn: () => endpoints.getAgentStats(selectedAgent!),
    enabled: !!selectedAgent,
    refetchInterval: 30000,
  });

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(2)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  const formatTimestamp = (timestamp: string): string => {
    return new Date(timestamp).toLocaleString();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge bg="success">Active</Badge>;
      case 'analyzing':
        return <Badge bg="warning">Analyzing</Badge>;
      case 'inactive':
        return <Badge bg="secondary">Inactive</Badge>;
      case 'error':
        return <Badge bg="danger">Error</Badge>;
      default:
        return <Badge bg="info">{status}</Badge>;
    }
  };

  if (overviewLoading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '400px' }}>
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </div>
    );
  }

  if (overviewError) {
    return (
      <Alert variant="danger">
        <Alert.Heading>Error Loading Analysis Statistics</Alert.Heading>
        <p>Failed to load analysis statistics. Please try again later.</p>
      </Alert>
    );
  }

  return (
    <div className="container-fluid">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>
          <FaChartLine className="me-2" />
          Analysis Statistics
        </h2>
      </div>

      {/* Overview Cards */}
      <Row className="mb-4">
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <FaServer className="text-primary mb-2" size={24} />
              <h4>{overview?.total_agents || 0}</h4>
              <p className="text-muted mb-0">Total Agents</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <FaCheckCircle className="text-success mb-2" size={24} />
              <h4>{overview?.active_agents || 0}</h4>
              <p className="text-muted mb-0">Active Agents</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <FaClock className="text-info mb-2" size={24} />
              <h4>{overview?.total_analysis_cycles || 0}</h4>
              <p className="text-muted mb-0">Analysis Cycles</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={3}>
          <Card className="text-center">
            <Card.Body>
              <FaExclamationTriangle className="text-warning mb-2" size={24} />
              <h4>{overview?.total_anomalies_detected || 0}</h4>
              <p className="text-muted mb-0">Anomalies Detected</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Processing Statistics */}
      <Row className="mb-4">
        <Col md={6}>
          <Card>
            <Card.Header>
              <h5 className="mb-0">Log Processing</h5>
            </Card.Header>
            <Card.Body>
              <div className="mb-3">
                <div className="d-flex justify-content-between">
                  <span>Logs Processed</span>
                  <span className="fw-bold">{overview?.total_logs_processed || 0}</span>
                </div>
                <ProgressBar 
                  now={overview?.total_logs_processed || 0} 
                  max={Math.max(overview?.total_logs_processed || 1, 1000)}
                  className="mt-1"
                />
              </div>
              <div className="mb-3">
                <div className="d-flex justify-content-between">
                  <span>Features Extracted</span>
                  <span className="fw-bold">{overview?.total_features_extracted || 0}</span>
                </div>
                <ProgressBar 
                  now={overview?.total_features_extracted || 0} 
                  max={Math.max(overview?.total_features_extracted || 1, 100)}
                  variant="info"
                  className="mt-1"
                />
              </div>
            </Card.Body>
          </Card>
        </Col>
        <Col md={6}>
          <Card>
            <Card.Header>
              <h5 className="mb-0">Agent Status Overview</h5>
            </Card.Header>
            <Card.Body>
              <Table striped bordered hover size="sm">
                <thead>
                  <tr>
                    <th>Agent</th>
                    <th>Status</th>
                    <th>Last Run</th>
                  </tr>
                </thead>
                <tbody>
                  {overview?.agent_stats.map((stat) => (
                    <tr key={stat.agent.id}>
                      <td>{stat.agent.name}</td>
                      <td>{getStatusBadge(stat.agent.status)}</td>
                      <td>
                        {stat.agent.last_run 
                          ? formatTimestamp(stat.agent.last_run)
                          : 'Never'
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Detailed Agent Statistics */}
      <Card>
        <Card.Header>
          <h5 className="mb-0">Detailed Agent Statistics</h5>
        </Card.Header>
        <Card.Body>
          <Row>
            <Col md={4}>
              <h6>Select Agent</h6>
              <select 
                className="form-select"
                value={selectedAgent || ''}
                onChange={(e) => setSelectedAgent(e.target.value || null)}
              >
                <option value="">Choose an agent...</option>
                {overview?.agent_stats.map((stat) => (
                  <option key={stat.agent.id} value={stat.agent.id}>
                    {stat.agent.name}
                  </option>
                ))}
              </select>
            </Col>
          </Row>

          {selectedAgent && agentStatsError && (
            <Alert variant="danger" className="mt-4">
              <Alert.Heading>Error Loading Agent Statistics</Alert.Heading>
              <p>Failed to load statistics for {selectedAgent}. Please try again later.</p>
            </Alert>
          )}

          {selectedAgent && agentStats && (
            <div className="mt-4">
              <Row>
                <Col md={6}>
                  <h6>Analysis Performance</h6>
                  <Table striped bordered size="sm">
                    <tbody>
                      <tr>
                        <td>Analysis Cycles</td>
                        <td>{agentStats.analysis_stats?.analysis_cycles || 0}</td>
                      </tr>
                      <tr>
                        <td>Logs Processed</td>
                        <td>{agentStats.analysis_stats?.logs_processed || 0}</td>
                      </tr>
                      <tr>
                        <td>Features Extracted</td>
                        <td>{agentStats.analysis_stats?.features_extracted || 0}</td>
                      </tr>
                      <tr>
                        <td>Anomalies Detected</td>
                        <td>{agentStats.analysis_stats?.anomalies_detected || 0}</td>
                      </tr>
                      <tr>
                        <td>Average Cycle Duration</td>
                        <td>{formatDuration(agentStats.analysis_stats?.avg_cycle_duration || 0)}</td>
                      </tr>
                      <tr>
                        <td>Last Cycle</td>
                        <td>{agentStats.analysis_stats?.last_cycle_timestamp ? formatTimestamp(agentStats.analysis_stats.last_cycle_timestamp) : 'Never'}</td>
                      </tr>
                    </tbody>
                  </Table>
                </Col>
                <Col md={6}>
                  <h6>Feature Analysis</h6>
                  <Table striped bordered size="sm">
                    <tbody>
                      <tr>
                        <td>Authentication Failures</td>
                        <td>{agentStats.analysis_stats?.feature_totals?.auth_failures || 0}</td>
                      </tr>
                      <tr>
                        <td>Deauthentication Count</td>
                        <td>{agentStats.analysis_stats?.feature_totals?.deauth_count || 0}</td>
                      </tr>
                      <tr>
                        <td>Beacon Count</td>
                        <td>{agentStats.analysis_stats?.feature_totals?.beacon_count || 0}</td>
                      </tr>
                      <tr>
                        <td>Unique MAC Addresses</td>
                        <td>{agentStats.analysis_stats?.feature_totals?.unique_mac_count || 0}</td>
                      </tr>
                      <tr>
                        <td>Unique SSIDs</td>
                        <td>{agentStats.analysis_stats?.feature_totals?.unique_ssid_count || 0}</td>
                      </tr>
                    </tbody>
                  </Table>
                </Col>
              </Row>

              <Row className="mt-3">
                <Col md={6}>
                  <h6>Anomaly Types Detected</h6>
                  <Table striped bordered size="sm">
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>Count</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(agentStats.analysis_stats?.anomaly_type_counts || {}).length > 0 ? (
                        Object.entries(agentStats.analysis_stats.anomaly_type_counts).map(([type, count]) => (
                          <tr key={type}>
                            <td>{type}</td>
                            <td>{count}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={2} className="text-center text-muted">No anomalies detected yet</td>
                        </tr>
                      )}
                    </tbody>
                  </Table>
                </Col>
                <Col md={6}>
                  <h6>Anomaly Severity Distribution</h6>
                  <Table striped bordered size="sm">
                    <thead>
                      <tr>
                        <th>Severity</th>
                        <th>Count</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(agentStats.analysis_stats?.anomaly_severity_counts || {}).length > 0 ? (
                        Object.entries(agentStats.analysis_stats.anomaly_severity_counts).map(([severity, count]) => (
                          <tr key={severity}>
                            <td>Level {severity}</td>
                            <td>{count}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={2} className="text-center text-muted">No anomalies detected yet</td>
                        </tr>
                      )}
                    </tbody>
                  </Table>
                </Col>
              </Row>
            </div>
          )}

          {selectedAgent && agentStatsLoading && (
            <div className="text-center mt-4">
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Loading agent statistics...</span>
              </Spinner>
            </div>
          )}
        </Card.Body>
      </Card>
    </div>
  );
};

export default AnalysisStats; 