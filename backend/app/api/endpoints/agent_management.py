from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel
import json
from datetime import datetime

from app.mcp_service.components.agent_registry import agent_registry
from app.mcp_service.data_service import DataService
from app.config.config import Config

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Agent Management"])

class AgentModelRequest(BaseModel):
    model_path: str

class AgentConfigRequest(BaseModel):
    config: Dict[str, Any]

class AgentConfigValidationRequest(BaseModel):
    config: Dict[str, Any]

class AgentConfigValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class AgentConfigResponse(BaseModel):
    agent_id: str
    config: Dict[str, Any]
    saved_at: str
    is_valid: bool

class AgentResponse(BaseModel):
    id: str
    name: str
    status: str
    is_running: bool
    last_run: Optional[str]
    capabilities: List[str]
    process_filters: List[str]
    description: str
    model_path: Optional[str]
    agent_type: str
    config: Dict[str, Any]

class AgentDetailedInfo(BaseModel):
    id: str
    name: str
    description: str
    agent_type: str
    status: str
    is_running: bool
    capabilities: List[str]
    data_requirements: Dict[str, Any]
    export_considerations: Dict[str, Any]
    configuration: Dict[str, Any]
    model_info: Optional[Dict[str, Any]]
    performance_metrics: Optional[Dict[str, Any]]

class ModelInfo(BaseModel):
    name: str
    path: str
    size: int
    modified: str

@router.get("", response_model=List[AgentResponse])
async def list_agents():
    """List all registered agents with their status."""
    try:
        # Get agents that are actually created and registered
        created_agents = agent_registry.list_agents()
        
        # Get all available configurations
        configs = agent_registry.list_agent_configs()
        
        # Create a map of created agents by ID
        created_agents_map = {agent['id']: agent for agent in created_agents}
        
        # Build response including both created agents and configured agents
        agents_response = []
        
        for config_info in configs:
            agent_id = config_info['agent_id']
            config = agent_registry.get_agent_config(agent_id)
            
            if agent_id in created_agents_map:
                # Agent is created and registered
                agent_info = created_agents_map[agent_id]
                
                # Extract process filters from config
                process_filters = []
                if config:
                    config_process_filters = config.get('process_filters', [])
                    if isinstance(config_process_filters, list):
                        process_filters = config_process_filters
                    elif isinstance(config_process_filters, str):
                        process_filters = [config_process_filters]
                
                agents_response.append(AgentResponse(
                    id=agent_id,
                    name=agent_info.get('name', config.get('name', agent_id)),
                    status=agent_info.get('status', 'unknown'),
                    is_running=agent_info.get('is_running', False),
                    last_run=agent_info.get('last_run'),
                    capabilities=agent_info.get('capabilities', config.get('capabilities', [])),
                    process_filters=process_filters,
                    description=agent_info.get('description', config.get('description', '')),
                    model_path=agent_info.get('model_path'),
                    agent_type=agent_info.get('agent_type', config.get('agent_type', 'unknown')),
                    config=config or {}
                ))
            else:
                # Agent is configured but not created
                
                # Extract process filters from config
                process_filters = []
                if config:
                    config_process_filters = config.get('process_filters', [])
                    if isinstance(config_process_filters, list):
                        process_filters = config_process_filters
                    elif isinstance(config_process_filters, str):
                        process_filters = [config_process_filters]
                
                agents_response.append(AgentResponse(
                    id=agent_id,
                    name=config.get('name', agent_id),
                    status='configured',
                    is_running=False,
                    last_run=None,
                    capabilities=config.get('capabilities', []),
                    process_filters=process_filters,
                    description=config.get('description', ''),
                    model_path=config.get('model_path'),
                    agent_type=config.get('agent_type', 'unknown'),
                    config=config or {}
                ))
        
        return agents_response
        
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

