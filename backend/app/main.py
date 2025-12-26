from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
import redis
from elasticsearch import Elasticsearch

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "message": "Bias News Detection API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy"}

@app.get("/api/v1/health/full")
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
        from app.db.session import supabase
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
