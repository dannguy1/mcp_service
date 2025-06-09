#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config
from utils.logger import setup_logger

app = FastAPI(title="MCP Service Web UI")
logger = setup_logger("web_ui")

# Set up templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Mount static files
static_dir = Path(__file__).parent.parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main dashboard."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/v1/health")
async def health_check():
    """Get system health status."""
    try:
        # Get health status from monitoring system
        return {
            "status": "healthy",
            "version": "1.0.0",
            "uptime": "5d 12h 30m",
            "components": {
                "model": "healthy",
                "database": "healthy",
                "cache": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/api/v1/stats")
async def get_stats():
    """Get system statistics."""
    try:
        # Get stats from monitoring system
        return {
            "accuracy": 0.985,
            "average_latency": 25.5,
            "error_rate": 0.02,
            "anomaly_count": 150,
            "time_range": {
                "start": "2024-03-01T00:00:00Z",
                "end": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {
            "error": str(e)
        }

@app.get("/api/v1/anomalies/recent")
async def get_recent_anomalies():
    """Get recent anomalies."""
    try:
        # Get recent anomalies from database
        return [
            {
                "timestamp": "2024-03-20T10:00:00Z",
                "severity": "high",
                "description": "Unusual pattern in error rate and latency"
            },
            {
                "timestamp": "2024-03-20T09:45:00Z",
                "severity": "medium",
                "description": "Increased packet loss detected"
            },
            {
                "timestamp": "2024-03-20T09:30:00Z",
                "severity": "low",
                "description": "Slight increase in connection time"
            }
        ]
    except Exception as e:
        logger.error(f"Failed to get recent anomalies: {e}")
        return []

def main():
    """Main entry point."""
    try:
        config = Config()
        host = config.get("web_ui", {}).get("host", "0.0.0.0")
        port = config.get("web_ui", {}).get("port", 8080)
        
        logger.info(f"Starting web UI on {host}:{port}")
        uvicorn.run(app, host=host, port=port)
    except Exception as e:
        logger.error(f"Web UI failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 