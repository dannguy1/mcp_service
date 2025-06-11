import psutil
import logging

class ResourceMonitor:
    def __init__(self, cpu_threshold=80, memory_threshold=70):
        """
        Initialize the resource monitor.
        
        Args:
            cpu_threshold (int): CPU usage threshold percentage (default: 80)
            memory_threshold (int): Memory usage threshold percentage (default: 70)
        """
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.logger = logging.getLogger("ResourceMonitor")

    def is_healthy(self) -> bool:
        """
        Check if system resources are within healthy limits.
        
        Returns:
            bool: True if resources are healthy, False otherwise
        """
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Log resource usage
            self.logger.debug(
                f"Resource usage - CPU: {cpu_percent}%, Memory: {memory_percent}%"
            )
            
            # Check thresholds
            if cpu_percent > self.cpu_threshold:
                self.logger.warning(
                    f"CPU usage too high: {cpu_percent}% > {self.cpu_threshold}%"
                )
                return False
                
            if memory_percent > self.memory_threshold:
                self.logger.warning(
                    f"Memory usage too high: {memory_percent}% > {self.memory_threshold}%"
                )
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error monitoring resources: {e}")
            return False

    def get_resource_usage(self) -> dict:
        """
        Get current resource usage statistics.
        
        Returns:
            dict: Dictionary containing CPU and memory usage statistics
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "threshold": self.cpu_threshold
                },
                "memory": {
                    "percent": memory.percent,
                    "threshold": self.memory_threshold,
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting resource usage: {e}")
            return {
                "error": str(e)
            } 