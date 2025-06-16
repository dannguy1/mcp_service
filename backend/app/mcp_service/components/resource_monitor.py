import logging
import psutil

logger = logging.getLogger(__name__)

class ResourceMonitor:
    def __init__(self):
        self.cpu_threshold = 80  # 80% CPU usage threshold
        self.memory_threshold = 80  # 80% memory usage threshold

    def check_resources(self) -> bool:
        """Check if system resources are within acceptable limits."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent

            if cpu_percent > self.cpu_threshold:
                logger.warning(f"CPU usage too high: {cpu_percent}%")
                return False

            if memory_percent > self.memory_threshold:
                logger.warning(f"Memory usage too high: {memory_percent}%")
                return False

            return True
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return False

    def is_running(self) -> bool:
        """Check if the resource monitor is running."""
        return True  # ResourceMonitor is always running as it's a passive monitor 