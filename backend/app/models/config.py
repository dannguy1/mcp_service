from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import os
import yaml
from pathlib import Path

class ModelParameters(BaseModel):
    """Model training parameters."""
    type: str = Field(default="isolation_forest", description="Type of model to use")
    n_estimators: int = Field(default=100, description="Number of trees in the forest")
    max_samples: str = Field(default="auto", description="Maximum samples per tree")
    contamination: float = Field(default=0.1, description="Expected proportion of outliers")
    random_state: int = Field(default=42, description="Random seed for reproducibility")

class FeatureConfig(BaseModel):
    """Feature engineering configuration."""
    numeric: List[str] = Field(default_factory=list, description="Numeric features")
    categorical: List[str] = Field(default_factory=list, description="Categorical features")
    temporal: List[str] = Field(default_factory=list, description="Temporal features")

class TrainingConfig(BaseModel):
    """Training configuration."""
    test_size: float = Field(default=0.2, description="Proportion of data for testing")
    validation_size: float = Field(default=0.1, description="Proportion of data for validation")
    random_state: int = Field(default=42, description="Random seed")
    n_jobs: int = Field(default=-1, description="Number of parallel jobs")

class StorageConfig(BaseModel):
    """Model storage configuration."""
    directory: str = Field(default="models", description="Directory to save models")
    version_format: str = Field(default="%Y%m%d_%H%M%S", description="Version format string")
    keep_last_n_versions: int = Field(default=5, description="Number of versions to keep")
    backup_enabled: bool = Field(default=True, description="Enable model backup")
    compression: bool = Field(default=True, description="Enable model compression")
    retention_days: int = Field(default=30, description="Model retention period in days")

class EvaluationConfig(BaseModel):
    """Model evaluation configuration."""
    metrics: List[str] = Field(default_factory=list, description="Evaluation metrics")
    thresholds: Dict[str, float] = Field(default_factory=dict, description="Performance thresholds")

class IntegrationConfig(BaseModel):
    """Integration configuration for training service."""
    training_service_path: str = Field(default="/home/dannguyen/WNC/mcp_training", 
                                      description="Path to training service")
    auto_import: bool = Field(default=False, description="Auto-import new models")
    import_interval: int = Field(default=3600, description="Import check interval (seconds)")
    validate_imports: bool = Field(default=True, description="Validate imported models")

class MonitoringConfig(BaseModel):
    """Monitoring configuration for model inference."""
    enable_drift_detection: bool = Field(default=True, description="Enable drift detection")
    drift_threshold: float = Field(default=0.1, description="Drift detection threshold")
    performance_tracking: bool = Field(default=True, description="Enable performance tracking")
    resource_monitoring: bool = Field(default=True, description="Enable resource monitoring")
    model_health_checks: bool = Field(default=True, description="Enable model health checks")
    alerting: Dict[str, Any] = Field(default_factory=lambda: {
        "enabled": True,
        "email_notifications": False,
        "slack_notifications": False
    }, description="Alerting configuration")

class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")
    file: str = Field(default="logs/model_training.log", description="Log file path")
    rotation: Dict[str, Any] = Field(default_factory=lambda: {
        "max_size": "100MB",
        "backup_count": 10
    }, description="Log rotation configuration")

class ModelConfig(BaseModel):
    """Enhanced configuration for model management and inference."""
    version: str = Field(default="2.0.0", description="Configuration version")
    
    # Model parameters
    model: ModelParameters = Field(default_factory=ModelParameters)
    
    # Feature configuration
    features: FeatureConfig = Field(default_factory=FeatureConfig)
    
    # Training configuration
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    
    # Storage configuration
    storage: StorageConfig = Field(default_factory=StorageConfig)
    
    # Evaluation configuration
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)
    
    # Integration configuration
    integration: IntegrationConfig = Field(default_factory=IntegrationConfig)
    
    # Monitoring configuration
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    
    # Logging configuration
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    model_config = {
        'protected_namespaces': ()  # Disable protected namespaces
    }
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'ModelConfig':
        """Load configuration from YAML file."""
        with open(yaml_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return cls(**config_dict)
    
    def to_yaml(self, yaml_path: str) -> None:
        """Save configuration to YAML file."""
        config_dict = self.model_dump()
        with open(yaml_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)
    
    def get_model_path(self) -> Path:
        """Get the full path to the model file."""
        return Path(self.storage.directory) / "versions" / "model.joblib"
    
    def get_metadata_path(self) -> Path:
        """Get the full path to the model metadata file."""
        return Path(self.storage.directory) / "versions" / "model_metadata.yaml"

    # Model architecture settings
    version_format: str = "%Y%m%d_%H%M%S"
    
    # Inference settings
    prediction_threshold: float = 0.8
    batch_size: int = 1000 