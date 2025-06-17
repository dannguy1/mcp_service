#!/usr/bin/env python3
"""
Optimization script for low-performance devices.
This script adjusts various configuration parameters to reduce resource usage.
"""

import os
import json
import sqlite3
import psutil
import logging
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LowPerformanceOptimizer:
    """Optimizer for low-performance devices."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.config = self._load_current_config()
    
    def _load_current_config(self) -> Dict[str, Any]:
        """Load current configuration."""
        return {
            'cpu_count': psutil.cpu_count(),
            'memory_gb': psutil.virtual_memory().total / (1024**3),
            'disk_gb': psutil.disk_usage('/').total / (1024**3),
            'is_low_performance': self._is_low_performance_device()
        }
    
    def _is_low_performance_device(self) -> bool:
        """Determine if this is a low-performance device."""
        memory_gb = psutil.virtual_memory().total / (1024**3)
        cpu_count = psutil.cpu_count()
        
        # Consider device low-performance if:
        # - Less than 4GB RAM, or
        # - Less than 2 CPU cores, or
        # - Less than 10GB free disk space
        free_disk_gb = psutil.disk_usage('/').free / (1024**3)
        
        return (memory_gb < 4 or cpu_count < 2 or free_disk_gb < 10)
    
    def optimize_sqlite_config(self):
        """Optimize SQLite configuration for low-performance devices."""
        logger.info("Optimizing SQLite configuration...")
        
        db_path = self.project_root / "data" / "sqlite" / "mcp_anomalies.db"
        if not db_path.exists():
            logger.warning("SQLite database not found, skipping optimization")
            return
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Set optimized PRAGMA values for low-performance
            optimizations = {
                'journal_mode': 'DELETE',  # Faster than WAL for low-performance
                'synchronous': 'OFF',      # Fastest but less safe
                'cache_size': '-1000',     # 1MB cache
                'temp_store': 'MEMORY',    # Use memory for temp storage
                'mmap_size': '10000000000', # 10GB mmap
                'page_size': '4096',       # Standard page size
                'max_page_count': '1000000', # Limit database size
                'auto_vacuum': 'INCREMENTAL', # Incremental vacuum
                'incremental_vacuum': '1000', # Vacuum 1000 pages at a time
                'foreign_keys': 'ON',      # Keep foreign key constraints
                'checkpoint_fullfsync': 'OFF', # Disable full fsync on checkpoint
                'wal_autocheckpoint': '1000', # Checkpoint every 1000 pages
            }
            
            for pragma, value in optimizations.items():
                cursor.execute(f"PRAGMA {pragma} = {value}")
            
            # Analyze tables for better query planning
            cursor.execute("ANALYZE")
            
            conn.commit()
            conn.close()
            
            logger.info("SQLite optimization completed")
            
        except Exception as e:
            logger.error(f"Failed to optimize SQLite: {e}")
    
    def optimize_redis_config(self):
        """Optimize Redis configuration for low-performance devices."""
        logger.info("Optimizing Redis configuration...")
        
        redis_conf_path = self.project_root / "data" / "redis" / "redis.low_performance.conf"
        
        if not redis_conf_path.exists():
            logger.warning("Redis configuration not found, creating optimized config...")
            self._create_redis_config()
    
    def _create_redis_config(self):
        """Create optimized Redis configuration."""
        redis_conf_path = self.project_root / "data" / "redis" / "redis.low_performance.conf"
        redis_conf_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_content = f"""# Redis configuration for low-performance devices
port 6379
bind 127.0.0.1
timeout 0
tcp-keepalive 300
daemonize yes
supervised no
pidfile /var/run/redis_6379.pid
loglevel warning
logfile ""
databases 4
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir ./
maxmemory {min(256, int(self.config['memory_gb'] * 50))}mb
maxmemory-policy allkeys-lru
maxmemory-samples 3
appendonly no
appendfilename "appendonly.aof"
appendfsync no
no-appendfsync-on-rewrite yes
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 32mb
aof-load-truncated yes
lua-time-limit 3000
slowlog-log-slower-than 5000
slowlog-max-len 64
latency-monitor-threshold 50
notify-keyspace-events ""
hash-max-ziplist-entries 256
hash-max-ziplist-value 32
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 256
zset-max-ziplist-entries 64
zset-max-ziplist-value 32
hll-sparse-max-bytes 1500
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit slave 128mb 32mb 30
client-output-buffer-limit pubsub 16mb 4mb 30
hz 5
aof-rewrite-incremental-fsync yes
"""
        
        with open(redis_conf_path, 'w') as f:
            f.write(config_content)
        
        logger.info(f"Created optimized Redis configuration: {redis_conf_path}")
    
    def optimize_prometheus_config(self):
        """Optimize Prometheus configuration for low-performance devices."""
        logger.info("Optimizing Prometheus configuration...")
        
        prometheus_conf_path = self.project_root / "data" / "prometheus" / "prometheus.low_performance.yml"
        prometheus_conf_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_content = f"""global:
  scrape_interval: 120s
  evaluation_interval: 120s
  external_labels:
    monitor: 'mcp-service'

