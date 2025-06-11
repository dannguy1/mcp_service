import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

class BaseMonitor:
    """Base class for all monitoring components."""
    
    def __init__(self, name: str):
        """Initialize the base monitor.
        
        Args:
            name: Name of the monitor for logging and metrics
        """
        self.name = name
        self.registry = CollectorRegistry()
        self.metrics: Dict[str, Any] = {}
        self._last_check = datetime.utcnow()
    
    def _create_counter(self, name: str, description: str, labels: Optional[List[str]] = None) -> Counter:
        """Create a Prometheus counter metric.
        
        Args:
            name: Metric name
            description: Metric description
            labels: Optional list of label names
            
        Returns:
            Counter metric
        """
        metric_name = f"{self.name}_{name}"
        if labels:
            return Counter(metric_name, description, labels, registry=self.registry)
        return Counter(metric_name, description, registry=self.registry)
    
    def _create_gauge(self, name: str, description: str, labels: Optional[List[str]] = None) -> Gauge:
        """Create a Prometheus gauge metric.
        
        Args:
            name: Metric name
            description: Metric description
            labels: Optional list of label names
            
        Returns:
            Gauge metric
        """
        metric_name = f"{self.name}_{name}"
        if labels:
            return Gauge(metric_name, description, labels, registry=self.registry)
        return Gauge(metric_name, description, registry=self.registry)
    
    def _create_histogram(self, name: str, description: str, buckets: List[float],
                         labels: Optional[List[str]] = None) -> Histogram:
        """Create a Prometheus histogram metric.
        
        Args:
            name: Metric name
            description: Metric description
            buckets: List of bucket boundaries
            labels: Optional list of label names
            
        Returns:
            Histogram metric
        """
        metric_name = f"{self.name}_{name}"
        if labels:
            return Histogram(metric_name, description, buckets=buckets, labels=labels, registry=self.registry)
        return Histogram(metric_name, description, buckets=buckets, registry=self.registry)
    
    def _create_alert(self, alert_type: str, severity: str, message: str) -> Dict[str, Any]:
        """Create an alert dictionary.
        
        Args:
            alert_type: Type of alert
            severity: Alert severity
            message: Alert message
            
        Returns:
            Alert dictionary
        """
        if 'alerts_total' in self.metrics:
            self.metrics['alerts_total'].labels(severity=severity).inc()
        
        return {
            'type': alert_type,
            'severity': severity,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics from the registry.
        
        Returns:
            Dictionary of metric names and values
        """
        metrics = {}
        for metric in self.registry.collect():
            for sample in metric.samples:
                metrics[sample.name] = sample.value
        return metrics 