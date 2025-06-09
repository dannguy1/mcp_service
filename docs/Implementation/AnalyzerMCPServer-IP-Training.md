# AnalyzerMCPServer Implementation Plan - Training

## Overview

This document details the implementation of the model training and deployment process for the AnalyzerMCPServer, including log export, model training, and deployment mechanisms.

## 1. Log Export Implementation

### 1.1 Export Script (`export_logs.py`)

```python
import asyncio
import asyncpg
import pandas as pd
import logging
from datetime import datetime, timedelta
from config import Config

async def export_logs(config: Config, output_file: str, days: int = 30):
    """Export logs from database to CSV file."""
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=config.db.host,
            port=config.db.port,
            user=config.db.user,
            password=config.db.password,
            database=config.db.database
        )
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Query logs
        rows = await conn.fetch('''
            SELECT * FROM wifi_logs 
            WHERE timestamp BETWEEN $1 AND $2
            ORDER BY timestamp
        ''', start_time, end_time)
        
        # Convert to DataFrame
        df = pd.DataFrame([dict(row) for row in rows])
        
        # Save to CSV
        df.to_csv(output_file, index=False)
        logging.info(f"Exported {len(df)} logs to {output_file}")
        
        await conn.close()
        
    except Exception as e:
        logging.error(f"Failed to export logs: {str(e)}")
        raise

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    config = Config()
    asyncio.run(export_logs(config, 'wifi_logs.csv'))
```

## 2. Model Training Implementation

### 2.1 Training Script (`train_model.py`)

```python
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import json
import logging
from datetime import datetime
from components.feature_extractor import WiFiFeatureExtractor

def train_model(input_file: str, output_dir: str):
    """Train WiFi anomaly detection model."""
    try:
        # Load data
        df = pd.read_csv(input_file)
        logging.info(f"Loaded {len(df)} records from {input_file}")
        
        # Extract features
        feature_extractor = WiFiFeatureExtractor()
        features = []
        
        # Process in 5-minute windows
        window_size = pd.Timedelta(minutes=5)
        for start_time in pd.date_range(
            df['timestamp'].min(),
            df['timestamp'].max(),
            freq=window_size
        ):
            end_time = start_time + window_size
            window_logs = df[
                (df['timestamp'] >= start_time) &
                (df['timestamp'] < end_time)
            ]
            
            if len(window_logs) > 0:
                window_features = feature_extractor.extract_features(
                    window_logs.to_dict('records')
                )
                features.append(window_features)
        
        # Convert to DataFrame
        features_df = pd.DataFrame(features)
        
        # Scale features
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features_df)
        
        # Train model
        model = IsolationForest(
            n_estimators=100,
            contamination=0.1,
            random_state=42
        )
        model.fit(scaled_features)
        
        # Save model and scaler
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_path = f"{output_dir}/wifi_model_{timestamp}.joblib"
        scaler_path = f"{output_dir}/wifi_scaler_{timestamp}.joblib"
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        # Save metadata
        metadata = {
            'timestamp': timestamp,
            'n_samples': len(features_df),
            'feature_means': features_df.mean().to_dict(),
            'feature_stds': features_df.std().to_dict(),
            'model_params': model.get_params()
        }
        
        metadata_path = f"{output_dir}/wifi_metadata_{timestamp}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logging.info(f"Model saved to {model_path}")
        logging.info(f"Scaler saved to {scaler_path}")
        logging.info(f"Metadata saved to {metadata_path}")
        
    except Exception as e:
        logging.error(f"Failed to train model: {str(e)}")
        raise

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    train_model('wifi_logs.csv', 'models')
```

## 3. Model Deployment Implementation

### 3.1 Deployment Script (`deploy_model.py`)