rule_files:
  - "prometheus_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 120s

  - job_name: 'mcp-service'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics'
    scrape_interval: 120s
    scrape_timeout: 15s

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']
    scrape_interval: 120s

storage:
  tsdb:
    retention.time: 3d
    retention.size: 500MB
    path: ./data/prometheus/data
    wal:
      retention.period: 12h
      retention.size: 50MB

alerting:
  alertmanagers:
    - static_configs:
        - targets: []
      scheme: http
      timeout: 15s
      api_version: v1

query:
  lookback_delta: 10m
  max_concurrency: 1
  timeout: 3m

query_range:
  align_query_with_step: true
  max_retries: 1
  split_queries_by_interval: 30m

remote_write:
  - url: ""
    remote_timeout: 60s
    write_relabel_configs: []
    queue_config:
      capacity: 500
      max_shards: 5
      max_samples_per_send: 50
      batch_send_deadline: 10s
      max_retries: 5
      min_backoff: 60ms
      max_backoff: 200ms

remote_read:
  - url: ""
    remote_timeout: 2m
    read_recent: false
    required_matchers:
      label: value
"""
        
        with open(prometheus_conf_path, 'w') as f:
            f.write(config_content)
        
        logger.info(f"Created optimized Prometheus configuration: {prometheus_conf_path}")
    
    def optimize_environment_variables(self):
        """Create optimized environment variables file."""
        logger.info("Creating optimized environment variables...")
        
        env_path = self.project_root / ".env.low_performance"
        
        env_content = f"""# Low Performance Device Configuration

# Database Configuration (PostgreSQL - Read Only)
DB_HOST=192.168.10.14
DB_PORT=5432
DB_NAME=netmonitor_db
DB_USER=netmonitor_user
DB_PASSWORD=netmonitor_password
DB_MIN_CONNECTIONS=2
DB_MAX_CONNECTIONS=5
DB_POOL_TIMEOUT=15

# SQLite Configuration (Optimized for low memory)
SQLITE_DB_PATH=./data/sqlite/mcp_anomalies.db
SQLITE_JOURNAL_MODE=DELETE
SQLITE_SYNCHRONOUS=OFF
SQLITE_CACHE_SIZE=-1000
SQLITE_TEMP_STORE=MEMORY
SQLITE_MMAP_SIZE=10000000000
SQLITE_PAGE_SIZE=4096
SQLITE_MAX_PAGE_COUNT=1000000

# Redis Configuration (Minimal)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_MAX_CONNECTIONS=5
REDIS_SOCKET_TIMEOUT=3

# Service Configuration (Reduced intervals)
SERVICE_HOST=0.0.0.0
SERVICE_PORT=5555
LOG_LEVEL=WARNING
ANALYSIS_INTERVAL=600
BATCH_SIZE=500
MAX_RETRIES=2
RETRY_DELAY=3
ANOMALY_RETENTION_DAYS=7

# Resource Limits (Conservative)
MAX_WORKERS={min(2, self.config['cpu_count'])}
MEMORY_LIMIT={min(512, int(self.config['memory_gb'] * 256))}
CPU_LIMIT=1

# Logging (Minimal)
LOG_DIR=./logs
LOG_RETENTION=7
LOG_FORMAT=simple
LOG_ROTATION_MAX_SIZE=10MB
LOG_ROTATION_BACKUP_COUNT=3

# Model Configuration (Lightweight)
MODEL_PATH=./models
MODEL_VERSION=1.0.0
MODEL_UPDATE_INTERVAL=7200
MODEL_CACHE_SIZE=100

# Monitoring (Reduced frequency)
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
METRICS_INTERVAL=120
HEALTH_CHECK_INTERVAL=300

# Export Configuration (Minimal)
EXPORT_PATH=./exports
EXPORT_RETENTION=30
EXPORT_BATCH_SIZE=100

