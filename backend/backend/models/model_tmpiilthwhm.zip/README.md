# Test Model Package

This is a test model package for demonstrating flexible import validation.

## Usage

```python
import joblib
model = joblib.load('model.joblib')
predictions = model.predict(data)
```

## Model Information

- Type: IsolationForest
- Features: 5
- Training samples: 1000
- Contamination: 0.1
