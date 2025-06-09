# AnalyzerMCPServer Implementation Plan - Agent

## Overview

This document details the implementation of the agent system components of the AnalyzerMCPServer, including the base agent framework, WiFi agent implementation, and supporting components.

## 1. Base Agent Framework

### 1.1 Base Agent (`agents/base_agent.py`)

```python
from abc import ABC, abstractmethod
import asyncio
import logging
from typing import Optional

class BaseAgent(ABC):
    def __init__(self, data_service, config):
        self.data_service = data_service
        self.config = config
        self.running = False
        self.task: Optional[asyncio.Task] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name."""
        pass
    
    async def start(self):
        """Start the agent."""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._run())
        logging.info(f"{self.name} agent started")
    
    async def stop(self):
        """Stop the agent."""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logging.info(f"{self.name} agent stopped")
    
    async def _run(self):
        """Main agent loop."""
        while self.running:
            try:
                await self.run_analysis_cycle()
                await asyncio.sleep(self.config.service.analysis_interval)
            except Exception as e:
                logging.error(f"Error in {self.name} agent: {str(e)}")
                await asyncio.sleep(5)  # Back off on error
    
    @abstractmethod
    async def run_analysis_cycle(self):
        """Run one analysis cycle."""
        pass
```

## 2. Resource Monitor

### 2.1 Resource Monitor (`components/resource_monitor.py`)

```python
import psutil
import logging
from typing import Dict, Tuple

class ResourceMonitor:
    def __init__(self, cpu_threshold: float = 80.0, memory_threshold: float = 80.0):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
    
    def check_resources(self) -> Tuple[bool, Dict[str, float]]:
        """Check system resource usage."""
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        metrics = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used': memory.used,
            'memory_total': memory.total
        }
        
        # Check thresholds
        if cpu_percent > self.cpu_threshold:
            logging.warning(f"High CPU usage: {cpu_percent}%")
        
        if memory.percent > self.memory_threshold:
            logging.warning(f"High memory usage: {memory.percent}%")
        
        return (
            cpu_percent <= self.cpu_threshold and memory.percent <= self.memory_threshold,
            metrics
        )
```

## 3. WiFi Agent Implementation

### 3.1 Feature Extractor (`components/feature_extractor.py`)

```python
import pandas as pd
import numpy as np
import logging
from typing import Dict, List

class WiFiFeatureExtractor:
    def __init__(self):
        self.required_columns = [
            'timestamp', 'level', 'message',
            'client_mac', 'ap_mac', 'event_type'
        ]
    
    def extract_features(self, logs: List[Dict]) -> Dict[str, float]:
        """Extract features from WiFi logs."""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(logs)
            
            # Check required columns
            missing_cols = set(self.required_columns) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Calculate features
            features = {}
            
            # Error log ratio
            error_logs = df[df['level'].isin(['error', 'critical'])]
            features['error_ratio'] = len(error_logs) / len(df) if len(df) > 0 else 0
            
            # Disassociation events
            disassoc_events = df[df['event_type'] == 'disassociation']
            features['disassoc_rate'] = len(disassoc_events) / len(df) if len(df) > 0 else 0
            
            # Authentication failures
            auth_failures = df[df['event_type'] == 'authentication_failure']
            features['auth_failure_rate'] = len(auth_failures) / len(df) if len(df) > 0 else 0
            
            # Connection attempts
            conn_attempts = df[df['event_type'] == 'connection_attempt']
            features['conn_attempt_rate'] = len(conn_attempts) / len(df) if len(df) > 0 else 0
            
            # Client count
            features['unique_clients'] = df['client_mac'].nunique()
            
            # AP count
            features['unique_aps'] = df['ap_mac'].nunique()
            
            return features
            
        except Exception as e:
            logging.error(f"Error extracting features: {str(e)}")
            raise
```

### 3.2 Model Manager (`components/model_manager.py`)

```python
import joblib
import os
import logging
from typing import Dict, Optional
from datetime import datetime

class WiFiModelManager:
    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.model = None
        self.model_version = None
        self.last_check = None
    
    async def start(self):
        """Start the model manager."""
        await self.load_model()
    
    async def stop(self):
        """Stop the model manager."""
        self.model = None
        self.model_version = None
    
    async def load_model(self):
        """Load the latest model."""
        try:
            # Find latest model
            model_files = [f for f in os.listdir(self.model_dir) if f.endswith('.joblib')]
            if not model_files:
                raise FileNotFoundError("No model files found")
            
            latest_model = max(model_files)
            model_path = os.path.join(self.model_dir, latest_model)
            
            # Load model
            self.model = joblib.load(model_path)
            self.model_version = latest_model.replace('.joblib', '')
            self.last_check = datetime.now()
            
            logging.info(f"Loaded model version: {self.model_version}")
            
        except Exception as e:
            logging.error(f"Error loading model: {str(e)}")
            raise
    
    async def check_for_updates(self) -> bool:
        """Check for model updates."""
        try:
            model_files = [f for f in os.listdir(self.model_dir) if f.endswith('.joblib')]
            if not model_files:
                return False
            
            latest_model = max(model_files)
            if latest_model.replace('.joblib', '') != self.model_version:
                await self.load_model()
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking for updates: {str(e)}")
            return False
    
    def predict(self, features: Dict[str, float]) -> float:
        """Make prediction using the model."""
        if not self.model:
            raise RuntimeError("Model not loaded")
        
        # Convert features to array
        feature_array = np.array([[
            features['error_ratio'],
            features['disassoc_rate'],
            features['auth_failure_rate'],
            features['conn_attempt_rate'],
            features['unique_clients'],
            features['unique_aps']
        ]])
        
        # Make prediction
        return self.model.predict(feature_array)[0]
```

