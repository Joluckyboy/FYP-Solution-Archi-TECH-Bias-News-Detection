import json
import hashlib
import logging

import redis
import vars as vars

logger = logging.getLogger(__name__)

# Default TTL: 24 hours
DEFAULT_TTL = 60 * 60 * 24

try:
    _redis = redis.from_url(vars.redis_url, decode_responses=True)
    _redis.ping()
    logger.info("Connected to Redis successfully")
except Exception as e:
    logger.warning(f"Redis unavailable, caching disabled: {e}")
    _redis = None


def _cache_key(url: str) -> str:
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    return f"analysis:{url_hash}"


def get_cached_result(url: str) -> dict | None:
    """Retrieve cached analysis result for a URL. Returns None on miss or error."""
    if _redis is None:
        return None
    try:
        data = _redis.get(_cache_key(url))
        if data:
            logger.info(f"Redis cache HIT for {url}")
            return json.loads(data)
        logger.info(f"Redis cache MISS for {url}")
        return None
    except Exception as e:
        logger.warning(f"Redis get error: {e}")
        return None


def cache_result(url: str, data: dict, ttl: int = DEFAULT_TTL):
    """Cache analysis result for a URL with a TTL (seconds)."""
    if _redis is None:
        return
    try:
        _redis.set(_cache_key(url), json.dumps(data, default=str), ex=ttl)
        logger.info(f"Cached result for {url} (TTL={ttl}s)")
    except Exception as e:
        logger.warning(f"Redis set error: {e}")


def delete_cached_result(url: str):
    """Delete cached result for a URL (used on force re-analyze)."""
    if _redis is None:
        return
    try:
        _redis.delete(_cache_key(url))
        logger.info(f"Deleted cache for {url}")
    except Exception as e:
        logger.warning(f"Redis delete error: {e}")


def is_analysis_complete(data: dict) -> bool:
    """Check if all analysis fields are present in the cached data."""
    required = ["sentiment_result", "emotion_result", "propaganda_result",
                 "factcheck_result", "summarise_result"]
    for field in required:
        if not data.get(field):
            return False

    data_summary = data.get("data_summary")
    if not data_summary or (isinstance(data_summary, dict) and len(data_summary) == 0):
        return False

    return True
