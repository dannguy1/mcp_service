from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from app.models.export import DataValidationResult

logger = logging.getLogger(__name__)

class DataValidator:
    """Validates data for export."""
    
    def __init__(self, validation_level: str = "basic"):
        self.validation_level = validation_level
        self.required_fields = {
            "log_entry": ["timestamp", "level", "message", "source"],
            "anomaly": ["timestamp", "score", "type", "details"],
            "ip": ["address", "first_seen", "last_seen", "risk_score"]
        }

    def validate_log_entry(self, entry: Dict[str, Any]) -> DataValidationResult:
        """Validate a log entry."""
        errors = []
        missing_fields = []
        invalid_values = {}

        # Check required fields
        for field in self.required_fields["log_entry"]:
            if field not in entry:
                missing_fields.append(field)
            elif entry[field] is None:
                invalid_values[field] = ["null"]

        # Validate timestamp
        if "timestamp" in entry:
            try:
                if isinstance(entry["timestamp"], str):
                    datetime.fromisoformat(entry["timestamp"])
            except ValueError:
                invalid_values["timestamp"] = [entry["timestamp"]]

        # Validate log level
        if "level" in entry and entry["level"] not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            invalid_values["level"] = [entry["level"]]

        # Calculate quality metrics
        quality_metrics = {
            "completeness": 1.0 - (len(missing_fields) / len(self.required_fields["log_entry"])),
            "validity": 1.0 - (len(invalid_values) / len(self.required_fields["log_entry"]))
        }

        is_valid = len(missing_fields) == 0 and len(invalid_values) == 0

        return DataValidationResult(
            is_valid=is_valid,
            validation_errors=errors,
            quality_metrics=quality_metrics,
            missing_fields=missing_fields,
            invalid_values=invalid_values
        )

    def validate_anomaly(self, anomaly: Dict[str, Any]) -> DataValidationResult:
        """Validate an anomaly detection result."""
        errors = []
        missing_fields = []
        invalid_values = {}

        # Check required fields
        for field in self.required_fields["anomaly"]:
            if field not in anomaly:
                missing_fields.append(field)
            elif anomaly[field] is None:
                invalid_values[field] = ["null"]

        # Validate score
        if "score" in anomaly:
            try:
                score = float(anomaly["score"])
                if not 0 <= score <= 1:
                    invalid_values["score"] = [anomaly["score"]]
            except (ValueError, TypeError):
                invalid_values["score"] = [anomaly["score"]]

        # Calculate quality metrics
        quality_metrics = {
            "completeness": 1.0 - (len(missing_fields) / len(self.required_fields["anomaly"])),
            "validity": 1.0 - (len(invalid_values) / len(self.required_fields["anomaly"]))
        }

        is_valid = len(missing_fields) == 0 and len(invalid_values) == 0

        return DataValidationResult(
            is_valid=is_valid,
            validation_errors=errors,
            quality_metrics=quality_metrics,
            missing_fields=missing_fields,
            invalid_values=invalid_values
        )

    def validate_ip(self, ip: Dict[str, Any]) -> DataValidationResult:
        """Validate an IP address record."""
        errors = []
        missing_fields = []
        invalid_values = {}

        # Check required fields
        for field in self.required_fields["ip"]:
            if field not in ip:
                missing_fields.append(field)
            elif ip[field] is None:
                invalid_values[field] = ["null"]

        # Validate IP address format
        if "address" in ip:
            import ipaddress
            try:
                ipaddress.ip_address(ip["address"])
            except ValueError:
                invalid_values["address"] = [ip["address"]]

        # Validate risk score
        if "risk_score" in ip:
            try:
                score = float(ip["risk_score"])
                if not 0 <= score <= 100:
                    invalid_values["risk_score"] = [ip["risk_score"]]
            except (ValueError, TypeError):
                invalid_values["risk_score"] = [ip["risk_score"]]

        # Calculate quality metrics
        quality_metrics = {
            "completeness": 1.0 - (len(missing_fields) / len(self.required_fields["ip"])),
            "validity": 1.0 - (len(invalid_values) / len(self.required_fields["ip"]))
        }

        is_valid = len(missing_fields) == 0 and len(invalid_values) == 0

        return DataValidationResult(
            is_valid=is_valid,
            validation_errors=errors,
            quality_metrics=quality_metrics,
            missing_fields=missing_fields,
            invalid_values=invalid_values
        ) 