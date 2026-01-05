from pydantic import BaseModel, Field 

class TextInput(BaseModel):
    text: str = Field(
        ...,
        example="This is a test sentence."
    )
    
class PropagandaResult(BaseModel):
    non_propaganda_probability: float = Field(
        ...,
        example=0.85
    )
    propaganda_probability: float = Field(
        ...,
        example=0.15
    )
    formatted_result: list = Field(
        ...,
        example=[
            ['Loaded_Language', 'stunning'],
            ['Name_Calling,Labeling', 'war - battered'],
            ['Exaggeration,Minimisation', 'unbelievable ”'],
            ['Loaded_Language', 'war - battered'],
            ['Exaggeration,Minimisation', 'could so magnificent ”'],
            ['Loaded_Language', 'shock revelation']
        ]
    )

class PropagandaResponse(BaseModel):
    propaganda_result: PropagandaResult