from pydantic import BaseModel

class ModelDataFormat(BaseModel):
    sentiment_result: str
    emotion_result: str
    propaganda_result: str