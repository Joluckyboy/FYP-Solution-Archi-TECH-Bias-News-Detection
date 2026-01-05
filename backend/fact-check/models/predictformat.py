from pydantic import BaseModel

class PredictFormat(BaseModel):
    statement: str
    accuracy: str
    explanation: str