from pydantic import BaseModel
from typing import Optional

class DataPayload(BaseModel):
    content: str
    title: str
    url: Optional[str] = None

class ModelDataPayload(BaseModel):
    sentiment_result: dict
    emotion_result: dict
    propaganda_result: dict
    summarise_result: str

class SummarisePayload(BaseModel):
    content: str