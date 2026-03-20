from pydantic import BaseModel

class ModelDataFormat(BaseModel):
    sentiment_summary: str
    emotion_summary: str
    propaganda_summary: str
    political_bias_summary: str