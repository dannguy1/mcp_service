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
import asyncio
from contextlib import asynccontextmanager

# Load environment variables from .env file
load_dotenv()

# Import existing components
from app.mcp_service.data_service import DataService
from app.mcp_service.components.resource_monitor import ResourceMonitor
from app.components.model_manager import ModelManager
from app.models.config import ModelConfig
from app.mcp_service.components.agent_registry import agent_registry
from app.mcp_service.status_manager import MCPStatusManager
from app.config.config import config
from app.db import get_db_connection
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Import routers
from app.api.endpoints.export import router as export_router
from app.api.endpoints.model_management import router as model_management_router
from app.api.endpoints.agent_management import router as agent_management_router

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
resource_monitor = ResourceMonitor()
status_manager = MCPStatusManager(redis_host=config.redis['host'], redis_port=config.redis['port'])

# Initialize main ModelManager for ML model loading
model_config = ModelConfig()
main_model_manager = ModelManager(model_config)

# Set Redis client for model manager
main_model_manager.set_redis_client(redis_client)

# Set Redis client for agent registry
agent_registry.redis_client = redis_client

# Define lifespan function before app creation
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global data_service, resource_monitor, status_manager, analysis_task
    
    # Startup
    try:
        # Initialize services
        data_service = DataService(config)
        resource_monitor = ResourceMonitor()
        status_manager = MCPStatusManager(redis_host=config.redis['host'], redis_port=config.redis['port'])
        
        # Start services
        await data_service.start()
        status_manager.start_status_updates()
        
        # Create and start agents using the Generic Agent Framework
        logger.info("Creating agents using Generic Agent Framework...")
        
        # Get all available agent configurations and create agents
        agent_configs = agent_registry.list_agent_configs()
        logger.info(f"Found {len(agent_configs)} agent configurations")
        
        for config_info in agent_configs:
            agent_id = config_info['agent_id']
            agent_name = config_info['name']
            agent_type = config_info['agent_type']
            
            logger.info(f"Creating {agent_type} agent: {agent_name} ({agent_id})")
            
            # Create agent from configuration
            agent = agent_registry.create_agent(agent_id, data_service, main_model_manager)
            if agent:
                # Register and start the agent
                agent_registry.register_agent(agent, agent_id)
                await agent.start()
                logger.info(f"{agent_name} ({agent_id}) created and started successfully")
            else:
                logger.warning(f"Failed to create {agent_name} ({agent_id}) from configuration")
        
        # Start background analysis task
        analysis_task = asyncio.create_task(run_analysis_cycles())
        
        logger.info("MCP Service components initialized successfully")
        
        # Scan for new models
        new_models = await main_model_manager.scan_model_directory()
        if new_models:
            logger.info(f"Found {len(new_models)} new models during startup")
        
        # Load the most recent deployed model
        models = await main_model_manager.list_models()
        deployed_models = [m for m in models if m['status'] == 'deployed']
        
        if deployed_models:
            # Use 'created_at' field instead of 'imported_at'
            latest_model = max(deployed_models, key=lambda x: x.get('created_at', ''))
            await main_model_manager.load_model_version(latest_model['version'])
            logger.info(f"Loaded deployed model: {latest_model['version']}")
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP Service components: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    try:
        # Cancel background task
        if analysis_task:
            analysis_task.cancel()
            try:
                await analysis_task
            except asyncio.CancelledError:
                pass
        
        # Stop and unregister all agents
        agents = agent_registry.list_agents()
        for agent_info in agents:
            agent_id = agent_info['id']
            agent = agent_registry.get_agent(agent_id)
            if agent:
                await agent.stop()
                agent_registry.unregister_agent(agent_id)
                logger.info(f"Stopped and unregistered agent: {agent_id}")
        
        # Stop services
        if data_service:
            await data_service.stop()
        if status_manager:
            status_manager.stop_status_updates()
        
        logger.info("MCP Service components stopped successfully")
    except Exception as e:
        logger.error(f"Failed to stop MCP Service components: {e}", exc_info=True)
        raise

async def run_analysis_cycles():
    """Background task to run agent analysis cycles."""
    try:
        while True:
            # Get all registered agents and run their analysis cycles
            agents = agent_registry.list_agents()
            
            for agent_info in agents:
                agent_id = agent_info['id']
                agent = agent_registry.get_agent(agent_id)
                
                if agent and agent.is_running:
                    try:
                        await agent.run_analysis_cycle()
                        logger.debug(f"{agent_id} analysis cycle completed successfully")
                    except Exception as e:
                        logger.error(f"Error in {agent_id} analysis cycle: {e}")
                else:
                    logger.debug(f"{agent_id} not running, skipping analysis cycle")
            
            # Wait for next cycle (default 5 minutes)
            await asyncio.sleep(getattr(config, 'ANALYSIS_INTERVAL', 300))
    except asyncio.CancelledError:
        logger.info("Analysis cycles task cancelled")
        raise
    except Exception as e:
        logger.error(f"Error in analysis cycles task: {e}")
        raise

