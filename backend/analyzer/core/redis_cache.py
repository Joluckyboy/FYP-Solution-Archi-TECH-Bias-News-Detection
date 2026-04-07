"""
core/redis_cache.py
~~~~~~~~~~~~~~~~~~~
Lightweight Redis cache for the analyzer service.
Gracefully degrades if Redis is unavailable.
"""

import json
import logging
import os

import redis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

try:
    _redis = redis.from_url(REDIS_URL, decode_responses=True)
    _redis.ping()
    logger.info("Analyzer connected to Redis successfully")
except Exception as e:
    logger.warning(f"Redis unavailable, caching disabled: {e}")
    _redis = None


def get_cached(key: str) -> dict | list | None:
    """Return cached JSON value or None on miss/error."""
    if _redis is None:
        return None
    try:
        data = _redis.get(key)
        if data:
            logger.info(f"Redis cache HIT: {key}")
            return json.loads(data)
        return None
    except Exception as e:
        logger.warning(f"Redis get error: {e}")
        return None


def set_cached(key: str, value, ttl: int = 600):
    """Cache a JSON-serialisable value with a TTL (seconds)."""
    if _redis is None:
        return
    try:
        _redis.set(key, json.dumps(value, default=str), ex=ttl)
        logger.info(f"Redis cached: {key} (TTL={ttl}s)")
    except Exception as e:
        logger.warning(f"Redis set error: {e}")


def delete_cached(key: str):
    """Delete a cached key."""
    if _redis is None:
        return
    try:
        _redis.delete(key)
    except Exception as e:
        logger.warning(f"Redis delete error: {e}")
