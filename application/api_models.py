from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class FactCheckItem(BaseModel):
    statement: str
    correctness: str
    explanation: str
    citations: List[str]
    
class URLInput(BaseModel):
    url: str = Field(
        ...,
        json_schema_extra={"example": "https://www.example.com"}
    )

class URLItem(BaseModel):
    url: Optional[str] = None

class URLwithBG(URLItem):
    background: Optional[bool] = True
    force: Optional[bool] = False

# class inherited from URLItem
class NewsItem(URLItem):
    id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    uploader: Optional[str] = None  
    sentiment_result: Optional[Dict[str, Any]] = None
    emotion_result: Optional[Dict[str, Any]] = None
    propaganda_result: Optional[Dict[str, Any]] = None
    political_bias_result: Optional[Dict[str, Any]] = None
    factcheck_result: Optional[List[FactCheckItem]] = None
    summarise_result: Optional[str] = None
    data_summary: Optional[Dict[str, Any]] = None