import psutil
from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

def get_uptime() -> str:
    """Get system uptime in human readable format"""
    uptime_seconds = psutil.boot_time()
    uptime = datetime.now() - datetime.fromtimestamp(uptime_seconds)
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}d {hours}h {minutes}m {seconds}s"

@router.get("/stats")
async def get_server_stats() -> Dict[str, Any]:
    try:
        # CPU Information
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        try:
            # Try to get CPU temperature if available
            temps = psutil.sensors_temperatures()
            cpu_temp = next(iter(temps.values()))[0].current if temps else 0
        except:
            cpu_temp = 0

        # Memory Information
        memory = psutil.virtual_memory()
        
        # Disk Information
        disk = psutil.disk_usage('/')

        return {
            "cpu": {
                "usage": cpu_percent,
                "cores": cpu_count,
                "temperature": cpu_temp
            },
            "memory": {
                "total": memory.total,
                "used": memory.used,
                "free": memory.available
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free
            },
            "uptime": get_uptime()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get server stats: {str(e)}")
