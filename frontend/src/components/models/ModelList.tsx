import React from "react";
import { Card, Button, Badge } from "react-bootstrap";
import type { Model } from "../../services/types";

interface ModelListProps {
  models: Model[];
  onActivate: (modelId: string) => void;
  onDeploy: (modelId: string) => void;
}

const ModelList: React.FC<ModelListProps> = ({ models, onActivate, onDeploy }) => {
  return (
    <div className="row">
      {models.map((model) => (
        <div key={model.id} className="col-md-4 mb-4">
          <Card>
            <Card.Header className="d-flex justify-content-between align-items-center">
              <h5 className="mb-0">{model.name}</h5>
              <Badge bg={model.is_active ? "success" : "secondary"}>
                {model.is_active ? "Active" : "Inactive"}
              </Badge>
            </Card.Header>
            <Card.Body>
              <p className="mb-2">
                <strong>Version:</strong> {model.metadata.version}
              </p>
              <p className="mb-2">
                <strong>Created:</strong> {new Date(model.metadata.created_at).toLocaleString()}
              </p>
              <div className="mt-3">
                <Button
                  variant={model.is_active ? "outline-danger" : "outline-success"}
                  className="me-2"
                  onClick={() => onActivate(model.id)}
                >
                  {model.is_active ? "Deactivate" : "Activate"}
                </Button>
                <Button
                  variant="outline-primary"
                  onClick={() => onDeploy(model.id)}
                >
                  Deploy
                </Button>
              </div>
            </Card.Body>
          </Card>
        </div>
      ))}
    </div>
  );
};

export default ModelList;