from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import logging
from typing import Dict, Any, List, Optional
import os
import redis
from datetime import datetime, timedelta
import psutil
from sqlalchemy import text
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import existing components
from app.mcp_service.data_service import DataService
from app.mcp_service.agents.wifi_agent import WiFiAgent
from app.mcp_service.components.resource_monitor import ResourceMonitor
from app.mcp_service.components.model_manager import model_manager
from app.mcp_service.status_manager import MCPStatusManager
from app.config.config import config
from app.db import get_db_connection
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Import routers
from app.api.endpoints.export import router as export_router
from app.api.endpoints.model_management import router as model_management_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Redis client
redis_client = redis.Redis(
    host=config.redis['host'],
    port=config.redis['port'],
    db=config.redis['db'],
    decode_responses=True,
    socket_timeout=config.redis['socket_timeout'],
    socket_connect_timeout=config.redis['socket_timeout']
)

# Initialize MCP Service components
data_service = DataService(config=config)
wifi_agent = WiFiAgent(config=config, data_service=data_service, model_manager=model_manager)
resource_monitor = ResourceMonitor()
status_manager = MCPStatusManager(redis_host=config.redis['host'], redis_port=config.redis['port'])

# Set Redis client for model manager
model_manager.set_redis_client(redis_client)

# Create FastAPI app
app = FastAPI(
    title="MCP Service API",
    description="API for MCP Service",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)

# Configure CORS
# Parse CORS origins from environment variable or use defaults
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://192.168.10.8:3000,http://192.168.10.12:3000")
allowed_origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

