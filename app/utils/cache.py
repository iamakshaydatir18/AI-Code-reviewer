import hashlib
import json
from typing import Optional, Dict, Any
from functools import wraps
from app.utils.logger import logger

# Simple in-memory cache (can be replaced with Redis)
_cache: Dict[str, Any] = {}

def get_cache_key(language: str, code: str) -> str:
    """Generate cache key from language and code"""
    content = f"{language}:{code}"
    return hashlib.md5(content.encode()).hexdigest()

def get_cached_review(language: str, code: str) -> Optional[Dict[str, Any]]:
    """Get cached review if exists"""
    cache_key = get_cache_key(language, code)
    if cache_key in _cache:
        logger.info(f"Cache hit for key: {cache_key[:8]}...")
        return _cache[cache_key]
    return None

def cache_review(language: str, code: str, review: Dict[str, Any], ttl: int = 3600):
    """Cache review result"""
    cache_key = get_cache_key(language, code)
    _cache[cache_key] = {
        "review": review,
        "timestamp": __import__("time").time(),
        "ttl": ttl
    }
    logger.info(f"Cached review with key: {cache_key[:8]}...")

def clear_expired_cache():
    """Remove expired cache entries"""
    import time
    current_time = time.time()
    expired_keys = [
        key for key, value in _cache.items()
        if current_time - value["timestamp"] > value["ttl"]
    ]
    for key in expired_keys:
        del _cache[key]
    if expired_keys:
        logger.info(f"Cleared {len(expired_keys)} expired cache entries")

