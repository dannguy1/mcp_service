import logging
import numpy as np
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import joblib
from datetime import datetime

from ..models.config import ModelConfig

logger = logging.getLogger(__name__)

class ModelValidator:
    """Comprehensive model validation and quality assurance."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
    
    async def validate_model_quality(self, model_path: str) -> Dict[str, Any]:
        """Validate model quality and performance."""
        try:
            validation_result = {
                'is_valid': True,
                'score': 0.0,
                'errors': [],
                'warnings': [],
                'recommendations': []
            }
            
            # Load model and metadata
            model_dir = Path(model_path)
            model = joblib.load(model_dir / 'model.joblib')
            
            with open(model_dir / 'metadata.json', 'r') as f:
                metadata = json.load(f)
            
            # Check model structure
            structure_check = self._validate_model_structure(model)
            validation_result['errors'].extend(structure_check['errors'])
            validation_result['warnings'].extend(structure_check['warnings'])
            
            # Check performance metrics
            performance_check = self._validate_performance_metrics(metadata)
            validation_result['errors'].extend(performance_check['errors'])
            validation_result['warnings'].extend(performance_check['warnings'])
            validation_result['recommendations'].extend(performance_check['recommendations'])
            
            # Check feature compatibility
            feature_check = self._validate_feature_compatibility(metadata)
            validation_result['warnings'].extend(feature_check['warnings'])
            
            # Check model age
            age_check = self._validate_model_age(metadata)
            validation_result['warnings'].extend(age_check['warnings'])
            
            # Calculate overall score
            validation_result['score'] = self._calculate_quality_score(validation_result)
            
            # Determine validity
            if validation_result['score'] < 0.6:
                validation_result['is_valid'] = False
                validation_result['errors'].append("Model quality score below threshold")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating model quality: {e}")
            return {
                'is_valid': False,
                'score': 0.0,
                'errors': [f"Validation failed: {str(e)}"],
                'warnings': [],
                'recommendations': []
            }
    
    def _validate_model_structure(self, model: Any) -> Dict[str, Any]:
        """Validate model structure and methods."""
        errors = []
        warnings = []
        
        # Check required methods
        required_methods = ['predict', 'score_samples']
        for method in required_methods:
            if not hasattr(model, method):
                errors.append(f"Model missing required method: {method}")
        
        # Check model parameters
        if hasattr(model, 'n_estimators'):
            if model.n_estimators < 50:
                warnings.append("Low number of estimators may affect performance")
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_performance_metrics(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate model performance metrics."""
        errors = []
        warnings = []
        recommendations = []
        
        evaluation_metrics = metadata.get('evaluation_info', {}).get('basic_metrics', {})
        
        # Check F1 score
        f1_score = evaluation_metrics.get('f1_score', 0)
        if f1_score < 0.5:
            errors.append("F1 score below acceptable threshold (0.5)")
        elif f1_score < 0.7:
            warnings.append("F1 score below recommended threshold (0.7)")
            recommendations.append("Consider retraining with more data or different parameters")
        
        # Check ROC AUC
        roc_auc = evaluation_metrics.get('roc_auc', 0)
        if roc_auc < 0.6:
            errors.append("ROC AUC below acceptable threshold (0.6)")
        elif roc_auc < 0.8:
            warnings.append("ROC AUC below recommended threshold (0.8)")
            recommendations.append("Consider feature engineering or model tuning")
        
        # Check precision and recall
        precision = evaluation_metrics.get('precision', 0)
        recall = evaluation_metrics.get('recall', 0)
        
        if precision < 0.5:
            warnings.append("Low precision may result in many false positives")
        if recall < 0.5:
            warnings.append("Low recall may miss many anomalies")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'recommendations': recommendations
        }
    
    def _validate_feature_compatibility(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate feature compatibility with current system."""
        warnings = []
        
        training_info = metadata.get('training_info', {})
        feature_names = training_info.get('feature_names', [])
        
        # Check feature count
        if len(feature_names) < 5:
            warnings.append("Low feature count may limit model performance")
        
        # Check for expected features
        expected_features = ['hour_of_day', 'day_of_week', 'message_length']
        missing_features = [f for f in expected_features if f not in feature_names]
        if missing_features:
            warnings.append(f"Missing expected features: {missing_features}")
        
        return {
            'warnings': warnings
        }
    
    def _validate_model_age(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate model age and freshness."""
        warnings = []
        
        created_at = metadata.get('model_info', {}).get('created_at')
        if created_at:
            try:
                # Handle different date formats
                if 'T' in created_at:
                    created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    created_date = datetime.fromisoformat(created_at)
                
                age_days = (datetime.now() - created_date).days
                
                if age_days > 30:
                    warnings.append(f"Model is {age_days} days old, consider retraining")
                elif age_days > 7:
                    warnings.append(f"Model is {age_days} days old, monitor for drift")
            except Exception as e:
                warnings.append(f"Could not parse model creation date: {e}")
        
        return {
            'warnings': warnings
        }
    
    def _calculate_quality_score(self, validation_result: Dict[str, Any]) -> float:
        """Calculate overall model quality score."""
        score = 1.0
        
        # Deduct for errors
        score -= len(validation_result['errors']) * 0.2
        
        # Deduct for warnings
        score -= len(validation_result['warnings']) * 0.05
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    async def validate_model_compatibility(self, model_path: str, 
                                         target_features: List[str]) -> Dict[str, Any]:
        """Validate model compatibility with target feature set."""
        try:
            result = {
                'compatible': True,
                'missing_features': [],
                'extra_features': [],
                'feature_mismatch_score': 0.0
            }
            
            # Load model metadata
            model_dir = Path(model_path)
            metadata_path = model_dir / 'metadata.json'
            
            if not metadata_path.exists():
                result['compatible'] = False
                result['missing_features'] = target_features
                return result
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Get model features
            model_features = metadata.get('training_info', {}).get('feature_names', [])
            
            # Check for missing features
            missing_features = [f for f in target_features if f not in model_features]
            result['missing_features'] = missing_features
            
            # Check for extra features
            extra_features = [f for f in model_features if f not in target_features]
            result['extra_features'] = extra_features
            
            # Calculate compatibility score
            if target_features:
                common_features = set(target_features) & set(model_features)
                result['feature_mismatch_score'] = len(common_features) / len(target_features)
                
                # Mark as incompatible if too many features are missing
                if result['feature_mismatch_score'] < 0.8:
                    result['compatible'] = False
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating model compatibility: {e}")
            return {
                'compatible': False,
                'missing_features': target_features,
                'extra_features': [],
                'feature_mismatch_score': 0.0,
                'error': str(e)
            }
    
    async def generate_validation_report(self, model_path: str) -> Dict[str, Any]:
        """Generate a comprehensive validation report."""
        try:
            # Perform quality validation
            quality_result = await self.validate_model_quality(model_path)
            
            # Load metadata for additional information
            model_dir = Path(model_path)
            metadata_path = model_dir / 'metadata.json'
            
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            
            # Generate report
            report = {
                'model_path': model_path,
                'validation_timestamp': datetime.now().isoformat(),
                'quality_validation': quality_result,
                'model_info': metadata.get('model_info', {}),
                'training_info': metadata.get('training_info', {}),
                'evaluation_info': metadata.get('evaluation_info', {}),
                'recommendations': self._generate_recommendations(quality_result, metadata)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating validation report: {e}")
            return {
                'model_path': model_path,
                'validation_timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _generate_recommendations(self, quality_result: Dict[str, Any], 
                                metadata: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Add quality-based recommendations
        recommendations.extend(quality_result.get('recommendations', []))
        
        # Add metadata-based recommendations
        if 'training_info' in metadata:
            training_samples = metadata['training_info'].get('training_samples', 0)
            if training_samples < 1000:
                recommendations.append("Consider training with more data for better performance")
        
        if 'evaluation_info' in metadata:
            metrics = metadata['evaluation_info'].get('basic_metrics', {})
            if metrics.get('precision', 1) < 0.8:
                recommendations.append("High false positive rate detected - consider threshold tuning")
            if metrics.get('recall', 1) < 0.8:
                recommendations.append("High false negative rate detected - consider model retraining")
        
        return recommendations 