from fastapi import APIRouter
from app.utils.cache import _cache
from app.utils.logger import logger
import time

router = APIRouter()


@router.get("/metrics")
async def get_metrics():
    """Get application metrics"""
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        return {
            "cache": {
                "entries": len(_cache),
                "size_mb": round(sum(len(str(v).encode()) for v in _cache.values()) / (1024 * 1024), 2)
            },
            "system": {
                "cpu_percent": round(process.cpu_percent(interval=0.1), 2),
                "memory_mb": round(process.memory_info().rss / (1024 * 1024), 2),
                "uptime_seconds": round(time.time() - process.create_time(), 2)
            },
            "status": "healthy"
        }
    except ImportError:
        return {
            "cache": {
                "entries": len(_cache),
                "size_mb": 0
            },
            "system": {
                "note": "psutil not available"
            },
            "status": "healthy"
        }


@router.get("/metrics/cache")
async def get_cache_metrics():
    """Get cache-specific metrics"""
    return {
        "total_entries": len(_cache),
        "cache_keys": list(_cache.keys())[:10]  # First 10 keys
    }

