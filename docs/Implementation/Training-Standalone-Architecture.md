ls d# Standalone Training System Architecture

## Overview

The Standalone Training System is a completely independent module that consumes exported data from the MCP service exporter and produces trained models for the inferencing system. It operates as a separate service with its own configuration, dependencies, and deployment process.

## Directory Structure

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
├── docker-compose.dev.yml
├── Dockerfile.dev
├── config/
│   ├── __init__.py
│   ├── config.py
│   ├── model_config.yaml
│   ├── training_config.yaml
│   └── logging_config.yaml
├── src/
│   └── mcp_training/
│       ├── __init__.py
│       ├── main.py
│       ├── cli.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── routes/
│       │   │   ├── __init__.py
│       │   │   ├── training.py
│       │   │   ├── models.py
│       │   │   └── health.py
│       │   └── middleware/
│       │       ├── __init__.py
│       │       ├── auth.py
│       │       └── logging.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── training_pipeline.py
│       │   ├── model_trainer.py
│       │   ├── feature_extractor.py
│       │   ├── model_evaluator.py
│       │   └── export_validator.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── metadata.py
│       │   └── registry.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── training_service.py
│       │   ├── model_service.py
│       │   └── storage_service.py
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── logger.py
│       │   ├── file_utils.py
│       │   └── validation.py
│       └── web/
│           ├── __init__.py
│           ├── static/
│           │   ├── css/
│           │   ├── js/
│           │   └── index.html
│           └── templates/
│               ├── base.html
│               ├── training.html
│               └── models.html
├── scripts/
│   ├── train_model.py
│   ├── validate_export.py
│   ├── list_models.py
│   ├── deploy_model.py
│   └── setup_dev_env.sh
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_training_pipeline.py
│   │   ├── test_model_trainer.py
│   │   ├── test_feature_extractor.py
│   │   └── test_model_evaluator.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_training_api.py
│   │   └── test_export_validation.py
│   └── fixtures/
│       ├── sample_export.json
│       └── test_config.yaml
├── models/
│   ├── .gitkeep
│   └── README.md
├── logs/
│   ├── .gitkeep
│   └── README.md
├── exports/
│   ├── .gitkeep
│   └── README.md
├── docs/
│   ├── api.md
│   ├── deployment.md
│   ├── development.md
│   └── usage.md
└── monitoring/
    ├── prometheus.yml
    ├── grafana/
    │   └── dashboards/
    └── alerts/
        └── training_alerts.yml
```

## Core Components

### 1. Configuration Management
```python
# src/mcp_training/config/config.py
from pydantic import BaseSettings, Field
from typing import Optional, Dict, Any
import yaml
from pathlib import Path

class TrainingConfig(BaseSettings):
    """Main configuration for the training system."""
    
    # Service configuration
    service_name: str = Field(default="mcp-training", description="Service name")
    service_version: str = Field(default="1.0.0", description="Service version")
    debug: bool = Field(default=False, description="Debug mode")
    
    # API configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8001, description="API port")
    api_workers: int = Field(default=1, description="API workers")
    
    # Storage configuration
    models_dir: str = Field(default="models", description="Models directory")
    exports_dir: str = Field(default="exports", description="Exports directory")
    logs_dir: str = Field(default="logs", description="Logs directory")
    
    # Training configuration
    max_training_time: int = Field(default=3600, description="Max training time (seconds)")
    max_memory_usage: int = Field(default=4096, description="Max memory usage (MB)")
    enable_gpu: bool = Field(default=False, description="Enable GPU training")
    
    # Model configuration
    default_model_type: str = Field(default="isolation_forest", description="Default model type")
    model_config_file: str = Field(default="config/model_config.yaml", description="Model config file")
    
    # Logging configuration
    log_level: str = Field(default="INFO", description="Log level")
    log_file: str = Field(default="logs/training.log", description="Log file")
    
    # Monitoring configuration
    enable_monitoring: bool = Field(default=True, description="Enable monitoring")
    prometheus_port: int = Field(default=9091, description="Prometheus port")
    
    class Config:
        env_file = ".env"
        env_prefix = "TRAINING_"

class ConfigManager:
    """Configuration manager for the training system."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.config = TrainingConfig()
        self.model_config = {}
        self.training_config = {}
        
        if config_file:
            self.load_config_file(config_file)
    
    def load_config_file(self, config_file: str):
        """Load configuration from YAML file."""
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Update configuration
            for key, value in config_data.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration."""
        if not self.model_config:
            model_config_path = Path(self.config.model_config_file)
            if model_config_path.exists():
                with open(model_config_path, 'r') as f:
                    self.model_config = yaml.safe_load(f)
        
        return self.model_config
    
    def get_training_config(self) -> Dict[str, Any]:
        """Get training configuration."""
        if not self.training_config:
            training_config_path = Path("config/training_config.yaml")
            if training_config_path.exists():
                with open(training_config_path, 'r') as f:
                    self.training_config = yaml.safe_load(f)
        
        return self.training_config
