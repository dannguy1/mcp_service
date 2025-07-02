from fastapi import APIRouter, HTTPException, BackgroundTasks, File, UploadFile
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import tempfile
import os

from ...services.model_transfer_service import ModelTransferService
from ...services.model_validator import ModelValidator
from ...services.model_performance_monitor import ModelPerformanceMonitor
from ...services.model_loader import ModelLoader
from ...components.model_manager import ModelManager
from ...models.config import ModelConfig
from app.mcp_service.components.agent_registry import agent_registry

router = APIRouter(tags=["model-management"])
logger = logging.getLogger(__name__)

def _get_model_agent_assignments() -> Dict[str, List[Dict[str, Any]]]:
    """Get which agents are assigned to each model path."""
    try:
        agent_assignments = {}
        
        # Get all agent configurations
        for agent_id, config in agent_registry.agent_configs.items():
            model_path = config.get('model_path')
            if model_path:
                if model_path not in agent_assignments:
                    agent_assignments[model_path] = []
                
                agent_assignments[model_path].append({
                    'agent_id': agent_id,
                    'agent_name': config.get('name', agent_id),
                    'agent_type': config.get('agent_type', 'unknown'),
                    'capabilities': config.get('capabilities', []),
                    'status': 'configured'
                })
        
        # Also check running agents
        for agent_id, agent in agent_registry.agents.items():
            if hasattr(agent, 'model_path') and agent.model_path:
                if agent.model_path not in agent_assignments:
                    agent_assignments[agent.model_path] = []
                
                # Check if agent is already in the list
                existing_agent = next(
                    (a for a in agent_assignments[agent.model_path] if a['agent_id'] == agent_id), 
                    None
                )
                
                if existing_agent:
                    # Update status for running agent
                    existing_agent['status'] = 'running' if agent.is_running else 'stopped'
                else:
                    # Add new agent entry
                    agent_assignments[agent.model_path].append({
                        'agent_id': agent_id,
                        'agent_name': getattr(agent, 'agent_name', agent_id),
                        'agent_type': getattr(agent, 'agent_type', 'unknown'),
                        'capabilities': getattr(agent, 'capabilities', []),
                        'status': 'running' if agent.is_running else 'stopped'
                    })
        
        return agent_assignments
        
    except Exception as e:
        logger.error(f"Error getting model agent assignments: {e}")
        return {}

@router.get("/training-service/models")
async def get_training_service_models() -> List[Dict[str, Any]]:
    """Get available models from training service."""
    try:
        config = ModelConfig()
        transfer_service = ModelTransferService(config)
        models = await transfer_service.scan_training_service_models()
        return models
    except Exception as e:
        logger.error(f"Error getting training service models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_model_package(
    file: UploadFile = File(...),
    validate: bool = True
) -> Dict[str, Any]:
    """Import a model package from a zip file."""
    try:
        config = ModelConfig()
        model_manager = ModelManager.get_instance(config)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Import the model
            result = await model_manager.import_model_from_training_service(temp_file_path, validate)
            return result
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Error importing model package: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/{model_path:path}")
async def import_model_from_training_service(model_path: str, 
                                           validate: bool = True) -> Dict[str, Any]:
    """Import a model from the training service."""
    try:
        config = ModelConfig()
        model_manager = ModelManager.get_instance(config)
        result = await model_manager.import_model_from_training_service(model_path, validate)
        return result
    except Exception as e:
        logger.error(f"Error importing model from training service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import-latest")
async def import_latest_model(validate: bool = True) -> Dict[str, Any]:
    """Import the latest model from the training service."""
    try:
        config = ModelConfig()
        model_manager = ModelManager.get_instance(config)
        result = await model_manager.import_model_from_training_service("latest", validate)
        return result
    except Exception as e:
        logger.error(f"Error importing latest model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{version}/validate")
async def validate_model(version: str) -> Dict[str, Any]:
    """Validate a specific model version."""
    try:
        config = ModelConfig()
        model_manager = ModelManager.get_instance(config)
        validator = ModelValidator(config)
        
        # Find model path
        models = await model_manager.list_models()
        model_info = next((m for m in models if m['version'] == version), None)
        
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        validation_result = await validator.validate_model(model_info['path'])
        return validation_result
        
    except Exception as e:
        logger.error(f"Error validating model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{version}/deploy")
async def deploy_model(version: str) -> Dict[str, Any]:
    """Deploy a specific model version."""
    try:
        config = ModelConfig()
        model_manager = ModelManager.get_instance(config)
        
        success = await model_manager.deploy_model(version)
        
        if success:
            return {
                "version": version,
                "status": "deployed",
                "deployed_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to deploy model")
            
    except Exception as e:
        logger.error(f"Error deploying model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{version}/rollback")
async def rollback_model(version: str) -> Dict[str, Any]:
    """Rollback to a specific model version."""
    try:
        config = ModelConfig()
        model_manager = ModelManager.get_instance(config)
        
        success = await model_manager.rollback_model(version)
        
        if success:
            return {
                "version": version,
                "status": "rolled_back",
                "rolled_back_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to rollback model")
            
    except Exception as e:
        logger.error(f"Error rolling back model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{version}")
async def delete_model(version: str) -> Dict[str, Any]:
    """Delete a specific model version. Only allowed if not assigned to any agent."""
    try:
        config = ModelConfig()
        model_manager = ModelManager.get_instance(config)
        # Find model path
        models = await model_manager.list_models()
        model_info = next((m for m in models if m['version'] == version), None)
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Check agent assignments first
        agent_assignments = _get_model_agent_assignments()
        model_path = model_info.get('path', '')
        assigned_agents = agent_assignments.get(model_path, [])
        if assigned_agents:
            raise HTTPException(status_code=400, detail="Model is currently assigned to one or more agents and cannot be deleted.")
        
        # If no agent assignments, allow deletion regardless of deployment status
        success = await model_manager.delete_model(version)
        if success:
            return {
                "version": version,
                "status": "deleted",
                "deleted_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to delete model")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transfer-history")
