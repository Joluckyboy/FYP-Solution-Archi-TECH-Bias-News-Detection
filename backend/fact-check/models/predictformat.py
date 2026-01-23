from pydantic import BaseModel

class PredictFormat(BaseModel):
    statement: str
    correctness: str
    explanation: str