#!/usr/bin/env python3
"""
Inference example for the model.
"""

import joblib
import numpy as np
import json

def load_model(model_path):
    """Load the trained model."""
    return joblib.load(model_path)

def predict_anomaly(model, data):
    """Predict anomalies using the model."""
    predictions = model.predict(data)
    scores = model.score_samples(data)
    return predictions, scores

def main():
    """Example usage."""
    # Load model
    model = load_model("model.joblib")
    
    # Create sample data
    sample_data = np.random.randn(5, 5)
    
    # Make predictions
    predictions, scores = predict_anomaly(model, sample_data)
    
    print("Predictions:", predictions)
    print("Scores:", scores)

if __name__ == "__main__":
    main()
