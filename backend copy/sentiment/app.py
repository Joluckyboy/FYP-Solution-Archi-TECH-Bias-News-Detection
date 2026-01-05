from fastapi import FastAPI, Request

from api_models import TextInput, SentimentResponse
from model import sentiment_model


app = FastAPI(
    title="Sentiment Analysis API",
    description="API for analyzing sentiment of text using a pre-trained model.",
    version="1.0.0"
)

model = sentiment_model()


@app.get("/")
async def health_check():
    # return 200
    return {"status": "ok"}


@app.get("/sentiment")
def health_check2():
    # return 200
    return {"status": "ok"}


@app.post(
    "/sentiment/analyze_sentiment", 
    response_model= SentimentResponse, 
    summary= "Analyze Sentiment", 
    description="Analyze the sentiment of the provided text."
    )
async def analyze_sentiment(input: TextInput):
    text_chunks = model.chunk_text(input.text)
    
    results = []
    weights = []
    total_weight = 0

    for chunk in text_chunks:
        sentiment_result = model.predict_sentiment(chunk)

        results.append(sentiment_result)
        
        chunk_weight = len(chunk['input_ids'][0])
        weights.append(chunk_weight)
        total_weight += chunk_weight


    # print("results", results)
    # print("weights", weights)
    # print("total_weight", total_weight)
    
    # sentiment_results = sum(weight/total_weight * output for weight, output in zip(weights, results))
    # sentiment_results = sentiment_results.tolist()

    sentiment_results = [0, 0, 0]

    # Calculate weighted sentiment scores
    for weight, output in zip(weights, results):
        for i in range(len(sentiment_results)):
            sentiment_results[i] += weight / total_weight * output[i]


    sentiment_dict = {
        "positive": sentiment_results[2],
        "negative": sentiment_results[0],
        "neutral": sentiment_results[1]
    }

    return {
        "sentiment_result": sentiment_dict
    }

if __name__ == '__main__':
    app.run(debug=True)