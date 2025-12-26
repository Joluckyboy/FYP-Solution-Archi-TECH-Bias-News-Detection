from fastapi import APIRouter
from app.api.v1.endpoints import news, analysis, health, tasks

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
