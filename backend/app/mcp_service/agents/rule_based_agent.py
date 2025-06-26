import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from .generic_agent import GenericAgent

class RuleBasedAgent(GenericAgent):
    """
    Rule-based agent that uses predefined rules and thresholds for anomaly detection.
    Based on the current LogLevelAgent implementation.
    """
    
    def __init__(self, config: Dict[str, Any], data_service, model_manager=None):
        """
        Initialize the rule-based agent.
        
        Args:
            config: Configuration dictionary containing agent settings
            data_service: DataService instance for database access
            model_manager: Optional ModelManager instance (not used for rule-based agents)
        """
        super().__init__(config, data_service, model_manager)
        
        # Rule-based specific configuration
        self.target_levels = self.analysis_rules.get('target_levels', ['error', 'critical'])
        self.confidence = self.analysis_rules.get('confidence', 1.0)
        self.exclude_patterns = self.analysis_rules.get('exclude_patterns', [])
        self.include_patterns = self.analysis_rules.get('include_patterns', [])
        self.alert_cooldown = self.analysis_rules.get('alert_cooldown', 300)  # 5 minutes
        self.escalation_rules = self.analysis_rules.get('escalation_rules', {})
        
        # Compile regex patterns for performance
        self._compiled_exclude_patterns = [re.compile(pattern) for pattern in self.exclude_patterns]
        self._compiled_include_patterns = [re.compile(pattern) for pattern in self.include_patterns]
        
        # Track last alert times for cooldown
        self.last_alert_times = {}
    
    async def _perform_analysis(self, logs: List[Dict[str, Any]]):
        """
        Perform rule-based analysis on logs.
        
        Args:
            logs: List of log entries to analyze
        """
        try:
            # Filter logs based on rules
            filtered_logs = self._filter_logs_by_rules(logs)
            self.logger.info(f"Filtered {len(filtered_logs)} logs from {len(logs)} total logs")
            
            if not filtered_logs:
                self.logger.info("No logs match the rule criteria")
                return
            
            # Process each log and generate anomalies
            anomalies_created = 0
            for log in filtered_logs:
                try:
                    await self._process_log_for_anomaly(log)
                    anomalies_created += 1
                except Exception as e:
                    self.logger.error(f"Error processing log {log.get('id')}: {e}")
                    continue
            
            self.logger.info(f"Created {anomalies_created} anomalies from {len(filtered_logs)} filtered logs")
            
        except Exception as e:
            self.logger.error(f"Error in rule-based analysis: {e}")
            raise
    
    def _filter_logs_by_rules(self, logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter logs based on rule-based criteria.
        
        Args:
            logs: List of log entries to filter
            
        Returns:
            List of filtered log entries
        """
        filtered_logs = []
        
        for log in logs:
            # Check if log should be excluded
            if self._should_exclude_log(log):
                continue
            
            # Check if log should be included
            if not self._should_include_log(log):
                continue
            
            # Check if log level matches target levels
            if self._matches_target_level(log):
                filtered_logs.append(log)
        
        return filtered_logs
    
    def _should_exclude_log(self, log: Dict[str, Any]) -> bool:
        """
        Check if a log should be excluded based on exclude patterns.
        
        Args:
            log: Log entry to check
            
        Returns:
            bool: True if log should be excluded
        """
        log_message = log.get('message', '').lower()
        
        for pattern in self._compiled_exclude_patterns:
            if pattern.search(log_message):
                return True
        
        return False
    
    def _should_include_log(self, log: Dict[str, Any]) -> bool:
        """
        Check if a log should be included based on include patterns.
        
        Args:
            log: Log entry to check
            
        Returns:
            bool: True if log should be included
        """
        # If no include patterns specified, include all logs
        if not self._compiled_include_patterns:
            return True
        
        log_message = log.get('message', '').lower()
        
        for pattern in self._compiled_include_patterns:
            if pattern.search(log_message):
                return True
        
        return False
    
    def _matches_target_level(self, log: Dict[str, Any]) -> bool:
        """
        Check if a log matches the target levels.
        
        Args:
            log: Log entry to check
            
        Returns:
            bool: True if log level matches target levels
        """
        log_level = log.get('level', '').lower()
        return log_level in [level.lower() for level in self.target_levels]
    
    async def _process_log_for_anomaly(self, log: Dict[str, Any]):
        """
        Process a single log entry and create an anomaly if needed.
        
        Args:
            log: Log entry to process
        """
        # Check alert cooldown
        log_key = f"{log.get('program', 'unknown')}_{log.get('level', 'unknown')}"
        if self._is_in_cooldown(log_key):
            return
        
        # Determine severity based on log level
        log_level = log.get('level', '').lower()
        severity = self.severity_mapping.get(log_level, 3)
        
        # Check for escalation rules
        if log_key in self.escalation_rules:
            escalation_threshold = self.escalation_rules[log_key]
            # Apply escalation logic here if needed
            severity = min(5, severity + 1)  # Increase severity by 1, max 5
        
        # Create anomaly description
        description = self._create_anomaly_description(log)
        
        # Store the anomaly
        await self.store_anomaly(
            anomaly_type=f"{log_level}_log_detected",
            severity=severity,
            confidence=self.confidence,
            description=description,
            features={
                'log_level': log_level,
                'program': log.get('program', 'unknown'),
                'message': log.get('message', ''),
                'timestamp': log.get('timestamp', ''),
                'source': 'rule_based_agent'
            }
        )
        
        # Update last alert time
        self.last_alert_times[log_key] = datetime.now()
    
    def _is_in_cooldown(self, log_key: str) -> bool:
        """
        Check if a log key is in cooldown period.
        
        Args:
            log_key: Key to check for cooldown
            
        Returns:
            bool: True if in cooldown
        """
        if log_key not in self.last_alert_times:
            return False
        
        time_since_last_alert = datetime.now() - self.last_alert_times[log_key]
        return time_since_last_alert.total_seconds() < self.alert_cooldown
    
    def _create_anomaly_description(self, log: Dict[str, Any]) -> str:
        """
        Create a human-readable description for the anomaly.
        
        Args:
            log: Log entry that triggered the anomaly
            
        Returns:
            str: Description of the anomaly
        """
        log_level = log.get('level', 'unknown')
        program = log.get('program', 'unknown')
        message = log.get('message', '')
        
        # Truncate message if too long
        if len(message) > 200:
            message = message[:200] + "..."
        
        return f"{log_level.upper()} log detected from {program}: {message}"
    
    def get_rule_info(self) -> Dict[str, Any]:
        """
        Get information about the current rules.
        
        Returns:
            dict: Rule information
        """
        return {
            'target_levels': self.target_levels,
            'confidence': self.confidence,
            'exclude_patterns': self.exclude_patterns,
            'include_patterns': self.include_patterns,
            'alert_cooldown': self.alert_cooldown,
            'escalation_rules': self.escalation_rules,
            'severity_mapping': self.severity_mapping
        }
    
    def update_rules(self, new_rules: Dict[str, Any]):
        """
        Update the agent rules.
        
        Args:
            new_rules: New rule configuration
        """
        try:
            # Update rule-based specific configuration
            if 'target_levels' in new_rules:
                self.target_levels = new_rules['target_levels']
            
            if 'confidence' in new_rules:
                self.confidence = new_rules['confidence']
            
            if 'exclude_patterns' in new_rules:
                self.exclude_patterns = new_rules['exclude_patterns']
                self._compiled_exclude_patterns = [re.compile(pattern) for pattern in self.exclude_patterns]
            
            if 'include_patterns' in new_rules:
                self.include_patterns = new_rules['include_patterns']
                self._compiled_include_patterns = [re.compile(pattern) for pattern in self.include_patterns]
            
            if 'alert_cooldown' in new_rules:
                self.alert_cooldown = new_rules['alert_cooldown']
            
            if 'escalation_rules' in new_rules:
                self.escalation_rules = new_rules['escalation_rules']
            
            self.logger.info("Updated agent rules")
            
        except Exception as e:
            self.logger.error(f"Error updating rules: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the rule-based agent.
        
        Returns:
            dict: Dictionary containing agent status information
        """
        status = super().get_status()
        status.update({
            'rule_info': self.get_rule_info(),
            'last_alert_times': {
                key: time.isoformat() for key, time in self.last_alert_times.items()
            }
        })
        return status 