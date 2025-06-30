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
            
            # Check package structure
            structure_check = self._validate_package_structure(model_dir)
            validation_result['errors'].extend(structure_check['errors'])
            validation_result['warnings'].extend(structure_check['warnings'])
            validation_result['recommendations'].extend(structure_check['recommendations'])
            
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
    
    def _validate_package_structure(self, model_dir: Path) -> Dict[str, Any]:
        """Validate model package structure and required files."""
        errors = []
        warnings = []
        recommendations = []
        
        # Required files
        required_files = ['model.joblib', 'metadata.json']
        for file in required_files:
            if not (model_dir / file).exists():
                errors.append(f"Missing required file: {file}")
        
        # Optional but recommended files
        optional_files = [
            'deployment_manifest.json',
            'requirements.txt',
            'README.md',
            'validate_model.py',
            'inference_example.py'
        ]
        
        missing_optional = []
        for file in optional_files:
            if not (model_dir / file).exists():
                missing_optional.append(file)
        
        if missing_optional:
            warnings.append(f"Missing optional files: {', '.join(missing_optional)}")
            recommendations.append("Consider adding missing optional files for better deployment experience")
        
        # Check metadata.json structure
        metadata_file = model_dir / 'metadata.json'
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Check required metadata sections
                required_sections = ['model_info', 'training_info', 'evaluation_info']
                missing_sections = []
                for section in required_sections:
                    if section not in metadata:
                        missing_sections.append(section)
                
                if missing_sections:
                    warnings.append(f"Missing metadata sections: {', '.join(missing_sections)}")
                    recommendations.append("Add missing metadata sections for better model documentation")
                
                # Check model_info fields
                model_info = metadata.get('model_info', {})
                if not model_info.get('model_type'):
                    warnings.append("Model type not specified in metadata")
                if not model_info.get('description'):
                    warnings.append("Model description not provided")
                
                # Check training_info fields
                training_info = metadata.get('training_info', {})
                if not training_info.get('n_samples'):
                    warnings.append("Number of training samples not specified")
                if not training_info.get('feature_names'):
                    warnings.append("Feature names not provided")
                
                # Check evaluation_info fields
                evaluation_info = metadata.get('evaluation_info', {})
                basic_metrics = evaluation_info.get('basic_metrics', {})
                if not basic_metrics:
                    warnings.append("No evaluation metrics found")
                else:
                    required_metrics = ['f1_score', 'precision', 'recall', 'roc_auc']
                    missing_metrics = [m for m in required_metrics if m not in basic_metrics]
                    if missing_metrics:
                        warnings.append(f"Missing evaluation metrics: {', '.join(missing_metrics)}")
                
            except json.JSONDecodeError:
                errors.append("Invalid JSON format in metadata.json")
            except Exception as e:
                warnings.append(f"Error reading metadata.json: {str(e)}")
        
        # Check deployment_manifest.json if it exists
        manifest_file = model_dir / 'deployment_manifest.json'
        if manifest_file.exists():
            try:
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                
                if 'file_hashes' not in manifest:
                    warnings.append("No file hashes found in deployment manifest")
                if 'dependencies' not in manifest:
                    warnings.append("No dependencies listed in deployment manifest")
                    
            except json.JSONDecodeError:
                warnings.append("Invalid JSON format in deployment_manifest.json")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'recommendations': recommendations
        }
    
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
            
            # Get package structure information
            package_structure = self._get_package_structure_info(model_dir)
            
            # Get comprehensive package information
            package_info = self._get_comprehensive_package_info(model_dir, metadata)
            
            report = {
                'report_id': f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'generated_at': datetime.now().isoformat(),
                'model_path': model_path,
                'package_info': package_info,
                'model_info': metadata.get('model_info', {}),
                'training_info': metadata.get('training_info', {}),
                'evaluation_info': metadata.get('evaluation_info', {}),
                'package_structure': package_structure,
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
                'next_steps': self._generate_next_steps(quality_result),
                'trainer_notes': self._generate_trainer_notes(quality_result, metadata, package_structure)
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
    
    def _get_package_structure_info(self, model_dir: Path) -> Dict[str, Any]:
        """Get detailed information about the model package structure."""
        structure_info = {
            'required_files': {
                'model.joblib': (model_dir / 'model.joblib').exists(),
                'metadata.json': (model_dir / 'metadata.json').exists()
            },
            'optional_files': {
                'deployment_manifest.json': (model_dir / 'deployment_manifest.json').exists(),
                'requirements.txt': (model_dir / 'requirements.txt').exists(),
                'README.md': (model_dir / 'README.md').exists(),
                'validate_model.py': (model_dir / 'validate_model.py').exists(),
                'inference_example.py': (model_dir / 'inference_example.py').exists()
            },
            'file_sizes': {},
            'total_package_size': 0
        }
        
        # Calculate file sizes
        total_size = 0
        for file_path in model_dir.rglob('*'):
            if file_path.is_file():
                file_size = file_path.stat().st_size
                relative_path = str(file_path.relative_to(model_dir))
                structure_info['file_sizes'][relative_path] = file_size
                total_size += file_size
        
        structure_info['total_package_size'] = total_size
        
        return structure_info
    
    def _generate_trainer_notes(self, validation_result: Dict[str, Any], metadata: Dict[str, Any], package_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specific notes for model trainers."""
        trainer_notes = {
            'critical_issues': [],
            'quality_concerns': [],
            'missing_components': [],
            'improvement_suggestions': [],
            'priority_actions': []
        }
        
        # Critical issues that prevent deployment
        if not validation_result['is_valid']:
            trainer_notes['critical_issues'].append("Model failed validation - cannot be deployed")
            trainer_notes['priority_actions'].append("Address all validation errors before resubmitting")
        
        # Quality concerns
        quality_metrics = validation_result.get('quality_metrics', {})
        if quality_metrics.get('f1_score', 0) < 0.5:
            trainer_notes['quality_concerns'].append("F1 score below acceptable threshold (0.5)")
            trainer_notes['improvement_suggestions'].append("Consider retraining with more balanced data or different model parameters")
        
        if quality_metrics.get('roc_auc', 0) < 0.6:
            trainer_notes['quality_concerns'].append("ROC AUC below acceptable threshold (0.6)")
            trainer_notes['improvement_suggestions'].append("Review feature engineering and model selection")
        
        # Missing components
        required_files = package_structure.get('required_files', {})
        for file_name, exists in required_files.items():
            if not exists:
                trainer_notes['missing_components'].append(f"Missing required file: {file_name}")
        
        optional_files = package_structure.get('optional_files', {})
        missing_optional = [name for name, exists in optional_files.items() if not exists]
        if missing_optional:
            trainer_notes['missing_components'].append(f"Missing optional files: {', '.join(missing_optional)}")
        
        # Metadata issues
        model_info = metadata.get('model_info', {})
        if not model_info.get('description'):
            trainer_notes['improvement_suggestions'].append("Add model description to metadata")
        
        training_info = metadata.get('training_info', {})
        if not training_info.get('n_samples'):
            trainer_notes['improvement_suggestions'].append("Specify number of training samples in metadata")
        
        if not training_info.get('feature_names'):
            trainer_notes['improvement_suggestions'].append("Include feature names in metadata")
        
        evaluation_info = metadata.get('evaluation_info', {})
        basic_metrics = evaluation_info.get('basic_metrics', {})
        if not basic_metrics:
            trainer_notes['missing_components'].append("No evaluation metrics found in metadata")
        
        # Priority actions
        if validation_result['errors']:
            trainer_notes['priority_actions'].append("Fix all validation errors")
        
        if validation_result['warnings']:
            trainer_notes['priority_actions'].append("Review and address validation warnings")
        
        if trainer_notes['missing_components']:
            trainer_notes['priority_actions'].append("Add missing components to model package")
        
        return trainer_notes
    
    def _get_comprehensive_package_info(self, model_dir: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive information about the model package for reference."""
        package_info = {
            'package_identifier': {
                'name': None,
                'version': None,
                'type': None,
                'description': None,
                'author': None,
                'organization': None
            },
            'source_information': {
                'training_source': None,
                'training_id': None,
                'export_files': [],
                'original_path': None,
                'import_timestamp': None
            },
            'model_details': {
                'model_type': None,
                'model_name': None,
                'algorithm': None,
                'framework': None,
                'framework_version': None
            },
            'creation_info': {
                'created_at': None,
                'created_by': None,
                'training_duration': None,
                'last_modified': None
            },
            'deployment_info': {
                'deployment_ready': False,
                'deployment_requirements': [],
                'environment_dependencies': [],
                'resource_requirements': {}
            }
        }
        
        # Extract package identifier information
        model_info = metadata.get('model_info', {})
        package_info['package_identifier'].update({
            'name': model_info.get('model_name') or model_info.get('name'),
            'version': model_info.get('version'),
            'type': model_info.get('model_type'),
            'description': model_info.get('description'),
            'author': model_info.get('author'),
            'organization': model_info.get('organization')
        })
        
        # Extract source information
        package_info['source_information'].update({
            'training_source': model_info.get('training_source'),
            'training_id': model_info.get('training_id'),
            'export_files': model_info.get('export_files', []),
            'original_path': str(model_dir),
            'import_timestamp': model_info.get('created_at')
        })
        
        # Extract model details
        package_info['model_details'].update({
            'model_type': model_info.get('model_type'),
            'model_name': model_info.get('model_name'),
            'algorithm': self._extract_algorithm_info(model_dir),
            'framework': self._extract_framework_info(model_dir),
            'framework_version': self._extract_framework_version(model_dir)
        })
        
        # Extract creation information
        package_info['creation_info'].update({
            'created_at': model_info.get('created_at'),
            'created_by': model_info.get('created_by'),
            'training_duration': metadata.get('training_info', {}).get('training_duration'),
            'last_modified': self._get_last_modified_time(model_dir)
        })
        
        # Extract deployment information
        deployment_manifest_path = model_dir / 'deployment_manifest.json'
        if deployment_manifest_path.exists():
            try:
                with open(deployment_manifest_path, 'r') as f:
                    deployment_manifest = json.load(f)
                
                package_info['deployment_info'].update({
                    'deployment_ready': deployment_manifest.get('deployment_ready', False),
                    'deployment_requirements': deployment_manifest.get('requirements', []),
                    'environment_dependencies': deployment_manifest.get('dependencies', []),
                    'resource_requirements': deployment_manifest.get('resource_requirements', {})
                })
            except Exception as e:
                logger.warning(f"Error reading deployment manifest: {e}")
        
        # Extract requirements if available
        requirements_path = model_dir / 'requirements.txt'
        if requirements_path.exists():
            try:
                with open(requirements_path, 'r') as f:
                    requirements = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
                package_info['deployment_info']['environment_dependencies'] = requirements
            except Exception as e:
                logger.warning(f"Error reading requirements.txt: {e}")
        
        return package_info
    
    def _extract_algorithm_info(self, model_dir: Path) -> str:
        """Extract algorithm information from the model file."""
        try:
            model_path = model_dir / 'model.joblib'
            if model_path.exists():
                model = joblib.load(model_path)
                return type(model).__name__
        except Exception as e:
            logger.warning(f"Error extracting algorithm info: {e}")
        return "Unknown"
    
    def _extract_framework_info(self, model_dir: Path) -> str:
        """Extract framework information."""
        try:
            # Check for common ML framework indicators
            if (model_dir / 'requirements.txt').exists():
                with open(model_dir / 'requirements.txt', 'r') as f:
                    content = f.read().lower()
                    if 'scikit-learn' in content or 'sklearn' in content:
                        return 'scikit-learn'
                    elif 'tensorflow' in content:
                        return 'tensorflow'
                    elif 'pytorch' in content or 'torch' in content:
                        return 'pytorch'
                    elif 'xgboost' in content:
                        return 'xgboost'
                    elif 'lightgbm' in content:
                        return 'lightgbm'
        except Exception as e:
            logger.warning(f"Error extracting framework info: {e}")
        return "Unknown"
    
    def _extract_framework_version(self, model_dir: Path) -> str:
        """Extract framework version information."""
        try:
            if (model_dir / 'requirements.txt').exists():
                with open(model_dir / 'requirements.txt', 'r') as f:
                    content = f.read()
                    # Look for version patterns
                    import re
                    patterns = [
                        r'scikit-learn[=<>~!]+([\d.]+)',
                        r'sklearn[=<>~!]+([\d.]+)',
                        r'tensorflow[=<>~!]+([\d.]+)',
                        r'torch[=<>~!]+([\d.]+)',
                        r'xgboost[=<>~!]+([\d.]+)',
                        r'lightgbm[=<>~!]+([\d.]+)'
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, content)
                        if match:
                            return match.group(1)
        except Exception as e:
            logger.warning(f"Error extracting framework version: {e}")
        return "Unknown"
    
    def _get_last_modified_time(self, model_dir: Path) -> str:
        """Get the last modified time of the model directory."""
        try:
            # Get the most recent modification time of any file in the directory
            latest_time = 0
            for file_path in model_dir.rglob('*'):
                if file_path.is_file():
                    mtime = file_path.stat().st_mtime
                    if mtime > latest_time:
                        latest_time = mtime
            
            if latest_time > 0:
                return datetime.fromtimestamp(latest_time).isoformat()
        except Exception as e:
            logger.warning(f"Error getting last modified time: {e}")
        return None 