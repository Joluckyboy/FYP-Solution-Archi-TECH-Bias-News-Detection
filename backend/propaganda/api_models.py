from pydantic import BaseModel, Field
from typing import Optional

class TextInput(BaseModel):
    text: str = Field(
        ...,
        json_schema_extra={"example": "This is a test sentence."}
    )

class PropagandaResult(BaseModel):
    non_propaganda_probability: float
    propaganda_probability: float
    formatted_result: list
    techniques:   Optional[list]  = []
    coverage_pct: Optional[float] = None
    severity:     Optional[str]   = None

class PropagandaResponse(BaseModel):
    propaganda_result: PropagandaResult