from fastapi import APIRouter
import redis
from elasticsearch import Elasticsearch
from app.core.config import settings
from app.db.session import supabase

router = APIRouter()

@router.get("/")
async def basic_health():
    """Simple health check endpoint"""
    return {"status": "healthy"}

@router.get("/full")
async def full_health_check():
    """Comprehensive health check for all services"""
    
    health_status = {
        "api": "healthy",
        "supabase": "unknown",
        "redis": "unknown",
        "elasticsearch": "unknown"
    }
    
    # Test Supabase connection
    try:
        result = supabase.table("news_articles").select("id").limit(1).execute()
        health_status["supabase"] = "healthy"
    except Exception as e:
        health_status["supabase"] = f"error: {str(e)[:100]}"
    
    # Test Redis connection
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        health_status["redis"] = "healthy"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)[:100]}"
    
    # Test Elasticsearch connection
    try:
        es = Elasticsearch([settings.ELASTICSEARCH_URL])
        if es.ping():
            health_status["elasticsearch"] = "healthy"
        else:
            health_status["elasticsearch"] = "not responding"
    except Exception as e:
        health_status["elasticsearch"] = f"error: {str(e)[:100]}"
    
    return health_status
