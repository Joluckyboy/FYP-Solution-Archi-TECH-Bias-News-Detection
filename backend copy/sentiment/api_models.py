from pydantic import BaseModel, Field

class TextInput(BaseModel):
    text: str = Field(
        ...,
        example="This is a test sentence."
    )
    

class SentimentResponse(BaseModel):
    sentiment_result: dict[str, float] = Field(
        ...,
        example={"positive": 0.89, "negative": 0.05, "neutral": 0.05}
    )