```python
import os
import paramiko
import logging
from config import Config

def deploy_model(config: Config, model_dir: str):
    """Deploy model to remote server."""
    try:
        # Validate input files
        model_files = [f for f in os.listdir(model_dir) if f.endswith('.joblib')]
        metadata_files = [f for f in os.listdir(model_dir) if f.endswith('.json')]
        
        if not model_files or not metadata_files:
            raise ValueError("No model or metadata files found")
        
        # Get latest files
        latest_model = max(model_files)
        latest_metadata = max(metadata_files)
        
        # Connect to SFTP server
        transport = paramiko.Transport((config.sftp.host, config.sftp.port))
        transport.connect(
            username=config.sftp.user,
            password=config.sftp.password
        )
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        # Upload files
        remote_model_path = f"{config.sftp.remote_path}/{latest_model}"
        remote_metadata_path = f"{config.sftp.remote_path}/{latest_metadata}"
        
        sftp.put(
            os.path.join(model_dir, latest_model),
            remote_model_path
        )
        sftp.put(
            os.path.join(model_dir, latest_metadata),
            remote_metadata_path
        )
        
        # Update symlinks
        ssh = transport.open_session()
        ssh.exec_command(f"""
            cd {config.sftp.remote_path} && \
            ln -sf {latest_model} wifi_model.joblib && \
            ln -sf {latest_metadata} wifi_metadata.json
        """)
        
        sftp.close()
        transport.close()
        
        logging.info(f"Deployed model {latest_model} to {config.sftp.host}")
        
    except Exception as e:
        logging.error(f"Failed to deploy model: {str(e)}")
        raise

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    config = Config()
    deploy_model(config, 'models')
```

## 4. Training Pipeline

### 4.1 Training Workflow

1. **Data Collection**
   - Export logs from production database
   - Filter and preprocess data
   - Split into training and validation sets

2. **Feature Engineering**
   - Extract features using `WiFiFeatureExtractor`
   - Scale features using `StandardScaler`
   - Handle missing values and outliers

3. **Model Training**
   - Train `IsolationForest` model
   - Tune hyperparameters
   - Validate model performance

4. **Model Deployment**
   - Save model artifacts
   - Generate metadata
   - Deploy to production server

### 4.2 Training Script (`train_pipeline.py`)

```python
import logging
from datetime import datetime
from config import Config
from export_logs import export_logs
from train_model import train_model
from deploy_model import deploy_model

def run_training_pipeline(config: Config):
    """Run complete training pipeline."""
    try:
        # Create output directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f"training_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Export logs
        log_file = f"{output_dir}/wifi_logs.csv"
        export_logs(config, log_file)
        
        # Train model
        model_dir = f"{output_dir}/models"
        os.makedirs(model_dir, exist_ok=True)
        train_model(log_file, model_dir)
        
        # Deploy model
        deploy_model(config, model_dir)
        
        logging.info("Training pipeline completed successfully")
        
    except Exception as e:
        logging.error(f"Training pipeline failed: {str(e)}")
        raise

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    config = Config()
    run_training_pipeline(config)
```

## 5. Model Monitoring

### 5.1 Performance Monitoring

1. **Model Metrics**
   - Anomaly detection rate
   - False positive rate
   - Feature importance
   - Prediction confidence

2. **Data Drift Detection**
   - Feature distribution changes
   - Concept drift detection
   - Performance degradation

3. **Resource Usage**
   - Inference time
   - Memory usage
   - CPU utilization

### 5.2 Monitoring Script (`monitor_model.py`)

```python
import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
import logging
from datetime import datetime, timedelta
from config import Config
from components.feature_extractor import WiFiFeatureExtractor
from components.model_manager import WiFiModelManager

async def monitor_model_performance(config: Config):
    """Monitor model performance."""
    try:
        # Get recent logs
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        logs = await config.data_service.get_logs(
            start_time.isoformat(),
            end_time.isoformat()
        )
        
        if not logs:
            return
        
        # Extract features
        feature_extractor = WiFiFeatureExtractor()
        features = feature_extractor.extract_features(logs)
        
        # Load model
        model_manager = WiFiModelManager(config.sftp.remote_path)
        await model_manager.start()
        
        # Make predictions
        predictions = model_manager.predict(features)
        
        # Calculate metrics
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'n_samples': len(logs),
            'anomaly_rate': np.mean(predictions < -0.5),
            'feature_stats': {
                name: {
                    'mean': np.mean(values),
                    'std': np.std(values)
                }
                for name, values in features.items()
            }
        }
        
        # Save metrics
        metrics_file = f"model_metrics_{datetime.now().strftime('%Y%m%d')}.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logging.info(f"Model metrics saved to {metrics_file}")
        
    except Exception as e:
        logging.error(f"Failed to monitor model: {str(e)}")
        raise

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    config = Config()
    asyncio.run(monitor_model_performance(config))
```

## Next Steps

1. Review the [Testing Implementation](AnalyzerMCPServer-IP-Testing.md) for testing procedures
2. Check the [Deployment Guide](AnalyzerMCPServer-IP-Deployment.md) for setup instructions
3. Follow the [Documentation Guide](AnalyzerMCPServer-IP-Docs.md) for documentation templates 