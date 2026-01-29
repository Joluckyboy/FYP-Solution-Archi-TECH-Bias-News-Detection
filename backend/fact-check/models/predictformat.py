from typing import List, Optional

from pydantic import BaseModel


class PredictFormat(BaseModel):
    statement: str
    correctness: str
    explanation: str
    citations: List[str] = []
    citation_confidence: Optional[str] = None