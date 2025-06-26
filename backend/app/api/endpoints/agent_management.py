from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel
import json

from app.mcp_service.components.agent_registry import agent_registry
from app.mcp_service.data_service import DataService
from app.config.config import Config

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Agent Management"])

class AgentModelRequest(BaseModel):
    model_path: str

class AgentResponse(BaseModel):
    id: str
    name: str
    status: str
    is_running: bool
    last_run: Optional[str]
    capabilities: List[str]
    description: str
    model_path: Optional[str]
    config: Dict[str, Any]

class ModelInfo(BaseModel):
    name: str
    path: str
    size: int
    modified: str

@router.get("", response_model=List[AgentResponse])
async def list_agents():
    """List all registered agents with their status and model associations."""
    try:
        agents = agent_registry.list_agents()
        return agents
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list agents")

@router.get("/available-models", response_model=List[ModelInfo])
async def get_available_models():
    """Get list of available models that can be assigned to agents."""
    try:
        models = agent_registry.get_available_models()
        return models
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available models")

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get detailed information about a specific agent."""
    try:
        agents = agent_registry.list_agents()
        agent = next((a for a in agents if a['id'] == agent_id), None)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent")

@router.post("/{agent_id}/set-model")
async def set_agent_model(agent_id: str, request: AgentModelRequest):
    """Set the model for a specific agent."""
    try:
        success = agent_registry.set_agent_model(agent_id, request.model_path)
        
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {"message": f"Model updated for agent {agent_id}", "model_path": request.model_path}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting model for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to set agent model")

@router.get("/{agent_id}/model")
async def get_agent_model(agent_id: str):
    """Get the current model path for a specific agent."""
    try:
        model_path = agent_registry.get_agent_model(agent_id)
        
        if model_path is None:
            raise HTTPException(status_code=404, detail="Agent not found or no model set")
        
        return {"agent_id": agent_id, "model_path": model_path}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent model")

@router.post("/{agent_id}/restart")
async def restart_agent(agent_id: str):
    """Restart a specific agent."""
    try:
        success = await agent_registry.restart_agent(agent_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {"message": f"Agent {agent_id} restarted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restarting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to restart agent")

@router.delete("/{agent_id}")
async def unregister_agent(agent_id: str):
    """Unregister an agent from the registry."""
    try:
        success = agent_registry.unregister_agent(agent_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {"message": f"Agent {agent_id} unregistered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to unregister agent")

@router.get("/{agent_id}/stats", response_model=Dict[str, Any])
async def get_agent_stats(agent_id: str):
    """Get analysis statistics for a specific agent."""
    try:
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get basic agent info
        agent_info = {
            "id": agent_id,
            "name": agent.__class__.__name__,
            "status": agent.status,
            "is_running": agent.is_running,
            "last_run": agent.last_run.isoformat() if agent.last_run else None,
            "capabilities": agent.capabilities,
            "description": agent.description
        }
        
        # Get analysis statistics from Redis if available
        stats = {}
        if agent_registry.redis_client:
            try:
                # Get analysis cycle stats
                cycle_key = f"mcp:agent:{agent_id}:analysis_stats"
                cycle_stats = agent_registry.redis_client.get(cycle_key)
                if cycle_stats:
                    stats.update(json.loads(cycle_stats))
                
                # Get feature extraction stats
                feature_key = f"mcp:agent:{agent_id}:feature_stats"
                feature_stats = agent_registry.redis_client.get(feature_key)
                if feature_stats:
                    stats.update(json.loads(feature_stats))
                
                # Get anomaly detection stats
                anomaly_key = f"mcp:agent:{agent_id}:anomaly_stats"
                anomaly_stats = agent_registry.redis_client.get(anomaly_key)
                if anomaly_stats:
                    stats.update(json.loads(anomaly_stats))
                    
            except Exception as e:
                logger.warning(f"Error getting Redis stats for {agent_id}: {e}")
        
        # Combine agent info with stats
        result = {
            "agent": agent_info,
            "analysis_stats": stats
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent stats")

@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_analysis_overview():
    """Get overview of analysis statistics for all agents."""
    try:
        agents = agent_registry.list_agents()
        
        overview = {
            "total_agents": len(agents),
            "active_agents": len([a for a in agents if a.get('is_running', False)]),
            "total_analysis_cycles": 0,
            "total_logs_processed": 0,
            "total_features_extracted": 0,
            "total_anomalies_detected": 0,
            "agent_stats": []
        }
        
        for agent in agents:
            agent_id = agent['id']
            
            # Get basic agent info
            agent_info = {
                "id": agent_id,
                "name": agent['name'],
                "status": agent['status'],
                "is_running": agent['is_running'],
                "last_run": agent['last_run'],
                "capabilities": agent['capabilities'],
                "description": agent['description']
            }
            
            # Get analysis statistics from Redis if available
            stats = {}
            if agent_registry.redis_client:
                try:
                    # Get analysis cycle stats
                    cycle_key = f"mcp:agent:{agent_id}:analysis_stats"
                    cycle_stats = agent_registry.redis_client.get(cycle_key)
                    if cycle_stats:
                        stats.update(json.loads(cycle_stats))
                except Exception as e:
                    logger.warning(f"Error getting Redis stats for {agent_id}: {e}")
            
            # Create agent stats object
            agent_stats = {
                "agent": agent_info,
                "analysis_stats": stats
            }
            
            overview["agent_stats"].append(agent_stats)
            
            # Aggregate stats
            overview["total_analysis_cycles"] += stats.get("analysis_cycles", 0)
            overview["total_logs_processed"] += stats.get("logs_processed", 0)
            overview["total_features_extracted"] += stats.get("features_extracted", 0)
            overview["total_anomalies_detected"] += stats.get("anomalies_detected", 0)
        
        return overview
        
    except Exception as e:
        logger.error(f"Error getting analysis overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis overview") 