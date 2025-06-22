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

router = APIRouter(tags=["model-management"])
logger = logging.getLogger(__name__)

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
    """Import a model package ZIP file."""
    try:
        # File validation
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Initialize model loader for validation
        model_loader = ModelLoader()
        
        # Validate file
        content = await file.read()
        if not model_loader.validate_uploaded_file(file.filename, len(content)):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file. Must be a ZIP file following naming convention: model_{version}_deployment.zip"
            )
        
        # Save to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Process the model package
            result = await model_loader.process_model_package(tmp_file_path, validate)
            return result
        finally:
            # Cleanup temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing model package: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.post("/import/{model_path:path}")
async def import_model_from_training_service(model_path: str, 
                                           validate: bool = True) -> Dict[str, Any]:
    """Import a model from training service."""
    try:
        config = ModelConfig()
        transfer_service = ModelTransferService(config)
        result = await transfer_service.import_model(model_path, validate)
        return result
    except Exception as e:
        logger.error(f"Error importing model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import-latest")
async def import_latest_model(validate: bool = True) -> Dict[str, Any]:
    """Import the latest model from training service."""
    try:
        config = ModelConfig()
        transfer_service = ModelTransferService(config)
        result = await transfer_service.import_latest_model(validate)
        return result
    except Exception as e:
        logger.error(f"Error importing latest model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{version}/validate")
async def validate_model(version: str) -> Dict[str, Any]:
    """Validate a specific model version."""
    try:
        config = ModelConfig()
        validator = ModelValidator(config)
        model_manager = ModelManager(config)
        
        # Find model path
        models = await model_manager.list_models()
        model_info = next((m for m in models if m['version'] == version), None)
        
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
        validation_result = await validator.validate_model_quality(model_info['path'])
        return validation_result
        
    except Exception as e:
        logger.error(f"Error validating model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{version}/deploy")
async def deploy_model(version: str) -> Dict[str, Any]:
    """Deploy a specific model version."""
    try:
        config = ModelConfig()
        model_manager = ModelManager(config)
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
        model_manager = ModelManager(config)
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
        model_manager = ModelManager(config)
        
        # Scan for new models first
        await model_manager.scan_model_directory()
        
        models = await model_manager.list_models()
        return models
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{version}")
async def get_model_info(version: str) -> Dict[str, Any]:
    """Get detailed information about a specific model."""
    try:
        config = ModelConfig()
        model_manager = ModelManager(config)
        
        models = await model_manager.list_models()
        model_info = next((m for m in models if m['version'] == version), None)
        
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        
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
        model_manager = ModelManager(config)
        
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
        model_manager = ModelManager(config)
        
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