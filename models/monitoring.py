import logging
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from prometheus_client import Counter, Gauge, Histogram
from sklearn.metrics import precision_recall_curve, average_precision_score

from data_service import data_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelMonitor:
    """Monitors model performance and drift."""
    
    def __init__(self):
        """Initialize the model monitor."""
        # Initialize Prometheus metrics
        self.metrics = {
            'predictions_total': Counter(
                'model_predictions_total',
                'Total number of predictions made'
            ),
            'anomalies_detected': Counter(
                'model_anomalies_detected',
                'Total number of anomalies detected'
            ),
            'prediction_latency': Histogram(
                'model_prediction_latency_seconds',
                'Time taken for predictions',
                buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
            ),
            'model_load_time': Histogram(
                'model_load_time_seconds',
                'Time taken to load model',
                buckets=[1.0, 5.0, 10.0, 30.0, 60.0]
            ),
            'feature_drift': Gauge(
                'model_feature_drift',
                'Feature drift score',
                ['feature']
            ),
            'prediction_drift': Gauge(
                'model_prediction_drift',
                'Prediction drift score'
            ),
            'data_quality': Gauge(
                'model_data_quality',
                'Data quality score',
                ['metric']
            )
        }
        
        # Initialize drift detection parameters
        self.drift_threshold = 0.1
        self.window_size = 1000
        self.reference_data = None
    
    async def update_metrics(self, predictions: np.ndarray, scores: np.ndarray,
                           features: Dict, latency: float) -> None:
        """Update monitoring metrics.
        
        Args:
            predictions: Model predictions (-1 for anomalies, 1 for normal)
            scores: Anomaly scores
            features: Input features
            latency: Prediction latency in seconds
        """
        # Update basic metrics
        self.metrics['predictions_total'].inc(len(predictions))
        self.metrics['anomalies_detected'].inc(np.sum(predictions == -1))
        self.metrics['prediction_latency'].observe(latency)
        
        # Update drift metrics
        await self._update_drift_metrics(features, scores)
        
        # Update data quality metrics
        await self._update_data_quality_metrics(features)
    
    async def _update_drift_metrics(self, features: Dict, scores: np.ndarray) -> None:
        """Update feature and prediction drift metrics.
        
        Args:
            features: Input features
            scores: Anomaly scores
        """
        # Initialize reference data if not exists
        if self.reference_data is None:
            self.reference_data = {
                'features': features,
                'scores': scores
            }
            return
        
        # Calculate feature drift
        for feature_name, feature_values in features.items():
            if feature_name in self.reference_data['features']:
                ref_values = self.reference_data['features'][feature_name]
                drift_score = self._calculate_drift_score(feature_values, ref_values)
                self.metrics['feature_drift'].labels(feature=feature_name).set(drift_score)
        
        # Calculate prediction drift
        drift_score = self._calculate_drift_score(scores, self.reference_data['scores'])
        self.metrics['prediction_drift'].set(drift_score)
        
        # Update reference data
        self.reference_data = {
            'features': features,
            'scores': scores
        }
    
    def _calculate_drift_score(self, current: np.ndarray, reference: np.ndarray) -> float:
        """Calculate drift score between current and reference data.
        
        Args:
            current: Current data
            reference: Reference data
            
        Returns:
            Drift score (0 to 1, higher means more drift)
        """
        # Use Kolmogorov-Smirnov test for drift detection
        from scipy import stats
        ks_statistic, _ = stats.ks_2samp(current, reference)
        return ks_statistic
    
    async def _update_data_quality_metrics(self, features: Dict) -> None:
        """Update data quality metrics.
        
        Args:
            features: Input features
        """
        # Calculate missing values ratio
        missing_ratio = np.mean([np.isnan(v).mean() for v in features.values()])
        self.metrics['data_quality'].labels(metric='missing_ratio').set(missing_ratio)
        
        # Calculate feature statistics
        for feature_name, feature_values in features.items():
            if np.issubdtype(type(feature_values[0]), np.number):
                # Calculate mean and std
                mean = np.nanmean(feature_values)
                std = np.nanstd(feature_values)
                
                self.metrics['data_quality'].labels(
                    metric=f'{feature_name}_mean'
                ).set(mean)
                self.metrics['data_quality'].labels(
                    metric=f'{feature_name}_std'
                ).set(std)
    
    async def check_drift(self) -> Dict[str, bool]:
        """Check if drift is detected in any metric.
        
        Returns:
            Dictionary of drift flags for each metric
        """
        drift_flags = {}
        
        # Check feature drift
        for feature in self.metrics['feature_drift']._metrics:
            drift_score = self.metrics['feature_drift'].labels(feature=feature)._value.get()
            drift_flags[f'feature_{feature}'] = drift_score > self.drift_threshold
        
        # Check prediction drift
        drift_score = self.metrics['prediction_drift']._value.get()
        drift_flags['prediction'] = drift_score > self.drift_threshold
        
        return drift_flags
    
    async def get_performance_metrics(self, start_time: Optional[datetime] = None,
                                    end_time: Optional[datetime] = None) -> Dict:
        """Get model performance metrics for a time period.
        
        Args:
            start_time: Start time for metrics
            end_time: End time for metrics
            
        Returns:
            Dictionary of performance metrics
        """
        # Query database for predictions and actual outcomes
        query = """
            SELECT prediction, score, is_anomaly
            FROM predictions
            WHERE timestamp BETWEEN $1 AND $2
        """
        results = await data_service.fetch_all(query, start_time, end_time)
        
        if not results:
            return {}
        
        # Calculate metrics
        predictions = np.array([r['prediction'] for r in results])
        scores = np.array([r['score'] for r in results])
        actual = np.array([r['is_anomaly'] for r in results])
        
        # Calculate precision-recall curve
        precision, recall, thresholds = precision_recall_curve(actual, scores)
        avg_precision = average_precision_score(actual, scores)
        
        return {
            'average_precision': avg_precision,
            'precision': precision.tolist(),
            'recall': recall.tolist(),
            'thresholds': thresholds.tolist(),
            'predictions_total': len(predictions),
            'anomalies_detected': np.sum(predictions == -1),
            'true_anomalies': np.sum(actual == 1)
        }

# Initialize global monitor instance
model_monitor = ModelMonitor() 