from typing import Dict, List, Any
from datetime import datetime
import json
import logging
from app.models.export import ExportConfig

logger = logging.getLogger(__name__)

class DataTransformer:
    """Transforms data for export."""
    
    def __init__(self, config: ExportConfig):
        self.config = config
        self.transformations = {
            "log_entry": self._transform_log_entry,
            "anomaly": self._transform_anomaly,
            "ip": self._transform_ip
        }

    def transform(self, data_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data based on its type."""
        if data_type not in self.transformations:
            raise ValueError(f"Unsupported data type: {data_type}")
        
        return self.transformations[data_type](data)

    def _transform_log_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a log entry."""
        transformed = entry.copy()
        
        # Standardize timestamp
        if "timestamp" in transformed:
            if isinstance(transformed["timestamp"], str):
                try:
                    dt = datetime.fromisoformat(transformed["timestamp"])
                    transformed["timestamp"] = dt.isoformat()
                except ValueError:
                    logger.warning(f"Invalid timestamp format: {transformed['timestamp']}")
        
        # Add transformation metadata
        transformed["_metadata"] = {
            "transformed_at": datetime.utcnow().isoformat(),
            "transformation_version": "1.0"
        }
        
        return transformed

    def _transform_anomaly(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """Transform an anomaly detection result."""
        transformed = anomaly.copy()
        
        # Standardize timestamp
        if "timestamp" in transformed:
            if isinstance(transformed["timestamp"], str):
                try:
                    dt = datetime.fromisoformat(transformed["timestamp"])
                    transformed["timestamp"] = dt.isoformat()
                except ValueError:
                    logger.warning(f"Invalid timestamp format: {transformed['timestamp']}")
        
        # Normalize score to 0-1 range if needed
        if "score" in transformed:
            try:
                score = float(transformed["score"])
                if score > 1:
                    transformed["score"] = score / 100
            except (ValueError, TypeError):
                logger.warning(f"Invalid score format: {transformed['score']}")
        
        # Add transformation metadata
        transformed["_metadata"] = {
            "transformed_at": datetime.utcnow().isoformat(),
            "transformation_version": "1.0"
        }
        
        return transformed

    def _transform_ip(self, ip: Dict[str, Any]) -> Dict[str, Any]:
        """Transform an IP address record."""
        transformed = ip.copy()
        
        # Standardize timestamps
        for field in ["first_seen", "last_seen"]:
            if field in transformed:
                if isinstance(transformed[field], str):
                    try:
                        dt = datetime.fromisoformat(transformed[field])
                        transformed[field] = dt.isoformat()
                    except ValueError:
                        logger.warning(f"Invalid timestamp format: {transformed[field]}")
        
        # Normalize risk score to 0-100 range
        if "risk_score" in transformed:
            try:
                score = float(transformed["risk_score"])
                if score > 100:
                    transformed["risk_score"] = score / 10
            except (ValueError, TypeError):
                logger.warning(f"Invalid risk score format: {transformed['risk_score']}")
        
        # Add transformation metadata
        transformed["_metadata"] = {
            "transformed_at": datetime.utcnow().isoformat(),
            "transformation_version": "1.0"
        }
        
        return transformed

    def batch_transform(self, data_type: str, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform a batch of data."""
        return [self.transform(data_type, item) for item in data_list] 