# Create static directory if it doesn't exist
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(export_router, prefix="/api/v1")
app.include_router(model_management_router, prefix="/api/v1/model-management")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint that redirects to API documentation"""
    return {"message": "Welcome to MCP Service API. Visit /api/v1/docs for documentation."}

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint that verifies critical services"""
    try:
        # Check Redis connection
        redis_client.ping()
        
        # Check database connection
        with get_db_connection() as conn:
            conn.execute(text('SELECT 1'))
        
        # Check if services are running
        services_healthy = all([
            data_service.is_running(),
            model_manager.is_running(),
            wifi_agent.check_running(),
            resource_monitor.is_running()
        ])
        
        if not services_healthy:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "error": "One or more services are not running"}
            )
        
        return {"status": "healthy"}
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Server status endpoint
@app.get("/api/v1/server/status")
async def get_server_status():
    """Get detailed server status information"""
    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get service statuses
        services = {
            'database': {
                'status': 'healthy',
                'last_check': datetime.now().isoformat(),
                'error': None
            },
            'redis': {
                'status': 'healthy',
                'last_check': datetime.now().isoformat(),
                'error': None
            },
            'model_service': {
                'status': 'healthy',
                'last_check': datetime.now().isoformat(),
                'error': None
            },
            'data_source': {
                'status': 'healthy',
                'last_check': datetime.now().isoformat(),
                'error': None
            },
            'mcp_service': {
                'status': 'healthy',
                'last_check': datetime.now().isoformat(),
                'error': None
            }
        }

        # Check database connection
        try:
            with get_db_connection() as conn:
                conn.execute(text('SELECT 1'))
        except Exception as e:
            services['database']['status'] = 'error'
            services['database']['error'] = str(e)

        # Check Redis connection
        try:
            redis_client.ping()
        except Exception as e:
            services['redis']['status'] = 'error'
            services['redis']['error'] = str(e)

        # Calculate overall system status
        system_status = 'healthy'
        if any(service['status'] == 'error' for service in services.values()):
            system_status = 'unhealthy'

        return {
            'status': system_status,
            'version': '1.0.0',
            'uptime': get_uptime(),
            'components': {
                'database': services['database']['status'],
                'model': services['model_service']['status'],
                'cache': services['redis']['status']
            },
            'metrics': {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'response_time': 120  # Placeholder value
            },
            'services': [
                {
                    'name': service_name,
                    'status': service_info['status'],
                    'uptime': get_uptime(),
                    'memoryUsage': memory.percent
                }
                for service_name, service_info in services.items()
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_uptime() -> str:
    """Get system uptime in human readable format"""
    uptime_seconds = psutil.boot_time()
    uptime = datetime.now() - datetime.fromtimestamp(uptime_seconds)
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Start MCP Service components
        await data_service.start()
        await wifi_agent.start()
        # ResourceMonitor doesn't have start/stop methods, just initialize it
        model_manager.start()
        status_manager.start_status_updates()
        logger.info("MCP Service components initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MCP Service components: {e}", exc_info=True)
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown"""
    try:
        # Stop MCP Service components
        await data_service.stop()
        await wifi_agent.stop()
        # ResourceMonitor doesn't have start/stop methods
        model_manager.stop()
        status_manager.stop_status_updates()
        logger.info("MCP Service components stopped successfully")
    except Exception as e:
        logger.error(f"Failed to stop MCP Service components: {e}", exc_info=True)
        raise

# Logs endpoint
@app.get("/api/v1/logs")
async def get_logs(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    level: Optional[str] = Query(None, description="Log level filter"),
    program: Optional[str] = Query(None, description="Program filter"),
    page: int = Query(1, description="Page number"),
    per_page: int = Query(25, description="Number of logs per page")
):
    """Get filtered logs"""
    try:
        # Handle time range - if not provided, query all logs
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError as e:
                logger.error(f"Invalid start date format: {e}")
                raise HTTPException(status_code=400, detail="Invalid start date format")
                
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError as e:
                logger.error(f"Invalid end date format: {e}")
                raise HTTPException(status_code=400, detail="Invalid end date format")
            
        # Set programs - if specific program requested, use it; otherwise get all logs
        programs = None
        if program:
            programs = [program]
            
        # Get logs from the real database
        logs = await data_service.get_logs_by_program(start_datetime, end_datetime, programs)
        
        # Transform logs to match frontend expectations
        transformed_logs = []
        for log in logs:
            transformed_log = {
                "id": str(log.get("id", "")),
                "device_id": log.get("device_id", ""),
                "device_ip": log.get("device_ip", ""),
                "timestamp": log.get("timestamp", ""),
                "level": log.get("log_level", ""),
                "process": log.get("process_name", ""),
                "message": log.get("message", ""),
                "raw_message": log.get("raw_message", ""),
                "structured_data": log.get("structured_data", {}),
                "pushed_to_ai": log.get("pushed_to_ai", False),
                "pushed_at": log.get("pushed_at", None),
                "push_attempts": log.get("push_attempts", 0),
                "last_push_error": log.get("last_push_error", None)
            }
            transformed_logs.append(transformed_log)
        
        # Apply level filter if provided
        if level:
            transformed_logs = [log for log in transformed_logs if log["level"] == level.upper()]
            
        # Apply pagination
        total_logs = len(transformed_logs)
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_logs = transformed_logs[start_index:end_index]
        
        # Get unique programs from the data for filters
        unique_programs = list(set(log["process"] for log in transformed_logs))
        unique_programs.sort()
        
        return {
            "logs": paginated_logs,
            "total": total_logs,
            "filters": {
                "severity": ["emergency", "alert", "critical", "error", "warning", "notice", "info", "debug"],
                "programs": unique_programs
            }
        }
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Anomalies endpoint
@app.get("/api/v1/anomalies")
async def get_anomalies(
    limit: int = Query(100, description="Number of anomalies to return"),
    status: Optional[str] = Query(None, description="Anomaly status filter")
):
    """Get recent anomalies"""
    try:
        # This would query the database in a real implementation
        # For now, return mock data
        anomalies = [
            {
                "id": 1,
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                "type": "network",
                "severity": 8,
                "description": "Unusual network traffic pattern detected",
                "status": "active"
            }
        ]
        return anomalies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard endpoint
@app.get("/api/v1/dashboard")
async def get_dashboard():
    """Get dashboard data"""
    try:
        # Get system status
        system_status = {
            "status": "healthy",
            "uptime": get_uptime(),
            "version": "1.0.0",
            "metrics": {
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
                "response_time": 120  # Placeholder value
            },
            "connections": {
                "mcp_service": {
                    "status": "connected",
                    "last_check": datetime.now().isoformat(),
                    "error": None
                },
                "backend_service": {
                    "status": "connected",
                    "last_check": datetime.now().isoformat(),
                    "error": None
                },
                "data_source": {
                    "status": "connected",
                    "last_check": datetime.now().isoformat(),
                    "error": None
                },
                "database": {
                    "status": "connected",
                    "last_check": datetime.now().isoformat(),
                    "error": None
                },
                "model_service": {
                    "status": "connected",
                    "last_check": datetime.now().isoformat(),
                    "error": None
                },
                "redis": {
                    "status": "connected",
                    "last_check": datetime.now().isoformat(),
                    "error": None
                }
            }
        }
        
        # Get recent anomalies (mock data for now)
        recent_anomalies = [
            {
                "id": "1",
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                "type": "network",
                "severity": 8,
                "description": "Unusual network traffic pattern detected",
                "status": "detected"
            },
            {
                "id": "2",
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "type": "system",
                "severity": 6,
                "description": "High CPU usage detected",
                "status": "investigating"
            },
            {
                "id": "3",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "type": "security",
                "severity": 9,
                "description": "Multiple failed login attempts",
                "status": "resolved"
            }
        ]
        
        return {
            "system_status": system_status,
            "recent_anomalies": recent_anomalies,
            "performance_metrics": system_status["metrics"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Models endpoints
@app.get("/api/v1/models")
async def get_models():
    """Get list of models"""
    try:
        models = model_manager.get_all_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/models/{model_id}/info")
async def get_model_info(model_id: str):
    """Get model details"""
    try:
        model_info = model_manager.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        return model_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/models/{model_id}/activate")
async def activate_model(model_id: str):
    """Activate a model"""
    try:
        success = model_manager.activate_model(model_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to activate model")
        return {"status": "success", "message": f"Model {model_id} activated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/models/{model_id}/deactivate")
async def deactivate_model(model_id: str):
    """Deactivate a model"""
    try:
        success = model_manager.deactivate_model(model_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to deactivate model")
        return {"status": "success", "message": f"Model {model_id} deactivated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/models/{model_id}/deploy")
async def deploy_model(model_id: str):
    """Deploy a model"""
    try:
        # This would implement model deployment logic
        return {"status": "success", "message": f"Model {model_id} deployed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/models/current")
async def get_current_model():
    """Get current model information"""
    try:
        # Get current model info from the enhanced ModelManager
        from app.components.model_manager import ModelManager
        from app.models.config import ModelConfig
        
        config = ModelConfig()
        model_manager = ModelManager(config)
        current_model_info = model_manager.get_model_info()
        
        if not current_model_info:
            return {"message": "No model currently loaded"}
        
        return current_model_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/models/{version}/load")
async def load_model_version(version: str):
    """Load a specific model version"""
    try:
        from app.components.model_manager import ModelManager
        from app.models.config import ModelConfig
        
        config = ModelConfig()
        model_manager = ModelManager(config)
        
        # Find model path
        models = await model_manager.list_models()
        model_info = next((m for m in models if m['version'] == version), None)
        
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Load the model
        success = await model_manager.load_model_version(version)
        
        if success:
            return {
                "version": version,
                "status": "loaded",
                "model_info": model_manager.get_model_info()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to load model")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/models/analyze")
async def analyze_logs(logs: List[Dict[str, Any]]):
    """Analyze logs with current model"""
    try:
        from app.components.model_manager import ModelManager
        from app.models.config import ModelConfig
        from app.components.feature_extractor import FeatureExtractor
        import numpy as np
        
        config = ModelConfig()
        model_manager = ModelManager(config)
        
        # Check if model is loaded
        if not model_manager.is_model_loaded():
            raise HTTPException(status_code=400, detail="No model loaded")
        
        # Extract features from logs
        feature_extractor = FeatureExtractor()
        features = []
        
        for log in logs:
            # Extract features from log entry
            log_features = feature_extractor.extract_features(log)
            features.append(log_features)
        
        if not features:
            raise HTTPException(status_code=400, detail="No valid features extracted from logs")
        
        # Convert to numpy array
        features_array = np.array(features)
        
        # Make predictions
        predictions = await model_manager.predict(features_array)
        probabilities = await model_manager.predict_proba(features_array)
        
        # Format results
        results = []
        for i, log in enumerate(logs):
            prediction = predictions[i] if i < len(predictions) else 0
            prob = probabilities[i][0] if i < len(probabilities) and len(probabilities[i]) > 0 else 0
            
            results.append({
                "log_entry": log,
                "analysis_result": {
                    "prediction": int(prediction),
                    "anomaly_score": float(prob),
                    "is_anomaly": bool(prediction == 1),
                    "model_version": model_manager.current_model_version,
                    "timestamp": datetime.now().isoformat()
                },
                "analysis_timestamp": datetime.now().isoformat(),
                "model_version": model_manager.current_model_version
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error analyzing logs: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 