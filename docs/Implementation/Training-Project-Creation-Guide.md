# Standalone Training Project Creation Guide

## Overview

This guide provides comprehensive details for creating a standalone training project that consumes exported data from the MCP service and produces trained models for the inferencing system. The training system operates completely independently with its own configuration, dependencies, and deployment process.

## Project Structure

```
mcp_training/
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── pyproject.toml
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── config/
│   ├── __init__.py
│   ├── config.py
│   ├── model_config.yaml
│   └── training_config.yaml
├── src/
│   └── mcp_training/
│       ├── __init__.py
│       ├── main.py
│       ├── cli.py
│       ├── api/
│       ├── core/
│       ├── models/
│       ├── services/
│       └── utils/
├── scripts/
├── tests/
├── models/
├── logs/
├── exports/
└── docs/
```

## Dependencies

### Core Dependencies (requirements.txt)
```txt
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
click==8.1.7

# Data Processing
numpy==1.24.3
pandas==2.0.3
scikit-learn==1.3.0
joblib==1.3.2

# Configuration and Utilities
pyyaml==6.0.1
python-multipart==0.0.6
aiofiles==23.2.1

# Monitoring
prometheus-client==0.19.0

# Async Support
asyncio-mqtt==0.16.1
```

### Development Dependencies (requirements-dev.txt)
```txt
-r requirements.txt

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0

# Code Quality
black==23.11.0
flake8==6.1.0
mypy==1.7.1
pre-commit==3.6.0

# Documentation
sphinx==7.2.6
sphinx-rtd-theme==1.3.0
```

## Export Data Format

### Expected Export Structure
The training system expects exported data in the following JSON format:

```json
{
  "export_metadata": {
    "created_at": "2024-01-01T12:00:00Z",
    "total_records": 1000,
    "format": "json",
    "export_id": "export_12345",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-01T23:59:59Z",
    "programs": ["hostapd", "wpa_supplicant"]
  },
  "data": [
    {
      "id": 1,
      "device_id": "device_001",
      "device_ip": "192.168.1.100",
      "timestamp": "2024-01-01T12:00:00Z",
      "log_level": "INFO",
      "process_name": "hostapd",
      "message": "AP-STA-CONNECTED 00:11:22:33:44:55",
      "raw_message": "AP-STA-CONNECTED 00:11:22:33:44:55",
      "structured_data": {
        "event_type": "connection",
        "mac_address": "00:11:22:33:44:55",
        "ssid": "test_network"
      },
      "pushed_to_ai": false,
      "pushed_at": null,
      "push_attempts": 0,
      "last_push_error": null
    }
  ]
}
```

### Required Log Fields
- `timestamp`: ISO format timestamp
- `message`: Log message content
- `process_name`: Process that generated the log (e.g., "hostapd", "wpa_supplicant")
- `log_level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `structured_data`: Optional structured data (JSON object)

## Core Components Implementation

### 1. Feature Extractor (src/mcp_training/core/feature_extractor.py)

```python
import re
import logging
from typing import List, Dict, Any
from collections import defaultdict
import numpy as np
from datetime import datetime

