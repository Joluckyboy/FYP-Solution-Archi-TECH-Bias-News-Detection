from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union

class TextInput(BaseModel):
    text: str = Field(
        ...,
        example="This is a test sentence."
    )
    

class SentenceSentiment(BaseModel):
    sentence: str
    label: str   # "positive" | "negative" | "neutral"
    positive: float
    negative: float
    neutral: float

class SentimentResult(BaseModel):
    positive: float
    negative: float
    neutral: float
    sentence_sentiments: List[SentenceSentiment] = []

class SentimentResponse(BaseModel):
    sentiment_result: SentimentResult
    sentence_sentiments: Optional[List[SentenceSentiment]] = []