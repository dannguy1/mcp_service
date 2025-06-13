import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import os

from .base_agent import BaseAgent
from ..components.feature_extractor import FeatureExtractor
from ..components.model_manager import model_manager
from ..components.anomaly_classifier import AnomalyClassifier

class WiFiAgent(BaseAgent):
    def __init__(self, config, data_service):
        """Initialize the WiFi agent."""
        super().__init__(config, data_service)
        self.feature_extractor = FeatureExtractor()
        self.classifier = AnomalyClassifier()
        self.model_path = os.path.join(config.model_dir, 'wifi_anomaly_model.pkl')
        self.programs = ['hostapd', 'wpa_supplicant']
        self.description = "WiFi anomaly detection agent"
        self.capabilities = [
            "Authentication failure detection",
            "Deauthentication flood detection",
            "Beacon frame flood detection"
        ]
        self.status = "initialized"
        self.is_running = False
        self.last_run = None
        self.logger = logging.getLogger(__name__)
        self.model_id = "wifi_agent"  # Consistent model identifier

    async def start(self):
        """Start the WiFi agent."""
        try:
            # Load the model
            self.model = await model_manager.load_model(self.model_path)
            self.logger.info("Loaded WiFi anomaly detection model")
            
            # Initialize classifier
            self.classifier.set_model(self.model)
            self.logger.info("Initialized anomaly classifier")
            
            # Register with model manager using consistent model_id
            model_manager.register_model(self, model_id=self.model_id)
            
            self.is_running = True
            self.status = "running"
            self.logger.info("WiFi agent started")
            
        except Exception as e:
            self.logger.error(f"Failed to start WiFi agent: {e}")
            self.status = "error"
            self.is_running = False
            raise

    async def stop(self):
        """Stop the WiFi agent."""
        try:
            self.is_running = False
            self.status = "stopped"
            self.logger.info("WiFi agent stopped")
        except Exception as e:
            self.logger.error(f"Error stopping WiFi agent: {e}")
            self.status = "error"
            raise

    async def run_analysis_cycle(self):
        """Run one analysis cycle."""
        try:
            if not self.is_running:
                self.logger.warning("Agent is not running, skipping analysis cycle")
                return

            self.status = "analyzing"
            self.logger.info("Starting analysis cycle")
            
            # Calculate time range for log retrieval
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=5)
            
            # Fetch logs
            logs = await self.data_service.get_logs_by_program(
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                programs=self.programs
            )
            
            if not logs:
                self.logger.debug("No logs found in time range")
                return
                
            # Extract features
            features = self.feature_extractor.extract_wifi_features(logs)
            
            # Detect anomalies
            anomalies = self.classifier.detect_anomalies(features)
            
            # Store anomalies
            for anomaly in anomalies:
                await self.store_anomaly(
                    anomaly_type=anomaly['type'],
                    severity=anomaly['severity'],
                    confidence=anomaly['confidence'],
                    description=anomaly['description'],
                    features=anomaly['features'],
                    device_id=anomaly.get('device_id')
                )
            
            self.last_run = datetime.now()
            self.status = "running"
            self.logger.info("Analysis cycle completed")
            
        except Exception as e:
            self.logger.error(f"Error in analysis cycle: {e}")
            self.status = "error"
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the agent."""
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

    def _get_anomaly_description(self, anomaly_type: str, features: Dict[str, Any]) -> str:
        """Generate a human-readable description for an anomaly."""
        if anomaly_type == 'auth_failure':
            return (
                f"Multiple authentication failures detected "
                f"({features.get('auth_failures', 0)} failures in 5 minutes)"
            )
        elif anomaly_type == 'deauth_flood':
            return (
                f"Deauthentication flood detected "
                f"({features.get('deauth_count', 0)} deauth frames in 5 minutes)"
            )
        elif anomaly_type == 'beacon_flood':
            return (
                f"Beacon frame flood detected "
                f"({features.get('beacon_count', 0)} beacon frames in 5 minutes)"
            )
        else:
            return f"Unknown anomaly type: {anomaly_type}" 