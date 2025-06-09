import logging
import os
import psutil
from datetime import datetime
from typing import Dict, List, Any, Optional

from prometheus_client import Gauge, Counter

from config import settings

logger = logging.getLogger(__name__)

# Prometheus metrics
CPU_USAGE = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('system_memory_usage_percent', 'Memory usage percentage')
DISK_USAGE = Gauge('system_disk_usage_percent', 'Disk usage percentage')
NETWORK_IO = Gauge('system_network_io_bytes', 'Network I/O in bytes', ['direction'])
ALERT_COUNTER = Counter('system_alerts_total', 'Number of system alerts', ['severity'])

class ResourceMonitor:
    """Component for monitoring system resources and generating alerts."""
    
    def __init__(self):
        self._thresholds = {
            'cpu': 80.0,      # 80% CPU usage
            'memory': 85.0,   # 85% memory usage
            'disk': 90.0,     # 90% disk usage
            'network': 1000000  # 1MB/s network I/O
        }
        
        self._last_network_io = {
            'bytes_sent': 0,
            'bytes_recv': 0
        }
        self._last_check = datetime.utcnow()
    
    def check_resources(self) -> Dict[str, float]:
        """Check current system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            DISK_USAGE.set(disk.percent)
            
            # Network I/O
            net_io = psutil.net_io_counters()
            current_time = datetime.utcnow()
            time_diff = (current_time - self._last_check).total_seconds()
            
            if time_diff > 0:
                bytes_sent_rate = (net_io.bytes_sent - self._last_network_io['bytes_sent']) / time_diff
                bytes_recv_rate = (net_io.bytes_recv - self._last_network_io['bytes_recv']) / time_diff
                
                NETWORK_IO.labels(direction='sent').set(bytes_sent_rate)
                NETWORK_IO.labels(direction='received').set(bytes_recv_rate)
            
            self._last_network_io = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv
            }
            self._last_check = current_time
            
            return {
                'cpu': cpu_percent,
                'memory': memory.percent,
                'disk': disk.percent,
                'network_sent': bytes_sent_rate if time_diff > 0 else 0,
                'network_recv': bytes_recv_rate if time_diff > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return {}
    
    def check_alerts(self, resources: Dict[str, float]) -> List[Dict[str, Any]]:
        """Check if any resource usage exceeds thresholds."""
        alerts = []
        
        # CPU alert
        if resources.get('cpu', 0) > self._thresholds['cpu']:
            alerts.append(self._create_alert(
                'high_cpu_usage',
                'critical',
                f"CPU usage is {resources['cpu']:.1f}% (threshold: {self._thresholds['cpu']}%)"
            ))
        
        # Memory alert
        if resources.get('memory', 0) > self._thresholds['memory']:
            alerts.append(self._create_alert(
                'high_memory_usage',
                'critical',
                f"Memory usage is {resources['memory']:.1f}% (threshold: {self._thresholds['memory']}%)"
            ))
        
        # Disk alert
        if resources.get('disk', 0) > self._thresholds['disk']:
            alerts.append(self._create_alert(
                'high_disk_usage',
                'warning',
                f"Disk usage is {resources['disk']:.1f}% (threshold: {self._thresholds['disk']}%)"
            ))
        
        # Network alert
        network_sent = resources.get('network_sent', 0)
        network_recv = resources.get('network_recv', 0)
        if network_sent > self._thresholds['network'] or network_recv > self._thresholds['network']:
            alerts.append(self._create_alert(
                'high_network_io',
                'warning',
                f"Network I/O is high (sent: {network_sent:.0f} B/s, recv: {network_recv:.0f} B/s)"
            ))
        
        return alerts
    
    def _create_alert(self, alert_type: str, severity: str, message: str) -> Dict[str, Any]:
        """Create an alert dictionary."""
        ALERT_COUNTER.labels(severity=severity).inc()
        return {
            'type': alert_type,
            'severity': severity,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_thresholds(self) -> Dict[str, float]:
        """Get current resource thresholds."""
        return self._thresholds.copy()
    
    def set_thresholds(self, thresholds: Dict[str, float]) -> None:
        """Update resource thresholds."""
        for resource, threshold in thresholds.items():
            if resource in self._thresholds and threshold > 0:
                self._thresholds[resource] = threshold
            else:
                logger.warning(f"Invalid threshold for {resource}: {threshold}")
    
    def get_process_info(self) -> Dict[str, Any]:
        """Get information about the current process."""
        process = psutil.Process(os.getpid())
        return {
            'pid': process.pid,
            'cpu_percent': process.cpu_percent(),
            'memory_percent': process.memory_percent(),
            'num_threads': process.num_threads(),
            'create_time': datetime.fromtimestamp(process.create_time()).isoformat()
        } 