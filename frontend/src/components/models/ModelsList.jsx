import { useState, useEffect } from 'react';
import { Card, Table, Badge, Spinner, Alert, Button } from 'react-bootstrap';
import { FaDatabase, FaExclamationTriangle, FaPlus, FaSync } from 'react-icons/fa';
import { fetchModels } from '../../services/api';

function ModelsList() {
  const [models, setModels] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const data = await fetchModels();
      setModels(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-spinner">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="danger" className="mt-3">
        <Alert.Heading>
          <FaExclamationTriangle className="me-2" />
          Error Loading Models
        </Alert.Heading>
        <p>{error}</p>
        <Button variant="outline-danger" onClick={fetchData}>
          <FaSync className="me-2" />
          Retry
        </Button>
      </Alert>
    );
  }

  return (
    <div className="models-container">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Models</h2>
        <div className="d-flex gap-2">
          <Button variant="outline-primary" onClick={fetchData}>
            <FaSync className="me-2" />
            Refresh
          </Button>
          <Button variant="primary">
            <FaPlus className="me-2" />
            Add Model
          </Button>
        </div>
      </div>

      <Card className="dashboard-card">
        <Card.Header className="bg-white text-dark">
          <h5 className="mb-0">
            <FaDatabase className="me-2" />
            Available Models
          </h5>
        </Card.Header>
        <Card.Body>
          {models.length === 0 ? (
            <Alert variant="info">
              No models available. Click "Add Model" to get started.
            </Alert>
          ) : (
            <div className="table-container">
              <Table striped bordered hover responsive>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Version</th>
                    <th>Status</th>
                    <th>Last Updated</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {models.map((model) => (
                    <tr key={model.id}>
                      <td>{model.name}</td>
                      <td>
                        <Badge bg="secondary">{model.version}</Badge>
                      </td>
                      <td>
                        <Badge bg={model.status === 'active' ? 'success' : 'warning'}>
                          {model.status}
                        </Badge>
                      </td>
                      <td>{new Date(model.last_updated).toLocaleString()}</td>
                      <td>
                        <div className="d-flex gap-2">
                          <Button variant="outline-primary" size="sm">
                            View
                          </Button>
                          <Button variant="outline-danger" size="sm">
                            Delete
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Model Statistics */}
      <Card className="dashboard-card mt-4">
        <Card.Header className="bg-white text-dark">
          <h5 className="mb-0">Model Statistics</h5>
        </Card.Header>
        <Card.Body>
          <div className="row">
            <div className="col-md-4">
              <div className="stat-item">
                <h6>Total Models</h6>
                <h3>{models.length}</h3>
              </div>
            </div>
            <div className="col-md-4">
              <div className="stat-item">
                <h6>Active Models</h6>
                <h3>
                  {models.filter(m => m.status === 'active').length}
                </h3>
              </div>
            </div>
            <div className="col-md-4">
              <div className="stat-item">
                <h6>Latest Update</h6>
                <h3>
                  {models.length > 0
                    ? new Date(Math.max(...models.map(m => new Date(m.last_updated))))
                        .toLocaleDateString()
                    : 'N/A'}
                </h3>
              </div>
            </div>
          </div>
        </Card.Body>
      </Card>
    </div>
  );
}

export default ModelsList; 