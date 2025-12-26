from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.db.session import supabase

router = APIRouter()

class NewsArticle(BaseModel):
    id: int
    title: str
    content: str
    source: Optional[str] = None
    author: Optional[str] = None
    url: Optional[str] = None
    published_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class NewsArticleCreate(BaseModel):
    title: str
    content: str
    source: Optional[str] = None
    author: Optional[str] = None
    url: Optional[str] = None
    published_date: Optional[datetime] = None

@router.get("/", response_model=List[NewsArticle])
async def get_news_articles():
    """Get all news articles from Supabase"""
    try:
        response = supabase.table("news_articles").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch articles: {str(e)}")

@router.get("/{article_id}", response_model=NewsArticle)
async def get_news_article(article_id: int):
    """Get a specific news article from Supabase"""
    try:
        response = supabase.table("news_articles").select("*").eq("id", article_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Article not found")
        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch article: {str(e)}")

@router.post("/", response_model=NewsArticle)
async def create_news_article(article: NewsArticleCreate):
    """Create a new news article in Supabase"""
    try:
        # Convert Pydantic model to dict
        article_data = article.model_dump()
        
        # Insert into Supabase
        response = supabase.table("news_articles").insert(article_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create article")
        
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create article: {str(e)}")

@router.post("/ingest")
async def ingest_news():
    """Trigger news ingestion task"""
    # This will use Dramatiq to process in background
    return {"message": "News ingestion started"}
