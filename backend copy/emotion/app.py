from fastapi import FastAPI, Request
from pydantic import BaseModel

from methods import predict, aggregate_emotions_weighted, aggregate_emotions_majority_vote, hybrid_aggregation
from api_models import TextInput, EmotionResponse
from model import emotion_model

app = FastAPI(
    title="Emotion Analysis API",
    description="API for analyzing emotion of text using a pre-trained model.",
    version="1.0.0"
)


model = emotion_model()

@app.get("/")
def health_check():
    # return 200
    return {"status": "ok"}

@app.get("/emotion")
def health_check2():
    # return 200
    return {"status": "ok"}

@app.post("/emotion/analyze_emotion", 
          response_model= EmotionResponse, 
          summary= "Analyze Emotion", 
          description="Analyze the emotion of the provided text."
          )
async def analyze_emotion(input: TextInput):
    
    text_chunks = model.chunk_text(input.text)
    # print("text_chunks", text_chunks)

    weights = [len(chunk) for chunk in text_chunks]
    # print("weights", weights)

    emotion_results = predict(text_chunks, model.tokenizer, model.classifier)
    # print("emotion_results", emotion_results)

    weighted_avg, majority_vote = hybrid_aggregation(emotion_results, weights)
    # print("weighted_avg", weighted_avg)

    return {
        "emotion_result": {
            "weighted_avg": weighted_avg,
            "majority_vote": majority_vote
        }
    }


