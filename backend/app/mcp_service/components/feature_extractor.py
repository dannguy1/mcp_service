import logging
from typing import List, Dict, Any
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """Extracts features from various types of logs for anomaly detection."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def extract_wifi_features(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract features from WiFi-related logs.
        
        Args:
            logs: List of log entries from hostapd and wpa_supplicant
            
        Returns:
            Dictionary of extracted features
        """
        try:
            features = {
                'auth_failures': 0,
                'deauth_count': 0,
                'beacon_count': 0,
                'association_count': 0,
                'disassociation_count': 0,
                'unique_macs': set(),
                'failed_auth_macs': set(),
                'timestamp': datetime.now().isoformat()
            }
            
            for log in logs:
                message = log.get('message', '').lower()
                
                # Count authentication failures
                if 'authentication failed' in message:
                    features['auth_failures'] += 1
                    # Extract MAC address if present
                    mac = self._extract_mac(message)
                    if mac:
                        features['failed_auth_macs'].add(mac)
                
                # Count deauthentication frames
                elif 'deauthentication' in message:
                    features['deauth_count'] += 1
                
                # Count beacon frames
                elif 'beacon' in message:
                    features['beacon_count'] += 1
                
                # Count associations
                elif 'association' in message:
                    features['association_count'] += 1
                    mac = self._extract_mac(message)
                    if mac:
                        features['unique_macs'].add(mac)
                
                # Count disassociations
                elif 'disassociation' in message:
                    features['disassociation_count'] += 1
                
                # Extract MAC addresses
                mac = self._extract_mac(message)
                if mac:
                    features['unique_macs'].add(mac)
            
            # Convert sets to counts for JSON serialization
            features['unique_mac_count'] = len(features['unique_macs'])
            features['failed_auth_mac_count'] = len(features['failed_auth_macs'])
            
            # Remove sets as they're not JSON serializable
            del features['unique_macs']
            del features['failed_auth_macs']
            
            self.logger.debug(f"Extracted features: {features}")
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting WiFi features: {e}")
            raise
    
    def _extract_mac(self, message: str) -> str:
        """Extract MAC address from log message."""
        mac_pattern = r'([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}'
        match = re.search(mac_pattern, message)
        return match.group(0) if match else None 