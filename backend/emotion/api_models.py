from pydantic import BaseModel, Field
from typing import Optional

class TextInput(BaseModel):
    text: str = Field(
        ...,
        example="This is a test sentence."
    )
    

class EmotionResult(BaseModel):
    weighted_avg: dict
    majority_vote: list
    dominant_emotion: Optional[str] = None  
    dominant_score: Optional[float] = None    
    section_emotions: Optional[list] = []     
    sentence_emotions: Optional[list] = []    

class EmotionResponse(BaseModel):
    emotion_result: EmotionResult