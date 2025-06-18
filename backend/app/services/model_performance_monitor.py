import logging
import numpy as np
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from ..models.config import ModelConfig

logger = logging.getLogger(__name__)

class ModelPerformanceMonitor:
    """Monitor model performance and detect drift."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.performance_file = Path(config.storage.directory) / "performance_metrics.json"
        self.drift_threshold = config.monitoring.drift_threshold
        
        # Ensure performance file directory exists
        self.performance_file.parent.mkdir(parents=True, exist_ok=True)
    
    async def record_inference_metrics(self, model_version: str, 
                                     inference_time: float,
                                     anomaly_score: float,
                                     is_anomaly: bool) -> None:
        """Record inference performance metrics."""
        try:
            metrics = self._load_performance_metrics()
            
            timestamp = datetime.now().isoformat()
            
            if model_version not in metrics:
                metrics[model_version] = {
                    'inference_times': [],
                    'anomaly_scores': [],
                    'anomaly_counts': [],
                    'total_inferences': 0,
                    'last_updated': timestamp
                }
            
            # Record metrics
            metrics[model_version]['inference_times'].append(inference_time)
            metrics[model_version]['anomaly_scores'].append(anomaly_score)
            metrics[model_version]['anomaly_counts'].append(1 if is_anomaly else 0)
            metrics[model_version]['total_inferences'] += 1
            metrics[model_version]['last_updated'] = timestamp
            
            # Keep only recent metrics (last 1000 inferences)
            max_metrics = 1000
            for key in ['inference_times', 'anomaly_scores', 'anomaly_counts']:
                if len(metrics[model_version][key]) > max_metrics:
                    metrics[model_version][key] = metrics[model_version][key][-max_metrics:]
            
            self._save_performance_metrics(metrics)
            
        except Exception as e:
            logger.error(f"Error recording inference metrics: {e}")
    
    async def check_model_drift(self, model_version: str) -> Dict[str, Any]:
        """Check for model drift."""
        try:
            metrics = self._load_performance_metrics()
            
            if model_version not in metrics:
                return {
                    'drift_detected': False,
                    'confidence': 0.0,
                    'metrics': {}
                }
            
            model_metrics = metrics[model_version]
            
            # Calculate drift indicators
            drift_indicators = {
                'anomaly_rate_change': self._calculate_anomaly_rate_change(model_metrics),
                'score_distribution_change': self._calculate_score_distribution_change(model_metrics),
                'inference_time_change': self._calculate_inference_time_change(model_metrics)
            }
            
            # Determine overall drift
            drift_score = np.mean(list(drift_indicators.values()))
            drift_detected = drift_score > self.drift_threshold
            
            return {
                'drift_detected': drift_detected,
                'drift_score': drift_score,
                'confidence': min(drift_score, 1.0),
                'indicators': drift_indicators,
                'threshold': self.drift_threshold
            }
            
        except Exception as e:
            logger.error(f"Error checking model drift: {e}")
            return {
                'drift_detected': False,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _calculate_anomaly_rate_change(self, metrics: Dict[str, Any]) -> float:
        """Calculate change in anomaly rate."""
        anomaly_counts = metrics.get('anomaly_counts', [])
        if len(anomaly_counts) < 20:
            return 0.0
        
        # Compare recent vs older anomaly rates
        recent_rate = np.mean(anomaly_counts[-10:])
        older_rate = np.mean(anomaly_counts[-20:-10])
        
        if older_rate == 0:
            return 0.0
        
        return abs(recent_rate - older_rate) / older_rate
    
    def _calculate_score_distribution_change(self, metrics: Dict[str, Any]) -> float:
        """Calculate change in anomaly score distribution."""
        scores = metrics.get('anomaly_scores', [])
        if len(scores) < 20:
            return 0.0
        
        # Compare recent vs older score distributions
        recent_scores = scores[-10:]
        older_scores = scores[-20:-10]
        
        recent_mean = np.mean(recent_scores)
        older_mean = np.mean(older_scores)
        
        if older_mean == 0:
            return 0.0
        
        return abs(recent_mean - older_mean) / older_mean
    
    def _calculate_inference_time_change(self, metrics: Dict[str, Any]) -> float:
        """Calculate change in inference time."""
        times = metrics.get('inference_times', [])
        if len(times) < 20:
            return 0.0
        
        # Compare recent vs older inference times
        recent_times = times[-10:]
        older_times = times[-20:-10]
        
        recent_mean = np.mean(recent_times)
        older_mean = np.mean(older_times)
        
        if older_mean == 0:
            return 0.0
        
        return abs(recent_mean - older_mean) / older_mean
    
    def _load_performance_metrics(self) -> Dict[str, Any]:
        """Load performance metrics from file."""
        if self.performance_file.exists():
            with open(self.performance_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_performance_metrics(self, metrics: Dict[str, Any]) -> None:
        """Save performance metrics to file."""
        with open(self.performance_file, 'w') as f:
            json.dump(metrics, f, indent=2)
    
    async def get_performance_summary(self, model_version: str) -> Dict[str, Any]:
        """Get performance summary for a model version."""
        try:
            metrics = self._load_performance_metrics()
            
            if model_version not in metrics:
                return {
                    'model_version': model_version,
                    'total_inferences': 0,
                    'last_updated': None,
                    'performance_metrics': {}
                }
            
            model_metrics = metrics[model_version]
            
            # Calculate performance statistics
            inference_times = model_metrics.get('inference_times', [])
            anomaly_scores = model_metrics.get('anomaly_scores', [])
            anomaly_counts = model_metrics.get('anomaly_counts', [])
            
            performance_metrics = {
                'total_inferences': model_metrics['total_inferences'],
                'avg_inference_time': np.mean(inference_times) if inference_times else 0,
                'max_inference_time': np.max(inference_times) if inference_times else 0,
                'min_inference_time': np.min(inference_times) if inference_times else 0,
                'avg_anomaly_score': np.mean(anomaly_scores) if anomaly_scores else 0,
                'anomaly_rate': np.mean(anomaly_counts) if anomaly_counts else 0,
                'total_anomalies': sum(anomaly_counts)
            }
            
            return {
                'model_version': model_version,
                'total_inferences': model_metrics['total_inferences'],
                'last_updated': model_metrics['last_updated'],
                'performance_metrics': performance_metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {
                'model_version': model_version,
                'error': str(e)
            }
    
    async def get_all_model_performance(self) -> List[Dict[str, Any]]:
        """Get performance summary for all models."""
        try:
            metrics = self._load_performance_metrics()
            summaries = []
            
            for model_version in metrics.keys():
                summary = await self.get_performance_summary(model_version)
                summaries.append(summary)
            
            # Sort by total inferences (most active first)
            summaries.sort(key=lambda x: x.get('total_inferences', 0), reverse=True)
            return summaries
            
        except Exception as e:
            logger.error(f"Error getting all model performance: {e}")
            return []
    
    async def cleanup_old_metrics(self, days_to_keep: int = 30):
        """Clean up old performance metrics."""
        try:
            metrics = self._load_performance_metrics()
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            cleaned_metrics = {}
            for model_version, model_metrics in metrics.items():
                last_updated = datetime.fromisoformat(model_metrics['last_updated'])
                if last_updated > cutoff_date:
                    cleaned_metrics[model_version] = model_metrics
            
            self._save_performance_metrics(cleaned_metrics)
            logger.info(f"Cleaned up performance metrics, kept {len(cleaned_metrics)} models")
            
        except Exception as e:
            logger.error(f"Error cleaning up performance metrics: {e}")
    
    async def generate_performance_report(self, model_version: str) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        try:
            # Get performance summary
            summary = await self.get_performance_summary(model_version)
            
            # Check for drift
            drift_result = await self.check_model_drift(model_version)
            
            # Generate report
            report = {
                'model_version': model_version,
                'report_timestamp': datetime.now().isoformat(),
                'performance_summary': summary,
                'drift_analysis': drift_result,
                'recommendations': self._generate_performance_recommendations(summary, drift_result)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {
                'model_version': model_version,
                'report_timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _generate_performance_recommendations(self, summary: Dict[str, Any], 
                                            drift_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on performance analysis."""
        recommendations = []
        
        # Performance-based recommendations
        if summary.get('total_inferences', 0) < 100:
            recommendations.append("Limited inference data - collect more data for reliable analysis")
        
        avg_inference_time = summary.get('performance_metrics', {}).get('avg_inference_time', 0)
        if avg_inference_time > 1.0:  # More than 1 second
            recommendations.append("High inference time detected - consider model optimization")
        
        anomaly_rate = summary.get('performance_metrics', {}).get('anomaly_rate', 0)
        if anomaly_rate > 0.3:  # More than 30% anomalies
            recommendations.append("High anomaly rate - consider threshold adjustment or model retraining")
        
        # Drift-based recommendations
        if drift_result.get('drift_detected', False):
            recommendations.append("Model drift detected - consider retraining with recent data")
        
        drift_score = drift_result.get('drift_score', 0)
        if drift_score > 0.5:
            recommendations.append("Significant drift indicators - monitor closely and prepare for retraining")
        
        return recommendations 