# Create FastAPI app
app = FastAPI(
    title="MCP Service API",
    description="API for MCP Service",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
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
app.include_router(agent_management_router, prefix="/api/v1/agents")

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
        
        # Check if services are running (handle uninitialized services)
        services_healthy = True
        
        if data_service:
            services_healthy = services_healthy and data_service.is_running()
        else:
            services_healthy = False
            
        if main_model_manager:
            services_healthy = services_healthy and main_model_manager.is_running()
        else:
            services_healthy = False
            
        if wifi_agent:
            services_healthy = services_healthy and wifi_agent.check_running()
        else:
            services_healthy = False
            
        if log_level_agent:
            services_healthy = services_healthy and log_level_agent.is_running
        else:
            services_healthy = False
            
        if resource_monitor:
            services_healthy = services_healthy and resource_monitor.is_running()
        else:
            services_healthy = False
        
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

# Logs endpoint
@app.get("/api/v1/logs")
async def get_logs(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    level: Optional[str] = Query(None, description="Log level filter (comma-separated for multiple)"),
    program: Optional[str] = Query(None, description="Program filter (comma-separated for multiple)"),
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
            
        # Handle program filter - support multiple programs
        programs = None
        if program:
            programs = [p.strip() for p in program.split(',') if p.strip()]
            
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
        
        # Apply level filter if provided - support multiple levels
        if level:
            levels = [l.strip().lower() for l in level.split(',') if l.strip()]
            transformed_logs = [log for log in transformed_logs if log["level"].lower() in levels]
            
        # Apply pagination
        total_logs = len(transformed_logs)
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_logs = transformed_logs[start_index:end_index]
        
        # Get unique programs from the data for filters
        unique_programs = [p for p in set(log["process"] for log in transformed_logs) if p]
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
        models = main_model_manager.get_all_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/models/{model_id}/info")
async def get_model_info(model_id: str):
    """Get model details"""
    try:
        model_info = main_model_manager.get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        return model_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/models/{model_id}/activate")
async def activate_model(model_id: str):
    """Activate a model"""
    try:
        success = main_model_manager.activate_model(model_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to activate model")
        return {"status": "success", "message": f"Model {model_id} activated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/models/{model_id}/deactivate")
async def deactivate_model(model_id: str):
    """Deactivate a model"""
    try:
        success = main_model_manager.deactivate_model(model_id)
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
        
        model_config = ModelConfig()
        model_manager = ModelManager(model_config)
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
        
        model_config = ModelConfig()
        model_manager = ModelManager(model_config)
        
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
        
        model_config = ModelConfig()
        model_manager = ModelManager(model_config)
        
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

# Database configuration endpoints
@app.get("/api/v1/settings/database")
async def get_database_config():
    """Get current database configuration"""
    try:
        return {
            "host": os.getenv('DB_HOST', 'localhost'),
            "port": int(os.getenv('DB_PORT', '5432')),
            "database": os.getenv('DB_NAME', 'netmonitor_db'),
            "user": os.getenv('DB_USER', 'netmonitor_user'),
            "password": os.getenv('DB_PASSWORD', 'netmonitor_password'),
            "min_connections": int(os.getenv('DB_MIN_CONNECTIONS', '5')),
            "max_connections": int(os.getenv('DB_MAX_CONNECTIONS', '20')),
            "pool_timeout": int(os.getenv('DB_POOL_TIMEOUT', '30'))
        }
    except Exception as e:
        logger.error(f"Error getting database config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/settings/database")
async def update_database_config(config: Dict[str, Any]):
    """Update database configuration"""
    try:
        # Validate required fields
        required_fields = ['host', 'port', 'database', 'user', 'password']
        for field in required_fields:
            if field not in config:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Test the new database connection
        test_config = {
            'host': config['host'],
            'port': config['port'],
            'database': config['database'],
            'user': config['user'],
            'password': config['password']
        }
        
        # Try to connect with the new configuration
        try:
            import asyncpg
            conn = await asyncpg.connect(
                host=test_config['host'],
                port=test_config['port'],
                database=test_config['database'],
                user=test_config['user'],
                password=test_config['password']
            )
            await conn.close()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Database connection test failed: {str(e)}")
        
        # If connection test passes, update environment variables
        # Note: In a production environment, you might want to write to a config file
        # or use a configuration management system instead of environment variables
        os.environ['DB_HOST'] = str(config['host'])
        os.environ['DB_PORT'] = str(config['port'])
        os.environ['DB_NAME'] = str(config['database'])
        os.environ['DB_USER'] = str(config['user'])
        os.environ['DB_PASSWORD'] = str(config['password'])
        
        if 'min_connections' in config:
            os.environ['DB_MIN_CONNECTIONS'] = str(config['min_connections'])
        if 'max_connections' in config:
            os.environ['DB_MAX_CONNECTIONS'] = str(config['max_connections'])
        if 'pool_timeout' in config:
            os.environ['DB_POOL_TIMEOUT'] = str(config['pool_timeout'])
        
        logger.info("Database configuration updated successfully")
        
        return {
            "status": "success",
            "message": "Database configuration updated successfully",
            "config": config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating database config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/settings/database/test")
async def test_database_connection(config: Dict[str, Any]):
    """Test database connection with provided configuration"""
    try:
        # Validate required fields
        required_fields = ['host', 'port', 'database', 'user', 'password']
        for field in required_fields:
            if field not in config:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Validate field types and values
        try:
            port = int(config['port'])
            if port <= 0 or port > 65535:
                raise ValueError("Port must be between 1 and 65535")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid port number")
        
        if not config['host'] or not config['database'] or not config['user']:
            raise HTTPException(status_code=400, detail="Host, database name, and user cannot be empty")
        
        # Test the database connection with timeout
        try:
            import asyncpg
            import asyncio
            
            # Create connection with timeout
            conn = await asyncio.wait_for(
                asyncpg.connect(
                    host=config['host'],
                    port=port,
                    database=config['database'],
                    user=config['user'],
                    password=config['password'],
                    timeout=10.0  # 10 second timeout
                ),
                timeout=15.0  # Overall timeout including connection establishment
            )
            
            # Test a simple query
            result = await asyncio.wait_for(
                conn.fetchval('SELECT 1'),
                timeout=5.0  # Query timeout
            )
            
            await conn.close()
            
            return {
                "status": "success",
                "message": "Database connection test successful",
                "details": {
                    "host": config['host'],
                    "port": port,
                    "database": config['database'],
                    "user": config['user'],
                    "test_query_result": result
                }
            }
            
        except asyncio.TimeoutError:
            return {
                "status": "error",
                "message": "Database connection timed out. Please check the host, port, and network connectivity.",
                "details": {
                    "host": config['host'],
                    "port": port,
                    "database": config['database'],
                    "user": config['user'],
                    "error_type": "timeout"
                }
            }
        except asyncpg.InvalidPasswordError:
            return {
                "status": "error",
                "message": "Invalid username or password. Please check your credentials.",
                "details": {
                    "host": config['host'],
                    "port": port,
                    "database": config['database'],
                    "user": config['user'],
                    "error_type": "authentication"
                }
            }
        except asyncpg.InvalidCatalogNameError:
            return {
                "status": "error",
                "message": f"Database '{config['database']}' does not exist. Please check the database name.",
                "details": {
                    "host": config['host'],
                    "port": port,
                    "database": config['database'],
                    "user": config['user'],
                    "error_type": "database_not_found"
                }
            }
        except asyncpg.InvalidAuthorizationSpecificationError:
            return {
                "status": "error",
                "message": f"User '{config['user']}' does not exist or has insufficient privileges.",
                "details": {
                    "host": config['host'],
                    "port": port,
                    "database": config['database'],
                    "user": config['user'],
                    "error_type": "user_not_found"
                }
            }
        except asyncpg.ConnectionDoesNotExistError:
            return {
                "status": "error",
                "message": "Unable to establish connection to the database server. Please check the host and port.",
                "details": {
                    "host": config['host'],
                    "port": port,
                    "database": config['database'],
                    "user": config['user'],
                    "error_type": "connection_failed"
                }
            }
        except Exception as e:
            error_message = str(e)
            if "connection" in error_message.lower():
                return {
                    "status": "error",
                    "message": f"Connection failed: {error_message}. Please check the host, port, and ensure the database server is running.",
                    "details": {
                        "host": config['host'],
                        "port": port,
                        "database": config['database'],
                        "user": config['user'],
                        "error_type": "connection_error",
                        "raw_error": error_message
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": f"Database connection test failed: {error_message}",
                    "details": {
                        "host": config['host'],
                        "port": port,
                        "database": config['database'],
                        "user": config['user'],
                        "error_type": "unknown",
                        "raw_error": error_message
                    }
                }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing database connection: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 