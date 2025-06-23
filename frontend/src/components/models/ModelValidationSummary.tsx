import React from "react";
import { Card, Badge, ListGroup } from "react-bootstrap";
import type { ModelValidationSummary } from "../../services/types";

interface ModelValidationSummaryProps {
  validationSummary: ModelValidationSummary;
}

const ModelValidationSummaryComponent: React.FC<ModelValidationSummaryProps> = ({ 
  validationSummary 
}) => {
  const { required_files_present, optional_files_missing, warnings } = validationSummary;

  return (
    <Card className="mt-3">
      <Card.Header>
        <h6 className="mb-0">Import Validation Summary</h6>
      </Card.Header>
      <Card.Body>
        <div className="row">
          <div className="col-md-6">
            <h6 className="text-success">
              <i className="fas fa-check-circle me-2"></i>
              Required Files Present ({required_files_present.length})
            </h6>
            <ListGroup variant="flush" className="mb-3">
              {required_files_present.map((file, index) => (
                <ListGroup.Item key={index} className="py-1">
                  <Badge bg="success" className="me-2">✓</Badge>
                  {file}
                </ListGroup.Item>
              ))}
            </ListGroup>
          </div>
          
          <div className="col-md-6">
            <h6 className="text-warning">
              <i className="fas fa-exclamation-triangle me-2"></i>
              Optional Files Missing ({optional_files_missing.length})
            </h6>
            <ListGroup variant="flush" className="mb-3">
              {optional_files_missing.length > 0 ? (
                optional_files_missing.map((file, index) => (
                  <ListGroup.Item key={index} className="py-1">
                    <Badge bg="warning" text="dark" className="me-2">!</Badge>
                    {file}
                  </ListGroup.Item>
                ))
              ) : (
                <ListGroup.Item className="py-1 text-muted">
                  <Badge bg="success" className="me-2">✓</Badge>
                  All optional files present
                </ListGroup.Item>
              )}
            </ListGroup>
          </div>
        </div>

        {warnings.length > 0 && (
          <div className="mt-3">
            <h6 className="text-info">
              <i className="fas fa-info-circle me-2"></i>
              Warnings ({warnings.length})
            </h6>
            <ListGroup variant="flush">
              {warnings.map((warning, index) => (
                <ListGroup.Item key={index} className="py-1 text-info">
                  <i className="fas fa-info-circle me-2"></i>
                  {warning}
                </ListGroup.Item>
              ))}
            </ListGroup>
          </div>
        )}

        <div className="mt-3 p-2 bg-light rounded">
          <small className="text-muted">
            <i className="fas fa-info-circle me-1"></i>
            <strong>Required files:</strong> model.joblib, metadata.json, deployment_manifest.json
            <br />
            <strong>Optional files:</strong> validate_model.py, inference_example.py, requirements.txt, README.md
          </small>
        </div>
      </Card.Body>
    </Card>
  );
};

export default ModelValidationSummaryComponent; 