```

### 2. Training Pipeline
```python
# src/mcp_training/core/training_pipeline.py
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import uuid

from ..models.config import ModelConfig
from ..core.model_trainer import ModelTrainer
from ..core.feature_extractor import FeatureExtractor
from ..core.model_evaluator import ModelEvaluator
from ..core.export_validator import ExportDataValidator
from ..services.storage_service import StorageService
from ..utils.logger import get_logger

logger = get_logger(__name__)

class TrainingPipeline:
    """Main training pipeline for the standalone training system."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.trainer = ModelTrainer(config)
        self.feature_extractor = FeatureExtractor()
        self.evaluator = ModelEvaluator(config)
        self.validator = ExportDataValidator()
        self.storage = StorageService(config)
        self.training_tasks = {}
    
    async def train_from_export(self, export_file_path: str, 
                               training_id: Optional[str] = None,
                               config_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Train model from exported data with full pipeline."""
        
        if training_id is None:
            training_id = str(uuid.uuid4())
        
        try:
            # Initialize training task
            self.training_tasks[training_id] = {
                'id': training_id,
                'status': 'initializing',
                'progress': 0,
                'step': 'Validating export data',
                'error': None,
                'result': None,
                'start_time': datetime.now().isoformat(),
                'export_file': export_file_path
            }
            
            # Step 1: Validate export data
            await self._update_progress(training_id, 5, 'Validating export data')
            validation = await self.validator.validate_export_for_training(export_file_path)
            
            if not validation['is_valid']:
                await self._update_progress(training_id, 0, 'Validation failed', 
                                          error='; '.join(validation['errors']))
                return self.training_tasks[training_id]
            
            # Step 2: Load exported data
            await self._update_progress(training_id, 10, 'Loading export data')
            exported_data = await self._load_exported_data(export_file_path)
            
            # Step 3: Extract features
            await self._update_progress(training_id, 30, 'Extracting features')
            features = await self.feature_extractor.extract_wifi_features(exported_data['logs'])
            
            # Step 4: Prepare training data
            await self._update_progress(training_id, 50, 'Preparing training data')
            X, y = self._prepare_training_data(features)
            
            # Step 5: Train model
            await self._update_progress(training_id, 70, 'Training model')
            model = await self.trainer.train_model(X, y, config_overrides)
            
            # Step 6: Evaluate model
            await self._update_progress(training_id, 85, 'Evaluating model')
            evaluation_results = await self.evaluator.evaluate_model(model, X, y)
            
            # Step 7: Save model
            await self._update_progress(training_id, 95, 'Saving model')
            model_path = await self._save_model_with_metadata(
                model, features, evaluation_results, export_file_path, training_id
            )
            
            # Step 8: Complete
            await self._update_progress(training_id, 100, 'Training completed', 
                                      result={'model_path': str(model_path)})
            
            logger.info(f"Training completed successfully: {training_id}")
            return self.training_tasks[training_id]
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            await self._update_progress(training_id, 0, 'Training failed', error=str(e))
            return self.training_tasks[training_id]
    
    async def _load_exported_data(self, export_file_path: str) -> Dict[str, Any]:
        """Load data from exported JSON file."""
        try:
            with open(export_file_path, 'r') as f:
                data = json.load(f)
            
            # Validate export data structure
            if 'logs' not in data:
                raise ValueError("Export file must contain 'logs' section")
            
            logger.info(f"Loaded {len(data['logs'])} log entries from export file")
            return data
            
        except Exception as e:
            logger.error(f"Error loading exported data: {e}")
            raise
    
    def _prepare_training_data(self, features: Dict[str, Any]) -> tuple:
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
    
    async def _save_model_with_metadata(self, model: Any, features: Dict[str, Any],
                                      evaluation_results: Dict[str, Any],
                                      export_file_path: str,
                                      training_id: str) -> Path:
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
        joblib.dump(self.trainer.scaler, scaler_path)
        
        # Create metadata
        metadata = {
            'model_info': {
                'version': version,
                'created_at': datetime.now().isoformat(),
                'model_type': type(model).__name__,
                'training_source': 'export_data',
                'export_file': export_file_path,
                'training_id': training_id
            },
            'training_info': {
                'training_samples': len(features),
                'feature_names': list(features.keys()),
                'export_file_size': os.path.getsize(export_file_path),
                'training_duration': self._get_training_duration(training_id)
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
    
    async def _update_progress(self, training_id: str, progress: int, step: str,
                             error: Optional[str] = None, result: Optional[Dict] = None):
        """Update training progress."""
        if training_id in self.training_tasks:
            self.training_tasks[training_id].update({
                'progress': progress,
                'step': step,
                'error': error,
                'result': result,
                'updated_at': datetime.now().isoformat()
            })
            
            if error:
                self.training_tasks[training_id]['status'] = 'failed'
            elif progress >= 100:
                self.training_tasks[training_id]['status'] = 'completed'
            else:
                self.training_tasks[training_id]['status'] = 'running'
    
    def get_training_status(self, training_id: str) -> Optional[Dict[str, Any]]:
        """Get training status by ID."""
        return self.training_tasks.get(training_id)
    
    def list_training_tasks(self) -> Dict[str, Dict[str, Any]]:
        """List all training tasks."""
        return self.training_tasks.copy()
    
    def _get_training_duration(self, training_id: str) -> float:
        """Get training duration in seconds."""
        if training_id in self.training_tasks:
            task = self.training_tasks[training_id]
            start_time = datetime.fromisoformat(task['start_time'])
            end_time = datetime.fromisoformat(task.get('updated_at', task['start_time']))
            return (end_time - start_time).total_seconds()
        return 0.0
```

### 3. API Server
```python
# src/mcp_training/api/app.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

from ..config.config import ConfigManager
from ..core.training_pipeline import TrainingPipeline
from ..models.config import ModelConfig
from .routes import training, models, health

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting MCP Training Service...")
    
    # Initialize configuration
    config_manager = ConfigManager()
    app.state.config = config_manager
    
    # Initialize training pipeline
    model_config = ModelConfig(**config_manager.get_model_config())
    training_pipeline = TrainingPipeline(model_config)
    app.state.training_pipeline = training_pipeline
    
    logger.info("MCP Training Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MCP Training Service...")

def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="MCP Training Service",
        description="Standalone training service for MCP models",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="src/mcp_training/web/static"), name="static")
    
    # Include routers
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(training.router, prefix="/api/v1/training", tags=["training"])
    app.include_router(models.router, prefix="/api/v1/models", tags=["models"])
    
    return app