class FeatureExtractor:
    """Extract features from WiFi logs for training."""
    
    def __init__(self):
        self.logger = logging.getLogger("FeatureExtractor")
        
        # Regular expressions for log parsing
        self.patterns = {
            'auth_failure': re.compile(r'authentication failure|auth failed', re.IGNORECASE),
            'deauth': re.compile(r'deauthentication|deauth', re.IGNORECASE),
            'beacon': re.compile(r'beacon', re.IGNORECASE),
            'mac_address': re.compile(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'),
            'ssid': re.compile(r'SSID=\'([^\']+)\''),
            'reason_code': re.compile(r'reason=(\d+)'),
            'status_code': re.compile(r'status=(\d+)'),
            'signal_strength': re.compile(r'signal=(-?\d+)'),
            'channel': re.compile(r'channel=(\d+)'),
            'data_rate': re.compile(r'rate=(\d+)'),
            'packet_loss': re.compile(r'packet_loss=(\d+)')
        }

    def extract_wifi_features(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract comprehensive WiFi features from logs."""
        try:
            features = {
                # Basic event counts
                'auth_failures': 0,
                'deauth_count': 0,
                'beacon_count': 0,
                'association_count': 0,
                'disassociation_count': 0,
                
                # Network metrics
                'unique_macs': set(),
                'unique_ssids': set(),
                'failed_auth_macs': set(),
                
                # Performance metrics
                'signal_strengths': [],
                'data_rates': [],
                'packet_loss_rates': [],
                'channel_utilization': defaultdict(int),
                
                # Temporal features
                'hour_of_day': [],
                'day_of_week': [],
                'time_between_events': [],
                
                # Error patterns
                'reason_codes': defaultdict(int),
                'status_codes': defaultdict(int),
                'error_logs': 0,
                'warning_logs': 0,
                
                # Device activity
                'device_activity': defaultdict(int),
                'program_counts': defaultdict(int)
            }
            
            prev_timestamp = None
            
            for log in logs:
                message = log.get('message', '').lower()
                timestamp = log.get('timestamp')
                device_id = log.get('device_id')
                process_name = log.get('process_name', '')
                log_level = log.get('log_level', 'info')
                
                # Update device and program activity
                features['device_activity'][device_id] += 1
                features['program_counts'][process_name] += 1
                
                # Count log levels
                if log_level in ['error', 'critical']:
                    features['error_logs'] += 1
                elif log_level == 'warning':
                    features['warning_logs'] += 1
                
                # Extract temporal features
                if timestamp:
                    dt = datetime.fromisoformat(timestamp)
                    features['hour_of_day'].append(dt.hour)
                    features['day_of_week'].append(dt.weekday())
                    
                    if prev_timestamp:
                        time_diff = (dt - prev_timestamp).total_seconds()
                        features['time_between_events'].append(time_diff)
                    prev_timestamp = dt
                
                # Extract MAC addresses
                macs = self.patterns['mac_address'].findall(message)
                features['unique_macs'].update(macs)
                
                # Extract SSIDs
                ssid_match = self.patterns['ssid'].search(message)
                if ssid_match:
                    features['unique_ssids'].add(ssid_match.group(1))
                
                # Count events
                if self.patterns['auth_failure'].search(message):
                    features['auth_failures'] += 1
                    features['failed_auth_macs'].update(macs)
                elif self.patterns['deauth'].search(message):
                    features['deauth_count'] += 1
                elif self.patterns['beacon'].search(message):
                    features['beacon_count'] += 1
                elif 'association' in message:
                    features['association_count'] += 1
                elif 'disassociation' in message:
                    features['disassociation_count'] += 1
                
                # Extract performance metrics
                signal_match = self.patterns['signal_strength'].search(message)
                if signal_match:
                    features['signal_strengths'].append(int(signal_match.group(1)))
                
                rate_match = self.patterns['data_rate'].search(message)
                if rate_match:
                    features['data_rates'].append(int(rate_match.group(1)))
                
                loss_match = self.patterns['packet_loss'].search(message)
                if loss_match:
                    features['packet_loss_rates'].append(int(loss_match.group(1)))
                
                channel_match = self.patterns['channel'].search(message)
                if channel_match:
                    features['channel_utilization'][channel_match.group(1)] += 1
                
                # Extract reason and status codes
                reason_match = self.patterns['reason_code'].search(message)
                if reason_match:
                    features['reason_codes'][reason_match.group(1)] += 1
                
                status_match = self.patterns['status_code'].search(message)
                if status_match:
                    features['status_codes'][status_match.group(1)] += 1
            
            # Convert to final feature format
            final_features = self._convert_features_to_final_format(features)
            return final_features
            
        except Exception as e:
            self.logger.error(f"Error extracting WiFi features: {e}")
            raise

    def _convert_features_to_final_format(self, features: Dict) -> Dict[str, float]:
        """Convert extracted features to final numeric format."""
        final_features = {
            # Event ratios
            'auth_failure_ratio': features['auth_failures'] / max(len(features['device_activity']), 1),
            'deauth_ratio': features['deauth_count'] / max(len(features['device_activity']), 1),
            'beacon_ratio': features['beacon_count'] / max(len(features['device_activity']), 1),
            
            # Network metrics
            'unique_mac_count': len(features['unique_macs']),
            'unique_ssid_count': len(features['unique_ssids']),
            'failed_auth_mac_count': len(features['failed_auth_macs']),
            
            # Performance metrics
            'mean_signal_strength': np.mean(features['signal_strengths']) if features['signal_strengths'] else 0,
            'std_signal_strength': np.std(features['signal_strengths']) if features['signal_strengths'] else 0,
            'mean_data_rate': np.mean(features['data_rates']) if features['data_rates'] else 0,
            'mean_packet_loss': np.mean(features['packet_loss_rates']) if features['packet_loss_rates'] else 0,
            
            # Temporal features
            'mean_hour_of_day': np.mean(features['hour_of_day']) if features['hour_of_day'] else 12,
            'mean_day_of_week': np.mean(features['day_of_week']) if features['day_of_week'] else 3,
            'mean_time_between_events': np.mean(features['time_between_events']) if features['time_between_events'] else 0,
            
            # Error patterns
            'error_ratio': features['error_logs'] / max(len(features['device_activity']), 1),
            'warning_ratio': features['warning_logs'] / max(len(features['device_activity']), 1),
            
            # Device activity
            'total_devices': len(features['device_activity']),
            'max_device_activity': max(features['device_activity'].values()) if features['device_activity'] else 0,
            'mean_device_activity': np.mean(list(features['device_activity'].values())) if features['device_activity'] else 0
        }
        
        # Add reason code features (top 10 most common)
        reason_codes = sorted(features['reason_codes'].items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (code, count) in enumerate(reason_codes):
            final_features[f'reason_code_{code}'] = count
        
        # Add status code features (top 10 most common)
        status_codes = sorted(features['status_codes'].items(), key=lambda x: x[1], reverse=True)[:10]
        for i, (code, count) in enumerate(status_codes):
            final_features[f'status_code_{code}'] = count
        
        return final_features
```

### 2. Model Trainer (src/mcp_training/core/model_trainer.py)

```python
import logging
import joblib
import numpy as np
from typing import Dict, Any, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from pathlib import Path
import json
from datetime import datetime

from .feature_extractor import FeatureExtractor
from ..models.config import ModelConfig

logger = logging.getLogger(__name__)

class ModelTrainer:
    """Train machine learning models from exported data."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.feature_extractor = FeatureExtractor()
        self.scaler = StandardScaler()
        self.model = None
        self.feature_names = []
        
    async def train_from_export_data(self, export_file_path: str) -> Dict[str, Any]:
        """Train model using exported data."""
        try:
            logger.info(f"Training model from export data: {export_file_path}")
            
            # Load exported data
            exported_data = await self._load_exported_data(export_file_path)
            
            # Extract features from exported logs
            features = await self.feature_extractor.extract_wifi_features(exported_data['data'])
            
            # Prepare training data
            X, y = self._prepare_training_data(features)
            
            # Train model
            model = self._train_model(X, y)
            
            # Evaluate model
            evaluation_results = self._evaluate_model(model, X, y)
            
            # Save model with metadata
            model_path = await self._save_model_with_metadata(
                model, features, evaluation_results, export_file_path
            )
            
            return {
                'model_path': str(model_path),
                'evaluation_results': evaluation_results,
                'training_samples': len(X),
                'export_file': export_file_path
            }
            
        except Exception as e:
            logger.error(f"Error training from export data: {e}")
            raise
    
    async def _load_exported_data(self, export_file_path: str) -> Dict[str, Any]:
        """Load data from exported JSON file."""
        try:
            with open(export_file_path, 'r') as f:
                data = json.load(f)
            
            # Validate export data structure
            if 'data' not in data:
                raise ValueError("Export file must contain 'data' section")
            
            logger.info(f"Loaded {len(data['data'])} log entries from export file")
            return data
            
        except Exception as e:
            logger.error(f"Error loading exported data: {e}")
            raise
    
    def _prepare_training_data(self, features: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from extracted features."""
        # Convert features to feature matrix
        feature_matrix = []
        for feature_name in self.config.features.numeric:
            if feature_name in features:
                feature_matrix.append(float(features[feature_name]))
            else:
                feature_matrix.append(0.0)
        
        X = np.array([feature_matrix])
        y = np.zeros(len(X))  # Unsupervised learning
        
        return X, y
    
    def _train_model(self, X: np.ndarray, y: np.ndarray) -> Any:
        """Train the model."""
        try:
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Create and train model
            model_params = self.config.model.dict()
            model = IsolationForest(**model_params)
            model.fit(X_scaled)
            
            self.model = model
            self.feature_names = self.config.features.numeric
            
            logger.info(f"Model trained successfully with {len(X)} samples")
            return model
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    def _evaluate_model(self, model: Any, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Evaluate the trained model."""
        try:
            # Get anomaly scores
            X_scaled = self.scaler.transform(X)
            scores = -model.score_samples(X_scaled)
            
            # Calculate basic metrics
            threshold = np.percentile(scores, 90)
            predictions = (scores > threshold).astype(int)
            
            evaluation_results = {
                'basic_metrics': {
                    'mean_score': float(np.mean(scores)),
                    'std_score': float(np.std(scores)),
                    'anomaly_threshold': float(threshold),
                    'anomaly_ratio': float(np.mean(predictions))
                },
                'score_distribution': {
                    'min': float(np.min(scores)),
                    'max': float(np.max(scores)),
                    'percentiles': {
                        '25': float(np.percentile(scores, 25)),
                        '50': float(np.percentile(scores, 50)),
                        '75': float(np.percentile(scores, 75)),
                        '90': float(np.percentile(scores, 90)),
                        '95': float(np.percentile(scores, 95))
                    }
                }
            }
            
            return evaluation_results
            
        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            raise
    
    async def _save_model_with_metadata(self, model: Any, features: Dict[str, Any],
                                      evaluation_results: Dict[str, Any],
                                      export_file_path: str) -> Path:
        """Save model with comprehensive metadata."""
        # Generate version
        version = datetime.now().strftime(self.config.storage.version_format)
        
        # Create model directory
        model_dir = Path(self.config.storage.directory) / version
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_path = model_dir / 'model.joblib'
        joblib.dump(model, model_path)
        
        # Save scaler
        scaler_path = model_dir / 'scaler.joblib'
        joblib.dump(self.scaler, scaler_path)
        
        # Create metadata
        metadata = {
            'model_info': {
                'version': version,
                'created_at': datetime.now().isoformat(),
                'model_type': type(model).__name__,
                'training_source': 'export_data',
                'export_file': export_file_path
            },
            'training_info': {
                'training_samples': len(features),
                'feature_names': list(features.keys()),
                'export_file_size': Path(export_file_path).stat().st_size
            },
            'evaluation_info': evaluation_results,
            'deployment_info': {
                'status': 'available',
                'deployed_at': None,
                'deployed_by': None
            }
        }
        
        # Save metadata
        metadata_path = model_dir / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        return model_dir
```

### 3. Export Validator (src/mcp_training/core/export_validator.py)

```python
import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class ExportDataValidator:
    """Validate exported data for training suitability."""
    
    def __init__(self):
        self.logger = logging.getLogger("ExportDataValidator")
    
    async def validate_export_for_training(self, export_file_path: str) -> Dict[str, Any]:
        """Validate that exported data is suitable for training."""
        try:
            # Load export data
            with open(export_file_path, 'r') as f:
                data = json.load(f)
            
            validation_results = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'stats': {}
            }
            
            # Check required sections
            if 'data' not in data:
                validation_results['is_valid'] = False
                validation_results['errors'].append("Missing 'data' section in export file")
            
            if 'export_metadata' not in data:
                validation_results['warnings'].append("Missing 'export_metadata' section in export file")
            
            # Validate log entries
            if 'data' in data:
                log_validation = self._validate_log_entries(data['data'])
                validation_results['stats']['log_count'] = len(data['data'])
                validation_results['stats']['valid_logs'] = log_validation['valid_count']
                validation_results['stats']['invalid_logs'] = log_validation['invalid_count']
                
                if log_validation['errors']:
                    validation_results['errors'].extend(log_validation['errors'])
                
                if log_validation['warnings']:
                    validation_results['warnings'].extend(log_validation['warnings'])
            
            # Check data quality
            quality_check = self._check_data_quality(data)
            validation_results['stats'].update(quality_check['stats'])
            
            if quality_check['errors']:
                validation_results['errors'].extend(quality_check['errors'])
            
            # Determine overall validity
            if validation_results['errors']:
                validation_results['is_valid'] = False
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Error validating export file: {e}")
            return {
                'is_valid': False,
                'errors': [f"Validation failed: {str(e)}"],
                'warnings': [],
                'stats': {}
            }
    
    def _validate_log_entries(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate individual log entries."""
        valid_count = 0
        invalid_count = 0
        errors = []
        warnings = []
        
        required_fields = ['timestamp', 'message', 'process_name']
        
        for i, log in enumerate(logs):
            # Check required fields
            missing_fields = [field for field in required_fields if field not in log]
            if missing_fields:
                invalid_count += 1
                errors.append(f"Log {i}: Missing required fields: {missing_fields}")
                continue
            
            # Check data types
            if not isinstance(log['timestamp'], str):
                invalid_count += 1
                errors.append(f"Log {i}: Invalid timestamp format")
                continue
            
            if not isinstance(log['message'], str):
                invalid_count += 1
                errors.append(f"Log {i}: Invalid message format")
                continue
            
            valid_count += 1
        
        return {
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'errors': errors,
            'warnings': warnings
        }
    
    def _check_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check overall data quality."""
        stats = {}
        errors = []
        warnings = []
        
        if 'data' in data:
            logs = data['data']
            stats['total_logs'] = len(logs)
            
            # Check for WiFi-related logs
            wifi_logs = [log for log in logs if log.get('process_name') in ['hostapd', 'wpa_supplicant']]
            stats['wifi_logs'] = len(wifi_logs)
            stats['wifi_ratio'] = len(wifi_logs) / len(logs) if logs else 0
            
            if stats['wifi_ratio'] < 0.1:
                warnings.append("Low ratio of WiFi-related logs (< 10%)")
            
            # Check time range
            if logs:
                timestamps = [log.get('timestamp') for log in logs if log.get('timestamp')]
                if timestamps:
                    try:
                        times = [datetime.fromisoformat(ts) for ts in timestamps]
                        time_range = max(times) - min(times)
                        stats['time_range_days'] = time_range.days
                        
                        if time_range.days < 1:
                            warnings.append("Export contains less than 1 day of data")
                    except:
                        pass
        
        return {
            'stats': stats,
            'errors': errors,
            'warnings': warnings
        }
```

## Configuration Files

### 1. Model Configuration (config/model_config.yaml)
```yaml
version: '2.0.0'

model:
  type: isolation_forest
  n_estimators: 100
  max_samples: auto
  contamination: 0.1
  random_state: 42
  bootstrap: true
  max_features: 1.0

features:
  numeric:
    - auth_failure_ratio
    - deauth_ratio
    - beacon_ratio
    - unique_mac_count
    - unique_ssid_count
    - mean_signal_strength
    - std_signal_strength
    - mean_data_rate
    - mean_packet_loss
    - error_ratio
    - warning_ratio
    - mean_hour_of_day
    - mean_day_of_week
    - mean_time_between_events
    - total_devices
    - max_device_activity
    - mean_device_activity

training:
  test_size: 0.2
  validation_size: 0.1
  random_state: 42
  n_jobs: -1
  cross_validation_folds: 5

storage:
  directory: models
  version_format: '%Y%m%d_%H%M%S'
  keep_last_n_versions: 5
  backup_enabled: true
  compression: true

evaluation:
  metrics:
    - accuracy
    - precision
    - recall
    - f1_score
    - roc_auc
    - average_precision
  thresholds:
    accuracy: 0.8
    precision: 0.7
    recall: 0.7
    f1_score: 0.7
    roc_auc: 0.8
  cross_validation: true

logging:
  level: INFO
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  file: logs/training.log
  rotation:
    max_size: 100MB
    backup_count: 10
```

### 2. Training Configuration (config/training_config.yaml)
```yaml
service:
  name: mcp-training
  version: 1.0.0
  debug: false

api:
  host: 0.0.0.0
  port: 8001
  workers: 1

storage:
  models_dir: models
  exports_dir: exports
  logs_dir: logs

training:
  max_training_time: 3600
  max_memory_usage: 4096
  enable_gpu: false

monitoring:
  enable_monitoring: true
  prometheus_port: 9091
```

### 3. Environment Configuration (.env.example)
```bash
# Service Configuration
TRAINING_SERVICE_NAME=mcp-training
TRAINING_SERVICE_VERSION=1.0.0
TRAINING_DEBUG=false

# API Configuration
TRAINING_API_HOST=0.0.0.0
TRAINING_API_PORT=8001
TRAINING_API_WORKERS=1

# Storage Configuration
TRAINING_MODELS_DIR=models
TRAINING_EXPORTS_DIR=exports
TRAINING_LOGS_DIR=logs

# Training Configuration
TRAINING_MAX_TRAINING_TIME=3600
TRAINING_MAX_MEMORY_USAGE=4096
TRAINING_ENABLE_GPU=false

# Model Configuration
TRAINING_DEFAULT_MODEL_TYPE=isolation_forest
TRAINING_MODEL_CONFIG_FILE=config/model_config.yaml

# Logging Configuration
TRAINING_LOG_LEVEL=INFO
TRAINING_LOG_FILE=logs/training.log

# Monitoring Configuration
TRAINING_ENABLE_MONITORING=true
TRAINING_PROMETHEUS_PORT=9091
```

## Integration Points with Main MCP Service

### 1. Export Data Transfer
The training system expects exported data files from the main MCP service. These files should be placed in the `exports/` directory.

### 2. Model Transfer
Trained models are saved in the `models/` directory and can be transferred to the main MCP service for deployment.

### 3. Data Format Compatibility
The training system is designed to work with the exact export format produced by the MCP service exporter.

## Usage Examples

### 1. CLI Usage
```bash
# Train a model from exported data
python -m mcp_training.cli train exports/export_20240101.json

# Validate exported data
python -m mcp_training.cli validate exports/export_20240101.json

# List trained models
python -m mcp_training.cli list-models

# Deploy a model
python -m mcp_training.cli deploy 20240101_120000
```

### 2. API Usage
```bash
# Start the API server
uvicorn mcp_training.api.app:app --host 0.0.0.0 --port 8001

# Train a model via API
curl -X POST "http://localhost:8001/api/v1/training/train" \
  -H "Content-Type: application/json" \
  -d '{"export_file": "exports/export_20240101.json"}'

# Check training status
curl "http://localhost:8001/api/v1/training/status/{training_id}"

# List models
curl "http://localhost:8001/api/v1/models"
```

### 3. Docker Usage
```bash
# Build and run with Docker Compose
docker-compose up -d

# Train a model
docker exec mcp-training python -m mcp_training.cli train exports/export_20240101.json

# Access the API
curl "http://localhost:8001/api/v1/health"
```

## Testing

### 1. Unit Tests
```python
# tests/unit/test_feature_extractor.py
import pytest
from mcp_training.core.feature_extractor import FeatureExtractor

def test_extract_wifi_features():
    """Test WiFi feature extraction."""
    extractor = FeatureExtractor()
    
    # Sample logs
    logs = [
        {
            'timestamp': '2024-01-01T12:00:00Z',
            'message': 'AP-STA-CONNECTED 00:11:22:33:44:55',
            'process_name': 'hostapd',
            'log_level': 'INFO'
        },
        {
            'timestamp': '2024-01-01T12:01:00Z',
            'message': 'authentication failure for 00:11:22:33:44:55',
            'process_name': 'hostapd',
            'log_level': 'ERROR'
        }
    ]
    
    features = extractor.extract_wifi_features(logs)
    
    assert 'auth_failures' in features
    assert 'unique_mac_count' in features
    assert features['auth_failures'] == 1
    assert features['unique_mac_count'] == 1
```

### 2. Integration Tests
```python
# tests/integration/test_training_pipeline.py
import pytest
import asyncio
from mcp_training.core.training_pipeline import TrainingPipeline
from mcp_training.models.config import ModelConfig

@pytest.mark.asyncio
async def test_training_from_export():
    """Test complete training pipeline."""
    config = ModelConfig()
    pipeline = TrainingPipeline(config)
    
    # Test with sample export file
    result = await pipeline.train_from_export('tests/fixtures/sample_export.json')
    
    assert result['status'] == 'completed'
    assert 'model_path' in result['result']
```

## Deployment

### 1. Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p models exports logs

# Set environment variables
ENV PYTHONPATH=/app/src
ENV TRAINING_MODELS_DIR=/app/models
ENV TRAINING_EXPORTS_DIR=/app/exports
ENV TRAINING_LOGS_DIR=/app/logs

# Expose ports
EXPOSE 8001 9091

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/v1/health || exit 1

# Default command
CMD ["uvicorn", "mcp_training.api.app:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 2. Docker Compose
```yaml
version: '3.8'

services:
  mcp-training:
    build: .
    container_name: mcp-training
    ports:
      - "8001:8001"
      - "9091:9091"
    volumes:
      - ./models:/app/models
      - ./exports:/app/exports
      - ./logs:/app/logs
    environment:
      - TRAINING_DEBUG=false
      - TRAINING_LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  prometheus:
    image: prom/prometheus:latest
    container_name: mcp-training-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: mcp-training-grafana
    ports:
      - "3000:3000"
    volumes:
      - ./monitoring/grafana:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    restart: unless-stopped
```

## Key Dependencies from Current System

### 1. Feature Extraction Logic
The training system uses the same feature extraction logic as the main MCP service, ensuring compatibility between training and inference.

### 2. Export Data Format
The training system expects the exact export format produced by the MCP service exporter, maintaining data consistency.

### 3. Model Format
Trained models are saved in the same format expected by the main MCP service's ModelManager, ensuring seamless integration.

### 4. Configuration Structure
The training system uses similar configuration patterns to the main MCP service for consistency and maintainability.

This comprehensive guide provides all the details needed to create a standalone training project that operates independently while maintaining full compatibility with the main MCP service. 