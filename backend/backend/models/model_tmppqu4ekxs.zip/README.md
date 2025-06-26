# Model Deployment Package

## Model Information
- **Version**: 20250624_205530
- **Type**: default
- **Training Samples**: 35,915
- **Features**: 32
- **Deployed At**: 2025-06-24T21:41:51.927105
- **Training Duration**: 0.32s

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
- **Threshold**: 0.5582929987266498
- **Anomaly Ratio**: 0.10001392175971043
- **Score Percentile**: 90
- **Batch Size**: 1000
- **Timeout**: 30 seconds

### Feature Names
- hour_of_day
- day_of_week
- minute_of_hour
- time_since_midnight
- is_weekend
- is_business_hours
- is_connection_event
- is_auth_event
- is_error_event
- mac_count
- ip_count
- message_length
- word_count
- special_char_count
- uppercase_ratio
- number_count
- unique_chars
- process_rank
- log_level_numeric
- process_frequency
- window_5min_connection_count
- window_5min_unique_macs
- window_5min_error_count
- window_5min_process_diversity
- window_15min_connection_count
- window_15min_unique_macs
- window_15min_error_count
- window_15min_process_diversity
- window_1hour_connection_count
- window_1hour_unique_macs
- window_1hour_error_count
- window_1hour_process_diversity

## Performance Metrics

### Training Performance
- **score_mean**: 0.4468769600503917
- **score_std**: 0.07660276540786973
- **score_min**: 0.348993300758957
- **score_max**: 0.6733459125730712
- **anomaly_ratio**: 0.10001392175971043
- **threshold_value**: 0.5582929987266498
- **accuracy**: None
- **precision**: None
- **recall**: None
- **f1_score**: None
- **roc_auc**: None
- **average_precision**: None

### Model Parameters
```json
{
  "n_estimators": 100,
  "max_samples": "auto",
  "contamination": 0.1,
  "random_state": 42,
  "bootstrap": true,
  "max_features": 1.0
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
unzip -t model_20250624_205530_deployment.zip

# Check file permissions
ls -la model_20250624_205530_deployment/

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
- Contact your ML team with the model version: 20250624_205530

## Model Lifecycle

### Version History
- **Current**: 20250624_205530
- **Training ID**: db6a3ff7-b70c-4416-a5d6-ecf33faf1362
- **Source**: /home/wnc/mcp_training/exports/upload_20250624_205111_export_c040d84e-5e9f-4bed-9a74-c8352b99cdaa_20250623_142143.json

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
