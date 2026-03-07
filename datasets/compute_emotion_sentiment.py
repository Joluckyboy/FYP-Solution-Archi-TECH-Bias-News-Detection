import csv
import json
import time
import requests
import pandas as pd

SENTIMENT_URL = "http://localhost:8012/sentiment/analyze_sentiment"
EMOTION_URL   = "http://localhost:8013/emotion/analyze_emotion"

INPUT_CSV  = "Kaggle News Articles For Political Bias Classification.csv"
OUTPUT_CSV = "news_with_model_scores.csv"

def call_sentiment_api(text: str) -> dict:
    payload = {"text": text}
    resp = requests.post(SENTIMENT_URL, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data.get("sentiment_result", {})

def call_emotion_api(text: str) -> dict:
    payload = {"text": text}
    resp = requests.post(EMOTION_URL, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data.get("emotion_result", {})

def main():
    df = pd.read_csv(INPUT_CSV)

    if "page_text" not in df.columns:
        raise ValueError("CSV must have a 'page_text' column")

    sentiment_results = []
    emotion_weighted = []
    emotion_majority = []

    for idx, row in df.iterrows():
        text = str(row["page_text"])

        if not text.strip():
            sentiment_results.append({})
            emotion_weighted.append({})
            emotion_majority.append("")
            continue

        try:
            s = call_sentiment_api(text)
            e = call_emotion_api(text)

            sentiment_results.append(s)
            emotion_weighted.append(e.get("weighted_avg", {}))
            emotion_majority.append(e.get("majority_vote", ""))

        except Exception as ex:
            print(f"Row {idx}: error {ex}")
            sentiment_results.append({})
            emotion_weighted.append({})
            emotion_majority.append("")
            time.sleep(0.5)

        if (idx + 1) % 50 == 0:
            print(f"Processed {idx + 1} rows")

    df["sentiment_result_json"] = [json.dumps(x) for x in sentiment_results]
    df["emotion_weighted_json"] = [json.dumps(x) for x in emotion_weighted]
    df["emotion_majority"]      = emotion_majority

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved enriched CSV to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