@router.get("/detailed-info", response_model=List[AgentDetailedInfo])
async def get_agents_detailed_info(agent_ids: Optional[str] = Query(None, description="Comma-separated list of agent IDs to get detailed info for. If not provided, returns info for all agents")):
    """
    Get comprehensive detailed information about multiple agents.
    
    This endpoint provides detailed information about agents including:
    - Basic agent information
    - Data requirements and sources
    - Export considerations for training
    - Configuration details
    - Model associations
    - Performance metrics
    
    Args:
        agent_ids: Optional comma-separated list of agent IDs. If not provided, returns info for all agents
    
    Returns:
        List of detailed agent information
    """
    try:
        logger.info(f"Getting detailed info for agents: {agent_ids}")
        
        # Get list of agents to process
        if agent_ids:
            # Process specific agent IDs
            agent_id_list = [aid.strip() for aid in agent_ids.split(',')]
            agents_to_process = []
            
            for agent_id in agent_id_list:
                config = agent_registry.get_agent_config(agent_id)
                if config:
                    agents_to_process.append({
                        'id': agent_id,
                        'name': config.get('name', agent_id),
                        'description': config.get('description', ''),
                        'agent_type': config.get('agent_type', 'unknown'),
                        'status': 'configured',
                        'is_running': False,
                        'capabilities': config.get('capabilities', [])
                    })
                    logger.info(f"Added {agent_id} to processing list with capabilities: {config.get('capabilities', [])}")
                else:
                    logger.warning(f"Agent configuration not found: {agent_id}")
        else:
            # Get all available agent configurations
            configs = agent_registry.list_agent_configs()
            agents_to_process = []
            
            for config_info in configs:
                agent_id = config_info['agent_id']
                config = agent_registry.get_agent_config(agent_id)
                if config:
                    agents_to_process.append({
                        'id': agent_id,
                        'name': config.get('name', agent_id),
                        'description': config.get('description', ''),
                        'agent_type': config.get('agent_type', 'unknown'),
                        'status': 'configured',
                        'is_running': False,
                        'capabilities': config.get('capabilities', [])
                    })
                    logger.info(f"Added {agent_id} to processing list with capabilities: {config.get('capabilities', [])}")
        
        detailed_info = []
        
        for agent_info in agents_to_process:
            agent_id = agent_info['id']
            logger.info(f"Processing {agent_id}...")
            
            # Get agent instance for detailed information (may be None if not created)
            agent = agent_registry.get_agent(agent_id)
            
            # Get configuration
            config = agent_registry.get_agent_config(agent_id) or {}
            
            # Update agent info with actual agent data if available
            if agent and hasattr(agent, 'get_status'):
                actual_status = agent.get_status()
                agent_info.update({
                    'status': actual_status.get('status', 'active'),
                    'is_running': actual_status.get('is_running', False),
                    'capabilities': actual_status.get('capabilities', agent_info['capabilities'])
                })
            
            # Get data requirements
            data_requirements = _get_data_requirements(agent, config)
            logger.info(f"Data requirements for {agent_id}: {data_requirements}")
            
            # Get export considerations
            export_considerations = _get_export_considerations(agent, config)
            
            # Build detailed information
            detailed_agent_info = {
                "id": agent_id,
                "name": agent_info.get('name', agent_id),
                "description": agent_info.get('description', ''),
                "agent_type": agent_info.get('agent_type', 'unknown'),
                "status": agent_info.get('status', 'configured'),
                "is_running": agent_info.get('is_running', False),
                "capabilities": agent_info.get('capabilities', config.get('capabilities', [])),
                "data_requirements": data_requirements,
                "export_considerations": export_considerations,
                "configuration": _get_configuration_summary(config),
                "model_info": _get_model_info(agent, agent_registry),
                "performance_metrics": _get_performance_metrics(agent_id, agent_registry)
            }
            
            logger.info(f"Final capabilities for {agent_id}: {detailed_agent_info['capabilities']}")
            logger.info(f"Final process filters for {agent_id}: {detailed_agent_info['data_requirements']['process_filters']}")
            
            detailed_info.append(detailed_agent_info)
        
        logger.info(f"Returning detailed info for {len(detailed_info)} agents")
        return detailed_info
        
    except Exception as e:
        logger.error(f"Error getting detailed agent information: {e}")
        raise HTTPException(status_code=500, detail="Failed to get detailed agent information")

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

