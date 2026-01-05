from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class URLItem(BaseModel):
    url: Optional[str] = None

class FactCheckItem(BaseModel):
    statement: str
    correctness: str
    explanation: str
    citations: List[str]

# class inherited from URLItem
class NewsItem(URLItem):
    title: Optional[str] = None
    content: Optional[str] = None
    sentiment_result: Optional[Dict[str, Any]] = None
    emotion_result: Optional[Dict[str, Any]] = None
    propaganda_result: Optional[Dict[str, Any]] = None
    factcheck_result: Optional[List[FactCheckItem]] = None
    summarise_result: Optional[str] = None
    data_summary: Optional[Dict[str, Any]] = None


class QuizItem(BaseModel):
    question: str
    options: List[str]
    answer: List[int]
    question_type: str
    debrief: Optional[str] = None