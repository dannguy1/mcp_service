# Model Deployment Package

## Model Information
- **Version**: 20250630_114348
- **Type**: default
- **Training Samples**: 1,399
- **Features**: 30
- **Deployed At**: 2025-06-30T11:48:21.517503
- **Training Duration**: 0.00s

## Package Contents

### Core Files
- `model.joblib` - Trained model file
- `scaler.joblib` - Feature scaler (if applicable)
- `metadata.json` - Complete model metadata
- `deployment_manifest.json` - Deployment configuration and integrity checks

### Validation & Examples
- `validate_model.py` - Model validation script
- `inference_example.py` - Usage example
- `requirements.txt` - Python dependencies

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Validate Model
```bash
python validate_model.py
```

### 3. Run Inference Example
```bash
python inference_example.py
```

## Production Integration

### Using the ModelInference Class
```python
from inference_example import ModelInference

# Initialize
inference = ModelInference()

# Prepare features (must match training feature names)
features = [
    {
        'auth_failure_ratio': 0.1,
        'deauth_ratio': 0.05,
        # ... all other features
    }
]

# Make predictions
result = inference.predict(features)
print(f"Anomalies: {result['anomaly_count']}/{result['total_samples']}")
```

### API Integration Example
```python
from flask import Flask, request, jsonify
from inference_example import ModelInference

app = Flask(__name__)
inference = ModelInference()

@app.route('/predict', methods=['POST'])
def predict():
    features = request.json['features']
    result = inference.predict(features)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Batch Processing Example
```python
from inference_example import ModelInference
import pandas as pd

# Initialize model
inference = ModelInference()

# Load data in batches
def process_batches(data_file, batch_size=1000):
    for chunk in pd.read_csv(data_file, chunksize=batch_size):
        # Convert to required format
        features = chunk.to_dict('records')
        
        # Make predictions
        result = inference.predict(features)
        
        # Process results
        yield result

# Process large dataset
for batch_result in process_batches('large_dataset.csv'):
    print(f"Batch anomalies: {batch_result['anomaly_count']}")
