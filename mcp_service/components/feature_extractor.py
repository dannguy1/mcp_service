import re
from typing import List, Dict, Any
from collections import defaultdict
import logging

class FeatureExtractor:
    def __init__(self):
        """Initialize the feature extractor."""
        self.logger = logging.getLogger("FeatureExtractor")
        
        # Regular expressions for log parsing
        self.patterns = {
            'auth_failure': re.compile(r'authentication failure'),
            'deauth': re.compile(r'deauthentication'),
            'beacon': re.compile(r'beacon'),
            'mac_address': re.compile(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'),
            'ssid': re.compile(r'SSID=\'([^\']+)\''),
            'reason_code': re.compile(r'reason=(\d+)'),
            'status_code': re.compile(r'status=(\d+)')
        }

    def extract_wifi_features(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract features from WiFi logs.
        
        Args:
            logs: List of log entries
            
        Returns:
            dict: Dictionary of extracted features
        """
        try:
            features = {
                'auth_failures': 0,
                'deauth_count': 0,
                'beacon_count': 0,
                'unique_macs': set(),
                'unique_ssids': set(),
                'reason_codes': defaultdict(int),
                'status_codes': defaultdict(int),
                'program_counts': defaultdict(int)
            }
            
            for log in logs:
                message = log.get('message', '')
                program = log.get('program', '')
                
                # Count program occurrences
                features['program_counts'][program] += 1
                
                # Extract MAC addresses
                macs = self.patterns['mac_address'].findall(message)
                features['unique_macs'].update(macs)
                
                # Extract SSIDs
                ssid_match = self.patterns['ssid'].search(message)
                if ssid_match:
                    features['unique_ssids'].add(ssid_match.group(1))
                
                # Count authentication failures
                if self.patterns['auth_failure'].search(message):
                    features['auth_failures'] += 1
                
                # Count deauthentication frames
                if self.patterns['deauth'].search(message):
                    features['deauth_count'] += 1
                
                # Count beacon frames
                if self.patterns['beacon'].search(message):
                    features['beacon_count'] += 1
                
                # Extract reason codes
                reason_match = self.patterns['reason_code'].search(message)
                if reason_match:
                    features['reason_codes'][reason_match.group(1)] += 1
                
                # Extract status codes
                status_match = self.patterns['status_code'].search(message)
                if status_match:
                    features['status_codes'][status_match.group(1)] += 1
            
            # Convert sets to counts for JSON serialization
            features['unique_mac_count'] = len(features['unique_macs'])
            features['unique_ssid_count'] = len(features['unique_ssids'])
            
            # Remove sets from features
            del features['unique_macs']
            del features['unique_ssids']
            
            # Convert defaultdicts to regular dicts
            features['reason_codes'] = dict(features['reason_codes'])
            features['status_codes'] = dict(features['status_codes'])
            features['program_counts'] = dict(features['program_counts'])
            
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting features: {e}")
            raise

    def extract_firewall_features(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract features from firewall logs.
        
        Args:
            logs: List of log entries
            
        Returns:
            dict: Dictionary of extracted features
        """
        # TODO: Implement firewall feature extraction
        raise NotImplementedError("Firewall feature extraction not implemented yet")

    def extract_dns_features(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract features from DNS logs.
        
        Args:
            logs: List of log entries
            
        Returns:
            dict: Dictionary of extracted features
        """
        # TODO: Implement DNS feature extraction
        raise NotImplementedError("DNS feature extraction not implemented yet") 