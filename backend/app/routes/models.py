from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
from app.mcp_service.components.model_manager import model_manager

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/models", response_model=List[Dict[str, Any]])
async def get_models():
    """Get all registered models."""
    try:
        logger.info("Received request for /models endpoint")
        models = model_manager.get_all_models()
        logger.info(f"Retrieved {len(models)} models: {models}")
        return models
    except Exception as e:
        logger.error(f"Error retrieving models: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 