### 3.3 Anomaly Classifier (`components/anomaly_classifier.py`)

```python
from typing import Dict, Optional
import logging

class WiFiAnomalyClassifier:
    def __init__(self, threshold: float = -0.5):
        self.threshold = threshold
    
    def classify(self, prediction: float, features: Dict[str, float]) -> Optional[Dict]:
        """Classify prediction as anomaly."""
        if prediction < self.threshold:
            return {
                'type': 'wifi_anomaly',
                'severity': self._calculate_severity(prediction),
                'description': self._generate_description(prediction, features),
                'details': {
                    'prediction': float(prediction),
                    'features': features
                }
            }
        return None
    
    def _calculate_severity(self, prediction: float) -> int:
        """Calculate anomaly severity (1-5)."""
        if prediction < -0.8:
            return 5
        elif prediction < -0.6:
            return 4
        elif prediction < -0.4:
            return 3
        elif prediction < -0.2:
            return 2
        else:
            return 1
    
    def _generate_description(self, prediction: float, features: Dict[str, float]) -> str:
        """Generate human-readable description."""
        severity = self._calculate_severity(prediction)
        issues = []
        
        if features['error_ratio'] > 0.1:
            issues.append("high error rate")
        if features['disassoc_rate'] > 0.2:
            issues.append("frequent disconnections")
        if features['auth_failure_rate'] > 0.15:
            issues.append("authentication failures")
        
        return f"Severity {severity} WiFi anomaly detected: {', '.join(issues)}"
```

### 3.4 WiFi Agent (`agents/wifi_agent.py`)

```python
import logging
from datetime import datetime, timedelta
from .base_agent import BaseAgent
from components.feature_extractor import WiFiFeatureExtractor
from components.model_manager import WiFiModelManager
from components.anomaly_classifier import WiFiAnomalyClassifier
from components.resource_monitor import ResourceMonitor

class WiFiAgent(BaseAgent):
    def __init__(self, data_service, config):
        super().__init__(data_service, config)
        self.feature_extractor = WiFiFeatureExtractor()
        self.model_manager = WiFiModelManager(config.sftp.remote_path)
        self.anomaly_classifier = WiFiAnomalyClassifier()
        self.resource_monitor = ResourceMonitor()
    
    @property
    def name(self) -> str:
        return "WiFi"
    
    async def start(self):
        """Start the WiFi agent."""
        await self.model_manager.start()
        await super().start()
    
    async def stop(self):
        """Stop the WiFi agent."""
        await self.model_manager.stop()
        await super().stop()
    
    async def run_analysis_cycle(self):
        """Run one analysis cycle."""
        try:
            # Check for model updates
            await self.model_manager.check_for_updates()
            
            # Check system resources
            resources_ok, metrics = self.resource_monitor.check_resources()
            if not resources_ok:
                logging.warning("Skipping analysis due to high resource usage")
                return
            
            # Get logs for last 5 minutes
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=5)
            
            logs = await self.data_service.get_logs(
                start_time.isoformat(),
                end_time.isoformat()
            )
            
            if not logs:
                return
            
            # Extract features
            features = self.feature_extractor.extract_features(logs)
            
            # Make prediction
            prediction = self.model_manager.predict(features)
            
            # Classify anomaly
            anomaly = self.anomaly_classifier.classify(prediction, features)
            
            if anomaly:
                # Add model version
                anomaly['model_version'] = self.model_manager.model_version
                
                # Store anomaly
                await self.data_service.store_anomaly(anomaly)
                
                # Send notification if enabled
                if self.config.notification.enabled:
                    await self._send_notification(anomaly)
            
        except Exception as e:
            logging.error(f"Error in analysis cycle: {str(e)}")
            raise
    
    async def _send_notification(self, anomaly: dict):
        """Send notification about detected anomaly."""
        try:
            # Implementation depends on notification service
            pass
        except Exception as e:
            logging.error(f"Failed to send notification: {str(e)}")
```

## Next Steps

1. Review the [Training Implementation](AnalyzerMCPServer-IP-Training.md) for model management
2. Check the [Testing Implementation](AnalyzerMCPServer-IP-Testing.md) for testing procedures
3. Follow the [Deployment Guide](AnalyzerMCPServer-IP-Deployment.md) for setup instructions 