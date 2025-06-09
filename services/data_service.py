import pickle
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional
import redis.asyncio as redis
from config import config

class DataService:
    def __init__(self):
        self.logger = logging.getLogger("data_service")
        self.redis = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            password=config.redis_password,
            decode_responses=False  # Keep as bytes for pickle
        )
        self._setup_logging()
        self._setup_metrics()

    async def get_logs_by_program(self, start_time: datetime, end_time: datetime, program: str) -> List[Dict[str, Any]]:
        """Get logs for a specific program within a time range"""
        try:
            # Check cache first
            cache_key = f"logs:{program}:{start_time.isoformat()}:{end_time.isoformat()}"
            cached_data = await self.redis.get(cache_key)
            
            if cached_data:
                return pickle.loads(cached_data)
            
            # If not in cache, query database
            logs = await self._query_logs(start_time, end_time, program)
            
            # Cache the results
            if logs:
                await self.redis.setex(cache_key, 300, pickle.dumps(logs))
            
            return logs
            
        except Exception as e:
            self.logger.error(f"Error getting logs: {e}")
            return []

    async def save_anomaly(self, anomaly_data: Dict[str, Any]) -> bool:
        """Save an anomaly detection result"""
        try:
            # Convert datetime objects to ISO format for storage
            if 'timestamp' in anomaly_data:
                anomaly_data['timestamp'] = anomaly_data['timestamp'].isoformat()
            
            # Cache the anomaly
            cache_key = f"anomaly:{anomaly_data.get('id')}"
            await self.redis.setex(cache_key, 3600, pickle.dumps(anomaly_data))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving anomaly: {e}")
            return False 