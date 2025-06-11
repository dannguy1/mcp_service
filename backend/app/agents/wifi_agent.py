import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import os

from .base_agent import BaseAgent
from ..components.feature_extractor import FeatureExtractor
from ..components.model_manager import ModelManager
from ..components.anomaly_classifier import AnomalyClassifier

class WiFiAgent(BaseAgent):
    def __init__(self, config, data_service):
        """Initialize the WiFi agent."""
        super().__init__(config, data_service)
        self.feature_extractor = FeatureExtractor()
        self.model_manager = ModelManager()
        self.classifier = AnomalyClassifier()
        self.model_path = os.path.join(config.model_dir, 'wifi_anomaly_model.pkl')
        self.programs = ['hostapd', 'wpa_supplicant']

    async def start(self):
        """Start the WiFi agent."""
        try:
            # Load the model
            self.model = await self.model_manager.load_model(self.model_path)
            self.logger.info("Loaded WiFi anomaly detection model")
            
            # Initialize classifier
            self.classifier.set_model(self.model)
            self.logger.info("Initialized anomaly classifier")
            
            self.is_running = True
            self.logger.info("WiFi agent started")
            
        except Exception as e:
            self.logger.error(f"Failed to start WiFi agent: {e}")
            raise

    async def stop(self):
        """Stop the WiFi agent."""
        try:
            self.is_running = False
            self.logger.info("WiFi agent stopped")
        except Exception as e:
            self.logger.error(f"Error stopping WiFi agent: {e}")

    async def run_analysis_cycle(self):
        """Run a single analysis cycle for WiFi anomaly detection."""
        if not self.should_run():
            self.logger.debug("Skipping analysis cycle - too soon since last run")
            return

        try:
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
            
            self.update_last_run()
            self.logger.info(f"Completed analysis cycle - found {len(anomalies)} anomalies")
            
        except Exception as e:
            self.logger.error(f"Error in analysis cycle: {e}")
            raise

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