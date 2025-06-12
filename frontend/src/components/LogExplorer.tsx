import React, { useState, useEffect } from 'react';
import { Table, Card, Form, Row, Col, Button, Spinner, Pagination } from 'react-bootstrap';
import { fetchLogs } from '../api';
import { LogEntry } from '../types';

interface LogExplorerProps {
    onLogSelect?: (log: LogEntry) => void;
}

const LogExplorer: React.FC<LogExplorerProps> = ({ onLogSelect }) => {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [filters, setFilters] = useState({
        startDate: '',
        endDate: '',
        severity: [] as string[],
        programs: [] as string[]
    });
    const [pagination, setPagination] = useState({
        total: 0,
        per_page: 25,
        current_page: 1,
        total_pages: 0,
        has_next: false,
        has_prev: false
    });

    const loadLogs = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await fetchLogs(filters, pagination.current_page, pagination.per_page);
            
            console.log('LogExplorer received response:', response);
            
            if (response && response.logs && response.logs.logs) {
                console.log('Setting logs from response.logs.logs');
                setLogs(response.logs.logs);
                if (response.logs.pagination) {
                    console.log('Setting pagination from response.logs.pagination');
                    setPagination(response.logs.pagination);
                }
            } else {
                console.error('Unexpected response format:', response);
                setError('Invalid response format from server');
                setLogs([]);
            }
        } catch (err) {
            console.error('Error loading logs:', err);
            setError(err instanceof Error ? err.message : 'Failed to load logs');
            setLogs([]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadLogs();
    }, [filters, pagination.current_page]);

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

    const handlePageChange = (page: number) => {
        setPagination(prev => ({ ...prev, current_page: page }));
    };

    if (error) {
        return <div className="alert alert-danger">{error}</div>;
    }

    return (
        <Card>
            <Card.Header className="bg-white text-dark">
                <h5 className="mb-0">Log Explorer</h5>
            </Card.Header>
            <Card.Body>
                <Form className="mb-4">
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
                                <Form.Label>Severity</Form.Label>
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
                                <Form.Label>Program</Form.Label>
                                <Form.Select
                                    multiple
                                    name="programs"
                                    value={filters.programs}
                                    onChange={handleProgramChange}
                                >
                                    {/* Add program options dynamically */}
                                </Form.Select>
                            </Form.Group>
                        </Col>
                    </Row>
                    <Button variant="primary" onClick={loadLogs}>
                        Apply Filters
                    </Button>
                </Form>

                {loading ? (
                    <div className="d-flex justify-content-center">
                        <Spinner animation="border" role="status">
                            <span className="visually-hidden">Loading...</span>
                        </Spinner>
                    </div>
                ) : error ? (
                    <div className="alert alert-danger">{error}</div>
                ) : logs.length === 0 ? (
                    <div className="alert alert-info">No logs found</div>
                ) : (
                    <>
                        <Table striped bordered hover responsive>
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Level</th>
                                    <th>Program</th>
                                    <th>Message</th>
                                    <th>Device IP</th>
                                </tr>
                            </thead>
                            <tbody>
                                {Array.isArray(logs) && logs.map((log) => (
                                    <tr 
                                        key={log.id} 
                                        onClick={() => onLogSelect?.(log)}
                                        style={{ cursor: onLogSelect ? 'pointer' : 'default' }}
                                    >
                                        <td>{new Date(log.timestamp).toLocaleString()}</td>
                                        <td>
                                            <span className={`badge bg-${getSeverityColor(log.level)}`}>
                                                {log.level}
                                            </span>
                                        </td>
                                        <td>{log.program}</td>
                                        <td>{log.message}</td>
                                        <td>{log.device_ip}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </Table>

                        <div className="d-flex justify-content-between align-items-center">
                            <div>
                                Showing {logs.length} of {pagination.total} logs
                            </div>
                            <Pagination>
                                <Pagination.First 
                                    onClick={() => handlePageChange(1)}
                                    disabled={!pagination.has_prev}
                                />
                                <Pagination.Prev 
                                    onClick={() => handlePageChange(pagination.current_page - 1)}
                                    disabled={!pagination.has_prev}
                                />
                                <Pagination.Item active>{pagination.current_page}</Pagination.Item>
                                <Pagination.Next 
                                    onClick={() => handlePageChange(pagination.current_page + 1)}
                                    disabled={!pagination.has_next}
                                />
                                <Pagination.Last 
                                    onClick={() => handlePageChange(pagination.total_pages)}
                                    disabled={!pagination.has_next}
                                />
                            </Pagination>
                        </div>
                    </>
                )}
            </Card.Body>
        </Card>
    );
};

const getSeverityColor = (level: string): string => {
    switch (level.toLowerCase()) {
        case 'emergency':
        case 'alert':
        case 'critical':
            return 'danger';
        case 'error':
            return 'danger';
        case 'warning':
            return 'warning';
        case 'notice':
            return 'info';
        case 'info':
            return 'info';
        case 'debug':
            return 'secondary';
        default:
            return 'secondary';
    }
};

export default LogExplorer; 