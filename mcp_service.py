import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from prometheus_client import make_asgi_app

from config import settings
from data_service import data_service

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Create Prometheus metrics endpoint
metrics_app = make_asgi_app()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI application."""
    # Startup
    logger.info("Starting AnalyzerMCPServer...")
    await data_service.initialize()
    yield
    # Shutdown
    logger.info("Shutting down AnalyzerMCPServer...")
    await data_service.close()

# Create FastAPI application
app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    lifespan=lifespan
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION
    }

# Mount Prometheus metrics
app.mount("/metrics", metrics_app)

def main():
    """Main entry point for the service."""
    uvicorn.run(
        "mcp_service:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

if __name__ == "__main__":
    main()
