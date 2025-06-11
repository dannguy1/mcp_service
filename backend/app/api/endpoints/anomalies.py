from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, timedelta
import random

router = APIRouter()

# Mock data for demonstration
MOCK_ANOMALIES = [
    {
        "id": 1,
        "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
        "type": "network",
        "severity": 8,
        "description": "Unusual network traffic pattern detected",
        "status": "active"
    },
    {
        "id": 2,
        "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
        "type": "system",
        "severity": 6,
        "description": "High CPU usage detected",
        "status": "resolved"
    },
    {
        "id": 3,
        "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
        "type": "security",
        "severity": 9,
        "description": "Multiple failed login attempts",
        "status": "active"
    }
]

@router.get("/")
async def get_anomalies() -> List[dict]:
    try:
        # In a real implementation, this would query a database
        return MOCK_ANOMALIES
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get anomalies: {str(e)}") 