@router.get("/{agent_id}/detailed", response_model=AgentDetailedInfo)
async def get_agent_detailed_info(agent_id: str):
    """
    Get comprehensive detailed information about a specific agent.
    
    This endpoint provides detailed information about an agent including:
    - Basic agent information
    - Data requirements and sources
    - Export considerations for training
    - Configuration details
    - Model associations
    - Performance metrics
    
    Args:
        agent_id: The ID of the agent to get detailed information for
    
    Returns:
        Detailed agent information
    """
    try:
        # Get agent instance
        agent = agent_registry.get_agent(agent_id)
        
        # Get configuration (this should always exist if the agent is configured)
        config = agent_registry.get_agent_config(agent_id)
        if not config:
            raise HTTPException(status_code=404, detail="Agent configuration not found")
        
        # Get basic agent info from agent if available, otherwise from config
        if agent and hasattr(agent, 'get_status'):
            agent_info = agent.get_status()
        else:
            # Fallback to configuration-based info
            agent_info = {
                'name': config.get('name', agent_id),
                'description': config.get('description', ''),
                'agent_type': config.get('agent_type', 'unknown'),
                'status': 'configured',
                'is_running': False,
                'capabilities': config.get('capabilities', [])
            }
        
        # Build detailed information
        detailed_agent_info = {
            "id": agent_id,
            "name": agent_info.get('name', config.get('name', agent_id)),
            "description": agent_info.get('description', config.get('description', '')),
            "agent_type": agent_info.get('agent_type', config.get('agent_type', 'unknown')),
            "status": agent_info.get('status', 'configured'),
            "is_running": agent_info.get('is_running', False),
            "capabilities": agent_info.get('capabilities', config.get('capabilities', [])),
            "data_requirements": _get_data_requirements(agent, config),
            "export_considerations": _get_export_considerations(agent, config),
            "configuration": _get_configuration_summary(config),
            "model_info": _get_model_info(agent, agent_registry),
            "performance_metrics": _get_performance_metrics(agent_id, agent_registry)
        }
        
        return detailed_agent_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting detailed agent information for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get detailed agent information")

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
    """Get overview statistics for all agents."""
    try:
        agents = agent_registry.list_agents()
        configs = agent_registry.list_agent_configs()
        
        total_agents = len(agents)
        total_configs = len(configs)
        running_agents = sum(1 for agent in agents if agent.get('is_running', False))
        
        # Get model statistics
        models = agent_registry.get_available_models()
        total_models = len(models)
        
        # Calculate total model size
        total_model_size = sum(model.get('size', 0) for model in models)
        
        # Get agent type distribution
        agent_types = {}
        for config_info in configs:
            agent_id = config_info['agent_id']
            config = agent_registry.get_agent_config(agent_id)
            if config:
                agent_type = config.get('agent_type', 'unknown')
                agent_types[agent_type] = agent_types.get(agent_type, 0) + 1
        
        # Build agent_stats array for frontend
        agent_stats = []
        total_analysis_cycles = 0
        total_logs_processed = 0
        total_features_extracted = 0
        total_anomalies_detected = 0
        
        for agent_info in agents:
            agent_id = agent_info['id']
            
            # Get agent stats from Redis if available
            agent_stats_data = {}
            if agent_registry.redis_client:
                try:
                    stats_key = f"mcp:agent:{agent_id}:analysis_stats"
                    stats_data = agent_registry.redis_client.get(stats_key)
                    if stats_data:
                        agent_stats_data = json.loads(stats_data)
                        
                        # Accumulate totals
                        total_analysis_cycles += agent_stats_data.get('analysis_cycles', 0)
                        total_logs_processed += agent_stats_data.get('logs_processed', 0)
                        total_features_extracted += agent_stats_data.get('features_extracted', 0)
                        total_anomalies_detected += agent_stats_data.get('anomalies_detected', 0)
                except Exception as e:
                    logger.warning(f"Error getting Redis stats for {agent_id}: {e}")
            
            # Create agent stats entry
            agent_stats.append({
                "agent": {
                    "id": agent_id,
                    "name": agent_info.get('name', agent_id),
                    "status": agent_info.get('status', 'unknown'),
                    "last_run": agent_info.get('last_run')
                },
                "analysis_stats": agent_stats_data
            })
        
        return {
            "total_agents": total_agents,
            "active_agents": running_agents,  # Changed from running_agents to active_agents
            "total_configurations": total_configs,
            "total_models": total_models,
            "total_model_size_bytes": total_model_size,
            "agent_type_distribution": agent_types,
            "total_analysis_cycles": total_analysis_cycles,
            "total_logs_processed": total_logs_processed,
            "total_features_extracted": total_features_extracted,
            "total_anomalies_detected": total_anomalies_detected,
            "agent_stats": agent_stats,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting analysis overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis overview")

@router.post("/reset")
async def reset_agent_registry():
    """Reset the agent registry by clearing and reloading all configurations."""
    try:
        logger.info("Resetting agent registry...")
        
        # Reset the agent registry
        agent_registry.reset()
        
        logger.info("Agent registry reset completed")
        
        return {
            "message": "Agent registry reset successfully",
            "configurations_loaded": len(agent_registry.agent_configs),
            "agents_cleared": 0  # All agents are cleared during reset
        }
        
    except Exception as e:
        logger.error(f"Error resetting agent registry: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset agent registry")

@router.post("/{agent_id}/config", response_model=AgentConfigResponse)
async def save_agent_config(agent_id: str, request: AgentConfigRequest):
    """
    Save or update agent configuration.
    
    This endpoint allows you to save or update the configuration for an agent.
    The configuration will be validated before saving.
    
    Args:
        agent_id: The ID of the agent to configure
        request: The configuration data to save
        
    Returns:
        The saved configuration with metadata
    """
    try:
        config = request.config
        
        # Validate the configuration
        validation_result = _validate_agent_config(config)
        if not validation_result['is_valid']:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid configuration: {'; '.join(validation_result['errors'])}"
            )
        
        # Save the configuration
        success = agent_registry.save_agent_config(agent_id, config)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save configuration")
        
        # Return the saved configuration
        return AgentConfigResponse(
            agent_id=agent_id,
            config=config,
            saved_at=datetime.now().isoformat(),
            is_valid=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving agent configuration for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save agent configuration")

@router.post("/{agent_id}/config/validate", response_model=AgentConfigValidationResponse)
async def validate_agent_config(agent_id: str, request: AgentConfigValidationRequest):
    """
    Validate agent configuration without saving.
    
    This endpoint validates an agent configuration and returns any errors or warnings
    without actually saving the configuration.
    
    Args:
        agent_id: The ID of the agent to validate configuration for
        request: The configuration data to validate
        
    Returns:
        Validation results with errors and warnings
    """
    try:
        config = request.config
        
        # Validate the configuration
        validation_result = _validate_agent_config(config)
        
        return AgentConfigValidationResponse(
            is_valid=validation_result['is_valid'],
            errors=validation_result['errors'],
            warnings=validation_result['warnings']
        )
        
    except Exception as e:
        logger.error(f"Error validating agent configuration for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate agent configuration")

@router.get("/{agent_id}/config", response_model=AgentConfigResponse)
async def get_agent_config(agent_id: str):
    """
    Get the current configuration for an agent.
    
    Args:
        agent_id: The ID of the agent to get configuration for
        
    Returns:
        The current agent configuration
    """
    try:
        config = agent_registry.get_agent_config(agent_id)
        if not config:
            raise HTTPException(status_code=404, detail="Agent configuration not found")
        
        # Validate the configuration
        validation_result = _validate_agent_config(config)
        
        return AgentConfigResponse(
            agent_id=agent_id,
            config=config,
            saved_at=datetime.now().isoformat(),  # We don't track save time, so use current time
            is_valid=validation_result['is_valid']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent configuration for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent configuration")

@router.delete("/{agent_id}/config")
async def delete_agent_config(agent_id: str):
    """
    Delete an agent configuration.
    
    This will remove the configuration file and stop the agent if it's running.
    
    Args:
        agent_id: The ID of the agent to delete configuration for
        
    Returns:
        Success message
    """
    try:
        success = agent_registry.delete_agent_config(agent_id)
        if not success:
            raise HTTPException(status_code=404, detail="Agent configuration not found")
        
        return {"message": f"Agent configuration {agent_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent configuration for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete agent configuration")

@router.get("/configs/templates")
async def get_config_templates():
    """
    Get configuration templates for different agent types.
    
    Returns:
        Dictionary of configuration templates
    """
    templates = {
        "ml_based": {
            "agent_id": "example_ml_agent",
            "name": "Example ML Agent",
            "description": "Machine learning-based anomaly detection agent",
            "agent_type": "ml_based",
            "process_filters": ["process1", "process2"],
            "model_path": "/app/models/example_model.pkl",
            "capabilities": [
                "Anomaly detection",
                "Pattern recognition"
            ],
            "analysis_rules": {
                "lookback_minutes": 5,
                "analysis_interval": 60,
                "feature_extraction": {
                    "feature1": True,
                    "feature2": True
                },
                "severity_mapping": {
                    "anomaly_type1": 4,
                    "anomaly_type2": 5
                },
                "thresholds": {
                    "threshold1": 100,
                    "threshold2": 50
                }
            }
        },
        "rule_based": {
            "agent_id": "example_rule_agent",
            "name": "Example Rule Agent",
            "description": "Rule-based monitoring agent",
            "agent_type": "rule_based",
            "process_filters": [],
            "model_path": None,
            "capabilities": [
                "Threshold monitoring",
                "Pattern matching"
            ],
            "analysis_rules": {
                "lookback_minutes": 5,
                "analysis_interval": 60,
                "target_levels": ["error", "critical"],
                "severity_mapping": {
                    "error": 4,
                    "critical": 5
                },
                "exclude_patterns": [".*test.*"],
                "include_patterns": [".*production.*"],
                "alert_cooldown": 300
            }
        },
        "hybrid": {
            "agent_id": "example_hybrid_agent",
            "name": "Example Hybrid Agent",
            "description": "Hybrid ML and rule-based agent",
            "agent_type": "hybrid",
            "process_filters": ["process1"],
            "model_path": "/app/models/example_model.pkl",
            "capabilities": [
                "ML-based detection",
                "Rule-based fallback"
            ],
            "analysis_rules": {
                "lookback_minutes": 10,
                "analysis_interval": 120,
                "feature_extraction": {
                    "feature1": True
                },
                "severity_mapping": {
                    "anomaly": 4
                },
                "thresholds": {
                    "threshold1": 100
                },
                "fallback_rules": {
                    "enable_fallback": True,
                    "rule_based_detection": True
                }
            }
        }
    }
    
    return templates

def _get_data_requirements(agent, config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract data requirements for the agent."""
    logger.info(f"_get_data_requirements called with agent: {agent is not None}, config keys: {list(config.keys()) if config else 'None'}")
    
    requirements = {
        "data_sources": [],
        "process_filters": [],
        "feature_requirements": [],
        "lookback_period": None,
        "sampling_frequency": None
    }
    
    if agent:
        logger.info(f"Agent has process_filters: {hasattr(agent, 'process_filters')}")
        # Get process filters from agent
        if hasattr(agent, 'process_filters'):
            requirements["process_filters"] = agent.process_filters or []
            logger.info(f"Got process filters from agent: {requirements['process_filters']}")
        
        # Get lookback period
        if hasattr(agent, 'lookback_minutes'):
            requirements["lookback_period"] = f"{agent.lookback_minutes} minutes"
        
        # Get analysis interval
        if hasattr(agent, 'analysis_interval'):
            requirements["sampling_frequency"] = f"{agent.analysis_interval} seconds"
    
    # Get data sources and process filters from config
    if config:
        logger.info(f"Processing config with keys: {list(config.keys())}")
        
        # Extract data sources from configuration
        data_sources = config.get('data_sources', [])
        if isinstance(data_sources, list):
            requirements["data_sources"] = data_sources
        elif isinstance(data_sources, str):
            requirements["data_sources"] = [data_sources]
        
        # Extract process filters from configuration (if not already set from agent)
        if not requirements["process_filters"]:
            process_filters = config.get('process_filters', [])
            logger.info(f"Config process_filters: {process_filters}, type: {type(process_filters)}")
            if isinstance(process_filters, list):
                requirements["process_filters"] = process_filters
            elif isinstance(process_filters, str):
                requirements["process_filters"] = [process_filters]
            logger.info(f"Set process filters from config: {requirements['process_filters']}")
        
        # Extract feature requirements
        features = config.get('features', [])
        if isinstance(features, list):
            requirements["feature_requirements"] = features
        
        # Extract feature requirements from analysis rules if available
        analysis_rules = config.get('analysis_rules', {})
        if analysis_rules:
            feature_extraction = analysis_rules.get('feature_extraction', {})
            if feature_extraction and isinstance(feature_extraction, dict):
                requirements["feature_requirements"] = list(feature_extraction.keys())
    
    logger.info(f"Final requirements: {requirements}")
    return requirements

def _get_export_considerations(agent, config: Dict[str, Any]) -> Dict[str, Any]:
    """Get export considerations for training data preparation."""
    considerations = {
        "exportable_features": [],
        "data_format": "json",
        "required_fields": [],
        "optional_fields": [],
        "data_volume_estimate": "unknown",
        "training_data_requirements": [],
        "preprocessing_steps": []
    }
    
    if agent:
        # Get capabilities that might affect export
        capabilities = getattr(agent, 'capabilities', [])
        considerations["exportable_features"] = capabilities
        
        # Determine data format based on agent type
        agent_type = getattr(agent, 'agent_type', 'unknown')
        if agent_type in ['ml_based', 'hybrid']:
            considerations["data_format"] = "json"
            considerations["training_data_requirements"] = [
                "Labeled anomaly data",
                "Feature vectors",
                "Timestamp information",
                "Context metadata"
            ]
            considerations["preprocessing_steps"] = [
                "Feature normalization",
                "Missing value handling",
                "Outlier detection",
                "Data validation"
            ]
        elif agent_type == 'rule_based':
            considerations["data_format"] = "json"
            considerations["training_data_requirements"] = [
                "Rule condition data",
                "Threshold values",
                "Historical patterns"
            ]
            considerations["preprocessing_steps"] = [
                "Rule validation",
                "Threshold calibration",
                "Pattern extraction"
            ]
    
    # Get capabilities from config if not available from agent
    if config and not considerations["exportable_features"]:
        config_capabilities = config.get('capabilities', [])
        if isinstance(config_capabilities, list):
            considerations["exportable_features"] = config_capabilities
    
    # Get required fields from config
    if config:
        analysis_rules = config.get('analysis_rules', {})
        if analysis_rules:
            considerations["required_fields"] = list(analysis_rules.keys())
        
        # Estimate data volume based on configuration
        lookback = config.get('analysis_rules', {}).get('lookback_minutes', 5)
        interval = config.get('analysis_rules', {}).get('analysis_interval', 60)
        considerations["data_volume_estimate"] = f"~{lookback} minutes of data every {interval} seconds"
    
    return considerations

def _get_configuration_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get a summary of the agent configuration."""
    summary = {
        "agent_type": config.get('agent_type', 'unknown'),
        "analysis_rules": config.get('analysis_rules', {}),
        "severity_mapping": config.get('analysis_rules', {}).get('severity_mapping', {}),
        "model_path": config.get('model_path'),
        "enabled": config.get('enabled', True),
        "priority": config.get('priority', 'normal')
    }
    
    # Add any additional configuration sections
    for key, value in config.items():
        if key not in ['agent_type', 'analysis_rules', 'model_path', 'enabled', 'priority']:
            summary[key] = value
    
    return summary

def _get_model_info(agent, agent_registry) -> Optional[Dict[str, Any]]:
    """Get information about the agent's associated model."""
    if not agent:
        return None
    
    agent_id = getattr(agent, 'agent_id', None)
    if not agent_id:
        return None
    
    try:
        model_path = agent_registry.get_agent_model(agent_id)
        if not model_path:
            return None
        
        # Get model details if available
        model_info = {
            "path": model_path,
            "assigned": True,
            "type": "unknown"
        }
        
        # Try to get more model details from the model manager
        if hasattr(agent, 'model_manager') and agent.model_manager:
            try:
                # This would need to be implemented in the model manager
                # For now, we'll return basic info
                pass
            except Exception as e:
                logger.debug(f"Could not get detailed model info: {e}")
        
        return model_info
        
    except Exception as e:
        logger.debug(f"Error getting model info: {e}")
        return None

def _get_performance_metrics(agent_id: str, agent_registry) -> Optional[Dict[str, Any]]:
    """Get performance metrics for the agent."""
    metrics = {
        "analysis_cycles": 0,
        "anomalies_detected": 0,
        "average_cycle_time": None,
        "last_analysis_time": None,
        "success_rate": None
    }
    
    try:
        # Get metrics from Redis if available
        if agent_registry.redis_client:
            # Analysis cycle count
            cycle_key = f"mcp:agent:{agent_id}:analysis_cycles"
            cycle_count = agent_registry.redis_client.get(cycle_key)
            if cycle_count:
                metrics["analysis_cycles"] = int(cycle_count)
            
            # Anomaly count
            anomaly_key = f"mcp:agent:{agent_id}:anomalies_detected"
            anomaly_count = agent_registry.redis_client.get(anomaly_key)
            if anomaly_count:
                metrics["anomalies_detected"] = int(anomaly_count)
            
            # Last analysis time
            last_analysis_key = f"mcp:agent:{agent_id}:last_analysis"
            last_analysis = agent_registry.redis_client.get(last_analysis_key)
            if last_analysis:
                metrics["last_analysis_time"] = last_analysis
            
            # Average cycle time
            avg_time_key = f"mcp:agent:{agent_id}:avg_cycle_time"
            avg_time = agent_registry.redis_client.get(avg_time_key)
            if avg_time:
                metrics["average_cycle_time"] = float(avg_time)
            
            # Success rate
            success_key = f"mcp:agent:{agent_id}:success_rate"
            success_rate = agent_registry.redis_client.get(success_key)
            if success_rate:
                metrics["success_rate"] = float(success_rate)
                
    except Exception as e:
        logger.debug(f"Error getting performance metrics for {agent_id}: {e}")
    
    return metrics

def _validate_agent_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate agent configuration.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Dictionary with validation results
    """
    errors = []
    warnings = []
    
    # Required fields
    required_fields = ['agent_id', 'name', 'description', 'agent_type']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")
        elif not config[field]:
            errors.append(f"Required field '{field}' cannot be empty")
    
    # Validate agent_type
    if 'agent_type' in config:
        valid_types = ['ml_based', 'rule_based', 'hybrid']
        if config['agent_type'] not in valid_types:
            errors.append(f"Invalid agent_type: {config['agent_type']}. Must be one of: {', '.join(valid_types)}")
    
    # Validate process_filters
    if 'process_filters' in config:
        if not isinstance(config['process_filters'], list):
            errors.append("process_filters must be a list")
    
    # Validate capabilities
    if 'capabilities' in config:
        if not isinstance(config['capabilities'], list):
            errors.append("capabilities must be a list")
    
    # Validate model_path based on agent_type
    if 'agent_type' in config and 'model_path' in config:
        if config['agent_type'] == 'ml_based' and not config['model_path']:
            warnings.append("ML-based agent should have a model_path specified")
        elif config['agent_type'] == 'rule_based' and config['model_path']:
            warnings.append("Rule-based agent typically doesn't need a model_path")
    
    # Validate analysis_rules
    if 'analysis_rules' in config:
        analysis_rules = config['analysis_rules']
        
        # Validate lookback_minutes
        if 'lookback_minutes' in analysis_rules:
            try:
                lookback = int(analysis_rules['lookback_minutes'])
                if lookback <= 0:
                    errors.append("lookback_minutes must be positive")
                elif lookback > 1440:  # 24 hours
                    warnings.append("lookback_minutes is very large (>24 hours)")
            except (ValueError, TypeError):
                errors.append("lookback_minutes must be a number")
        
        # Validate analysis_interval
        if 'analysis_interval' in analysis_rules:
            try:
                interval = int(analysis_rules['analysis_interval'])
                if interval <= 0:
                    errors.append("analysis_interval must be positive")
                elif interval < 30:
                    warnings.append("analysis_interval is very short (<30 seconds)")
                elif interval > 3600:  # 1 hour
                    warnings.append("analysis_interval is very long (>1 hour)")
            except (ValueError, TypeError):
                errors.append("analysis_interval must be a number")
        
        # Validate severity_mapping
        if 'severity_mapping' in analysis_rules:
            severity_mapping = analysis_rules['severity_mapping']
            if not isinstance(severity_mapping, dict):
                errors.append("severity_mapping must be a dictionary")
            else:
                for anomaly_type, severity in severity_mapping.items():
                    try:
                        severity_int = int(severity)
                        if severity_int < 1 or severity_int > 5:
                            errors.append(f"Severity for '{anomaly_type}' must be between 1 and 5")
                    except (ValueError, TypeError):
                        errors.append(f"Severity for '{anomaly_type}' must be a number")
    
    # Agent-type specific validation
    if 'agent_type' in config:
        if config['agent_type'] == 'rule_based':
            if 'analysis_rules' in config:
                analysis_rules = config['analysis_rules']
                if 'target_levels' in analysis_rules:
                    if not isinstance(analysis_rules['target_levels'], list):
                        errors.append("target_levels must be a list")
                
                if 'exclude_patterns' in analysis_rules:
                    if not isinstance(analysis_rules['exclude_patterns'], list):
                        errors.append("exclude_patterns must be a list")
                
                if 'include_patterns' in analysis_rules:
                    if not isinstance(analysis_rules['include_patterns'], list):
                        errors.append("include_patterns must be a list")
        
        elif config['agent_type'] == 'ml_based':
            if 'analysis_rules' in config:
                analysis_rules = config['analysis_rules']
                if 'feature_extraction' in analysis_rules:
                    if not isinstance(analysis_rules['feature_extraction'], dict):
                        errors.append("feature_extraction must be a dictionary")
                
                if 'thresholds' in analysis_rules:
                    if not isinstance(analysis_rules['thresholds'], dict):
                        errors.append("thresholds must be a dictionary")
        
        elif config['agent_type'] == 'hybrid':
            if 'analysis_rules' in config:
                analysis_rules = config['analysis_rules']
                if 'fallback_rules' in analysis_rules:
                    fallback_rules = analysis_rules['fallback_rules']
                    if not isinstance(fallback_rules, dict):
                        errors.append("fallback_rules must be a dictionary")
    
    return {
        'is_valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    } 