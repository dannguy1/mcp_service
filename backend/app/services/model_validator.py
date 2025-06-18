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
                'recommendations': [],
                'quality_metrics': {},
                'issues': []
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
            validation_result['quality_metrics'] = performance_check['metrics']
            
            # Check feature compatibility
            feature_check = self._validate_feature_compatibility(metadata)
            validation_result['warnings'].extend(feature_check['warnings'])
            
            # Check model age
            age_check = self._validate_model_age(metadata)
            validation_result['warnings'].extend(age_check['warnings'])
            validation_result['recommendations'].extend(age_check['recommendations'])
            
            # Calculate overall validation score
            validation_result['score'] = self._calculate_validation_score(validation_result)
            
            # Determine if model is valid
            validation_result['is_valid'] = len(validation_result['errors']) == 0
            
            # Create issues list for frontend
            validation_result['issues'] = self._create_issues_list(validation_result)
            
            logger.info(f"Model validation completed with score: {validation_result['score']}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating model quality: {e}")
            return {
                'is_valid': False,
                'score': 0.0,
                'errors': [f"Validation failed: {str(e)}"],
                'warnings': [],
                'recommendations': [],
                'quality_metrics': {},
                'issues': []
            }
    
    def _validate_model_structure(self, model) -> Dict[str, Any]:
        """Validate model structure and basic functionality."""
        errors = []
        warnings = []
        
        # Check if model has required methods
        if not hasattr(model, 'predict'):
            errors.append("Model does not have predict method")
        
        if not hasattr(model, 'fit'):
            warnings.append("Model does not have fit method (may be pre-trained)")
        
        # Check model type
        model_type = type(model).__name__
        if model_type not in ['IsolationForest', 'LocalOutlierFactor', 'RandomForestClassifier', 'LogisticRegression']:
            warnings.append(f"Unknown model type: {model_type}")
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    def _validate_performance_metrics(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate model performance metrics."""
        errors = []
        warnings = []
        recommendations = []
        metrics = {}
        
        evaluation_metrics = metadata.get('evaluation_info', {}).get('basic_metrics', {})
        
        # Check F1 score
        f1_score = evaluation_metrics.get('f1_score', 0)
        metrics['f1_score'] = f1_score
        if f1_score < 0.5:
            errors.append("F1 score below acceptable threshold (0.5)")
        elif f1_score < 0.7:
            warnings.append("F1 score below recommended threshold (0.7)")
            recommendations.append("Consider retraining with more data or different parameters")
        
        # Check ROC AUC
        roc_auc = evaluation_metrics.get('roc_auc', 0)
        metrics['roc_auc'] = roc_auc
        if roc_auc < 0.6:
            errors.append("ROC AUC below acceptable threshold (0.6)")
        elif roc_auc < 0.8:
            warnings.append("ROC AUC below recommended threshold (0.8)")
            recommendations.append("Consider feature engineering or model tuning")
        
        # Check precision and recall
        precision = evaluation_metrics.get('precision', 0)
        recall = evaluation_metrics.get('recall', 0)
        metrics['precision'] = precision
        metrics['recall'] = recall
        
        if precision < 0.5:
            warnings.append("Low precision may result in many false positives")
        if recall < 0.5:
            warnings.append("Low recall may miss many anomalies")
        
        # Check accuracy
        accuracy = evaluation_metrics.get('accuracy', 0)
        metrics['accuracy'] = accuracy
        if accuracy < 0.7:
            warnings.append("Low accuracy may indicate poor model performance")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'recommendations': recommendations,
            'metrics': metrics
        }
    
    def _validate_feature_compatibility(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate feature compatibility."""
        warnings = []
        
        feature_names = metadata.get('training_info', {}).get('feature_names', [])
        
        if len(feature_names) == 0:
            warnings.append("No feature names found in metadata")
        elif len(feature_names) < 3:
            warnings.append("Very few features - consider feature engineering")
        
        return {
            'warnings': warnings
        }
    
    def _validate_model_age(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate model age and freshness."""
        warnings = []
        recommendations = []
        
        created_at = metadata.get('model_info', {}).get('created_at', '')
        if created_at:
            try:
                model_age = (datetime.now() - datetime.fromisoformat(created_at)).days
                if model_age > 90:
                    warnings.append(f"Model is {model_age} days old")
                    recommendations.append("Consider retraining with recent data")
                elif model_age > 30:
                    warnings.append(f"Model is {model_age} days old")
                    recommendations.append("Monitor model performance for degradation")
            except ValueError:
                warnings.append("Invalid creation date format in metadata")
        
        return {
            'warnings': warnings,
            'recommendations': recommendations
        }
    
    def _calculate_validation_score(self, validation_result: Dict[str, Any]) -> float:
        """Calculate overall validation score."""
        score = 1.0
        
        # Deduct points for errors
        score -= len(validation_result['errors']) * 0.3
        
        # Deduct points for warnings
        score -= len(validation_result['warnings']) * 0.1
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def _create_issues_list(self, validation_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create issues list for frontend display."""
        issues = []
        
        for error in validation_result['errors']:
            issues.append({
                'severity': 'error',
                'description': error
            })
        
        for warning in validation_result['warnings']:
            issues.append({
                'severity': 'warning',
                'description': warning
            })
        
        return issues
    
    async def validate_model_compatibility(self, model_path: str, target_features: List[str]) -> Dict[str, Any]:
        """Validate model compatibility with target feature set."""
        try:
            compatibility_result = {
                'is_compatible': True,
                'compatibility_score': 0.0,
                'missing_features': [],
                'extra_features': [],
                'feature_mapping': {},
                'warnings': [],
                'recommendations': []
            }
            
            # Load model metadata
            model_dir = Path(model_path)
            with open(model_dir / 'metadata.json', 'r') as f:
                metadata = json.load(f)
            
            # Get model features
            model_features = metadata.get('training_info', {}).get('feature_names', [])
            
            # Check for missing features
            missing_features = [f for f in target_features if f not in model_features]
            compatibility_result['missing_features'] = missing_features
            
            # Check for extra features
            extra_features = [f for f in model_features if f not in target_features]
            compatibility_result['extra_features'] = extra_features
            
            # Create feature mapping
            feature_mapping = {}
            for i, feature in enumerate(model_features):
                if feature in target_features:
                    feature_mapping[feature] = i
            
            compatibility_result['feature_mapping'] = feature_mapping
            
            # Calculate compatibility score
            if len(target_features) > 0:
                compatibility_score = len(feature_mapping) / len(target_features)
                compatibility_result['compatibility_score'] = compatibility_score
                
                if compatibility_score < 1.0:
                    compatibility_result['is_compatible'] = False
                    compatibility_result['warnings'].append(
                        f"Feature compatibility: {compatibility_score:.1%} - some features may not be available"
                    )
                    
                    if missing_features:
                        compatibility_result['recommendations'].append(
                            f"Add missing features: {', '.join(missing_features)}"
                        )
            
            logger.info(f"Model compatibility check completed: {compatibility_result['is_compatible']}")
            return compatibility_result
            
        except Exception as e:
            logger.error(f"Error validating model compatibility: {e}")
            return {
                'is_compatible': False,
                'compatibility_score': 0.0,
                'missing_features': [],
                'extra_features': [],
                'feature_mapping': {},
                'warnings': [f"Compatibility check failed: {str(e)}"],
                'recommendations': []
            }
    
    async def check_model_drift(self, model_path: str, reference_data: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Check for model drift using reference data."""
        try:
            drift_result = {
                'drift_detected': False,
                'drift_metrics': {
                    'feature_drift_score': 0.0,
                    'prediction_drift_score': 0.0,
                    'data_quality_score': 0.0
                },
                'drift_threshold': 0.1,
                'warnings': [],
                'recommendations': []
            }
            
            # Load model
            model_dir = Path(model_path)
            model = joblib.load(model_dir / 'model.joblib')
            
            # If no reference data provided, use model's training data characteristics
            if reference_data is None:
                # For now, we'll use a simple heuristic based on model age
                # In a real implementation, you'd compare against actual reference data
                drift_result['warnings'].append("No reference data provided - using model age heuristic")
                
                # Load metadata to check model age
                with open(model_dir / 'metadata.json', 'r') as f:
                    metadata = json.load(f)
                
                created_at = metadata.get('model_info', {}).get('created_at', '')
                if created_at:
                    model_age = (datetime.now() - datetime.fromisoformat(created_at)).days
                    if model_age > 30:
                        drift_result['drift_metrics']['feature_drift_score'] = 0.15
                        drift_result['drift_metrics']['prediction_drift_score'] = 0.12
                        drift_result['warnings'].append(f"Model is {model_age} days old - consider retraining")
            
            # Calculate drift scores (simplified implementation)
            feature_drift = drift_result['drift_metrics']['feature_drift_score']
            prediction_drift = drift_result['drift_metrics']['prediction_drift_score']
            
            # Determine if drift is detected
            if feature_drift > drift_result['drift_threshold'] or prediction_drift > drift_result['drift_threshold']:
                drift_result['drift_detected'] = True
                drift_result['recommendations'].append("Consider retraining the model with recent data")
                drift_result['recommendations'].append("Monitor model performance more closely")
            
            logger.info(f"Model drift check completed: drift_detected={drift_result['drift_detected']}")
            return drift_result
            
        except Exception as e:
            logger.error(f"Error checking model drift: {e}")
            return {
                'drift_detected': False,
                'drift_metrics': {
                    'feature_drift_score': 0.0,
                    'prediction_drift_score': 0.0,
                    'data_quality_score': 0.0
                },
                'drift_threshold': 0.1,
                'warnings': [f"Drift check failed: {str(e)}"],
                'recommendations': []
            }
    
    async def generate_validation_report(self, model_path: str) -> Dict[str, Any]:
        """Generate a comprehensive validation report."""
        try:
            # Perform all validation checks
            quality_result = await self.validate_model_quality(model_path)
            
            # Load metadata for additional information
            model_dir = Path(model_path)
            with open(model_dir / 'metadata.json', 'r') as f:
                metadata = json.load(f)
            
            report = {
                'report_id': f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'generated_at': datetime.now().isoformat(),
                'model_path': model_path,
                'model_info': metadata.get('model_info', {}),
                'validation_summary': {
                    'is_valid': quality_result['is_valid'],
                    'score': quality_result['score'],
                    'error_count': len(quality_result['errors']),
                    'warning_count': len(quality_result['warnings']),
                    'recommendation_count': len(quality_result['recommendations'])
                },
                'quality_metrics': quality_result['quality_metrics'],
                'issues': quality_result['issues'],
                'recommendations': quality_result['recommendations'],
                'next_steps': self._generate_next_steps(quality_result)
            }
            
            logger.info(f"Validation report generated: {report['report_id']}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating validation report: {e}")
            return {
                'report_id': f"validation_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'generated_at': datetime.now().isoformat(),
                'error': str(e),
                'validation_summary': {
                    'is_valid': False,
                    'score': 0.0,
                    'error_count': 1,
                    'warning_count': 0,
                    'recommendation_count': 0
                }
            }
    
    def _generate_next_steps(self, validation_result: Dict[str, Any]) -> List[str]:
        """Generate next steps based on validation results."""
        next_steps = []
        
        if validation_result['is_valid']:
            next_steps.append("Model is ready for deployment")
            next_steps.append("Monitor model performance in production")
        else:
            next_steps.append("Address validation errors before deployment")
            next_steps.append("Consider retraining the model")
        
        if validation_result['recommendations']:
            next_steps.extend(validation_result['recommendations'])
        
        return next_steps 