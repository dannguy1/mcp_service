import React, { useState } from 'react';
import { Card, Form, Button, Row, Col, Alert } from 'react-bootstrap';
import { FaSave, FaCog } from 'react-icons/fa';

const Settings: React.FC = () => {
  const [settings, setSettings] = useState({
    apiEndpoint: 'http://localhost:5000',
    refreshInterval: '30',
    logRetention: '7',
    enableNotifications: true,
    darkMode: false
  });

  const [showAlert, setShowAlert] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement settings save logic
    setShowAlert(true);
    setTimeout(() => setShowAlert(false), 3000);
  };

  return (
    <div className="settings-page">
      <h2 className="mb-4">
        <FaCog className="me-2" />
        Settings
      </h2>

      {showAlert && (
        <Alert variant="success" onClose={() => setShowAlert(false)} dismissible>
          Settings saved successfully!
        </Alert>
      )}

      <Card>
        <Card.Body>
          <Form onSubmit={handleSubmit}>
            <Row className="mb-3">
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>API Endpoint</Form.Label>
                  <Form.Control
                    type="text"
                    name="apiEndpoint"
                    value={settings.apiEndpoint}
                    onChange={handleChange}
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
                    value={settings.refreshInterval}
                    onChange={handleChange}
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
                    value={settings.logRetention}
                    onChange={handleChange}
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
                  checked={settings.enableNotifications}
                  onChange={handleChange}
                />
              </Col>
              <Col md={6}>
                <Form.Check
                  type="switch"
                  id="darkMode"
                  name="darkMode"
                  label="Dark Mode"
                  checked={settings.darkMode}
                  onChange={handleChange}
                />
              </Col>
            </Row>

            <Button variant="primary" type="submit">
              <FaSave className="me-2" />
              Save Settings
            </Button>
          </Form>
        </Card.Body>
      </Card>
    </div>
  );
};

export default Settings; 