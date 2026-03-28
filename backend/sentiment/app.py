from fastapi import FastAPI
from api_models import TextInput, SentimentResponse
from model import sentiment_model
from utils.text_preprocessing import preprocess_article_text, deduplicate_sentences
import re

app = FastAPI(
    title="Sentiment Analysis API",
    description="API for analyzing sentiment of text using a pre-trained model.",
    version="2.1.0"
)

model = sentiment_model()

NEUTRAL_THRESHOLD = 0.10
MAX_SENTENCES = 50


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

    if not sentences:
        return {
            "sentiment_result": {
                "positive": 0.0,
                "negative": 0.0,
                "neutral": 1.0,
                "sentence_sentiments": [],
            },
            "sentence_sentiments": [],
        }

    # Step 3: ONE batch call for ALL sentences instead of 30 sequential calls
    # This is the main speed improvement — 30x fewer model invocations
    all_scores = model.predict_sentiment_batch_sentences(sentences)

    sentence_results = []
    agg_pos, agg_neg, agg_neu = 0.0, 0.0, 0.0

    for i, sent in enumerate(sentences):
        scores = all_scores[i]
        neg_s = float(scores[0])
        neu_s = float(scores[1])
        pos_s = float(scores[2])

        if abs(pos_s - neg_s) < NEUTRAL_THRESHOLD:
            label = "neutral"
        elif pos_s >= neg_s:
            label = "positive"
        else:
            label = "negative"

        sentence_results.append({
            "sentence": sent,
            "label": label,
            "positive": round(pos_s, 4),
            "negative": round(neg_s, 4),
            "neutral":  round(neu_s, 4),
        })

        agg_pos += pos_s
        agg_neg += neg_s
        agg_neu += neu_s

    # Step 4: Deduplicate results AFTER model runs
    sentence_results = deduplicate_sentences(sentence_results)
    for s in sentence_results:
        s['sentence'] = fix_tokenizer_splits(s['sentence'])

    total_scored = len(sentence_results)
    sentiment_dict = {
        "positive": round(float(agg_pos / total_scored), 4),
        "negative": round(float(agg_neg / total_scored), 4),
        "neutral":  round(float(agg_neu / total_scored), 4),
        "sentence_sentiments": sentence_results,
    }

    return {
        "sentiment_result": sentiment_dict,
        "sentence_sentiments": sentence_results,
    }

def fix_tokenizer_splits(text: str) -> str:
    """Fix common RoBERTa tokenizer artifacts in reconstructed sentences."""
    # Fix split proper nouns and place names
    fixes = [
        (r'La\s+Guardia', 'LaGuardia'),
        (r'Mc\s+([A-Z])', r'Mc\1'),  # McDonald's etc
        (r'O\s+\'\s+([A-Z])', r"O'\1"),  # O'Brien etc
    ]
    for pattern, replacement in fixes:
        text = re.sub(pattern, replacement, text)
    return text

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8012)