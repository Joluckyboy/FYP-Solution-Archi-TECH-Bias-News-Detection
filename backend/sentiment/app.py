from fastapi import FastAPI
from api_models import TextInput, SentimentResponse
from model import sentiment_model
from utils.text_preprocessing import preprocess_article_text, deduplicate_sentences
import re

app = FastAPI(
    title="Sentiment Analysis API",
    description="API for analyzing sentiment of text using a pre-trained model.",
    version="2.0.0"
)

model = sentiment_model()

NEUTRAL_THRESHOLD = 0.10
MAX_SENTENCES = 30 


@app.get("/")
async def health_check():
    return {"status": "ok"}


@app.get("/sentiment")
def health_check2():
    return {"status": "ok"}


@app.post("/sentiment/analyze_sentiment", response_model=SentimentResponse)
async def analyze_sentiment(input: TextInput):
    # Step 1: Clean raw text BEFORE splitting into sentences
    clean_text = preprocess_article_text(input.text)
    
    # Step 2: Split into sentences
    sentences = [
        s.strip()
        for s in re.split(r'(?<=[.!?])\s+', clean_text)
        if s.strip()
    ]
    sentences = sentences[:MAX_SENTENCES]

    sentence_results = []
    agg_pos, agg_neg, agg_neu = 0.0, 0.0, 0.0
    total_scored = 0

    for sent in sentences:
        chunks = model.chunk_text(sent)
        if not chunks:
            continue

        # OPTIMIZATION: Batch process all chunks at once instead of one-by-one
        if len(chunks) == 1:
            # Single chunk - use original method
            scores = model.predict_sentiment(chunks[0])
            pos_s = float(scores[2])
            neg_s = float(scores[0])
            neu_s = float(scores[1])
        else:
            # Multiple chunks - use batch processing
            batch_scores = model.predict_sentiment_batch(chunks)
            chunk_weights = [len(chunk['input_ids'][0]) for chunk in chunks]
            total_chunk_weight = sum(chunk_weights)
            
            pos_s = sum(float(batch_scores[i][2]) * chunk_weights[i] for i in range(len(chunks))) / total_chunk_weight
            neg_s = sum(float(batch_scores[i][0]) * chunk_weights[i] for i in range(len(chunks))) / total_chunk_weight
            neu_s = sum(float(batch_scores[i][1]) * chunk_weights[i] for i in range(len(chunks))) / total_chunk_weight

        if abs(pos_s - neg_s) < NEUTRAL_THRESHOLD:
            label = "neutral"
        elif pos_s >= neg_s:
            label = "positive"
        else:
            label = "negative"

        sentence_results.append({
            "sentence": sent,
            "label": label,
            # round(float(...)) — double safety: convert then round
            "positive": round(float(pos_s), 4),
            "negative": round(float(neg_s), 4),
            "neutral":  round(float(neu_s), 4),
        })

        agg_pos += pos_s
        agg_neg += neg_s
        agg_neu += neu_s
        total_scored += 1

    # Step 3: Deduplicate results AFTER model runs
    sentence_results = deduplicate_sentences(sentence_results)

    if total_scored > 0:
        sentiment_dict = {
            "positive": round(float(agg_pos / total_scored), 4),
            "negative": round(float(agg_neg / total_scored), 4),
            "neutral":  round(float(agg_neu / total_scored), 4),
            "sentence_sentiments": sentence_results,
        }
    else:
        sentiment_dict = {
            "positive": 0.0,
            "negative": 0.0,
            "neutral":  1.0,
            "sentence_sentiments": [],
        }

    return {
        "sentiment_result": sentiment_dict,
        "sentence_sentiments": sentence_results,
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)