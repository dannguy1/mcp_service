# Model Loading Guide

This guide explains how to load new trained models into the MCP (Model Control Protocol) service system.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Model Loading Methods](#model-loading-methods)
- [Model Directory Structure](#model-directory-structure)
- [API Endpoints](#api-endpoints)
- [Frontend UI](#frontend-ui)
- [Validation and Deployment](#validation-and-deployment)
- [Monitoring and Performance](#monitoring-and-performance)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)

## Overview

The MCP service supports multiple methods for loading trained models, from simple file placement to automated imports from training services. The system automatically validates models, manages versions, and provides performance monitoring capabilities.

## Prerequisites

- MCP service is running and accessible
- Trained model file(s) are available
- Proper permissions to access model directories
- Model is compatible with the current feature set

## Model Loading Methods

### Method 1: Direct File Placement (Simplest)

This is the most straightforward method for loading models.

#### Steps:

1. **Navigate to the MCP service directory:**
   ```bash
   cd /home/dannguyen/WNC/mcp_service
   ```

2. **Copy your trained model to the models directory:**
   ```bash
   # For a single model file
   cp /path/to/your/trained_model.pkl backend/models/
   
   # For a model directory with multiple files
   cp -r /path/to/your/model_directory backend/models/
   ```

3. **Restart the service to load the new model:**
   ```bash
   # Restart the backend service
   docker-compose restart backend
   ```

#### Advantages:
- Simple and direct
- No additional configuration required
- Works with any model format

#### Disadvantages:
- Manual process
- No automatic validation
- Requires service restart

### Method 2: Using the Model Management API

The system provides REST API endpoints for automated model management.

#### A. Import Latest Model from Training Service

```bash
# Import the latest available model
curl -X POST "http://localhost:5000/api/v1/model-management/import-latest" \
  -H "Content-Type: application/json" \
  -d '{"validate": true}'
```

#### B. Import Specific Model

```bash
# Import a specific model by path
curl -X POST "http://localhost:5000/api/v1/model-management/import/path/to/model" \
  -H "Content-Type: application/json" \
  -d '{"validate": true}'
```

#### C. Deploy a Model Version

```bash
# Deploy a specific model version
curl -X POST "http://localhost:5000/api/v1/model-management/{version}/deploy" \
  -H "Content-Type: application/json"
```

#### Advantages:
- Automated process
- Built-in validation
- Version management
- Transfer history tracking

#### Disadvantages:
- Requires API access
- More complex setup

### Method 3: Using the Frontend UI

The MCP service provides a web interface for model management.

#### Steps:

1. **Access the Models page** in the MCP service frontend
2. **Use the "Import Latest" button** to import the newest model
3. **Deploy the model** using the deploy button in the model list

#### Advantages:
- User-friendly interface
- Visual feedback
- No command-line knowledge required

#### Disadvantages:
- Requires web browser access
- Limited to available UI features

### Method 4: Automated Import from Training Service

The system can automatically import models from a configured training service.

#### Configuration:

The training service path is configured in `backend/app/config/model_config.yaml`:

```yaml
integration:
  training_service_path: /home/dannguyen/WNC/mcp_training
  auto_import: false
  import_interval: 3600
  validate_imports: true
```

#### Commands:

1. **Check available models:**
   ```bash
   curl "http://localhost:5000/api/v1/model-management/training-service/models"
   ```

2. **Validate training service connection:**
   ```bash
   curl "http://localhost:5000/api/v1/model-management/training-service/connection"
   ```

3. **Import the latest model:**
   ```bash
   curl -X POST "http://localhost:5000/api/v1/model-management/import-latest"
   ```

## Model Directory Structure

Based on the configuration, models should be placed in:
```
/home/dannguyen/WNC/mcp_service/backend/models/
```

### Expected Structure:

```
backend/models/
├── model_v1.pkl                    # Model file
├── model_v2.pkl                    # Another model version
├── wifi_anomaly_model.pkl          # WiFi-specific model
├── metadata.json                   # Model metadata (optional)
└── model_registry.json            # Model registry (auto-generated)
```

### Model File Requirements:

- **Format**: Compatible with scikit-learn (typically `.pkl`)
- **Features**: Must match the expected feature set
- **Metadata**: Optional but recommended for enhanced management

## API Endpoints

### Model Management Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/model-management/models` | GET | List all available models |
| `/api/v1/model-management/models/{version}` | GET | Get model information |
| `/api/v1/model-management/import-latest` | POST | Import latest model |
| `/api/v1/model-management/import/{path}` | POST | Import specific model |
| `/api/v1/model-management/{version}/deploy` | POST | Deploy model version |
| `/api/v1/model-management/{version}/rollback` | POST | Rollback to version |
| `/api/v1/model-management/{version}/validate` | POST | Validate model |

### Performance Monitoring Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/model-management/performance` | GET | Get all model performance |
| `/api/v1/model-management/performance/{version}` | GET | Get model performance |
| `/api/v1/model-management/performance/{version}/check-drift` | POST | Check model drift |
| `/api/v1/model-management/performance/{version}/report` | GET | Generate performance report |

### Training Service Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/model-management/training-service/models` | GET | List training service models |
| `/api/v1/model-management/training-service/connection` | GET | Validate training service connection |

## Frontend UI

### Models Page

The Models page in the MCP service frontend provides:

- **Model List**: View all available models with their status
- **Import Latest**: Import the newest model from training service
- **Deploy/Rollback**: Manage model deployment
- **Validation**: Validate model quality and performance
- **Performance**: View model performance metrics

### Performance Tab

The Performance tab shows:

- **Total Inferences**: Number of times each model has been used
- **Average Inference Time**: Model performance speed
- **Anomaly Rate**: Percentage of predictions that are anomalies
- **Performance Trends**: Whether performance is improving or degrading

## Validation and Deployment Process

When a new model is loaded, the system performs the following steps:

### 1. Model Validation

- **Format Check**: Verify model file format and structure
- **Feature Compatibility**: Ensure model expects the correct features
- **Quality Assessment**: Evaluate model quality metrics
- **Performance Testing**: Test model performance on sample data

### 2. Model Registration

- **Version Assignment**: Assign unique version identifier
- **Metadata Extraction**: Extract model metadata
- **Registry Update**: Update model registry
- **History Recording**: Record model transfer history

### 3. Model Deployment

- **Status Update**: Update model status to "deployed"
- **Service Integration**: Integrate model with inference services
- **Performance Monitoring**: Start monitoring model performance
- **Health Checks**: Perform initial health checks

## Monitoring and Performance

### Performance Metrics

The system tracks the following metrics for each model:

- **Total Inferences**: Number of predictions made
- **Average Inference Time**: Time taken for predictions
- **Anomaly Rate**: Percentage of anomaly predictions
- **Throughput**: Predictions per second
- **Error Rate**: Failed predictions

### Drift Detection

The system monitors for model drift by tracking:

- **Feature Drift**: Changes in input feature distributions
- **Prediction Drift**: Changes in prediction patterns
- **Performance Drift**: Degradation in model performance

### Alerts and Notifications

Configure alerts for:

- **Model Loading Failures**: Failed model loading attempts
- **High Inference Latency**: Slow model performance
- **Model Errors**: Inference errors and exceptions
- **Model Drift**: Performance degradation over time

## Troubleshooting

### Common Issues

#### 1. Model Not Loading

**Symptoms:**
- Model doesn't appear in the model list
- Service fails to start

**Solutions:**
- Check model file format and permissions
- Verify model compatibility with feature set
- Check service logs for errors

#### 2. Model Validation Failures

**Symptoms:**
- Import fails with validation errors
- Model quality metrics below thresholds

**Solutions:**
- Review model training process
- Check feature engineering consistency
- Retrain model with better data

#### 3. Performance Issues

**Symptoms:**
- High inference latency
- Low throughput
- High error rates

**Solutions:**
- Optimize model architecture
- Check resource constraints
- Monitor system performance

### Debug Commands

```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs backend

# Check model directory
ls -la backend/models/

# Test API connectivity
curl "http://localhost:5000/api/v1/health"

# List available models
curl "http://localhost:5000/api/v1/model-management/models"
```

## Examples

### Complete Model Loading Workflow

```bash
# 1. Check current models
curl "http://localhost:5000/api/v1/model-management/models"

# 2. Import latest model from training service
curl -X POST "http://localhost:5000/api/v1/model-management/import-latest"

# 3. List models again to see the new model
curl "http://localhost:5000/api/v1/model-management/models"

# 4. Validate the new model
curl -X POST "http://localhost:5000/api/v1/model-management/{new_version}/validate"

# 5. Deploy the new model
curl -X POST "http://localhost:5000/api/v1/model-management/{new_version}/deploy"

# 6. Check model performance
curl "http://localhost:5000/api/v1/model-management/performance/{new_version}"

# 7. Monitor for drift
curl -X POST "http://localhost:5000/api/v1/model-management/performance/{new_version}/check-drift"
```

### Manual Model Placement Example

```bash
# Copy model file
cp /path/to/new_model.pkl backend/models/wifi_anomaly_model_v2.pkl

# Restart service
docker-compose restart backend

# Verify model is loaded
curl "http://localhost:5000/api/v1/model-management/models"
```

### Training Service Integration Example

```bash
# Check training service connection
curl "http://localhost:5000/api/v1/model-management/training-service/connection"

# List available models in training service
curl "http://localhost:5000/api/v1/model-management/training-service/models"

# Import latest model
curl -X POST "http://localhost:5000/api/v1/model-management/import-latest"

# Deploy the imported model
curl -X POST "http://localhost:5000/api/v1/model-management/{version}/deploy"
```

## Configuration

### Model Configuration File

The model configuration is defined in `backend/app/config/model_config.yaml`:

```yaml
storage:
  directory: models
  version_format: '%Y%m%d_%H%M%S'
  keep_last_n_versions: 5
  backup_enabled: true

integration:
  training_service_path: /home/dannguyen/WNC/mcp_training
  auto_import: false
  import_interval: 3600
  validate_imports: true

monitoring:
  enable_drift_detection: true
  drift_threshold: 0.1
  performance_tracking: true
```

### Environment Variables

Set these environment variables for customization:

```bash
export MCP_MODEL_DIR=/custom/model/path
export MCP_TRAINING_SERVICE_PATH=/custom/training/path
export MCP_VALIDATE_IMPORTS=true
export MCP_AUTO_IMPORT=false
```

## Best Practices

1. **Always validate models** before deployment in production
2. **Keep model versions** for rollback capability
3. **Monitor performance** after model deployment
4. **Use descriptive naming** for model files
5. **Document model changes** in transfer history
6. **Test models** on sample data before deployment
7. **Set up alerts** for model performance issues
8. **Regular drift monitoring** to detect degradation

## Support

For additional support:

- Check the service logs for detailed error messages
- Review the API documentation for endpoint details
- Consult the architecture documentation for system overview
- Contact the development team for complex issues

---

*Last updated: January 2025*
