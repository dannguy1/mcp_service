import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import os

from .base_agent import BaseAgent
from ..components.feature_extractor import FeatureExtractor
from ..components.model_manager import model_manager as global_model_manager
from ..components.anomaly_classifier import AnomalyClassifier

class WiFiAgent(BaseAgent):
    def __init__(self, config, data_service, model_manager=None):
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
        self.model_manager = model_manager or global_model_manager  # Use provided instance or global singleton

    async def start(self):
        """Start the WiFi agent."""
        try:
            # Load model
            model_path = os.path.join(self.config.model_dir, 'wifi_anomaly_model.pkl')
            if not os.path.exists(model_path):
                self.logger.warning(f"Model file not found at {model_path}, using default model")
                self.model = {
                    'type': 'wifi_anomaly',
                    'version': '1.0.0',
                    'thresholds': {
                        'auth_failures': 5,
                        'deauth_count': 10,
                        'beacon_count': 100
                    }
                }
            else:
                self.model = self.model_manager.load_model(model_path)
            self.logger.info("Loaded WiFi anomaly detection model")
            
            # Initialize classifier and set model
            self.classifier = AnomalyClassifier()
            self.classifier.set_model(self.model)
            self.logger.info("Initialized anomaly classifier")
            
            # Register with ModelManager
            if not self.model_manager.register_model(self, self.model_id):
                raise Exception("Failed to register model")
            
            # Set running state
            self.is_running = True
            self.status = 'active'
            self.last_run = datetime.now()
            
            # Update status in Redis
            self.model_manager._update_model_status(self.model_id, {
                'id': self.model_id,
                'name': self.__class__.__name__,
                'status': 'active',
                'is_running': True,
                'last_run': self.last_run.isoformat(),
                'capabilities': self.capabilities,
                'description': self.description
            })
            
            self.logger.info("WiFi agent started")
            
        except Exception as e:
            self.logger.error(f"Failed to start WiFi agent: {e}")
            self.status = 'error'
            # Update status in Redis
            if self.model_manager:
                self.model_manager._update_model_status(self.model_id, {
                    'id': self.model_id,
                    'name': self.__class__.__name__,
                    'status': 'error',
                    'is_running': False,
                    'last_run': datetime.now().isoformat(),
                    'capabilities': self.capabilities,
                    'description': self.description
                })
            raise

    async def stop(self):
        """Stop the WiFi agent."""
        try:
            self.logger.info("Stopping WiFi agent...")
            
            # Stop the agent
            self.is_running = False
            self.status = 'inactive'
            self.last_run = datetime.now()
            
            # Update model status in ModelManager
            if self.model_manager:
                self.model_manager._update_model_status(self.model_id, {
                    'id': self.model_id,
                    'name': self.__class__.__name__,
                    'status': 'inactive',
                    'is_running': False,
                    'last_run': self.last_run.isoformat(),
                    'capabilities': self.capabilities,
                    'description': self.description
                })
            
            self.logger.info("WiFi agent stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping WiFi agent: {e}")
            self.status = 'error'
            # Update status in Redis
            if self.model_manager:
                self.model_manager._update_model_status(self.model_id, {
                    'id': self.model_id,
                    'name': self.__class__.__name__,
                    'status': 'error',
                    'is_running': False,
                    'last_run': datetime.now().isoformat(),
                    'capabilities': self.capabilities,
                    'description': self.description
                })
            raise

    async def run_analysis_cycle(self):
        """Run a single analysis cycle."""
        if not self.is_running:
            return

        try:
            self.status = 'analyzing'
            # Update status in Redis
            if self.model_manager:
                self.model_manager._update_model_status(self.model_id, {
                    'id': self.model_id,
                    'name': self.__class__.__name__,
                    'status': 'analyzing',
                    'is_running': True,
                    'last_run': datetime.now().isoformat(),
                    'capabilities': self.capabilities,
                    'description': self.description
                })
            self.logger.info("Starting analysis cycle")

            # Get recent logs
            logs = await self.data_service.get_recent_logs(
                programs=self.programs,
                minutes=5
            )
            self.logger.info(f"Retrieved {len(logs)} logs")

            if not logs:
                self.logger.info("No logs to analyze")
                return

            # Extract features
            features = await self.feature_extractor.extract_features(logs)
            self.logger.info("Extracted features from logs")

            # Detect anomalies
            anomalies = self.classifier.detect_anomalies(features)
            self.logger.info(f"Detected {len(anomalies)} anomalies")

            # Store anomalies
            for anomaly in anomalies:
                await self.store_anomaly(
                    anomaly_type=anomaly['type'],
                    severity=anomaly['severity'],
                    confidence=anomaly['confidence'],
                    description=anomaly['description'],
                    features=anomaly['features']
                )

            self.status = 'active'
            # Update status in Redis
            if self.model_manager:
                self.model_manager._update_model_status(self.model_id, {
                    'id': self.model_id,
                    'name': self.__class__.__name__,
                    'status': 'active',
                    'is_running': True,
                    'last_run': datetime.now().isoformat(),
                    'capabilities': self.capabilities,
                    'description': self.description
                })
            self.last_run = datetime.now()
            self.logger.info("Analysis cycle completed")

        except Exception as e:
            self.logger.error(f"Error in analysis cycle: {e}")
            self.status = 'error'
            # Update status in Redis
            if self.model_manager:
                self.model_manager._update_model_status(self.model_id, {
                    'id': self.model_id,
                    'name': self.__class__.__name__,
                    'status': 'error',
                    'is_running': False,
                    'last_run': datetime.now().isoformat(),
                    'capabilities': self.capabilities,
                    'description': self.description
                })
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

    def is_running(self) -> bool:
        """Check if the agent is running."""
        return self.is_running

    def check_running(self) -> bool:
        """Check if the agent is running."""
        return self.is_running

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