```

## Model Configuration

### Inference Settings
- **Threshold**: -0.48855907766436535
- **Anomaly Ratio**: 0.1
- **Score Percentile**: 90
- **Batch Size**: 1000
- **Timeout**: 30 seconds

### Feature Names
- hour_of_day_mean
- hour_of_day_std
- day_of_week_mean
- day_of_week_std
- minute_of_hour_mean
- minute_of_hour_std
- avg_time_interval
- std_time_interval
- peak_hour
- peak_hour_count
- id_mean
- id_std
- id_min
- id_max
- id_median
- device_id_mean
- device_id_std
- device_id_min
- device_id_max
- device_id_median
- push_attempts_mean
- push_attempts_std
- push_attempts_min
- push_attempts_max
- push_attempts_median
- total_records
- missing_values_ratio
- duplicate_records_ratio
- connection_frequency
- burst_connections_ratio

## Performance Metrics

### Training Performance
- **score_mean**: -0.5116062735579955
- **score_std**: 0.018088189750736557
- **score_min**: -0.5852948210161463
- **score_max**: -0.4562370822899607
- **score_range**: 0.1290577387261856
- **score_median**: -0.5113579610333319
- **anomaly_ratio**: 0.1
- **threshold_value**: -0.48855907766436535
- **detected_anomalies**: 1259.0
- **total_samples**: 1399.0
- **score_variance**: 0.00032718260845865106
- **score_skewness**: -0.09573500346217609
- **score_kurtosis**: 0.18339714885900005

### Model Parameters
```json
{
  "bootstrap": false,
  "contamination": 0.1,
  "max_features": 1.0,
  "max_samples": "auto",
  "n_estimators": 100,
  "n_jobs": -1,
  "random_state": 42,
  "verbose": 0,
  "warm_start": false
}
```

## Security & Integrity

### File Integrity
All files include SHA256 hashes for integrity verification:
- Run `python validate_model.py` to verify
- Check `deployment_manifest.json` for expected hashes

### Model Validation
The validation script checks:
- File integrity (hash verification)
- Model loading capability
- Basic inference functionality
- Feature compatibility

## Error Handling

### Common Error Scenarios

1. **Feature Mismatch**
   ```python
   # Error: Missing required features
   ValueError: Feature 'auth_failure_ratio' not found in input
   
   # Solution: Ensure all training features are provided
   ```

2. **Model Loading Failure**
   ```python
   # Error: Corrupted model file
   joblib.UnpicklingError: Invalid pickle data
   
   # Solution: Re-download package and verify integrity
   ```

3. **Memory Issues**
   ```python
   # Error: Large batch processing
   MemoryError: Unable to allocate array
   
   # Solution: Reduce batch size or process in chunks
   ```

### Error Recovery
```python
from inference_example import ModelInference
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_predict(features, max_retries=3):
    for attempt in range(max_retries):
        try:
            inference = ModelInference()
            return inference.predict(features)
        except Exception as e:
            logger.error(f"Prediction attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(1)  # Brief delay before retry
```

## Performance Considerations

### Memory Usage
- **Model Loading**: ~50-200MB RAM
- **Feature Processing**: ~10-50MB per 1000 samples
- **Batch Processing**: Scale with batch size

### Processing Speed
- **Single Prediction**: ~1-5ms
- **Batch Processing**: ~100-500 predictions/second
- **Scalability**: Linear with CPU cores

### Optimization Tips
1. **Batch Processing**: Use appropriate batch sizes (500-2000)
2. **Memory Management**: Process large datasets in chunks
3. **Caching**: Reuse ModelInference instance for multiple predictions
4. **Parallel Processing**: Use multiple workers for high-throughput scenarios

## Troubleshooting

### Common Issues
1. **Import Errors**: Install requirements with `pip install -r requirements.txt`
2. **Feature Mismatch**: Ensure input features match the feature names exactly
3. **Memory Issues**: Reduce batch size in inference configuration
4. **Performance**: Consider model optimization or hardware upgrades

### Package Extraction Issues
```bash
# Verify package integrity
unzip -t model_20250630_114348_deployment.zip

# Check file permissions
ls -la model_20250630_114348_deployment/

# Validate file hashes
python validate_model.py
```

### Import Errors
```bash
# Check Python version compatibility
python --version

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import joblib, numpy, sklearn; print('OK')"
```

### Performance Issues
```python
# Profile memory usage
import psutil
process = psutil.Process()
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")

# Optimize batch size
for batch_size in [100, 500, 1000, 2000]:
    # Test performance with different batch sizes
    pass
```

## Support

### Package Contents
- **README.md**: Comprehensive usage guide
- **inference_example.py**: Working code examples
- **validate_model.py**: Self-diagnostic tool

### Additional Resources
- Model training logs and metrics
- Feature engineering documentation
- Performance benchmarks
- Integration examples

### Contact Information
For issues with this model deployment:
- Check the validation script output
- Review the deployment manifest
- Contact your ML team with the model version: 20250630_114348

## Model Lifecycle

### Version History
- **Current**: 20250630_114348
- **Training ID**: c94cef4e-ecf3-4a9c-bd01-41a1e956d7c5
- **Source**: ['/home/dannguyen/WNC/mcp_training/exports/upload_20250628_191413_export_f45bd6d1-064a-44a0-8545-3c878ed9d487.json']

### Monitoring
Monitor model performance in production:
- Prediction accuracy
- Feature drift detection
- Performance metrics
- Error rates

### Updates
When deploying model updates:
1. Validate new model with `validate_model.py`
2. Test with production-like data
3. A/B test if possible
4. Monitor performance after deployment

## Version History

### Package Format Version 1.0
- Initial release
- Comprehensive validation and documentation
- Production-ready inference class
- Industry-standard security practices

### Future Enhancements
- Model versioning and rollback support
- Advanced monitoring integration
- Automated performance optimization
- Cloud deployment templates