app = create_app()
```

### 4. CLI Interface
```python
# src/mcp_training/cli.py
import click
import asyncio
import logging
from pathlib import Path
from typing import Optional

from .config.config import ConfigManager
from .core.training_pipeline import TrainingPipeline
from .models.config import ModelConfig
from .utils.logger import setup_logging

logger = logging.getLogger(__name__)

@click.group()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose logging')
def cli(config: Optional[str], verbose: bool):
    """MCP Training Service CLI."""
    setup_logging(verbose=verbose)
    
    # Initialize configuration
    config_manager = ConfigManager(config)
    cli.config_manager = config_manager

@cli.command()
@click.argument('export_file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', default='models', help='Output directory for models')
@click.option('--config-overrides', help='JSON string of config overrides')
def train(export_file: str, output_dir: str, config_overrides: Optional[str]):
    """Train a model from exported data."""
    try:
        # Initialize training pipeline
        model_config = ModelConfig(**cli.config_manager.get_model_config())
        training_pipeline = TrainingPipeline(model_config)
        
        # Parse config overrides
        overrides = {}
        if config_overrides:
            import json
            overrides = json.loads(config_overrides)
        
        # Run training
        async def run_training():
            result = await training_pipeline.train_from_export(
                export_file, config_overrides=overrides
            )
            
            if result['status'] == 'completed':
                click.echo(f"✅ Training completed successfully!")
                click.echo(f"📁 Model saved to: {result['result']['model_path']}")
                return 0
            else:
                click.echo(f"❌ Training failed: {result['error']}")
                return 1
        
        exit_code = asyncio.run(run_training())
        exit(exit_code)
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        exit(1)

@cli.command()
@click.argument('export_file', type=click.Path(exists=True))
def validate(export_file: str):
    """Validate exported data for training."""
    try:
        from .core.export_validator import ExportDataValidator
        
        validator = ExportDataValidator()
        
        async def run_validation():
            result = await validator.validate_export_for_training(export_file)
            
            if result['is_valid']:
                click.echo("✅ Export file is valid for training")
                click.echo(f"📊 Statistics: {result['stats']}")
            else:
                click.echo("❌ Export file is not valid for training")
                for error in result['errors']:
                    click.echo(f"  - {error}")
            
            if result['warnings']:
                click.echo("⚠️  Warnings:")
                for warning in result['warnings']:
                    click.echo(f"  - {warning}")
        
        asyncio.run(run_validation())
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        exit(1)

