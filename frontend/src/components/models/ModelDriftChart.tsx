import React from 'react';
import { Card, Badge, ProgressBar } from 'react-bootstrap';
import type { ModelDriftResult } from '../../services/types';

interface ModelDriftChartProps {
  driftResult: ModelDriftResult;
  title?: string;
}

const ModelDriftChart: React.FC<ModelDriftChartProps> = ({ 
  driftResult, 
  title = 'Model Drift Analysis' 
}) => {
  const { drift_detected, drift_score, confidence, indicators, threshold } = driftResult;
  
  // Calculate percentages for visualization
  const driftScorePercent = drift_score * 100;
  const confidencePercent = confidence * 100;
  const thresholdPercent = threshold * 100;
  
  // Determine severity color
  const getSeverityColor = (score: number) => {
    if (score < 0.3) return 'success';
    if (score < 0.7) return 'warning';
    return 'danger';
  };

  const getIndicatorColor = (value: number) => {
    if (value < 0.1) return 'success';
    if (value < 0.3) return 'warning';
    return 'danger';
  };

  return (
    <Card>
      <Card.Header>
        <div className="d-flex justify-content-between align-items-center">
          <h6 className="mb-0">{title}</h6>
          <Badge bg={drift_detected ? 'danger' : 'success'}>
            {drift_detected ? 'Drift Detected' : 'No Drift'}
          </Badge>
        </div>
      </Card.Header>
      <Card.Body>
        <div className="row mb-4">
          <div className="col-md-6">
            <div className="mb-3">
              <div className="d-flex justify-content-between align-items-center mb-2">
                <span className="text-muted">Drift Score</span>
                <span className="fw-bold">{driftScorePercent.toFixed(1)}%</span>
              </div>
              <ProgressBar 
                variant={getSeverityColor(drift_score)}
                now={driftScorePercent} 
                className="mb-1"
              />
              <small className="text-muted">Threshold: {thresholdPercent.toFixed(1)}%</small>
            </div>
          </div>
          
          <div className="col-md-6">
            <div className="mb-3">
              <div className="d-flex justify-content-between align-items-center mb-2">
                <span className="text-muted">Confidence</span>
                <span className="fw-bold">{confidencePercent.toFixed(1)}%</span>
              </div>
              <ProgressBar 
                variant="info"
                now={confidencePercent} 
                className="mb-1"
              />
            </div>
          </div>
        </div>

        <div className="mb-4">
          <h6 className="text-muted mb-3">Drift Indicators</h6>
          
          <div className="mb-3">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <span className="text-muted">Anomaly Rate Change</span>
              <span className="fw-bold">{(indicators.anomaly_rate_change * 100).toFixed(1)}%</span>
            </div>
            <ProgressBar 
              variant={getIndicatorColor(indicators.anomaly_rate_change)}
              now={Math.min(indicators.anomaly_rate_change * 100, 100)} 
            />
          </div>
          
          <div className="mb-3">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <span className="text-muted">Score Distribution Change</span>
              <span className="fw-bold">{(indicators.score_distribution_change * 100).toFixed(1)}%</span>
            </div>
            <ProgressBar 
              variant={getIndicatorColor(indicators.score_distribution_change)}
              now={Math.min(indicators.score_distribution_change * 100, 100)} 
            />
          </div>
          
          <div className="mb-3">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <span className="text-muted">Inference Time Change</span>
              <span className="fw-bold">{(indicators.inference_time_change * 100).toFixed(1)}%</span>
            </div>
            <ProgressBar 
              variant={getIndicatorColor(indicators.inference_time_change)}
              now={Math.min(indicators.inference_time_change * 100, 100)} 
            />
          </div>
        </div>

        <div className="alert alert-info">
          <strong>Recommendation:</strong> {
            drift_detected 
              ? 'Consider retraining the model or investigating the data distribution changes.'
              : 'Model performance appears stable. Continue monitoring for any changes.'
          }
        </div>
      </Card.Body>
    </Card>
  );
};

export default ModelDriftChart; 