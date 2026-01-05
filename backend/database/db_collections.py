from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Define the schema for NewsData using Pydantic
class NewsData(BaseModel):
    id: Optional[str] = None
    url: str
    title: Optional[str] = None
    content: Optional[str] = None
    sentiment_result: Optional[Dict[str, Any]] = None
    emotion_result: Optional[Dict[str, Any]] = None
    propaganda_result: Optional[Dict[str, Any]] = None
    factcheck_result: Optional[List[Dict[str, Any]]] = None
    summarise_result: Optional[str] = None
    data_summary: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Define the schema for QuizData using Pydantic
class QuizData(BaseModel):
    id: Optional[str] = None
    question: str
    options: List[str]
    answer: Optional[List[int]] = None
    question_type: str
    debrief: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
