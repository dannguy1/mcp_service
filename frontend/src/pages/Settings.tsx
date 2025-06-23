import React, { useState, useEffect } from 'react';
import { Card, Form, Button, Row, Col, Alert, Spinner } from 'react-bootstrap';
import { FaSave, FaCog, FaDatabase, FaFlask } from 'react-icons/fa';
import { endpoints } from '../services/api';
import type { DatabaseConfig, DatabaseTestResult } from '../services/types';
import TabbedLayout from '../components/common/TabbedLayout';
import type { TabItem } from '../components/common/types';

const Settings: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [showAlert, setShowAlert] = useState(false);
  const [alertMessage, setAlertMessage] = useState('');
  const [alertVariant, setAlertVariant] = useState<'success' | 'danger'>('success');

  // General settings state
  const [generalSettings, setGeneralSettings] = useState({
    apiEndpoint: 'http://localhost:5000',
    refreshInterval: '30',
    logRetention: '7',
    enableNotifications: true,
    darkMode: false
  });

  // Database settings state
  const [databaseConfig, setDatabaseConfig] = useState<DatabaseConfig>({
    host: 'localhost',
    port: 5432,
    database: 'netmonitor_db',
    user: 'netmonitor_user',
    password: '',
    min_connections: 5,
    max_connections: 20,
    pool_timeout: 30
  });

  const [testResult, setTestResult] = useState<DatabaseTestResult | null>(null);
  const [testingConnection, setTestingConnection] = useState(false);

  // Load database configuration on component mount
  useEffect(() => {
    loadDatabaseConfig();
  }, []);

  const loadDatabaseConfig = async () => {
    try {
      setLoading(true);
      const config = await endpoints.getDatabaseConfig();
      setDatabaseConfig(config);
    } catch (error) {
      console.error('Error loading database config:', error);
      setAlertMessage('Failed to load database configuration');
      setAlertVariant('danger');
      setShowAlert(true);
    } finally {
      setLoading(false);
    }
  };

  const handleGeneralChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setGeneralSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleDatabaseChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target;
    setDatabaseConfig(prev => ({
      ...prev,
      [name]: type === 'number' ? parseInt(value) || 0 : value
    }));
  };

  const handleGeneralSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement general settings save logic
    setAlertMessage('General settings saved successfully!');
    setAlertVariant('success');
    setShowAlert(true);
    setTimeout(() => setShowAlert(false), 3000);
  };

  const handleDatabaseSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await endpoints.updateDatabaseConfig(databaseConfig);
      setAlertMessage('Database configuration updated successfully!');
      setAlertVariant('success');
      setShowAlert(true);
      setTimeout(() => setShowAlert(false), 3000);
    } catch (error: any) {
      console.error('Error updating database config:', error);
      setAlertMessage(error.response?.data?.detail || 'Failed to update database configuration');
      setAlertVariant('danger');
      setShowAlert(true);
      setTimeout(() => setShowAlert(false), 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    try {
      setTestingConnection(true);
      setTestResult(null);
      
      // Validate required fields before testing
      const requiredFields = ['host', 'port', 'database', 'user', 'password'];
      const missingFields = requiredFields.filter(field => !databaseConfig[field as keyof DatabaseConfig]);
      
      if (missingFields.length > 0) {
        setTestResult({
          status: 'error',
          message: `Missing required fields: ${missingFields.join(', ')}`
        });
        return;
      }
      
      const result = await endpoints.testDatabaseConnection(databaseConfig);
      setTestResult(result);
    } catch (error: any) {
      console.error('Error testing database connection:', error);
      
      // Handle different types of errors
      let errorMessage = 'Failed to test database connection';
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setTestResult({
        status: 'error',
        message: errorMessage
      });
    } finally {
      setTestingConnection(false);
    }
  };

  // General Settings Tab Content
  const GeneralSettingsContent = (
    <div>
      {showAlert && (
        <Alert variant={alertVariant} onClose={() => setShowAlert(false)} dismissible>
          {alertMessage}
        </Alert>
      )}

      <Form onSubmit={handleGeneralSubmit}>
        <Row className="mb-3">
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>API Endpoint</Form.Label>
              <Form.Control
                type="text"
                name="apiEndpoint"
                value={generalSettings.apiEndpoint}
                onChange={handleGeneralChange}
                placeholder="Enter API endpoint"
              />
            </Form.Group>
          </Col>
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Refresh Interval (seconds)</Form.Label>
              <Form.Control
                type="number"
                name="refreshInterval"
                value={generalSettings.refreshInterval}
                onChange={handleGeneralChange}
                min="5"
                max="300"
              />
            </Form.Group>
          </Col>
        </Row>

        <Row className="mb-3">
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Log Retention (days)</Form.Label>
              <Form.Control
                type="number"
                name="logRetention"
                value={generalSettings.logRetention}
                onChange={handleGeneralChange}
                min="1"
                max="365"
              />
            </Form.Group>
          </Col>
        </Row>

        <Row className="mb-3">
          <Col md={6}>
            <Form.Check
              type="switch"
              id="enableNotifications"
              name="enableNotifications"
              label="Enable Notifications"
              checked={generalSettings.enableNotifications}
              onChange={handleGeneralChange}
            />
          </Col>
          <Col md={6}>
            <Form.Check
              type="switch"
              id="darkMode"
              name="darkMode"
              label="Dark Mode"
              checked={generalSettings.darkMode}
              onChange={handleGeneralChange}
            />
          </Col>
        </Row>

        <Button variant="primary" type="submit" disabled={loading}>
          {loading ? <Spinner animation="border" size="sm" className="me-2" /> : <FaSave className="me-2" />}
          Save General Settings
        </Button>
      </Form>
    </div>
  );

  // Database Configuration Tab Content
  const DatabaseConfigContent = (
    <div>
      {showAlert && (
        <Alert variant={alertVariant} onClose={() => setShowAlert(false)} dismissible>
          {alertMessage}
        </Alert>
      )}

      <Form onSubmit={handleDatabaseSubmit}>
        <Row className="mb-3">
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Host</Form.Label>
              <Form.Control
                type="text"
                name="host"
                value={databaseConfig.host}
                onChange={handleDatabaseChange}
                placeholder="Database host"
                required
              />
            </Form.Group>
          </Col>
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Port</Form.Label>
              <Form.Control
                type="number"
                name="port"
                value={databaseConfig.port}
                onChange={handleDatabaseChange}
                placeholder="5432"
                required
              />
            </Form.Group>
          </Col>
        </Row>

        <Row className="mb-3">
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Database Name</Form.Label>
              <Form.Control
                type="text"
                name="database"
                value={databaseConfig.database}
                onChange={handleDatabaseChange}
                placeholder="Database name"
                required
              />
            </Form.Group>
          </Col>
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Username</Form.Label>
              <Form.Control
                type="text"
                name="user"
                value={databaseConfig.user}
                onChange={handleDatabaseChange}
                placeholder="Database user"
                required
              />
            </Form.Group>
          </Col>
        </Row>

        <Row className="mb-3">
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Password</Form.Label>
              <Form.Control
                type="password"
                name="password"
                value={databaseConfig.password}
                onChange={handleDatabaseChange}
                placeholder="Database password"
                required
              />
            </Form.Group>
          </Col>
        </Row>

        <Row className="mb-3">
          <Col md={4}>
            <Form.Group className="mb-3">
              <Form.Label>Min Connections</Form.Label>
              <Form.Control
                type="number"
                name="min_connections"
                value={databaseConfig.min_connections}
                onChange={handleDatabaseChange}
                min="1"
                max="50"
              />
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group className="mb-3">
              <Form.Label>Max Connections</Form.Label>
              <Form.Control
                type="number"
                name="max_connections"
                value={databaseConfig.max_connections}
                onChange={handleDatabaseChange}
                min="1"
                max="100"
              />
            </Form.Group>
          </Col>
          <Col md={4}>
            <Form.Group className="mb-3">
              <Form.Label>Pool Timeout (seconds)</Form.Label>
              <Form.Control
                type="number"
                name="pool_timeout"
                value={databaseConfig.pool_timeout}
                onChange={handleDatabaseChange}
                min="5"
                max="300"
              />
            </Form.Group>
          </Col>
        </Row>

        {testResult && (
          <Alert variant={testResult.status === 'success' ? 'success' : 'danger'} className="mb-3">
            <div>
              <strong>{testResult.status === 'success' ? 'Success!' : 'Error!'}</strong> {testResult.message}
              
              {testResult.details && (
                <div className="mt-2">
                  <small className="text-muted">
                    <strong>Connection Details:</strong><br />
                    Host: {testResult.details.host} | Port: {testResult.details.port}<br />
                    Database: {testResult.details.database} | User: {testResult.details.user}
                    {testResult.details.error_type && (
                      <>
                        <br />
                        <strong>Error Type:</strong> {testResult.details.error_type}
                      </>
                    )}
                    {testResult.details.test_query_result && (
                      <>
                        <br />
                        <strong>Test Query Result:</strong> {testResult.details.test_query_result}
                      </>
                    )}
                  </small>
                </div>
              )}
            </div>
          </Alert>
        )}

        <div className="d-flex gap-2">
          <Button variant="primary" type="submit" disabled={loading}>
            {loading ? <Spinner animation="border" size="sm" className="me-2" /> : <FaSave className="me-2" />}
            Save Database Configuration
          </Button>
          <Button 
            variant="outline-secondary" 
            onClick={handleTestConnection}
            disabled={testingConnection}
          >
            {testingConnection ? <Spinner animation="border" size="sm" className="me-2" /> : <FaFlask className="me-2" />}
            Test Connection
          </Button>
        </div>
      </Form>
    </div>
  );

  const tabs: TabItem[] = [
    {
      key: 'general',
      title: 'General Settings',
      icon: <FaCog />,
      content: GeneralSettingsContent
    },
    {
      key: 'database',
      title: 'Database Configuration',
      icon: <FaDatabase />,
      content: DatabaseConfigContent
    }
  ];

  return (
    <div className="container-fluid">
      <TabbedLayout title="Settings" tabs={tabs} />
    </div>
  );
};

export default Settings; 