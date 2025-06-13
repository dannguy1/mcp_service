from abc import ABC, abstractmethod
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class BaseAgent(ABC):
    def __init__(self, config, data_service):
        """
        Initialize the base agent.
        
        Args:
            config: Configuration object
            data_service: DataService instance for database access
        """
        self.config = config
        self.data_service = data_service
        self.logger = logging.getLogger(self.__class__.__name__)
        self.last_run = None
        self.is_running = False
        self.description = "Base agent class"
        self.capabilities: List[str] = []
        self.status = "initialized"

    @abstractmethod
    async def start(self):
        """Start the agent and perform any necessary initialization."""
        pass

    @abstractmethod
    async def stop(self):
        """Stop the agent and perform any necessary cleanup."""
        pass

    @abstractmethod
    async def run_analysis_cycle(self):
        """
        Run a single analysis cycle.
        
        This method should:
        1. Fetch relevant logs
        2. Process the logs
        3. Detect anomalies
        4. Store anomalies
        5. Send notifications if needed
        """
        pass

    async def store_anomaly(
        self,
        anomaly_type: str,
        severity: int,
        confidence: float,
        description: str,
        features: Dict[str, Any],
        device_id: Optional[int] = None
    ):
        """
        Store an anomaly in the database.
        
        Args:
            anomaly_type: Type of anomaly (e.g., 'wifi_auth_failure')
            severity: Severity level (1-5)
            confidence: Confidence score (0-1)
            description: Human-readable description
            features: Dictionary of features used for detection
            device_id: Optional device ID
        """
        try:
            anomaly = {
                "agent_name": self.__class__.__name__,
                "device_id": device_id,
                "timestamp": datetime.now().isoformat(),
                "anomaly_type": anomaly_type,
                "severity": severity,
                "confidence": confidence,
                "description": description,
                "features": features
            }
            
            await self.data_service.store_anomaly(anomaly)
            self.logger.info(f"Stored anomaly: {anomaly_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to store anomaly: {e}")
            raise

    def should_run(self) -> bool:
        """
        Check if the agent should run based on the last run time.
        
        Returns:
            bool: True if the agent should run, False otherwise
        """
        if not self.last_run:
            return True
            
        time_since_last_run = datetime.now() - self.last_run
        return time_since_last_run >= timedelta(seconds=self.config.analysis_interval)

    def update_last_run(self):
        """Update the last run timestamp."""
        self.last_run = datetime.now()

    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.
        
        Returns:
            dict: Dictionary containing agent status information
        """
        return {
            "name": self.__class__.__name__,
            "is_running": self.is_running,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": (
                (self.last_run + timedelta(seconds=self.config.analysis_interval)).isoformat()
                if self.last_run
                else None
            ),
            "status": self.status,
            "capabilities": self.capabilities,
            "description": self.description
        } 