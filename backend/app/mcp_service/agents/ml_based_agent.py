import logging
from typing import List, Dict, Any, Optional
import os
from datetime import datetime

from .generic_agent import GenericAgent
from ..components.feature_extractor import FeatureExtractor
from ..components.anomaly_classifier import AnomalyClassifier

class MLBasedAgent(GenericAgent):
    """
    ML-based agent that uses trained models for anomaly detection.
    Based on the current WiFiAgent implementation.
    """
    
    def __init__(self, config: Dict[str, Any], data_service, model_manager=None):
        """
        Initialize the ML-based agent.
        
        Args:
            config: Configuration dictionary containing agent settings
            data_service: DataService instance for database access
            model_manager: ModelManager instance for model handling
        """
        super().__init__(config, data_service, model_manager)
        
        # ML-specific components
        self.feature_extractor = FeatureExtractor()
        self.classifier = AnomalyClassifier()
        self.model = None
        
        # ML-specific configuration
        self.feature_extraction_config = self.analysis_rules.get('feature_extraction', {})
        self.thresholds = self.analysis_rules.get('thresholds', {})
        
        # Load model if path is provided
        if self.model_path and os.path.exists(self.model_path):
            self._load_model()
        else:
            self.logger.warning(f"Model file not found at {self.model_path}, using default model")
            self._create_default_model()
    
    def _load_model(self):
        """Load the ML model from the specified path."""
        try:
            if self.model_manager:
                self.model = self.model_manager.load_model(self.model_path)
            else:
                # Fallback to direct loading
                import pickle
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
            
            # Set model in classifier
            self.classifier.set_model(self.model)
            self.logger.info(f"Loaded model from {self.model_path}")
            
        except Exception as e:
            self.logger.error(f"Error loading model from {self.model_path}: {e}")
            self._create_default_model()
    
    def _create_default_model(self):
        """Create a default model when no model file is available."""
        self.model = {
            'type': f'{self.agent_id}_anomaly',
            'version': '1.0.0',
            'thresholds': self.thresholds or {
                'auth_failures': 5,
                'deauth_count': 10,
                'beacon_count': 100
            }
        }
        self.classifier.set_model(self.model)
        self.logger.info("Created default model")
    
    async def _perform_analysis(self, logs: List[Dict[str, Any]]):
        """
        Perform ML-based analysis on logs.
        
        Args:
            logs: List of log entries to analyze
        """
        try:
            # Check if model is available before analysis
            if not self.model or not hasattr(self.model, 'predict'):
                self.logger.warning(f"Skipping analysis for {self.agent_name}: No valid model loaded.")
                self.status = "inactive"
                # Update status in Redis
                self._update_redis_status({
                    'id': self.agent_id,
                    'name': self.agent_name,
                    'status': 'inactive',
                    'is_running': True,
                    'last_run': datetime.now().isoformat(),
                    'capabilities': self.capabilities,
                    'description': self.description,
                    'agent_type': self.agent_type,
                    'model_loaded': False,
                    'reason': 'No valid model loaded'
                })
                return
            
            # Extract features from logs
            features = await self.feature_extractor.extract_features(logs)
            self.logger.info("Extracted features from logs")
            
            # Detect anomalies using the classifier
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
            
            # Log analysis summary
            if anomalies:
                self.logger.info(f"Analysis completed: {len(anomalies)} anomalies detected")
            else:
                self.logger.info("Analysis completed: No anomalies detected")
                
        except Exception as e:
            self.logger.error(f"Error in ML-based analysis: {e}")
            raise
    
    async def start(self):
        """Start the ML-based agent."""
        try:
            # Validate model availability before starting
            if not self.model or not hasattr(self.model, 'predict'):
                self.status = "inactive"
                self.logger.warning(f"MLBasedAgent {self.agent_name} inactive: No valid model loaded.")
                # Update status in Redis to reflect inactive state
                self._update_redis_status({
                    'id': self.agent_id,
                    'name': self.agent_name,
                    'status': 'inactive',
                    'is_running': False,
                    'last_run': datetime.now().isoformat(),
                    'capabilities': self.capabilities,
                    'description': self.description,
                    'agent_type': self.agent_type,
                    'model_loaded': False,
                    'reason': 'No valid model loaded'
                })
                return
            
            # Start the generic agent
            await super().start()
            
            # Register with ModelManager if available
            if self.model_manager and self.model_path:
                if not self.model_manager.register_model(self, self.agent_id):
                    self.logger.warning("Failed to register model with ModelManager")
            
            self.logger.info(f"{self.agent_name} ML-based agent started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start ML-based agent: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            dict: Model information
        """
        if not self.model:
            return {
                'model_loaded': False,
                'model_path': self.model_path,
                'error': 'No model loaded'
            }
        
        return {
            'model_path': self.model_path,
            'model_type': self.model.get('type', 'unknown'),
            'model_version': self.model.get('version', 'unknown'),
            'thresholds': self.model.get('thresholds', {}),
            'is_loaded': self.model is not None,
            'model_loaded': bool(self.model and hasattr(self.model, 'predict'))
        }
    
    def update_model(self, new_model_path: str):
        """
        Update the model with a new model file.
        
        Args:
            new_model_path: Path to the new model file
        """
        try:
            self.model_path = new_model_path
            self._load_model()
            self.logger.info(f"Updated model to {new_model_path}")
        except Exception as e:
            self.logger.error(f"Error updating model: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the ML-based agent.
        
        Returns:
            dict: Dictionary containing agent status information
        """
        status = super().get_status()
        
        # Check if model is loaded
        model_loaded = bool(self.model and hasattr(self.model, 'predict'))
        
        # If no model is loaded, set status to inactive
        if not model_loaded:
            status['status'] = 'inactive'
            status['reason'] = 'No valid model loaded'
        
        status.update({
            'model_info': self.get_model_info(),
            'feature_extraction_config': self.feature_extraction_config,
            'thresholds': self.thresholds,
            'model_loaded': model_loaded
        })
        return status 