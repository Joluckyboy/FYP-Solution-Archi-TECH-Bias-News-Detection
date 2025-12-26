from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.tasks import process_news_ingestion, analyze_article_bias

router = APIRouter()

class IngestRequest(BaseModel):
    source_url: str

@router.post("/ingest", status_code=202)
async def enqueue_ingest(req: IngestRequest):
    """Enqueue a background ingestion job."""
    try:
        process_news_ingestion.send(req.source_url)
        return {"status": "queued", "job": "process_news_ingestion", "source_url": req.source_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enqueue ingestion: {str(e)}")

@router.post("/analyze/{article_id}", status_code=202)
async def enqueue_analysis(article_id: int):
    """Enqueue a background bias analysis job."""
    try:
        analyze_article_bias.send(article_id)
        return {"status": "queued", "job": "analyze_article_bias", "article_id": article_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enqueue analysis: {str(e)}")
