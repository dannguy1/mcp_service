import os
from typing import Optional, List
from pydantic import PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Environment
    ENV: str = "development"
    DEBUG: bool = True
    
    # Service
    SERVICE_NAME: str = "AnalyzerMCPServer"
    SERVICE_VERSION: str = "0.1.0"
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8000
    
    # Database
    DB_HOST: str = "192.168.10.14"
    DB_PORT: int = 5432
    DB_NAME: str = "netmonitor_db"
    DB_USER: str = "netmonitor_user"
    DB_PASSWORD: str = "netmonitor_password"
    POSTGRES_DB: str = "netmonitor_db"
    DATABASE_URL: str = "postgresql://netmonitor_user:netmonitor_password@192.168.10.14:5432/netmonitor_db"
    POSTGRES_POOL_MIN: int = 5
    POSTGRES_POOL_MAX: int = 20
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_TTL: int = 300  # 5 minutes
    
    # Model
    MODEL_DIR: str = "models"
    MODEL_VERSION: str = "latest"
    MODEL_PATH: str = "/models"
    MODEL_UPDATE_INTERVAL: int = 3600
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_DIR: str = "/var/log/mcp_service"
    LOG_RETENTION: int = 30
    
    # Monitoring
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3000
    GRAFANA_ADMIN_USER: str = "admin"
    GRAFANA_ADMIN_PASSWORD: str = "your_secure_password"
    
    # Agent Configuration
    AGENT_INTERVAL: int = 300
    BATCH_SIZE: int = 1000
    CACHE_TTL: int = 300
    
    # Security
    API_KEY: str = "your_api_key_here"
    JWT_SECRET: str = "your_jwt_secret_here"
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "192.168.10.14"]
    
    # Resource Limits
    MAX_CONNECTIONS: int = 20
    MAX_WORKERS: int = 4
    MEMORY_LIMIT: int = 2048
    
    # Training Configuration
    TRAINING_DATA_PATH: str = "/data/training"
    TRAINING_INTERVAL: int = 86400
    MIN_TRAINING_SAMPLES: int = 1000
    
    # Export Configuration
    EXPORT_PATH: str = "/data/exports"
    EXPORT_RETENTION: int = 90
    EXPORT_FORMAT: str = "csv"
    
    # Maintenance
    BACKUP_PATH: str = "/data/backups"
    BACKUP_RETENTION: int = 30
    BACKUP_SCHEDULE: str = "0 0 * * *"
    
    @property
    def postgres_dsn(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=str(self.DB_PORT),
            path=f"/{self.DB_NAME}",
        )
    
    @property
    def redis_dsn(self) -> RedisDsn:
        return RedisDsn.build(
            scheme="redis",
            host=self.REDIS_HOST,
            port=str(self.REDIS_PORT),
            path=f"/{self.REDIS_DB}",
            user=None,
            password=self.REDIS_PASSWORD,
        )
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from environment variables
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name == "ALLOWED_HOSTS":
                return [host.strip() for host in raw_val.split(",")]
            return raw_val

# Create global settings instance
settings = Settings()
