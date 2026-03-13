from fastapi import FastAPI
from pydantic import BaseModel
import re
import math
import concurrent.futures

from methods import predict, hybrid_aggregation
from api_models import TextInput, EmotionResponse
from model import emotion_model

app = FastAPI(title="Emotion Analysis API", version="2.2.0")
model = emotion_model()

THRESHOLD             = 0.02
MAX_SECTIONS          = 8
SENTENCES_PER_SECTION = 5
MAX_WORKERS           = 4
MAX_SENTENCES         = 40


@app.get("/")
def health_check():
    return {"status": "ok"}

@app.get("/emotion")
def health_check2():
    return {"status": "ok"}


def _split_into_sections(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) < 2:
        sentences  = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        paragraphs = [
            ' '.join(sentences[i:i + SENTENCES_PER_SECTION])
            for i in range(0, len(sentences), SENTENCES_PER_SECTION)
        ]
    if len(paragraphs) > MAX_SECTIONS:
        chunk_size = math.ceil(len(paragraphs) / MAX_SECTIONS)
        paragraphs = [
            ' '.join(paragraphs[i:i + chunk_size])
            for i in range(0, len(paragraphs), chunk_size)
        ][:MAX_SECTIONS]
    return paragraphs


def _analyze_section(args: tuple) -> dict | None:
    i, para = args
    if not para.strip():
        return None
    chunks  = model.chunk_text(para)
    weights = [len(c) for c in chunks]
    try:
        results = predict(chunks, model.tokenizer, model.classifier)
        avg, _  = hybrid_aggregation(results, weights)
    except Exception:
        return None

    filtered = {k: v for k, v in avg.items() if v >= THRESHOLD}
    if not filtered:
        dom, score = "neutral", 0.0
    else:
        dom   = max(filtered, key=filtered.get)
        score = filtered[dom]

    return {
        "section":          i + 1,
        "preview":          para[:60] + ("..." if len(para) > 60 else ""),
        "dominant_emotion": dom,
        "score":            round(score, 4),
    }


def _analyze_sentence(args: tuple) -> dict | None:
    """
    Analyse one sentence and return:
    - dominant emotion + score (as before)
    - top_emotions: top 3 emotions with scores (NEW)
      Allows frontend to find example sentences for non-dominant emotions
      e.g. Annoyance may never be dominant but appears in top 3 of several sentences
    """
    _, sentence = args
    sentence = sentence.strip()
    if not sentence or len(sentence.split()) < 6:
        return None

    chunks  = model.chunk_text(sentence)
    weights = [len(c) for c in chunks]
    try:
        results = predict(chunks, model.tokenizer, model.classifier)
        avg, _  = hybrid_aggregation(results, weights)
    except Exception:
        return None

    filtered = {k: round(float(v), 4) for k, v in avg.items() if v >= THRESHOLD}
    if not filtered:
        return None

    dom   = max(filtered, key=filtered.get)
    score = filtered[dom]

    # Skip overwhelmingly neutral — not useful as evidence for the reader
    if dom == "neutral" and score > 0.80:
        return None

    # ── NEW: top 3 emotions sorted by score ───────────────────────────────
    # This lets the frontend find example sentences for any emotion,
    # even if it wasn't the dominant one for any single sentence.
    top_emotions = sorted(
        [{"label": k, "score": v} for k, v in filtered.items()],
        key=lambda x: x["score"],
        reverse=True
    )[:3]

    return {
        "sentence":    sentence,
        "dominant":    dom,
        "score":       round(float(score), 4),
        "top_emotions": top_emotions,   # ← NEW
    }


@app.post("/emotion/analyze_emotion", response_model=EmotionResponse)
async def analyze_emotion(input: TextInput):

    # ── 1. Full-text weighted average ──────────────────────────────────────
    text_chunks = model.chunk_text(input.text)
    weights     = [len(c) for c in text_chunks]
    results     = predict(text_chunks, model.tokenizer, model.classifier)
    weighted_avg, majority_vote = hybrid_aggregation(results, weights)

    # ── 2. Dominant emotion ────────────────────────────────────────────────
    filtered = {k: v for k, v in weighted_avg.items() if v >= THRESHOLD}
    if filtered:
        dominant_emotion = max(filtered, key=filtered.get)
        dominant_score   = filtered[dominant_emotion]
    else:
        dominant_emotion = "neutral"
        dominant_score   = 0.0

    # ── 3. Section analysis ────────────────────────────────────────────────
    sections = _split_into_sections(input.text)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        section_results  = list(ex.map(_analyze_section, enumerate(sections)))
    section_emotions = [r for r in section_results if r is not None]

    # ── 4. Sentence-level analysis ─────────────────────────────────────────
    sentences = [
        s.strip()
        for s in re.split(r'(?<=[.!?])\s+', input.text)
        if s.strip()
    ][:MAX_SENTENCES]

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        sent_results = list(ex.map(_analyze_sentence, enumerate(sentences)))
    sentence_emotions = [r for r in sent_results if r is not None]

    # ── 5. Return ──────────────────────────────────────────────────────────
    return {
        "emotion_result": {
            "weighted_avg":      weighted_avg,
            "majority_vote":     majority_vote,
            "dominant_emotion":  dominant_emotion,
            "dominant_score":    round(float(dominant_score), 4),
            "section_emotions":  section_emotions,
            "sentence_emotions": sentence_emotions,
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013)