@cli.command()
def list_models():
    """List all trained models."""
    try:
        from .services.storage_service import StorageService
        
        storage = StorageService()
        
        async def run_list():
            models = await storage.list_models()
            
            if not models:
                click.echo("No models found")
                return
            
            click.echo("📋 Available Models:")
            for model in models:
                click.echo(f"  - {model['version']} ({model['model_type']})")
                click.echo(f"    Created: {model['created_at']}")
                click.echo(f"    Status: {model['deployment_status']}")
                click.echo()
        
        asyncio.run(run_list())
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        exit(1)

@cli.command()
@click.argument('model_version')
def deploy(model_version: str):
    """Deploy a model version."""
    try:
        from .services.storage_service import StorageService
        
        storage = StorageService()
        
        async def run_deploy():
            success = await storage.deploy_model(model_version)
            
            if success:
                click.echo(f"✅ Model {model_version} deployed successfully")
            else:
                click.echo(f"❌ Failed to deploy model {model_version}")
                exit(1)
        
        asyncio.run(run_deploy())
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        exit(1)

if __name__ == '__main__':
    cli()
```

## Configuration Files

### 1. Model Configuration
```yaml
# config/model_config.yaml
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
  categorical:
    - device_type
    - connection_type
  temporal:
    - mean_hour_of_day
    - mean_day_of_week
    - mean_time_between_events

training:
  test_size: 0.2
  validation_size: 0.1
  random_state: 42
  n_jobs: -1
  cross_validation_folds: 5
  early_stopping: true
  patience: 10

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

### 2. Training Configuration
```yaml
# config/training_config.yaml
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

### 3. Environment Configuration
```bash
# .env.example
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

## Dependencies

### 1. Requirements
```txt
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
click==8.1.7
pyyaml==6.0.1
numpy==1.24.3
pandas==2.0.3
scikit-learn==1.3.0
joblib==1.3.2
prometheus-client==0.19.0
python-multipart==0.0.6
aiofiles==23.2.1
```

### 2. Development Requirements
```txt
# requirements-dev.txt
-r requirements.txt
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.11.0
flake8==6.1.0
mypy==1.7.1
pre-commit==3.6.0
```

## Docker Configuration

### 1. Dockerfile
```dockerfile
# Dockerfile
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
# docker-compose.yml
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

## Integration with Main MCP Service

### 1. Model Transfer
```python
# Script to transfer trained models to main MCP service
import shutil
import json
from pathlib import Path

def transfer_model_to_mcp(training_model_path: str, mcp_models_dir: str):
    """Transfer a trained model to the main MCP service."""
    
    # Copy model files
    model_name = Path(training_model_path).name
    target_path = Path(mcp_models_dir) / model_name
    
    shutil.copytree(training_model_path, target_path)
    
    # Update metadata for MCP service
    metadata_path = target_path / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Update deployment status
        metadata['deployment_info']['status'] = 'available'
        metadata['deployment_info']['transferred_at'] = datetime.now().isoformat()
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
    
    print(f"Model transferred to: {target_path}")
```

### 2. Export Data Transfer
```python
# Script to transfer export data to training service
import shutil
from pathlib import Path

def transfer_export_to_training(mcp_export_path: str, training_exports_dir: str):
    """Transfer export data from MCP service to training service."""
    
    export_name = Path(mcp_export_path).name
    target_path = Path(training_exports_dir) / export_name
    
    shutil.copy2(mcp_export_path, target_path)
    
    print(f"Export transferred to: {target_path}")
```

## Benefits of Standalone Architecture

### 1. Independence
- **No Dependencies**: Can run without the main MCP service
- **Isolated Environment**: Separate configuration and dependencies
- **Independent Deployment**: Can be deployed separately

### 2. Scalability
- **Resource Isolation**: Training doesn't impact main service performance
- **Horizontal Scaling**: Can run multiple training instances
- **Load Balancing**: Can distribute training load

### 3. Development
- **Focused Development**: Clear separation of concerns
- **Independent Testing**: Can test training without main service
- **Version Control**: Separate versioning for training system

### 4. Operations
- **Independent Monitoring**: Separate monitoring and alerting
- **Resource Management**: Dedicated resources for training
- **Backup Strategy**: Independent backup and recovery

This standalone architecture provides a clean separation between the training system and the main MCP service, allowing for independent development, deployment, and operation while maintaining clear integration points for data flow and model transfer. 