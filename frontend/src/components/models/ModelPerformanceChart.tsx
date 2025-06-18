import React from 'react';
import { Card } from 'react-bootstrap';
import type { ModelPerformanceMetrics } from '../../services/types';

interface ModelPerformanceChartProps {
  performance: ModelPerformanceMetrics;
  title?: string;
}

const ModelPerformanceChart: React.FC<ModelPerformanceChartProps> = ({ 
  performance, 
  title = 'Performance Metrics' 
}) => {
  const metrics = performance.performance_metrics;
  
  // Calculate percentages for visualization
  const anomalyRatePercent = metrics.anomaly_rate * 100;
  const avgInferenceTimeMs = metrics.avg_inference_time * 1000;
  const maxInferenceTimeMs = metrics.max_inference_time * 1000;
  const minInferenceTimeMs = metrics.min_inference_time * 1000;

  return (
    <Card>
      <Card.Header>
        <h6 className="mb-0">{title}</h6>
      </Card.Header>
      <Card.Body>
        <div className="row">
          <div className="col-md-6 mb-3">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <span className="text-muted">Anomaly Rate</span>
              <span className="fw-bold">{anomalyRatePercent.toFixed(2)}%</span>
            </div>
            <div className="progress" style={{ height: '8px' }}>
              <div 
                className="progress-bar bg-warning" 
                style={{ width: `${Math.min(anomalyRatePercent * 2, 100)}%` }}
              />
            </div>
          </div>
          
          <div className="col-md-6 mb-3">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <span className="text-muted">Avg Inference Time</span>
              <span className="fw-bold">{avgInferenceTimeMs.toFixed(2)}ms</span>
            </div>
            <div className="progress" style={{ height: '8px' }}>
              <div 
                className="progress-bar bg-info" 
                style={{ width: `${Math.min((avgInferenceTimeMs / 100) * 10, 100)}%` }}
              />
            </div>
          </div>
          
          <div className="col-md-6 mb-3">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <span className="text-muted">Total Inferences</span>
              <span className="fw-bold">{performance.total_inferences.toLocaleString()}</span>
            </div>
            <div className="progress" style={{ height: '8px' }}>
              <div 
                className="progress-bar bg-success" 
                style={{ width: `${Math.min((performance.total_inferences / 10000) * 5, 100)}%` }}
              />
            </div>
          </div>
          
          <div className="col-md-6 mb-3">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <span className="text-muted">Total Anomalies</span>
              <span className="fw-bold">{metrics.total_anomalies.toLocaleString()}</span>
            </div>
            <div className="progress" style={{ height: '8px' }}>
              <div 
                className="progress-bar bg-danger" 
                style={{ width: `${Math.min((metrics.total_anomalies / 1000) * 10, 100)}%` }}
              />
            </div>
          </div>
        </div>
        
        <div className="row mt-3">
          <div className="col-12">
            <h6 className="text-muted mb-2">Inference Time Range</h6>
            <div className="d-flex justify-content-between">
              <span className="text-muted">Min: {minInferenceTimeMs.toFixed(2)}ms</span>
              <span className="text-muted">Max: {maxInferenceTimeMs.toFixed(2)}ms</span>
            </div>
            <div className="progress mt-1" style={{ height: '6px' }}>
              <div 
                className="progress-bar bg-primary" 
                style={{ 
                  width: `${((avgInferenceTimeMs - minInferenceTimeMs) / (maxInferenceTimeMs - minInferenceTimeMs)) * 100}%`,
                  marginLeft: `${(minInferenceTimeMs / maxInferenceTimeMs) * 100}%`
                }}
              />
            </div>
          </div>
        </div>
        
        <div className="mt-3">
          <small className="text-muted">
            Last updated: {new Date(performance.last_updated).toLocaleString()}
          </small>
        </div>
      </Card.Body>
    </Card>
  );
};

export default ModelPerformanceChart; 