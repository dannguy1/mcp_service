# Model Loading Guide

This guide explains how to load new trained models into the MCP (Model Context Protocol) service system.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Model Package Format](#model-package-format)
- [Model Loading Methods](#model-loading-methods)
- [Model Directory Structure](#model-directory-structure)
- [API Endpoints](#api-endpoints)
- [Frontend UI](#frontend-ui)
- [Validation and Deployment](#validation-and-deployment)
- [Monitoring and Performance](#monitoring-and-performance)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)

## Overview

The MCP service loads models that are packaged by the MCP Training Service. These packages are self-contained ZIP archives that include the trained model, scaler, metadata, validation scripts, and integration examples. The MCP system supports multiple loading methods, automatic validation, version management, and performance monitoring.

## Prerequisites

- MCP service is running and accessible
- Deployable model package ZIP file (see [Model Package Format](#model-package-format))
- Proper permissions to access model directories
- Model is compatible with the current feature set and MCP protocol

## Model Package Format

Models must be packaged as described in the [Deployable Model Package Specification](./Deployable-Package-Specification.md):

- **Format**: ZIP archive (e.g., `model_20241201_143022_deployment.zip`)
- **Contents**:
  - `model.joblib`: Trained model (required)
  - `scaler.joblib`: Feature scaler (optional)
  - `metadata.json`: Model metadata (required)
  - `deployment_manifest.json`: Deployment configuration and integrity info (required)
  - `validate_model.py`: Model validation script (required)
  - `inference_example.py`: Production-ready inference class (required)
  - `requirements.txt`: Python dependencies (required)
  - `README.md`: Documentation (required)

**See the Deployable Model Package Specification for full details on file structure and requirements.**

## Model Loading Methods

### Method 1: Direct Package Placement

1. **Copy the model package ZIP file** (e.g., `model_20241201_143022_deployment.zip`) to a location on the host filesystem accessible by the MCP backend (e.g., `/home/user/models/`).

2. **Extract the model package:**
   ```bash
   unzip model_20241201_143022_deployment.zip -d backend/models/model_20241201_143022
   ```

3. **Verify package contents:**
   ```bash
   ls backend/models/model_20241201_143022/
   # Should include model.joblib, scaler.joblib, metadata.json, deployment_manifest.json, etc.
   ```

4. **(Recommended) Run validation script:**
   ```bash
   cd backend/models/model_20241201_143022
   pip install -r requirements.txt
   python validate_model.py
   ```

5. **Restart the MCP service to load the new model:**
   ```bash
   docker-compose restart backend
   ```

#### Advantages:
- Ensures all required files are present and validated
- No manual file copying or renaming inside the container
- Supports versioned model directories

#### Disadvantages:
- Manual process
- Requires service restart

### Method 2: Using the Model Management API

The MCP backend provides REST API endpoints for automated model import and deployment.

#### A. Import Model Package

1. **Copy the model package ZIP file to the host filesystem.**
2. **Use the API to import the model:**
   ```bash
   curl -X POST "http://localhost:5000/api/v1/model-management/import" \
     -F "file=@/path/to/model_20241201_143022_deployment.zip"
   ```
   - The backend will extract, analyze, and validate the model package.
   - If a model of the same type already exists, it will be replaced by the new one.

#### B. Deploy a Model Version

```bash
curl -X POST "http://localhost:5000/api/v1/model-management/{version}/deploy"
```

#### C. Validate a Model

```bash
curl -X POST "http://localhost:5000/api/v1/model-management/{version}/validate"
```

#### Advantages:
- Automated validation and registration
- Version management and rollback support
- Transfer and deployment history tracking

#### Disadvantages:
- Requires API access and authentication

### Method 3: Using the Frontend UI

1. **Copy the model package ZIP file to the host filesystem.**
2. **Access the Models page** in the MCP service frontend.
3. **Select the model package ZIP file** using the "Import Model" button.
4. **The UI will analyze the package, display its metadata, and allow you to confirm import.**
5. **If a model of the same type exists, it will be replaced.**
6. **Deploy or validate the model** using the UI controls.

#### Advantages:
- User-friendly interface
- Visual feedback and status
- No command-line required

#### Disadvantages:
- Limited to available UI features

---

> **Note:**  
> The MCP system does **not** automatically scan or import models from the training service or any external directory.  
> All model imports must be initiated by a user via the UI or API, and the model package must be manually copied to the host filesystem first.

---

## Model Directory Structure

Models should be placed in versioned subdirectories under:

```
backend/models/
└── model_{version}/
    ├── model.joblib
    ├── scaler.joblib
    ├── metadata.json
    ├── deployment_manifest.json
    ├── validate_model.py
    ├── inference_example.py
    ├── requirements.txt
    └── README.md
```

- The MCP backend will automatically discover and manage models in this structure after import.

## API Endpoints

### Model Management Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/model-management/models` | GET | List all available models |
| `/api/v1/model-management/models/{version}` | GET | Get model information |
| `/api/v1/model-management/import` | POST | Import model package (ZIP) |
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

## Frontend UI

### Models Page

- **Model List**: View all available models and their status
- **Import Model**: Upload new model package ZIP files from the host filesystem
- **Deploy/Rollback**: Manage model deployment
- **Validation**: Validate model quality and performance
- **Performance**: View model performance metrics

### Performance Tab

- **Total Inferences**: Number of times each model has been used
- **Average Inference Time**: Model performance speed
- **Anomaly Rate**: Percentage of predictions that are anomalies
- **Performance Trends**: Whether performance is improving or degrading

## Validation and Deployment

When a new model package is loaded, the MCP system performs:

1. **Integrity Check**: Verifies SHA256 hashes for all files (see `deployment_manifest.json`)
2. **Model Loading**: Loads `model.joblib` and (if present) `scaler.joblib`
3. **Feature Compatibility**: Ensures model expects the correct features (see `metadata.json`)
4. **Validation Script**: Optionally runs `validate_model.py` for functional testing
5. **Registration**: Updates the model registry and assigns a version
6. **Deployment**: Deploys the model for inference (manual or automatic)
7. **Monitoring**: Starts performance and drift monitoring

## Monitoring and Performance

- **Performance Metrics**: Total inferences, average inference time, anomaly rate, throughput, error rate
- **Drift Detection**: Feature, prediction, and performance drift
- **Alerts**: Model loading failures, high latency, errors, drift

## Troubleshooting

### Common Issues

- **Model Not Loading**: Check package structure, file permissions, and logs
- **Validation Failures**: Run `validate_model.py` and review output
- **Performance Issues**: Monitor resource usage and adjust batch size

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
# 1. Copy model package to host filesystem
cp /path/from/training/model_20241201_143022_deployment.zip /host/path/

# 2. Import model package via API
curl -X POST "http://localhost:5000/api/v1/model-management/import" \
  -F "file=@/host/path/model_20241201_143022_deployment.zip"

# 3. List models
curl "http://localhost:5000/api/v1/model-management/models"

# 4. Validate the new model
curl -X POST "http://localhost:5000/api/v1/model-management/20241201_143022/validate"

# 5. Deploy the new model
curl -X POST "http://localhost:5000/api/v1/model-management/20241201_143022/deploy"

# 6. Check model performance
curl "http://localhost:5000/api/v1/model-management/performance/20241201_143022"
```

### Manual Model Placement Example

```bash
cp /path/from/training/model_20241201_143022_deployment.zip /host/path/
unzip model_20241201_143022_deployment.zip -d backend/models/model_20241201_143022
docker-compose restart backend
curl "http://localhost:5000/api/v1/model-management/models"
```

## Best Practices

1. **Always validate models** before deployment in production
2. **Keep model versions** for rollback capability
3. **Monitor performance** after model deployment
4. **Use descriptive naming** for model directories
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

*Last updated: June 2025*
