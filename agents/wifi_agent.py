import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import aiosmtplib
from aiohttp import web
from prometheus_client import Counter, Histogram, Gauge

from agents.base_agent import BaseAgent
from components.feature_extractor import FeatureExtractor
from components.model_manager import ModelManager
from components.anomaly_classifier import AnomalyClassifier
from components.resource_monitor import ResourceMonitor
from data_service import data_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
WIFI_LOGS_PROCESSED = Counter(
    'wifi_agent_logs_processed_total',
    'Total number of WiFi logs processed'
)

WIFI_ANOMALIES_DETECTED = Counter(
    'wifi_agent_anomalies_detected_total',
    'Total number of anomalies detected',
    ['severity', 'type']
)

WIFI_ALERTS_GENERATED = Counter(
    'wifi_agent_alerts_generated_total',
    'Total number of alerts generated',
    ['severity']
)

WIFI_PROCESSING_DURATION = Histogram(
    'wifi_agent_processing_duration_seconds',
    'Time spent processing WiFi logs'
)

WIFI_ACTIVE_DEVICES = Gauge(
    'wifi_agent_active_devices',
    'Number of active WiFi devices'
)

PROCESSING_TIME = Histogram(
    'wifi_agent_processing_seconds',
    'Time spent processing each batch of logs'
)

BATCH_SIZE = Gauge(
    'wifi_agent_batch_size',
    'Number of logs processed in each batch'
)

ANOMALIES_DETECTED = Counter(
    'wifi_agent_anomalies_total',
    'Total number of anomalies detected',
    ['type']
)

ALERTS_GENERATED = Counter(
    'wifi_agent_alerts_total',
    'Total number of alerts generated',
    ['severity']
)

