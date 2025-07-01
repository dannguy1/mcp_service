#!/usr/bin/env python3

Inference Example
Demonstrates how to use the deployed model for predictions.

import joblib
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Any

class ModelInference:
    def __init__(self, model_dir: str = "."):
        """Initialize model inference."""
        self.model_dir = Path(model_dir)
        with open(self.model_dir / 'deployment_manifest.json', 'r') as f:
            self.manifest = json.load(f)
        self.model = joblib.load(self.model_dir / 'model.joblib')
        self.scaler = None
        if (self.model_dir / 'scaler.joblib').exists():
            self.scaler = joblib.load(self.model_dir / 'scaler.joblib')
        self.threshold = self.manifest['inference_config']['threshold']
        self.feature_names = self.manifest['training_info']['feature_names']

    def preprocess_features(self, features: List[Dict[str, Any]]) -> np.ndarray:
        feature_array = []
        for feature_dict in features:
            feature_vector = []
            for feature_name in self.feature_names:
                if feature_name not in feature_dict:
                    raise ValueError("Feature '" + feature_name + "' not found in input")
                feature_vector.append(feature_dict[feature_name])
            feature_array.append(feature_vector)
        return np.array(feature_array)

    def predict(self, features: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            X = self.preprocess_features(features)
            if self.scaler:
                X = self.scaler.transform(X)
            scores = -self.model.score_samples(X)
            predictions = (scores > self.threshold).astype(int)
            return {{
                'predictions': predictions.tolist(),
                'scores': scores.tolist(),
                'threshold': self.threshold,
                'anomaly_count': int(predictions.sum()),
                'total_samples': len(predictions)
            }}
        except Exception as e:
            raise RuntimeError("Prediction failed: " + str(e))

def main():
    inference = ModelInference()
    sample_features = [
        {{
            'auth_failure_ratio': 0.1,
            'deauth_ratio': 0.05,
            'beacon_ratio': 0.3,
            'unique_mac_count': 15,
            'unique_ssid_count': 8,
            'mean_signal_strength': -45.0,
            'std_signal_strength': 5.0,
            'mean_data_rate': 54.0,
            'mean_packet_loss': 0.02,
            'error_ratio': 0.01,
            'warning_ratio': 0.03,
            'mean_hour_of_day': 14.0,
            'mean_day_of_week': 3.0,
            'mean_time_between_events': 120.0,
            'total_devices': 25,
            'max_device_activity': 0.8,
            'mean_device_activity': 0.4
        }}
    ]
    result = inference.predict(sample_features)
    print("🔍 Model Inference Example")
    print("Model Version: " + inference.manifest['model_version'])
    print("Threshold: " + str(result['threshold']))
    print("Predictions: " + str(result['predictions']))
    print("Scores: " + str(result['scores']))
    print("Anomalies detected: " + str(result['anomaly_count']) + "/" + str(result['total_samples']))

if __name__ == "__main__":
    main()
