from pydantic import BaseModel, Field

class TextInput(BaseModel):
    text: str = Field(
        ...,
        example="This is a test sentence."
    )
    

class EmotionResult(BaseModel):
    weighted_avg: dict = Field(
        ...,
        example={
            "neutral": 0.7604480385780334,
            "realization": 0.06248142197728157,
            "approval": 0.05592983588576317,
            "disappointment": 0.039574529975652695
        }
    )
    majority_vote: list = Field(
        ...,
        example=[["neutral", 1]]
    )

class EmotionResponse(BaseModel):
    emotion_result: EmotionResult