class WiFiAgent(BaseAgent):
    """Agent for analyzing WiFi logs and detecting anomalies."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the WiFi agent.
        
        Args:
            config: Configuration dictionary containing:
                - processing_interval: Time between processing cycles (seconds)
                - batch_size: Number of logs to process in each cycle
                - lookback_window: Time window for historical analysis (minutes)
                - model_path: Path to the anomaly detection model
        """
        super().__init__('wifi_agent', config)
        
        # Initialize components
        self.feature_extractor = FeatureExtractor(registry=self.registry)
        self.model_manager = ModelManager(registry=self.registry)
        self.anomaly_classifier = AnomalyClassifier(registry=self.registry)
        self.resource_monitor = ResourceMonitor(registry=self.registry)
        
        # Load the anomaly detection model
        if 'model_path' in config:
            self.model_manager.load_model(config['model_path'])
        
        # Configuration
        self.processing_interval = config.get('processing_interval', 60)
        self.batch_size = config.get('batch_size', 1000)
        self.lookback_window = config.get('lookback_window', 30)  # minutes
        
        # State
        self.last_processed_ts_key = f"agent:{self.agent_name}:last_ts"
        self.last_processed_timestamp: Optional[datetime] = None
        self.active_devices: Dict[str, datetime] = {}
        
        # Initialize web application for health checks
        self.app = web.Application()
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/metrics', self.metrics)
        self.app.router.add_get('/status', self.status)
        
        # Initialize runner
        self.runner = web.AppRunner(self.app)
        
        logger.info("WiFi agent initialized with config: %s", config)

    async def process_logs(self) -> None:
        """Process WiFi logs and detect anomalies."""
        try:
            # Get logs since last processing
            logs = await self._fetch_logs()
            if not logs:
                return
            
            # Update active devices
            self._update_active_devices(logs)
            
            # Extract features
            features = self.feature_extractor.extract_features(logs)
            
            # Detect anomalies
            anomalies = await self._detect_anomalies(features)
            
            # Classify anomalies
            classified_anomalies = self.anomaly_classifier.classify_anomalies(anomalies)
            
            # Generate alerts
            await self._generate_alerts(classified_anomalies)
            
            # Update metrics
            WIFI_LOGS_PROCESSED.inc(len(logs))
            WIFI_ACTIVE_DEVICES.set(len(self.active_devices))
            
            # Update last processed timestamp
            self.last_processed_timestamp = max(log['timestamp'] for log in logs)
            
        except Exception as e:
            logger.error(f"Error processing logs: {str(e)}")
            raise

    async def _fetch_logs(self) -> List[Dict[str, Any]]:
        """Fetch logs from the database."""
        try:
            # Calculate time window
            end_time = datetime.now()
            start_time = (
                self.last_processed_timestamp
                if self.last_processed_timestamp
                else end_time - timedelta(minutes=self.lookback_window)
            )
            
            # Fetch logs
            query = """
                SELECT *
                FROM wifi_logs
                WHERE timestamp > $1
                ORDER BY timestamp ASC
                LIMIT $2
            """
            logs = await data_service.fetch_all(
                query,
                start_time,
                self.batch_size
            )
            
            return logs
            
        except Exception as e:
            logger.error(f"Error fetching logs: {str(e)}")
            raise

    def _update_active_devices(self, logs: List[Dict[str, Any]]) -> None:
        """Update the list of active devices."""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(minutes=self.lookback_window)
        
        # Update active devices
        for log in logs:
            device_id = log['device_id']
            self.active_devices[device_id] = log['timestamp']
        
        # Remove inactive devices
        self.active_devices = {
            device_id: timestamp
            for device_id, timestamp in self.active_devices.items()
            if timestamp > cutoff_time
        }

    async def _detect_anomalies(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies using the model."""
        try:
            # Prepare features for prediction
            feature_matrix = self._prepare_feature_matrix(features)
            
            # Get predictions
            predictions = self.model_manager.predict(feature_matrix)
            probabilities = self.model_manager.predict_proba(feature_matrix)
            
            # Create anomaly records
            anomalies = []
            for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
                if pred == 1:  # Anomaly detected
                    anomaly = {
                        'timestamp': datetime.now(),
                        'device_id': features['device_ids'][i],
                        'anomaly_score': float(prob[1]),  # Probability of anomaly
                        'features': {
                            k: v[i] for k, v in features.items()
                            if k != 'device_ids'
                        }
                    }
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            raise

    def _prepare_feature_matrix(self, features: Dict[str, Any]) -> List[List[float]]:
        """Prepare feature matrix for model prediction."""
        # Extract numeric features
        numeric_features = [
            k for k, v in features.items()
            if k != 'device_ids' and isinstance(v, (list, tuple))
        ]
        
        # Create feature matrix
        matrix = []
        for i in range(len(features['device_ids'])):
            row = [features[feature][i] for feature in numeric_features]
            matrix.append(row)
        
        return matrix

    async def _generate_alerts(self, anomalies: List[Dict[str, Any]]) -> None:
        """Generate alerts for detected anomalies."""
        try:
            for anomaly in anomalies:
                # Create alert record
                alert = {
                    'timestamp': datetime.now(),
                    'device_id': anomaly['device_id'],
                    'severity': anomaly['severity'],
                    'type': anomaly['type'],
                    'description': self._generate_alert_description(anomaly),
                    'status': 'new'
                }
                
                # Save alert to database
                await data_service.execute(
                    """
                    INSERT INTO alerts (
                        timestamp, device_id, severity, type,
                        description, status
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    alert['timestamp'],
                    alert['device_id'],
                    alert['severity'],
                    alert['type'],
                    alert['description'],
                    alert['status']
                )
                
                # Update metrics
                WIFI_ANOMALIES_DETECTED.labels(
                    severity=anomaly['severity'],
                    type=anomaly['type']
                ).inc()
                WIFI_ALERTS_GENERATED.labels(
                    severity=anomaly['severity']
                ).inc()
                
        except Exception as e:
            logger.error(f"Error generating alerts: {str(e)}")
            raise

    def _generate_alert_description(self, anomaly: Dict[str, Any]) -> str:
        """Generate a human-readable description of the anomaly."""
        severity = anomaly['severity'].upper()
        anomaly_type = anomaly['type'].replace('_', ' ').title()
        device_id = anomaly['device_id']
        
        return (
            f"{severity} severity {anomaly_type} anomaly detected "
            f"for device {device_id}. "
            f"Anomaly score: {anomaly['anomaly_score']:.2f}"
        )

    async def start(self) -> None:
        """Start the WiFi agent."""
        if self.running:
            logger.warning("WiFi agent is already running")
            return
        
        try:
            # Load last processed timestamp from Redis
            last_ts_str = await data_service.redis.get(self.last_processed_ts_key)
            if last_ts_str:
                self.last_processed_timestamp = datetime.fromisoformat(last_ts_str.decode())
            else:
                self.last_processed_timestamp = datetime.now() - timedelta(minutes=self.lookback_window)
            
            # Start web server for health checks
            await self.runner.setup()
            site = web.TCPSite(self.runner, 'localhost', 8080)
            await site.start()
            logger.info("Health check server started on http://localhost:8080")
            
            # Start resource monitoring
            await self.resource_monitor.start()
            
            self.running = True
            logger.info("WiFi agent started")
            
            while self.running:
                try:
                    await self._process_logs()
                except Exception as e:
                    logger.error("Error processing logs: %s", str(e))
                
                await asyncio.sleep(self.processing_interval)
                
        except Exception as e:
            logger.error("Error starting WiFi agent: %s", str(e))
            raise
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the WiFi agent."""
        if not self.running:
            return
        
        try:
            self.running = False
            await self.resource_monitor.stop()
            await self.runner.cleanup()
            logger.info("WiFi agent stopped")
        except Exception as e:
            logger.error("Error stopping WiFi agent: %s", str(e))
            raise

    async def _process_logs(self):
        """Process a batch of logs."""
        start_time = time.time()
        logger.debug("Starting log processing cycle")
        
        try:
            # Fetch logs from database
            logs = await self._fetch_logs()
            BATCH_SIZE.set(len(logs))
            
            if not logs:
                logger.debug("No logs to process")
                return
            
            # Extract features
            features = await self.feature_extractor.extract(logs)
            logger.debug("Extracted features for %d logs", len(features))
            
            # Detect anomalies
            anomalies = await self.model_manager.detect_anomalies(features)
            logger.debug("Detected %d anomalies", len(anomalies))
            
            # Classify anomalies
            for anomaly in anomalies:
                anomaly_type = await self.anomaly_classifier.classify(anomaly)
                ANOMALIES_DETECTED.labels(type=anomaly_type).inc()
                logger.info("Detected %s anomaly: %s", anomaly_type, str(anomaly))
                
                # Generate alert
                alert = await self._create_alert(anomaly, anomaly_type)
                if alert:
                    ALERTS_GENERATED.labels(severity=alert['severity']).inc()
                    logger.info("Generated alert: %s", str(alert))
            
            # Update last processed timestamp in Redis
            if logs:
                latest_log_ts = max(log['timestamp'] for log in logs)
                self.last_processed_timestamp = latest_log_ts
                await data_service.redis.set(
                    self.last_processed_ts_key,
                    latest_log_ts.isoformat()
                )
            
            # Update metrics
            duration = time.time() - start_time
            PROCESSING_TIME.observe(duration)
            logger.debug("Completed log processing cycle in %.2f seconds", duration)
            
        except Exception as e:
            logger.error("Error in log processing cycle: %s", str(e))
            raise

    async def _create_alert(self, anomaly: Dict, anomaly_type: str) -> Optional[Dict]:
        """Create an alert for an anomaly."""
        try:
            alert = {
                'timestamp': time.time(),
                'device_id': anomaly.get('device_id'),
                'severity': self._determine_severity(anomaly),
                'type': anomaly_type,
                'description': self._generate_description(anomaly, anomaly_type),
                'status': 'new'
            }
            
            # Save alert to database
            query = """
                INSERT INTO alerts (timestamp, device_id, severity, type, description, status)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
            """
            result = await data_service.fetch_one(
                query,
                alert['timestamp'],
                alert['device_id'],
                alert['severity'],
                alert['type'],
                alert['description'],
                alert['status']
            )
            
            return dict(result) if result else None
            
        except Exception as e:
            logger.error("Error creating alert: %s", str(e))
            return None

    def _determine_severity(self, anomaly: Dict) -> str:
        """Determine alert severity based on anomaly characteristics."""
        # Implement severity determination logic
        return 'high'  # Placeholder

    def _generate_description(self, anomaly: Dict, anomaly_type: str) -> str:
        """Generate alert description."""
        # Implement description generation logic
        return f"Detected {anomaly_type} anomaly"  # Placeholder

    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint."""
        try:
            # Check database connection
            await data_service.fetch_one("SELECT 1")
            
            # Check resource monitor
            if not self.resource_monitor.is_running():
                return web.json_response({
                    'status': 'error',
                    'message': 'Resource monitor not running'
                }, status=500)
            
            return web.json_response({
                'status': 'healthy',
                'timestamp': time.time()
            })
            
        except Exception as e:
            logger.error("Health check failed: %s", str(e))
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=500)

    async def metrics(self, request: web.Request) -> web.Response:
        """Metrics endpoint."""
        try:
            from prometheus_client import generate_latest
            return web.Response(
                body=generate_latest(),
                content_type='text/plain'
            )
        except Exception as e:
            logger.error("Error generating metrics: %s", str(e))
            return web.json_response({
                'status': 'error',
                'message': str(e)
            }, status=500)

    async def status(self, request: web.Request) -> web.Response:
        """Status endpoint."""
        return web.json_response({
            'status': 'running' if self.running else 'stopped',
            'processing_interval': self.processing_interval,
            'batch_size': self.batch_size,
            'lookback_window': self.lookback_window,
            'timestamp': time.time()
        })

    async def _send_email_alert(self, anomalies: List[Dict[str, Any]]) -> None:
        """Send email alerts for detected anomalies."""
        try:
            # Build message body
            msg = self._build_email_message(anomalies)
            
            # Send email asynchronously
            await aiosmtplib.send(
                msg,
                hostname=self.config['smtp_server'],
                port=self.config['smtp_port'],
                username=self.config['smtp_user'],
                password=self.config['smtp_pass'],
                start_tls=True
            )
            self.logger.info("Successfully sent email alert via aiosmtplib")
        except Exception as e:
            self.logger.error(f"Failed to send async email alert: {e}")
            raise
