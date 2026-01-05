from pydantic import BaseModel

class DataPayload(BaseModel):
    content: str
    title: str

class ModelDataPayload(BaseModel):
    sentiment_result: dict
    emotion_result: dict
    propaganda_result: dict
    summarise_result: str

class SummarisePayload(BaseModel):
    content: str