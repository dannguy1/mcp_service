from fastapi import APIRouter
from app.api.endpoints import models, logs, server, anomalies, export

api_router = APIRouter()

api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(server.router, prefix="/server", tags=["server"])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["anomalies"])
api_router.include_router(export.router, prefix="/export", tags=["export"]) 