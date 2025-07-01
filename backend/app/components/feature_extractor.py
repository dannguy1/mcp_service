import re
from typing import List, Dict, Any
from collections import defaultdict
import logging
from datetime import datetime

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
            'status_code': re.compile(r'status=(\d+)'),
            'domain': re.compile(r'([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}'),
            'query_type': re.compile(r'(A|AAAA|MX|CNAME|TXT|NS|PTR|SOA)'),
            'response_time': re.compile(r'(\d+(?:\.\d+)?)\s*ms'),
            'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
            'port': re.compile(r':(\d{1,5})\b'),
            'protocol': re.compile(r'\b(TCP|UDP|ICMP|HTTP|HTTPS|FTP|SSH)\b')
        }

    def extract_features(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generic feature extraction method that delegates to specific extractors.
        
        Args:
            logs: List of log entries
            
        Returns:
            Dictionary of extracted features
        """
        try:
            if not logs:
                return self._get_empty_features()
            
            # Determine log type based on program names
            programs = set(log.get('program', '').lower() for log in logs)
            
            if any(prog in ['hostapd', 'wpa_supplicant'] for prog in programs):
                return self.extract_wifi_features(logs)
            elif any(prog in ['named', 'dnsmasq', 'systemd-resolved'] for prog in programs):
                return self.extract_dns_features(logs)
            elif any(prog in ['iptables', 'ufw', 'firewalld'] for prog in programs):
                return self.extract_firewall_features(logs)
            else:
                # Default to generic features
                return self.extract_generic_features(logs)
                
        except Exception as e:
            self.logger.error(f"Error in extract_features: {e}")
            return self._get_empty_features()
    
    def _get_empty_features(self) -> Dict[str, Any]:
        """Return empty feature set."""
        return {
            'auth_failures': 0,
            'deauth_count': 0,
            'beacon_count': 0,
            'unique_mac_count': 0,
            'unique_ssid_count': 0,
            'query_count': 0,
            'response_time': 0,
            'error_count': 0,
            'timestamp': datetime.now().isoformat()
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
                'program_counts': defaultdict(int),
                'timestamp': datetime.now().isoformat()
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
            
            self.logger.debug(f"Extracted WiFi features: {features}")
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting WiFi features: {e}")
            raise

    def extract_dns_features(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract features from DNS logs.
        
        Args:
            logs: List of log entries
            
        Returns:
            dict: Dictionary of extracted features
        """
        try:
            features = {
                'query_count': 0,
                'response_count': 0,
                'error_count': 0,
                'unique_domains': set(),
                'query_types': defaultdict(int),
                'response_times': [],
                'program_counts': defaultdict(int),
                'timestamp': datetime.now().isoformat()
            }
            
            for log in logs:
                message = log.get('message', '').lower()
                program = log.get('program', '')
                
                # Count program occurrences
                features['program_counts'][program] += 1
                
                # Count queries
                if any(term in message for term in ['query', 'request']):
                    features['query_count'] += 1
                    
                    # Extract domain names
                    domain = self._extract_domain(message)
                    if domain:
                        features['unique_domains'].add(domain)
                    
                    # Extract query type
                    qtype = self._extract_query_type(message)
                    if qtype:
                        features['query_types'][qtype] += 1
                
                # Count responses
                elif any(term in message for term in ['response', 'answer']):
                    features['response_count'] += 1
                    
                    # Extract response time if available
                    response_time = self._extract_response_time(message)
                    if response_time:
                        features['response_times'].append(response_time)
                
                # Count errors
                elif any(term in message for term in ['error', 'failed', 'timeout']):
                    features['error_count'] += 1
            
            # Convert sets to counts
            features['unique_domain_count'] = len(features['unique_domains'])
            del features['unique_domains']
            
            # Calculate average response time
            if features['response_times']:
                features['avg_response_time'] = sum(features['response_times']) / len(features['response_times'])
            else:
                features['avg_response_time'] = 0
            
            del features['response_times']
            
            # Convert defaultdicts to regular dicts
            features['query_types'] = dict(features['query_types'])
            features['program_counts'] = dict(features['program_counts'])
            
            self.logger.debug(f"Extracted DNS features: {features}")
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting DNS features: {e}")
            raise

    def extract_firewall_features(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract features from firewall logs.
        
        Args:
            logs: List of log entries
            
        Returns:
            dict: Dictionary of extracted features
        """
        try:
            features = {
                'blocked_connections': 0,
                'allowed_connections': 0,
                'unique_ips': set(),
                'unique_ports': set(),
                'protocols': defaultdict(int),
                'program_counts': defaultdict(int),
                'timestamp': datetime.now().isoformat()
            }
            
            for log in logs:
                message = log.get('message', '').lower()
                program = log.get('program', '')
                
                # Count program occurrences
                features['program_counts'][program] += 1
                
                # Count blocked connections
                if any(term in message for term in ['blocked', 'denied', 'drop']):
                    features['blocked_connections'] += 1
                
                # Count allowed connections
                elif any(term in message for term in ['allowed', 'accept']):
                    features['allowed_connections'] += 1
                
                # Extract IP addresses
                ips = self._extract_ips(message)
                features['unique_ips'].update(ips)
                
                # Extract ports
                ports = self._extract_ports(message)
                features['unique_ports'].update(ports)
                
                # Extract protocols
                protocol = self._extract_protocol(message)
                if protocol:
                    features['protocols'][protocol] += 1
            
            # Convert sets to counts
            features['unique_ip_count'] = len(features['unique_ips'])
            features['unique_port_count'] = len(features['unique_ports'])
            del features['unique_ips']
            del features['unique_ports']
            
            # Convert defaultdicts to regular dicts
            features['protocols'] = dict(features['protocols'])
            features['program_counts'] = dict(features['program_counts'])
            
            self.logger.debug(f"Extracted firewall features: {features}")
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting firewall features: {e}")
            raise

    def extract_generic_features(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract generic features from any type of logs.
        
        Args:
            logs: List of log entries
            
        Returns:
            dict: Dictionary of extracted features
        """
        try:
            features = {
                'log_count': len(logs),
                'error_count': 0,
                'warning_count': 0,
                'unique_programs': set(),
                'unique_hosts': set(),
                'program_counts': defaultdict(int),
                'timestamp': datetime.now().isoformat()
            }
            
            for log in logs:
                message = log.get('message', '').lower()
                program = log.get('program', '')
                host = log.get('host', '')
                
                # Count program occurrences
                features['program_counts'][program] += 1
                
                # Count log levels
                if any(term in message for term in ['error', 'critical', 'failed']):
                    features['error_count'] += 1
                elif 'warning' in message:
                    features['warning_count'] += 1
                
                # Track unique programs and hosts
                if program:
                    features['unique_programs'].add(program)
                if host:
                    features['unique_hosts'].add(host)
            
            # Convert sets to counts
            features['unique_program_count'] = len(features['unique_programs'])
            features['unique_host_count'] = len(features['unique_hosts'])
            del features['unique_programs']
            del features['unique_hosts']
            
            # Convert defaultdicts to regular dicts
            features['program_counts'] = dict(features['program_counts'])
            
            self.logger.debug(f"Extracted generic features: {features}")
            return features
            
        except Exception as e:
            self.logger.error(f"Error extracting generic features: {e}")
            raise
    
    def _extract_domain(self, message: str) -> str:
        """Extract domain name from log message."""
        match = self.patterns['domain'].search(message)
        return match.group(0) if match else None
    
    def _extract_query_type(self, message: str) -> str:
        """Extract DNS query type from log message."""
        match = self.patterns['query_type'].search(message)
        return match.group(1) if match else None
    
    def _extract_response_time(self, message: str) -> float:
        """Extract response time from log message."""
        match = self.patterns['response_time'].search(message)
        return float(match.group(1)) if match else None
    
    def _extract_ips(self, message: str) -> List[str]:
        """Extract IP addresses from log message."""
        return self.patterns['ip_address'].findall(message)
    
    def _extract_ports(self, message: str) -> List[str]:
        """Extract port numbers from log message."""
        return self.patterns['port'].findall(message)
    
    def _extract_protocol(self, message: str) -> str:
        """Extract protocol from log message."""
        match = self.patterns['protocol'].search(message)
        return match.group(1) if match else None 