async def get_transfer_history() -> List[Dict[str, Any]]:
    """Get model transfer history."""
    try:
        config = ModelConfig()
        transfer_service = ModelTransferService(config)
        history = await transfer_service.get_transfer_history()
        return history
            
    except Exception as e:
        logger.error(f"Error getting transfer history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_models() -> List[Dict[str, Any]]:
    """List all available models."""
    try:
        config = ModelConfig()
        model_manager = ModelManager.get_instance(config)
        
        # Scan for new models first
        await model_manager.scan_model_directory()
        
        models = await model_manager.list_models()
        
        # Get agent assignments for each model
        agent_assignments = _get_model_agent_assignments()
        
        # Add agent assignment information to each model
        for model in models:
            model_path = model.get('path', '')
            assigned_agents = agent_assignments.get(model_path, [])
            model['assigned_agents'] = assigned_agents
            model['agent_count'] = len(assigned_agents)
        
        return models
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{version}")
async def get_model_info(version: str) -> Dict[str, Any]:
    """Get detailed information about a specific model."""
    try:
        config = ModelConfig()
        model_manager = ModelManager.get_instance(config)
        
        models = await model_manager.list_models()
        model_info = next((m for m in models if m['version'] == version), None)
        
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Get agent assignments for this model
        agent_assignments = _get_model_agent_assignments()
        model_path = model_info.get('path', '')
        assigned_agents = agent_assignments.get(model_path, [])
        model_info['assigned_agents'] = assigned_agents
        model_info['agent_count'] = len(assigned_agents)
        
        return model_info
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/{version}")
async def get_model_performance(version: str) -> Dict[str, Any]:
    """Get performance metrics for a specific model version."""
    try:
        config = ModelConfig()
        monitor = ModelPerformanceMonitor(config)
        performance = await monitor.get_performance_summary(version)
        return performance
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
async def get_all_model_performance() -> List[Dict[str, Any]]:
    """Get performance metrics for all models."""
    try:
        config = ModelConfig()
        monitor = ModelPerformanceMonitor(config)
        performance = await monitor.get_all_model_performance()
        return performance
    except Exception as e:
        logger.error(f"Error getting all model performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/performance/{version}/check-drift")
async def check_model_drift(version: str) -> Dict[str, Any]:
    """Check for model drift."""
    try:
        config = ModelConfig()
        monitor = ModelPerformanceMonitor(config)
        drift_result = await monitor.check_model_drift(version)
        return drift_result
    except Exception as e:
        logger.error(f"Error checking model drift: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/{version}/report")
async def generate_performance_report(version: str) -> Dict[str, Any]:
    """Generate a comprehensive performance report."""
    try:
        config = ModelConfig()
        monitor = ModelPerformanceMonitor(config)
        report = await monitor.generate_performance_report(version)
        return report
    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{version}/validate-compatibility")
async def validate_model_compatibility(version: str, target_features: List[str]) -> Dict[str, Any]:
    """Validate model compatibility with target feature set."""
    try:
        config = ModelConfig()
        validator = ModelValidator(config)
        model_manager = ModelManager.get_instance(config)
        
        # Find model path
        models = await model_manager.list_models()
        model_info = next((m for m in models if m['version'] == version), None)
        
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        compatibility_result = await validator.validate_model_compatibility(
            model_info['path'], target_features
        )
        return compatibility_result
        
    except Exception as e:
        logger.error(f"Error validating model compatibility: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{version}/validation-report")
async def generate_validation_report(version: str) -> Dict[str, Any]:
    """Generate a comprehensive validation report."""
    try:
        config = ModelConfig()
        validator = ModelValidator(config)
        model_manager = ModelManager.get_instance(config)
        
        # Find model path
        models = await model_manager.list_models()
        model_info = next((m for m in models if m['version'] == version), None)
        
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        report = await validator.generate_validation_report(model_info['path'])
        return report
        
    except Exception as e:
        logger.error(f"Error generating validation report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/training-service/connection")
async def validate_training_service_connection() -> Dict[str, Any]:
    """Validate connection to training service."""
    try:
        config = ModelConfig()
        transfer_service = ModelTransferService(config)
        connection_result = await transfer_service.validate_training_service_connection()
        return connection_result
    except Exception as e:
        logger.error(f"Error validating training service connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/transfer-history")
async def cleanup_transfer_history(days_to_keep: int = 30) -> Dict[str, Any]:
    """Clean up old transfer records."""
    try:
        config = ModelConfig()
        transfer_service = ModelTransferService(config)
        await transfer_service.cleanup_old_transfers(days_to_keep)
        return {
            "status": "success",
            "message": f"Cleaned up transfer history older than {days_to_keep} days"
        }
    except Exception as e:
        logger.error(f"Error cleaning up transfer history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/performance/cleanup")
async def cleanup_performance_metrics(days_to_keep: int = 30) -> Dict[str, Any]:
    """Clean up old performance metrics."""
    try:
        config = ModelConfig()
        monitor = ModelPerformanceMonitor(config)
        await monitor.cleanup_old_metrics(days_to_keep)
        return {
            "status": "success",
            "message": f"Cleaned up performance metrics older than {days_to_keep} days"
        }
    except Exception as e:
        logger.error(f"Error cleaning up performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 