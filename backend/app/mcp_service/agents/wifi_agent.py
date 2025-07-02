import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import os

from .ml_based_agent import MLBasedAgent
from app.components.feature_extractor import FeatureExtractor
from ..components.anomaly_classifier import AnomalyClassifier

class WiFiAgent(MLBasedAgent):
    def __init__(self, config, data_service, model_manager=None):
        """Initialize the WiFi agent."""
        # Store config before calling parent init
        self.original_config = config
        self.model_path = config.get('model_path')
        
        # Call parent init but skip model loading
        super().__init__(config, data_service, model_manager)
        
        # Override the model loading with WiFiAgent's specific method
        self.feature_extractor = FeatureExtractor()
        self.classifier = AnomalyClassifier()
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
        self.model_manager = model_manager  # Use provided instance
        self.model = None
        self.scaler = None
        
        # Now load the model using WiFiAgent's method
        # Clear any model that might have been set by parent
        self.model = None
        self.logger.info(f"[DEBUG] WiFiAgent.__init__() - About to call _load_model()")
        self._load_model()
        self.logger.info(f"[DEBUG] WiFiAgent.__init__() - After _load_model(), model: {self.model}")
        self.logger.info(f"[DEBUG] WiFiAgent.__init__() - Model type: {type(self.model) if self.model else None}")
        self.logger.info(f"[DEBUG] WiFiAgent.__init__() - Model is valid: {self._is_valid_model(self.model) if self.model else False}")

    def _load_model_from_directory(self, model_dir: str):
        """Load model and scaler from a directory containing model files."""
        try:
            self.logger.info(f"[DEBUG] _load_model_from_directory called with: {model_dir}")
            
            # Check if the path is a directory
            if not os.path.isdir(model_dir):
                self.logger.warning(f"Model path {model_dir} is not a directory")
                return False
            
            # Look for model files
            model_file = os.path.join(model_dir, 'model.joblib')
            scaler_file = os.path.join(model_dir, 'scaler.joblib')
            metadata_file = os.path.join(model_dir, 'metadata.json')
            
            self.logger.info(f"[DEBUG] Looking for model file: {model_file}")
            self.logger.info(f"[DEBUG] Looking for scaler file: {scaler_file}")
            self.logger.info(f"[DEBUG] Looking for metadata file: {metadata_file}")
            
            # Load model
            if os.path.exists(model_file):
                try:
                    import joblib
                    self.logger.info(f"[DEBUG] Loading model from {model_file}")
                    self.model = joblib.load(model_file)
                    self.logger.info(f"Loaded model from {model_file}")
                    self.logger.info(f"[DEBUG] Model type: {type(self.model)}")
                    self.logger.info(f"[DEBUG] Model has predict: {hasattr(self.model, 'predict')}")
                except Exception as e:
                    self.logger.error(f"Error loading model from {model_file}: {e}")
                    import traceback
                    self.logger.error(f"Traceback: {traceback.format_exc()}")
                    return False
            else:
                self.logger.warning(f"Model file not found at {model_file}")
                return False
            
            # Load scaler
            if os.path.exists(scaler_file):
                try:
                    import joblib
                    self.logger.info(f"[DEBUG] Loading scaler from {scaler_file}")
                    self.scaler = joblib.load(scaler_file)
                    self.logger.info(f"Loaded scaler from {scaler_file}")
                except Exception as e:
                    self.logger.error(f"Error loading scaler from {scaler_file}: {e}")
                    # Continue without scaler if it fails to load
                    self.scaler = None
            
            # Load metadata for additional info
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    self.logger.info(f"Loaded metadata from {metadata_file}")
                    # Store metadata for reference
                    self.model_metadata = metadata
                except Exception as e:
                    self.logger.warning(f"Error loading metadata from {metadata_file}: {e}")
            
            self.logger.info(f"[DEBUG] _load_model_from_directory completed successfully")
            self.logger.info(f"[DEBUG] Final model: {self.model}")
            self.logger.info(f"[DEBUG] Final model type: {type(self.model)}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading model from directory {model_dir}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _load_model(self):
        """Load the ML model from the specified path (file or directory)."""
        try:
            import os
            import joblib
            model_path = self.model_path
            self.logger.info(f"[DEBUG] Attempting to load model from: {model_path}")
            if os.path.isdir(model_path):
                model_file = os.path.join(model_path, 'model.joblib')
                self.logger.info(f"[DEBUG] model_path is a directory, looking for: {model_file}")
                if os.path.exists(model_file):
                    self.model = joblib.load(model_file)
                    self.logger.info(f"[DEBUG] Loaded model from directory: {model_file}")
                else:
                    self.logger.warning(f"[DEBUG] No model.joblib found in directory: {model_path}")
                    self._create_default_model()
                    return
            elif os.path.isfile(model_path):
                self.logger.info(f"[DEBUG] model_path is a file, loading directly: {model_path}")
                self.model = joblib.load(model_path)
                self.logger.info(f"[DEBUG] Loaded model from file: {model_path}")
            else:
                self.logger.warning(f"[DEBUG] Model path does not exist: {model_path}")
                self._create_default_model()
                return
            self.logger.info(f"[DEBUG] Model type: {type(self.model)}")
            self.logger.info(f"[DEBUG] Model has predict: {hasattr(self.model, 'predict')}")
            self.classifier.set_model(self.model)
        except Exception as e:
            self.logger.error(f"[DEBUG] Error loading model from {self.model_path}: {e}")
            self._create_default_model()

    def _create_default_model(self):
        """Create a default model when no model file is available."""
        try:
            # Try to create a simple IsolationForest model as fallback
            from sklearn.ensemble import IsolationForest
            self.model = IsolationForest(contamination=0.1, random_state=42)
            self.logger.info("Created IsolationForest default model for WiFiAgent")
        except ImportError:
            # Fallback to dictionary-based model if sklearn is not available
            self.model = {
                'type': f'{self.agent_id}_anomaly',
                'version': '1.0.0',
                'thresholds': getattr(self, 'thresholds', {}) or {
                    'auth_failures': 5,
                    'deauth_count': 10,
                    'beacon_count': 100
                }
            }
            self.logger.info("Created dictionary-based default model for WiFiAgent")
        
        self.classifier.set_model(self.model)

    def _is_valid_model(self, model):
        """Check if the model is valid (has predict method or is a dictionary-based model)."""
        if model is None:
            return False
        if hasattr(model, 'predict'):
            return True
        elif isinstance(model, dict):
            # Any dictionary can be considered a valid model for rule-based detection
            return True
        return False

    def reload_model(self):
        """Reload the model from the main ModelManager or directory."""
        try:
            # Try to get the model from the main ModelManager first
            if self.model_manager and hasattr(self.model_manager, 'current_model') and self.model_manager.current_model:
                self.logger.info(f"[DEBUG] Reloading model from main ModelManager")
                self.model = self.model_manager.current_model
                self.logger.info(f"[DEBUG] Model type: {type(self.model)}")
                self.logger.info(f"[DEBUG] Model has predict: {hasattr(self.model, 'predict')}")
                self.classifier.set_model(self.model)
                return True
            else:
                # Fallback to loading from directory
                self.logger.info(f"[DEBUG] Main ModelManager has no model, loading from directory")
                self._load_model()
                return self.model is not None and self._is_valid_model(self.model)
        except Exception as e:
            self.logger.error(f"[DEBUG] Error reloading model: {e}")
            return False

    async def start(self):
        """Start the WiFi agent."""
        # Ensure we have a valid model before starting
        if not self.model or not self._is_valid_model(self.model):
            self.logger.info(f"[DEBUG] No valid model loaded, trying to load from directory")
            self._load_model()
        
        # Check if we have a valid model before starting
        if not self.model or not self._is_valid_model(self.model):
            self.status = "inactive"
            self.is_running = False
            self.logger.warning(f"[DEBUG] WiFiAgent inactive: No valid model loaded.")
            # Update status in ModelManager
            if self.model_manager:
                self.model_manager._update_model_status(self.model_id, {
                    'id': self.model_id,
                    'name': self.__class__.__name__,
                    'status': 'inactive',
                    'is_running': False,
                    'last_run': datetime.now().isoformat(),
                    'capabilities': self.capabilities,
                    'description': self.description,
                    'model_loaded': False,
                    'reason': 'No valid model loaded'
                })
            return
        
        # Call parent start method (which will handle the actual starting logic)
        await super().start()
        
        # Set the agent as running and active (only if we have a valid model)
        self.is_running = True
        self.status = 'active'
        self.last_run = datetime.now()
        
        # Update status in ModelManager
        if self.model_manager:
            self.model_manager._update_model_status(self.model_id, {
                'id': self.model_id,
                'name': self.__class__.__name__,
                'status': 'active',
                'is_running': True,
                'last_run': self.last_run.isoformat(),
                'capabilities': self.capabilities,
                'description': self.description,
                'model_loaded': True
            })
        
        self.logger.info("WiFi agent started successfully")

    async def stop(self, unregister=True):
        """Stop the WiFi agent.
        
        Args:
            unregister: Whether to unregister the agent from the registry
        """
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
            cycle_start_time = datetime.now()
            
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
            features = self.feature_extractor.extract_features(logs)
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

            # Calculate cycle statistics
            cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
            
            # Store analysis statistics
            await self._store_analysis_stats({
                'analysis_cycles': 1,
                'logs_processed': len(logs),
                'features_extracted': len(features) if isinstance(features, dict) else 1,
                'anomalies_detected': len(anomalies),
                'cycle_duration_seconds': cycle_duration,
                'last_cycle_timestamp': datetime.now().isoformat(),
                'feature_details': {
                    'auth_failures': features.get('auth_failures', 0),
                    'deauth_count': features.get('deauth_count', 0),
                    'beacon_count': features.get('beacon_count', 0),
                    'unique_mac_count': features.get('unique_mac_count', 0),
                    'unique_ssid_count': features.get('unique_ssid_count', 0)
                },
                'anomaly_types': [anomaly['type'] for anomaly in anomalies],
                'anomaly_severities': [anomaly['severity'] for anomaly in anomalies]
            })

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

    async def _store_analysis_stats(self, new_stats: Dict[str, Any]):
        """Store analysis statistics in Redis with cumulative tracking."""
        try:
            if not self.model_manager or not self.model_manager.redis_client:
                return
            
            # Get existing stats
            stats_key = f"mcp:agent:{self.model_id}:analysis_stats"
            existing_stats = self.model_manager.redis_client.get(stats_key)
            
            if existing_stats:
                current_stats = json.loads(existing_stats)
            else:
                current_stats = {
                    'analysis_cycles': 0,
                    'logs_processed': 0,
                    'features_extracted': 0,
                    'anomalies_detected': 0,
                    'total_cycle_duration': 0,
                    'avg_cycle_duration': 0,
                    'last_cycle_timestamp': None,
                    'feature_totals': {
                        'auth_failures': 0,
                        'deauth_count': 0,
                        'beacon_count': 0,
                        'unique_mac_count': 0,
                        'unique_ssid_count': 0
                    },
                    'anomaly_type_counts': {},
                    'anomaly_severity_counts': {}
                }
            
            # Update cumulative stats
            current_stats['analysis_cycles'] += new_stats['analysis_cycles']
            current_stats['logs_processed'] += new_stats['logs_processed']
            current_stats['features_extracted'] += new_stats['features_extracted']
            current_stats['anomalies_detected'] += new_stats['anomalies_detected']
            current_stats['total_cycle_duration'] += new_stats['cycle_duration_seconds']
            current_stats['avg_cycle_duration'] = current_stats['total_cycle_duration'] / current_stats['analysis_cycles']
            current_stats['last_cycle_timestamp'] = new_stats['last_cycle_timestamp']
            
            # Update feature totals
            for feature, value in new_stats['feature_details'].items():
                if feature in current_stats['feature_totals']:
                    current_stats['feature_totals'][feature] += value
            
            # Update anomaly type counts
            for anomaly_type in new_stats['anomaly_types']:
                current_stats['anomaly_type_counts'][anomaly_type] = current_stats['anomaly_type_counts'].get(anomaly_type, 0) + 1
            
            # Update anomaly severity counts
            for severity in new_stats['anomaly_severities']:
                current_stats['anomaly_severity_counts'][str(severity)] = current_stats['anomaly_severity_counts'].get(str(severity), 0) + 1
            
            # Store updated stats
            self.model_manager.redis_client.set(
                stats_key,
                json.dumps(current_stats),
                ex=86400  # Expire after 24 hours
            )
            
        except Exception as e:
            self.logger.error(f"Error storing analysis stats: {e}")

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