# Development Configuration
NODE_ENV=development
DEBUG=false
ENABLE_FRONTEND=false
"""
        
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        logger.info(f"Created optimized environment file: {env_path}")
    
    def optimize_logging_config(self):
        """Optimize logging configuration for low-performance devices."""
        logger.info("Optimizing logging configuration...")
        
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Create logrotate configuration
        logrotate_conf = f"""{self.project_root}/logs/*.log {{
    daily
    rotate 3
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
    postrotate
        # Restart services if needed
        if [ -f {self.project_root}/backend.pid ]; then
            kill -HUP $(cat {self.project_root}/backend.pid) 2>/dev/null || true
        fi
        if [ -f {self.project_root}/mcp_service.pid ]; then
            kill -HUP $(cat {self.project_root}/mcp_service.pid) 2>/dev/null || true
        fi
    endscript
}}
"""
        
        logrotate_path = self.project_root / "logs" / "logrotate.conf"
        with open(logrotate_path, 'w') as f:
            f.write(logrotate_conf)
        
        logger.info(f"Created logrotate configuration: {logrotate_path}")
    
    def create_optimized_startup_script(self):
        """Create optimized startup script."""
        logger.info("Creating optimized startup script...")
        
        script_path = self.project_root / "scripts" / "start_optimized.sh"
        
        script_content = f"""#!/bin/bash

set -e

# Get the absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Navigate to the project root
cd "$PROJECT_ROOT"

echo "[INFO] Starting MCP Service in optimized mode for low-performance device..."

# Load optimized environment variables
if [ -f ".env.low_performance" ]; then
    echo "[INFO] Loading optimized environment variables..."
    export $(grep -v '^#' .env.low_performance | xargs)
else
    echo "[ERROR] Optimized environment file not found"
    exit 1
fi

# Check system resources
check_system_resources() {{
    echo "[INFO] Checking system resources..."
    
    # Check available memory
    available_memory=$(free -m | awk 'NR==2{{printf "%.0f", $7}}')
    if [ "$available_memory" -lt 512 ]; then
        echo "[WARN] Low memory available: ${{available_memory}}MB"
        echo "[INFO] Consider closing other applications"
    fi
    
    # Check available disk space
    available_disk=$(df -m . | awk 'NR==2{{printf "%.0f", $4}}')
    if [ "$available_disk" -lt 1024 ]; then
        echo "[WARN] Low disk space available: ${{available_disk}}MB"
        echo "[INFO] Consider cleaning up disk space"
    fi
    
    # Check CPU load
    cpu_load=$(uptime | awk -F'load average:' '{{print $2}}' | awk '{{print $1}}' | sed 's/,//')
    if (( $(echo "$cpu_load > 1.5" | bc -l) )); then
        echo "[WARN] High CPU load: $cpu_load"
    fi
}}

# Start services in optimized order
start_services() {{
    echo "[INFO] Starting services in optimized order..."
    
    # Start Redis with optimized config
    if [ -f "data/redis/redis.low_performance.conf" ]; then
        echo "[INFO] Starting Redis with optimized configuration..."
        redis-server data/redis/redis.low_performance.conf &
        echo $! > redis.pid
        sleep 3
    fi
    
    # Start backend with minimal workers
    echo "[INFO] Starting backend with minimal workers..."
    cd backend
    source ../venv/bin/activate
    uvicorn app.main:app --host 0.0.0.0 --port 5000 --workers 1 --log-level warning &
    echo $! > ../backend.pid
    cd ..
    sleep 5
    
    # Start MCP service
    echo "[INFO] Starting MCP service..."
    cd backend
    source ../venv/bin/activate
    python app/core/mcp_service.py &
    echo $! > ../mcp_service.pid
    cd ..
    sleep 3
    
    # Start frontend only if enabled
    if [ "${{ENABLE_FRONTEND:-false}}" = "true" ]; then
        echo "[INFO] Starting frontend..."
        cd frontend
        npm run dev -- --port 3000 --host 0.0.0.0 &
        echo $! > ../frontend.pid
        cd ..
    fi
}}

# Main execution
main() {{
    check_system_resources
    start_services
    
    echo "[SUCCESS] All services started in optimized mode"
    echo "[INFO] Backend: http://localhost:5000"
    echo "[INFO] MCP Service: http://localhost:5555"
    if [ "${{ENABLE_FRONTEND:-false}}" = "true" ]; then
        echo "[INFO] Frontend: http://localhost:3000"
    fi
    echo "[INFO] Press Ctrl+C to stop all services"
    
    # Wait for interrupt
    trap 'echo "[INFO] Stopping services..."; ./scripts/stop_all.sh; exit 0' INT
    wait
}}

main "$@"
"""
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        logger.info(f"Created optimized startup script: {script_path}")
    
    def run_optimizations(self):
        """Run all optimizations."""
        logger.info("Starting low-performance optimizations...")
        logger.info(f"Device specs: {self.config['cpu_count']} CPUs, {self.config['memory_gb']:.1f}GB RAM")
        
        if self.config['is_low_performance']:
            logger.info("Detected low-performance device, applying optimizations...")
        else:
            logger.info("Device appears to have adequate resources, applying conservative optimizations...")
        
        try:
            self.optimize_sqlite_config()
            self.optimize_redis_config()
            self.optimize_prometheus_config()
            self.optimize_environment_variables()
            self.optimize_logging_config()
            self.create_optimized_startup_script()
            
            logger.info("All optimizations completed successfully!")
            logger.info("To start the system with optimizations:")
            logger.info("  ./scripts/start_optimized.sh")
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}")
            raise

def main():
    """Main function."""
    project_root = os.getcwd()
    optimizer = LowPerformanceOptimizer(project_root)
    optimizer.run_optimizations()

if __name__ == "__main__":
    main() 